"""
应付对账批次步骤：
- record_payable_account    financePayList（取 amount_list）→ orderPayAccountEdit（发起对账批次）
- confirm_payable_account   payAccountPage（验证批次状态）→ accountConfirm（确认应付对账）
- record_payable_invoice_apply
                          financePayList(开票) → getOrderInfoByFeeId → batchOrderEdit(submit)

LK19 = LK18 + 发起应付对账批次。
LK20 = LK19 + 确认应付对账。
LK21 = LK20 + 发起应付开票批次申请（apply_type=2，submit 即生效，无需审批）。
"""
from typing import Any, Dict

import allure

from api.pay.payable_api import PayableApi
from data.pay import PayableAccountData


def record_payable_account(
    bl_no: str,
) -> Dict[str, Any]:
    """
    发起应付对账批次（financePayList → orderPayAccountEdit）

    该步骤复用 link18 产生的 bl_no，不生成新提单号。

    流程：
      1. financePayList - 按提单号查询应付项列表（提取 amount_list，含 order_fee_real_id）
      2. orderPayAccountEdit - 发起应付对账批次（提交 select_list）

    Args:
        bl_no: 提单号（来自上游 link18 结果）

    Returns:
        {
            'bl_no': str,
            'pay_list_resp': Response,
            'pay_list_data': dict,
            'select_list': [...],           # 来自 financePayList.data.data
            'amount_list_flat': [...],     # 扁平化的 amount_list（含 order_fee_real_id）
            'submit_resp': Response,
            'submit_data': dict,
            'pay_account_id': str,
            'pay_account_no': str,
            'steps': [...],
        }
    """
    result: Dict[str, Any] = {
        "bl_no": bl_no,
        "steps": [],
    }

    # Step 1: financePayList - 查询应付项列表（重试 3 次，等后端同步应付数据）
    with allure.step('查询应付项列表（financePayList，重试最多 3 次）'):
        for attempt in range(1, 4):
            pay_list_resp = PayableApi.query_finance_pay_list(bl_no=bl_no)
            pay_list_data = pay_list_resp.json()
            result['pay_list_resp'] = pay_list_resp
            result['pay_list_data'] = pay_list_data
            result['steps'].append({
                'name': '查询应付项列表',
                'code': pay_list_data.get('code'),
                'msg': pay_list_data.get('msg'),
            })

            assert pay_list_resp.status_code == 200, (
                f'HTTP 状态码异常: {pay_list_resp.status_code}'
            )
            assert pay_list_data.get('code') == 200, (
                f'financePayList 查询失败: {pay_list_data}'
            )

            records = pay_list_data.get('data', {}).get('data', [])
            if records:
                break
            if attempt < 3:
                import time as _time
                _time.sleep(2)
                result['steps'].pop()

    # 从响应构建 select_list（与应收对账 build_select_list 逻辑一致）
    records = pay_list_data.get('data', {}).get('data', [])
    if not records:
        raise AssertionError(
            f'financePayList 查询到 bl_no={bl_no} 但 data=[]（重试 3 次后仍为空），'
            f'可能应付数据尚未同步: {pay_list_data}'
        )
    select_list = PayableAccountData.build_select_list_from_pay_list(
        pay_list_data.get('data', {})
    )
    result['select_list'] = select_list

    # 扁平化 amount_list，提取所有 order_fee_real_id 用于断言
    amount_list_flat = []
    for record in select_list:
        amount_list_flat.extend(record.get("amount_list", []))
    result['amount_list_flat'] = amount_list_flat

    if not select_list:
        raise AssertionError(
            f'financePayList 响应中未提取到 select_list，无法发起应付对账: {pay_list_data}'
        )

    # Step 2: orderPayAccountEdit - 发起应付对账批次
    with allure.step('发起应付对账批次（orderPayAccountEdit）'):
        submit_resp = PayableApi.submit_pay_account(
            select_list=select_list,
        )
        submit_data = submit_resp.json()
        result['submit_resp'] = submit_resp
        result['submit_data'] = submit_data

        submit_data_inner = submit_data.get('data', {})
        result['pay_account_id'] = submit_data_inner.get('pay_account_id', '')
        result['pay_account_no'] = submit_data_inner.get('pay_account_no', '')

        result['steps'].append({
            'name': '发起应付对账批次',
            'code': submit_data.get('code'),
            'msg': submit_data.get('msg'),
            'pay_account_id': result['pay_account_id'],
            'pay_account_no': result['pay_account_no'],
        })

        assert submit_resp.status_code == 200, (
            f'HTTP 状态码异常: {submit_resp.status_code}'
        )
        assert submit_data.get('code') == 200, (
            f'orderPayAccountEdit 失败: {submit_data}'
        )

    return result


