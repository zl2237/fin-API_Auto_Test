"""
链路测试 - 应付（Pay）域公共辅助函数

适用于 link19 ~ link25 的共享断言逻辑。
"""
from data.order import BookRealAmountData


def _build_fee_config():
    return {
        'to_customer_fees': BookRealAmountData.get_customer_standard_fees(),
        'to_supplier_fees': BookRealAmountData.get_supplier_standard_fees(),
    }


def _assert_link18_prerequisite_ok(result):
    """
    link19 的前置链路（link18）断言：
    - 新建 / 分发 / 生成子订单 / 录费用 / 审批 / 费用单 / 应收对账 / 发票 / 应收核销
    所有前置步骤必须通过。
    """
    assert result['create_data']['code'] == 200, f'新建失败: {result["create_data"]}'
    assert result['distribute_data']['code'] == 200, f'分发失败: {result["distribute_data"]}'
    gen_data = result['generate_sub_data']
    assert gen_data['code'] == 200, f'生成子订单失败: {gen_data}'

    # 录费用
    assert len(result['record_fee_results']) == 1
    fee_1 = result['record_fee_results'][0]
    assert fee_1['resp'].status_code == 200
    assert fee_1['data']['code'] == 200

    # 资产推送审批
    assert fee_1.get('audit_send_resp') is not None
    assert fee_1['audit_send_resp'].status_code == 200
    assert fee_1['audit_send_data']['code'] == 200
    assert fee_1.get('audit_id')
    assert fee_1['audit_approve_resp'].status_code == 200
    assert fee_1['audit_approve_data']['code'] == 200

    # 订单锁定审批
    lock_result = result['order_lock_result']
    assert lock_result is not None
    assert lock_result['send_resp'].status_code == 200
    assert lock_result['send_data']['code'] == 200
    assert lock_result.get('audit_id')
    assert lock_result['approve_resp'].status_code == 200
    assert lock_result['approve_data']['code'] == 200

    # 未放款开票申请审批
    invoice_result = result['invoice_apply_result']
    assert invoice_result is not None
    assert invoice_result['send_resp'].status_code == 200
    assert invoice_result['send_data']['code'] == 200
    assert invoice_result.get('audit_id')
    assert invoice_result['approve_resp'].status_code == 200
    assert invoice_result['approve_data']['code'] == 200

    # 供应商垫付申请审批
    advance_result = result['supplier_advance_result']
    assert advance_result is not None
    assert advance_result['send_resp'].status_code == 200
    assert advance_result['send_data']['code'] == 200
    assert advance_result.get('audit_id')
    assert advance_result['approve_resp'].status_code == 200
    assert advance_result['approve_data']['code'] == 200

    # 费用通知单
    notice_result = result['fee_notice_result']
    assert notice_result is not None
    assert notice_result['resp'].status_code == 200
    assert notice_result['data']['code'] == 200

    # 费用确认单
    fee_confirm_result = result['fee_confirm_result']
    assert fee_confirm_result is not None
    assert fee_confirm_result['resp'].status_code == 200
    assert fee_confirm_result['data']['code'] == 200

    # 应收对账批次
    receive_result = result['receive_account_result']
    assert receive_result is not None
    assert receive_result['put_list_resp'].status_code == 200
    assert receive_result['put_list_data'].get('code') == 200
    assert receive_result['submit_resp'].status_code == 200
    assert receive_result['submit_data'].get('code') == 200
    assert receive_result['submit_data'].get('msg') == '成功'
    assert receive_result['receive_account_id']
    assert receive_result['receive_account_no'].startswith('YSDZPC')

    # 确认应收对账
    confirm_result = result['confirm_account_result']
    assert confirm_result is not None
    assert confirm_result['confirm_list_resp'].status_code == 200
    assert confirm_result['confirm_list_data'].get('code') == 200
    assert confirm_result['submit_resp'].status_code == 200
    assert confirm_result['submit_data'].get('code') == 200
    assert confirm_result['submit_data'].get('msg') == '成功'

    # 发票批次
    invoice_batch_result = result['invoice_batch_result']
    assert invoice_batch_result is not None
    assert invoice_batch_result['invoice_submit_resp'].status_code == 200
    assert invoice_batch_result['invoice_submit_data'].get('code') == 200

    # 发票批次审核
    audit_result = result['invoice_batch_audit_result']
    assert audit_result is not None
    assert audit_result['audit_query_resp'].status_code == 200
    assert audit_result.get('audit_id')
    assert audit_result['audit_execute_resp'].status_code == 200
    assert audit_result['audit_execute_data'].get('code') == 200

    # 发票上传与登记
    upload_result = result['invoice_upload_result']
    assert upload_result is not None
    assert upload_result['add_resp'].status_code == 200
    assert upload_result['add_data'].get('code') == 200
    assert upload_result.get('receive_invoice_id')
    assert upload_result['apply_page_resp'].status_code == 200
    assert upload_result['apply_page_data'].get('code') == 200
    assert upload_result.get('receive_invoice_apply_id')
    assert upload_result['alloc_resp'].status_code == 200
    assert upload_result['alloc_data'].get('code') == 200

    # 应收核销
    writeoff_result = result['receive_writeoff_result']
    assert writeoff_result is not None
    assert writeoff_result['fee_take_page_resp'].status_code == 200
    assert writeoff_result['fee_take_page_data'].get('code') == 200
    order_fee_real_id_list = writeoff_result.get('order_fee_real_id_list', [])
    assert order_fee_real_id_list, f'应收核销 order_fee_real_id_list 不应为空'
    assert writeoff_result['writeoff_batch_resp'].status_code == 200
    assert writeoff_result['writeoff_batch_data'].get('code') == 200


