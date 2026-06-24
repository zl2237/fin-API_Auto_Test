"""
链路测试 - 应收发票（link15）

  link15 - 发起应收开票批次审批
"""
import allure
import pytest

from data.order import BookRealAmountData, generate_bl_no
from workflows.order_workflow import OrderWorkflow
from testcases.receive.helpers import _build_fee_config, _assert_audit_and_fee_doc_ok


# =============================================================================
# 链路15：新建...发起应收对账批次 → 确认应收对账 → 发起应收开票批次审批
# =============================================================================
@pytest.mark.link15
class TestLink15InvoiceBatch:
    """链路15：新建 → ... → 发起应收对账批次 → 确认应收对账 → 发起应收开票批次审批"""

    @allure.feature("链路测试")
    @allure.story("链路15：发起应收开票批次审批")
    @allure.severity("critical")
    @allure.title("链路15：发起应收对账 → 确认应收对账 → 发起应收开票批次审批")
    def test_link15_invoice_batch(self):
        """验证：完整链路（LINK14 + 发起应收开票批次审批），链路停在 invoice_batch 阶段"""
        bl_no = generate_bl_no(15)

        with allure.step('执行链路（新建→...→发起应收对账批次→确认应收对账→发起应收开票批次审批）'):
            result = OrderWorkflow.full_flow(
                stop_at='invoice_batch',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：LINK14 之前所有步骤成功'):
            _assert_audit_and_fee_doc_ok(result)

        with allure.step('断言：发起应收开票批次审批结果存在'):
            invoice_result = result['invoice_batch_result']
            assert invoice_result is not None, 'invoice_batch_result 不应为空'

        with allure.step('断言：financePutList 查询成功'):
            put_list_data = invoice_result['put_list_data']
            assert invoice_result['put_list_resp'].status_code == 200
            assert put_list_data.get('code') == 200, f'查询应收款项列表失败: {put_list_data}'

        with allure.step('断言：monthExchangeRate 获取汇率成功'):
            rate_data = invoice_result['rate_data']
            assert invoice_result['rate_resp'].status_code == 200
            assert rate_data.get('code') == 200, f'获取汇率失败: {rate_data}'
            assert invoice_result.get('exchange_rate'), '汇率为空'

        with allure.step('断言：getSellInfo 获取开票方信息成功'):
            sell_info_data = invoice_result['sell_info_data']
            assert invoice_result['sell_info_resp'].status_code == 200
            assert sell_info_data.get('code') == 200, f'获取开票方信息失败: {sell_info_data}'

        with allure.step('断言：batchOrderEdit 提交应收开票批次申请成功'):
            invoice_submit_data = invoice_result['invoice_submit_data']
            assert invoice_result['invoice_submit_resp'].status_code == 200
            assert invoice_submit_data.get('code') == 200, f'提交应收开票批次申请失败: {invoice_submit_data}'
            assert invoice_submit_data.get('msg') == '成功', f'提交应收开票批次申请 msg 不为"成功": {invoice_submit_data.get("msg")}'

        with allure.step('断言：batchPage 查询批次成功'):
            page_data = invoice_result['page_data']
            assert invoice_result['page_resp'].status_code == 200
            assert page_data.get('code') == 200, f'验证批次查询失败: {page_data}'
            assert page_data.get('msg') == '成功', f'批次查询 msg 不为"成功": {page_data.get("msg")}'

        with allure.step('断言：链路停在 invoice_batch 阶段'):
            assert result['stop_at'] == 'invoice_batch'

        with allure.step('断言：steps 记录完整'):
            step_names = [s['name'] for s in result['steps']]
            for name in [
                '新建订单', '按提单号查询', '分发订单', '查询订单',
                '暂存订单', '查询订单（暂存后）', '提交订单', '查询订单（提交后）',
                '生成子订单',
                '录费用(1)', '发起审批(1)', '查询审批ID(1)', '审批通过(1)',
                '获取箱型信息',
                '发起订单锁定审批', '查询订单锁定审批ID', '订单锁定审批通过',
                '发起未放款开票申请审批', '查询未放款开票申请审批ID', '未放款开票申请审批通过',
                '发起供应商垫付申请审批', '查询供应商垫付申请审批ID', '供应商垫付申请审批通过',
                '生成费用通知单',
                '生成费用确认单',
                '查询应收款项列表',
                '应收对账预校验',
                '发起应收对账批次',
                '查询应收对账批次详情',
                '查询应收确认列表',
                '确认应收对账',
                '确认后查询批次列表',
                '查询应收款项列表（开票）',
                '获取汇率',
                '获取开票方信息',
                '提交应收开票批次申请',
                '验证应收开票批次',
            ]:
                assert name in step_names, f'steps 缺少: {name}'