def confirm_payable_account(
    bl_no: str,
    pay_account_id: str = None,
) -> Dict[str, Any]:
    """
    确认应付对账（payAccountPage → accountConfirm）

    该步骤复用 link19 产生的 bl_no 和 pay_account_id。

    流程：
      1. payAccountPage - 按 bl_no 查询应付对账批次（验证状态，提取 pay_account_id）
      2. accountConfirm - 确认应付对账

    Args:
        bl_no          : 提单号（来自上游 link19 结果）
        pay_account_id : 应付对账批次ID（优先使用外部传入值，否则从 payAccountPage 响应提取）

    Returns:
        {
            'bl_no': str,
            'pay_account_page_resp': Response,
            'pay_account_page_data': dict,
            'pay_account_id': str,      # 优先用外部传入，兜底从响应提取
            'pay_account_no': str,
            'confirm_resp': Response,
            'confirm_data': dict,
            'steps': [...],
        }
    """
    result: Dict[str, Any] = {
        "bl_no": bl_no,
        "steps": [],
    }

    # Step 1: payAccountPage - 查询应付对账批次（重试 3 次，等后端处理）
    with allure.step('查询应付对账批次（payAccountPage，重试最多 3 次）'):
        for attempt in range(1, 4):
            page_resp = PayableApi.query_pay_account_page(bl_no=bl_no)
            page_data = page_resp.json()
            result['pay_account_page_resp'] = page_resp
            result['pay_account_page_data'] = page_data
            result['steps'].append({
                'name': '查询应付对账批次',
                'code': page_data.get('code'),
                'msg': page_data.get('msg'),
            })

            assert page_resp.status_code == 200, (
                f'HTTP 状态码异常: {page_resp.status_code}'
            )
            assert page_data.get('code') == 200, (
                f'payAccountPage 查询失败: {page_data}'
            )

            records = page_data.get('data', {}).get('data', [])
            if records:
                break
            if attempt < 3:
                import time as _time
                _time.sleep(2)
                result['steps'].pop()

    records = page_data.get('data', {}).get('data', [])
    if not records:
        raise AssertionError(
            f'payAccountPage 查询到 bl_no={bl_no} 但 data=[]（重试 3 次后仍为空），'
            f'应付对账批次可能尚未创建: {page_data}'
        )

    first_record = records[0]
    resolved_pay_account_id = (
        str(pay_account_id) if pay_account_id
        else str(first_record.get('pay_account_id', ''))
    )
    resolved_pay_account_no = str(first_record.get('pay_account_no', ''))

    result['pay_account_id'] = resolved_pay_account_id
    result['pay_account_no'] = resolved_pay_account_no

    if not resolved_pay_account_id:
        raise AssertionError(
            f'payAccountPage 响应中无法提取 pay_account_id: {first_record}'
        )

    # Step 2: accountConfirm - 确认应付对账
    with allure.step('确认应付对账（accountConfirm）'):
        confirm_resp = PayableApi.confirm_pay_account(
            pay_account_id=resolved_pay_account_id,
        )
        confirm_data = confirm_resp.json()
        result['confirm_resp'] = confirm_resp
        result['confirm_data'] = confirm_data
        result['steps'].append({
            'name': '确认应付对账',
            'code': confirm_data.get('code'),
            'msg': confirm_data.get('msg'),
            'pay_account_id': resolved_pay_account_id,
            'pay_account_no': resolved_pay_account_no,
        })

        assert confirm_resp.status_code == 200, (
            f'HTTP 状态码异常: {confirm_resp.status_code}'
        )
        assert confirm_data.get('code') == 200, (
            f'accountConfirm 失败: {confirm_data}'
        )
        assert confirm_data.get('msg') == '成功', (
            f'accountConfirm msg 不为"成功": {confirm_data.get("msg")}'
        )

    return result