def _assert_payable_account_ok(result):
    """
    link19 应付对账断言：financePayList + orderPayAccountEdit 全部成功。
    """
    payable_result = result['payable_account_result']
    assert payable_result is not None, 'payable_account_result 不应为空'

    pay_list_resp = payable_result['pay_list_resp']
    pay_list_data = payable_result['pay_list_data']
    assert pay_list_resp.status_code == 200, f'financePayList HTTP 状态码异常: {pay_list_resp.status_code}'
    assert pay_list_data.get('code') == 200, f'financePayList 失败: {pay_list_data}'
    assert pay_list_data.get('msg') == '成功', f'financePayList msg 不为"成功": {pay_list_data.get("msg")}'

    select_list = payable_result['select_list']
    assert select_list, f'select_list 不应为空: {pay_list_data}'

    amount_list_flat = payable_result.get('amount_list_flat', [])
    assert amount_list_flat, f'amount_list_flat 不应为空（financePayList 响应: {pay_list_data}）'
    for item in amount_list_flat:
        assert item.get('order_fee_real_id'), f'amount_list 中存在 order_fee_real_id 为空的项: {item}'

    submit_resp = payable_result['submit_resp']
    submit_data = payable_result['submit_data']
    assert submit_resp.status_code == 200, f'orderPayAccountEdit HTTP 状态码异常: {submit_resp.status_code}'
    assert submit_data.get('code') == 200, f'orderPayAccountEdit 失败: {submit_data}'
    assert submit_data.get('msg') == '成功', f'orderPayAccountEdit msg 不为"成功": {submit_data.get("msg")}'

    assert payable_result.get('pay_account_id'), f'pay_account_id 不应为空: {payable_result}'
    assert payable_result.get('pay_account_no'), f'pay_account_no 不应为空: {payable_result}'


def _assert_confirm_payable_ok(result):
    """
    link20 确认应付对账断言：payAccountPage + accountConfirm 全部成功。
    """
    confirm_result = result['confirm_payable_result']
    assert confirm_result is not None, 'confirm_payable_result 不应为空'

    page_resp = confirm_result['pay_account_page_resp']
    page_data = confirm_result['pay_account_page_data']
    assert page_resp.status_code == 200, f'payAccountPage HTTP 状态码异常: {page_resp.status_code}'
    assert page_data.get('code') == 200, f'payAccountPage 查询失败: {page_data}'
    assert page_data.get('msg') == '成功', f'payAccountPage msg 不为"成功": {page_data.get("msg")}'

    assert confirm_result.get('pay_account_id'), f'pay_account_id 不应为空: {confirm_result}'
    assert confirm_result.get('pay_account_no'), f'pay_account_no 不应为空: {confirm_result}'

    confirm_resp = confirm_result['confirm_resp']
    confirm_data = confirm_result['confirm_data']
    assert confirm_resp.status_code == 200, f'accountConfirm HTTP 状态码异常: {confirm_resp.status_code}'
    assert confirm_data.get('code') == 200, f'accountConfirm 失败: {confirm_data}'
    assert confirm_data.get('msg') == '成功', f'accountConfirm msg 不为"成功": {confirm_data.get("msg")}'


def _assert_payable_invoice_apply_ok(result):
    """
    link21 发起应付开票批次申请断言：financePayList（开票）+ getOrderInfoByFeeId + batchOrderEdit 全部成功。
    """
    invoice_result = result['payable_invoice_apply_result']
    assert invoice_result is not None, 'payable_invoice_apply_result 不应为空'

    pay_list_resp = invoice_result['pay_list_invoice_resp']
    pay_list_data = invoice_result['pay_list_invoice_data']
    assert pay_list_resp.status_code == 200, f'financePayList（开票）HTTP 状态码异常: {pay_list_resp.status_code}'
    assert pay_list_data.get('code') == 200, f'financePayList（开票）失败: {pay_list_data}'
    assert pay_list_data.get('msg') == '成功', f'financePayList（开票）msg 不为"成功": {pay_list_data.get("msg")}'

    assert invoice_result.get('main_id'), f'main_id 不应为空: {invoice_result}'
    assert invoice_result.get('pay_settle_object'), f'pay_settle_object 不应为空'

    order_info_records = invoice_result['order_info_records']
    assert order_info_records, f'order_info_records 不应为空: {invoice_result["order_info_data"]}'
    for rec in order_info_records:
        assert rec.get('order_fee_real_id'), f'record 中 order_fee_real_id 不应为空: {rec}'
        assert rec.get('book_supplier_id'), f'record 中 book_supplier_id 不应为空: {rec}'

    submit_resp = invoice_result['submit_resp']
    submit_data = invoice_result['submit_data']
    assert submit_resp.status_code == 200, f'batchOrderEdit HTTP 状态码异常: {submit_resp.status_code}'
    assert submit_data.get('code') == 200, f'batchOrderEdit 失败: {submit_data}'
    assert submit_data.get('msg') == '成功', f'batchOrderEdit msg 不为"成功": {submit_data.get("msg")}'