def record_payable_invoice_apply(
    bl_no: str,
    main_id: str = None,
    main_name: str = None,
    pay_settle_object: str = None,
    pay_settle_object_id: str = None,
) -> Dict[str, Any]:
    """
    发起应付开票批次申请（financePayList 开票模式 → getOrderInfoByFeeId → batchOrderEdit submit）

    该步骤复用 link20 产生的 bl_no。

    流程：
      1. financePayList（开票模式）  - 按 bl_no 查询应付开票项（提取 order_fee_real_id / amount_list）
      2. getOrderInfoByFeeId         - 按 order_fee_real_id 列表查询开票订单详情
      3. batchOrderEdit(submit)      - 提交应付开票批次申请（apply_type=2，submit 即生效）

    与 link15 发起应收开票批次的区别：
      - 应付方向 submit 后直接生效，无 link16 等价审核步骤
      - seller 是 book_supplier（应付方），purchaser 是 main（应收方主体）
      - 提交成功即可用于 link22 应付开票登记

    Args:
        bl_no               : 提单号（来自上游 link20 结果）
        main_id             : 主体ID（优先取上游 confirm_payable_result / payable_account_result，
                             兜底使用 confirm_payable_account.yaml 配置）
        main_name           : 主体名称
        pay_settle_object   : 付款结算对象名称
        pay_settle_object_id: 付款结算对象ID

    Returns:
        {
            'bl_no': str,
            'pay_list_invoice_resp': Response,
            'pay_list_invoice_data': dict,
            'order_info_resp': Response,
            'order_info_data': dict,
            'order_info_records': [...],
            'submit_resp': Response,
            'submit_data': dict,
            'cost_usd': str,
            'pay_settle_object': str,
            'pay_settle_object_id': str,
            'main_id': str,
            'main_name': str,
            'steps': [...],
        }
    """
    result: Dict[str, Any] = {
        "bl_no": bl_no,
        "steps": [],
    }

    # Step 1: financePayList（开票模式） - 查询应付开票项列表
    # main_id / pay_settle_object_id / pay_settle_object 优先从上游拿，
    # 拿不到时由 data 层从 YAML 默认值兜底（都没有则抛 AssertionError）

    # main_id / main_name / pay_settle_object(_id) 解析：
    #   优先级：入参 > 上游 confirm_payable_result > 上游 payable_account_result > YAML 默认值
    resolved_main_id = main_id
    resolved_main_name = main_name
    resolved_pay_settle_object = pay_settle_object
    resolved_pay_settle_object_id = pay_settle_object_id

    with allure.step('查询应付开票项列表（financePayList 开票模式）'):
        pay_list_resp = PayableApi.query_finance_pay_list_for_invoice(
            bl_no=bl_no,
            main_id=resolved_main_id,
            pay_settle_object_id=resolved_pay_settle_object_id,
            pay_settle_object=resolved_pay_settle_object,
        )
        pay_list_data = pay_list_resp.json()
        result['pay_list_invoice_resp'] = pay_list_resp
        result['pay_list_invoice_data'] = pay_list_data
        result['steps'].append({
            'name': '查询应付开票项列表',
            'code': pay_list_data.get('code'),
            'msg': pay_list_data.get('msg'),
        })

        assert pay_list_resp.status_code == 200, (
            f'HTTP 状态码异常: {pay_list_resp.status_code}'
        )
        assert pay_list_data.get('code') == 200, (
            f'financePayList（开票模式）查询失败: {pay_list_data}'
        )
        assert pay_list_data.get('msg') == '成功', (
            f'financePayList（开票模式）msg 不为"成功": {pay_list_data.get("msg")}'
        )

    pay_records = pay_list_data.get('data', {}).get('data', []) or []
    if not pay_records:
        raise AssertionError(
            f'financePayList（开票模式）未找到 bl_no={bl_no} 的应付开票项: {pay_list_data}'
        )

    # 提取 amount_list，扁平化得到 order_fee_real_id 列表
    amount_list_flat: List[Dict[str, Any]] = []
    for record in pay_records:
        amount_list_flat.extend(record.get('amount_list', []) or [])

    order_fee_real_ids = [
        str(item.get('order_fee_real_id', ''))
        for item in amount_list_flat
        if item.get('order_fee_real_id')
    ]
    if not order_fee_real_ids:
        raise AssertionError(
            f'financePayList（开票模式）响应中 amount_list 为空，'
            f'无法提取 order_fee_real_id: {pay_list_data}'
        )

    # 兜底 main_id / main_name / pay_settle_object(_id)
    first_record = pay_records[0]
    if not resolved_main_id:
        resolved_main_id = str(first_record.get('main_id', ''))
    if not resolved_main_name:
        resolved_main_name = first_record.get('main_name', '')
    if not resolved_pay_settle_object:
        resolved_pay_settle_object = first_record.get('pay_settle_object', '')
    if not resolved_pay_settle_object_id:
        resolved_pay_settle_object_id = str(first_record.get('pay_settle_object_id', ''))

    if not resolved_main_id:
        raise AssertionError(
            f'无法从 financePayList 响应中提取 main_id，无法发起应付开票: {pay_list_data}'
        )

    result['main_id'] = resolved_main_id
    result['main_name'] = resolved_main_name
    result['pay_settle_object'] = resolved_pay_settle_object
    result['pay_settle_object_id'] = resolved_pay_settle_object_id

    # 检查 amount_list 规模：开票模式理应只返回单个 sup/sub 对应的费用，
    # 若返回多个 fee 极可能是 main_id / pay_settle_object_id 未传入导致的全量返回
    fee_count = len(order_fee_real_ids)
    if fee_count > 1:
        import logging as _logging
        _logging.warning(
            f'financePayList（开票模式）返回了 {fee_count} 个 order_fee_real_id，'
            f'建议检查 main_id={resolved_main_id} / '
            f'pay_settle_object_id={resolved_pay_settle_object_id} 是否正确传递，'
            f'避免后续 batchOrderEdit 406。'
        )

    # Step 2: getOrderInfoByFeeId - 查询开票订单详情
    with allure.step('查询开票订单详情（getOrderInfoByFeeId）'):
        order_info_resp = PayableApi.get_order_info_by_fee_id(
            order_fee_real_ids=order_fee_real_ids,
        )
        order_info_data = order_info_resp.json()
        result['order_info_resp'] = order_info_resp
        result['order_info_data'] = order_info_data
        result['order_info_records'] = order_info_data.get('data', []) or []
        result['steps'].append({
            'name': '查询开票订单详情',
            'code': order_info_data.get('code'),
            'msg': order_info_data.get('msg'),
            'record_count': len(result['order_info_records']),
        })

        assert order_info_resp.status_code == 200, (
            f'HTTP 状态码异常: {order_info_resp.status_code}'
        )
        assert order_info_data.get('code') == 200, (
            f'getOrderInfoByFeeId 失败: {order_info_data}'
        )
        assert order_info_data.get('msg') == '成功', (
            f'getOrderInfoByFeeId msg 不为"成功": {order_info_data.get("msg")}'
        )

    if not result['order_info_records']:
        raise AssertionError(
            f'getOrderInfoByFeeId 返回 data=[]，无法发起应付开票: {order_info_data}'
        )

    # 总额合计（USD）
    amount_total_usd = 0.0
    for item in result['order_info_records']:
        try:
            amount_total_usd += float(item.get('real_amount', 0) or 0)
        except (TypeError, ValueError):
            pass
    amount_total_usd = round(amount_total_usd, 2)
    result['cost_usd'] = f"{amount_total_usd:.2f}"

    # Step 3: batchOrderEdit(submit) - 发起应付开票批次申请
    # 服务端校验时可能发现费用状态发生变化（其他批次已占用/核销），
    # 此时会返回 code=406 + data[] 内含 useAction='change' 的最新 amount_list，
    # 采用最新 amount_list 重试提交可成功。
    last_submit_data: Dict[str, Any] = {}
    for attempt in range(1, 4):
        with allure.step(f'发起应付开票批次申请（batchOrderEdit submit，第 {attempt} 次）'):
            submit_resp = PayableApi.submit_pay_invoice_batch(
                order_info_data_list=result['order_info_records'],
                finance_pay_records=pay_records,
                main_id=resolved_main_id,
                main_name=resolved_main_name,
                pay_settle_object=resolved_pay_settle_object,
                pay_settle_object_id=resolved_pay_settle_object_id,
            )
            submit_data = submit_resp.json()
            result['submit_resp'] = submit_resp
            result['submit_data'] = submit_data
            result['steps'].append({
                'name': '发起应付开票批次申请',
                'code': submit_data.get('code'),
                'msg': submit_data.get('msg'),
                'main_id': resolved_main_id,
                'pay_settle_object': resolved_pay_settle_object,
                'cost_usd': result['cost_usd'],
                'attempt': attempt,
            })

            assert submit_resp.status_code == 200, (
                f'HTTP 状态码异常: {submit_resp.status_code}'
            )

            # 成功：跳出重试循环
            if submit_data.get('code') == 200:
                assert submit_data.get('msg') == '成功', (
                    f'batchOrderEdit（应付开票）msg 不为"成功": {submit_data.get("msg")}'
                )
                last_submit_data = submit_data
                break

            # 失败：尝试从 406 响应中提取最新 amount_list 重试
            if submit_data.get('code') == 406:
                data_list = submit_data.get('data', []) or []
                change_items = [d for d in data_list if d.get('useAction') == 'change']
                if change_items:
                    import time as _time
                    _time.sleep(1)
                    new_fee_records: List[Dict[str, Any]] = []
                    for item in change_items:
                        new_fee_records.extend(item.get('amount_list', []) or [])
                    if new_fee_records:
                        result['order_info_records'] = new_fee_records
                        result['cost_usd'] = f"{sum(float(r.get('real_amount', 0) or 0) for r in new_fee_records):.2f}"
                        continue
                raise AssertionError(
                    f'batchOrderEdit（应付开票）406 错误且无可用 change 数据: {submit_data}'
                )

            # 其他错误：直接断言失败
            raise AssertionError(
                f'batchOrderEdit（应付开票）失败: {submit_data}'
            )
    else:
        raise AssertionError(
            f'batchOrderEdit（应付开票）3 次重试后仍未成功: {last_submit_data}'
        )

    return result


def record_payable_invoice_upload(
    bl_no: str,
    invoice_number: str = None,
    invoice_amount: str = None,
    buyer_chinese_header: str = None,
    buyer_identifier_no: str = None,
    seller_chinese_header: str = None,
    seller_identifier_no: str = None,
) -> Dict[str, Any]:
    """
    应付发票上传与登记（LK22）

    流程：uploadFile（Step 1）→ invoiceAdd（Step 2）→ applyPage（Step 3）→ allocationInvoiceFee（Step 4）

    Step 1 uploadFile：从 YAML 配置读取发票文件名，自动拼接完整路径上传，
                       响应含 file_id/file_name/file_url 供 Step 2 使用。

    Step 2 invoiceAdd：使用 Step 1 响应 + 上游 link21 响应数据构造发票登记请求体，
                        invoice_number 必须唯一（调用方生成或自动生成）。

    Step 3 applyPage：按 bl_nos 查询应付开票申请ID，提取 pay_invoice_apply_id。

    Step 4 allocationInvoiceFee：pay_invoice_id 来自 Step 2，pay_invoice_apply_id 来自 Step 3。

    Args:
        bl_no                  : 提单号（链路中传递）
        invoice_number         : 发票号码（可选，默认自动生成唯一值）
        invoice_amount        : 发票金额（默认从 YAML 读取）
        buyer_chinese_header  : 购买方名称（默认从 YAML 读取）
        buyer_identifier_no   : 购买方税号（默认从 YAML 读取）
        seller_chinese_header : 销售方名称（默认从 YAML 读取）
        seller_identifier_no  : 销售方税号（默认从 YAML 读取）

    Returns:
        {
            'bl_no': str,
            'upload_resp' / 'upload_data' / 'uploaded_file_info': ...,
            'add_resp' / 'add_data' / 'pay_invoice_id' / 'invoice_number': ...,
            'apply_page_resp' / 'apply_page_data' / 'pay_invoice_apply_id': ...,
            'alloc_resp' / 'alloc_data': ...,
            'steps': [...],
        }
    """
    result: Dict[str, Any] = {"bl_no": bl_no, "steps": []}

    # Step 1: uploadFile - 上传发票文件
    with allure.step('上传应付发票文件（uploadFile）'):
        from data.pay import PayableInvoiceUploadData

        invoice_file_path = PayableInvoiceUploadData.get_invoice_file_path()
        upload_resp = PayableApi.upload_pay_invoice_file(file_path=invoice_file_path)
        upload_data = upload_resp.json()
        result['upload_resp'] = upload_resp
        result['upload_data'] = upload_data
        uploaded_file_info = upload_data.get("data", {}) or {}
        result['uploaded_file_info'] = uploaded_file_info
        result['steps'].append({
            'name': '上传应付发票文件',
            'code': upload_data.get('code'),
            'msg': upload_data.get('msg'),
            'file_id': uploaded_file_info.get('file_id'),
            'file_name': uploaded_file_info.get('file_name'),
            'file_url': uploaded_file_info.get('file_url'),
            'file_type': uploaded_file_info.get('file_type'),
            'original_name': uploaded_file_info.get('original_name'),
        })

        assert upload_resp.status_code == 200, (
            f'uploadFile HTTP 状态码异常: {upload_resp.status_code}'
        )
        assert upload_data.get('code') == 200, (
            f'uploadFile 失败: {upload_data}'
        )
        if not uploaded_file_info.get('file_id'):
            raise AssertionError(f'uploadFile 响应中未找到 file_id: {upload_data}')

    # Step 2: invoiceAdd - 登记应付发票
    if invoice_number is None:
        invoice_number = _generate_unique_invoice_number(prefix="PAY_INV")
    if invoice_amount is None:
        invoice_amount = "1260"

    with allure.step('登记应付发票（invoiceAdd）'):
        add_resp = PayableApi.invoice_add(
            file_id=uploaded_file_info.get('file_id', ''),
            file_name=uploaded_file_info.get('file_name', ''),
            file_url=uploaded_file_info.get('file_url', ''),
            original_name=uploaded_file_info.get('original_name', ''),
            invoice_number=invoice_number,
            invoice_amount=invoice_amount,
            buyer_chinese_header=buyer_chinese_header,
            buyer_identifier_no=buyer_identifier_no,
            seller_chinese_header=seller_chinese_header,
            seller_identifier_no=seller_identifier_no,
        )
        add_data = add_resp.json()
        result['add_resp'] = add_resp
        result['add_data'] = add_data
        result['invoice_number'] = invoice_number

        add_data_inner = add_data.get("data", {}) or {}
        # 响应格式：data = {invoice_number: pay_invoice_id}
        pay_invoice_id = str(
            add_data_inner.get(invoice_number)
            or ""
        )
        result['pay_invoice_id'] = pay_invoice_id

        result['steps'].append({
            'name': '登记应付发票',
            'code': add_data.get('code'),
            'msg': add_data.get('msg'),
            'invoice_number': invoice_number,
            'pay_invoice_id': pay_invoice_id,
        })

        assert add_resp.status_code == 200, (
            f'invoiceAdd HTTP 状态码异常: {add_resp.status_code}'
        )
        assert add_data.get('code') == 200, (
            f'invoiceAdd 失败: {add_data}'
        )
        if not pay_invoice_id:
            raise AssertionError(f'invoiceAdd 响应中未找到 pay_invoice_id: {add_data}')

    # Step 3: applyPage - 按 bl_nos 查询应付开票申请ID
    with allure.step('查询应付开票申请ID（applyPage）'):
        apply_resp = PayableApi.apply_page(bl_nos=[bl_no])
        apply_data = apply_resp.json()
        result['apply_page_resp'] = apply_resp
        result['apply_page_data'] = apply_data

        records = apply_data.get("data", {}).get("data", []) or []
        first_record = records[0] if records else {}
        pay_invoice_apply_id = str(
            first_record.get("pay_invoice_apply_id") or ""
        )
        # 从 applyPage 记录中取未分配金额，供 Step 4 使用
        un_amount = (
            first_record.get("invoice_unused_amount")
            or first_record.get("un_writeoff_amount")
            or invoice_amount
        )
        result['pay_invoice_apply_id'] = pay_invoice_apply_id
        result['un_amount'] = un_amount

        result['steps'].append({
            'name': '查询应付开票申请ID',
            'code': apply_data.get('code'),
            'msg': apply_data.get('msg'),
            'pay_invoice_apply_id': pay_invoice_apply_id,
            'un_amount': un_amount,
            'record_count': len(records),
        })

        assert apply_resp.status_code == 200, (
            f'applyPage HTTP 状态码异常: {apply_resp.status_code}'
        )
        assert apply_data.get('code') == 200, (
            f'applyPage 失败: {apply_data}'
        )
        if not pay_invoice_apply_id:
            raise AssertionError(f'applyPage 响应中未找到 pay_invoice_apply_id: {apply_data}')

    # Step 4: allocationInvoiceFee - 分配发票到费用
    # pay_invoice_id 来自 Step 2，pay_invoice_apply_id / un_amount 来自 Step 3
    with allure.step('分配发票到费用（allocationInvoiceFee）'):
        alloc_resp = PayableApi.allocation_invoice_fee(
            pay_invoice_apply_id=pay_invoice_apply_id,
            pay_invoice_id=pay_invoice_id,
            un_amount=str(un_amount),
        )
        alloc_data = alloc_resp.json()
        result['alloc_resp'] = alloc_resp
        result['alloc_data'] = alloc_data
        result['steps'].append({
            'name': '分配发票到费用',
            'code': alloc_data.get('code'),
            'msg': alloc_data.get('msg'),
            'pay_invoice_id': pay_invoice_id,
            'un_amount': un_amount,
        })

        assert alloc_resp.status_code == 200, (
            f'allocationInvoiceFee HTTP 状态码异常: {alloc_resp.status_code}'
        )
        assert alloc_data.get('code') == 200, (
            f'allocationInvoiceFee 失败: {alloc_data}'
        )

    return result


def _generate_unique_invoice_number(prefix: str = "INV") -> str:
    """生成唯一发票号码：前缀 + 时间戳毫秒 + 4 位随机数"""
    import time as _time
    import random as _random

    ts = int(_time.time() * 1000) % 100000000
    rand = _random.randint(0, 9999)
    return f"{prefix}{ts}{rand:04d}"
