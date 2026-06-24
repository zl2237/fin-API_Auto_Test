"""
链路测试 - 应付开票申请（link21）

  link21 - 发起应付开票批次申请（link20 + financePayList(开票) + getOrderInfoByFeeId + batchOrderEdit submit）
"""
import allure
import pytest

from data.order import BookRealAmountData, generate_bl_no
from workflows.order_workflow import OrderWorkflow
from testcases.pay.helpers import (
    _build_fee_config,
    _assert_link18_prerequisite_ok,
    _assert_payable_account_ok,
    _assert_confirm_payable_ok,
    _assert_payable_invoice_apply_ok,
)


# =============================================================================
# 链路21：新建...确认应付对账 → 发起应付开票批次申请
# =============================================================================
@pytest.mark.link21
class TestLink21PayableInvoiceApply:
    """链路21：新建 → ... → 确认应付对账 → 发起应付开票批次申请"""

    @allure.feature("链路测试")
    @allure.story("链路21：发起应付开票批次申请")
    @allure.severity("critical")
    @allure.title("链路21：确认应付对账 → 发起应付开票批次申请（financePayList 开票 + getOrderInfoByFeeId + batchOrderEdit submit）")
    def test_link21_payable_invoice_apply(self):
        """验证：完整链路（LINK20 + 发起应付开票批次申请），链路停在 payable_invoice_apply 阶段"""
        bl_no = generate_bl_no(21)

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→...→确认应付对账→发起应付开票批次申请）'):
            result = OrderWorkflow.full_flow(
                stop_at='payable_invoice_apply',
                bl_no=bl_no,
                fee_configs=[fee_config],
            )

        # ---------- LINK20 前置步骤断言 ----------
        with allure.step('断言：LINK20 前置链路全部成功'):
            _assert_link18_prerequisite_ok(result)

        # ----- link19 应付对账 -----
        with allure.step('断言：发起应付对账批次成功'):
            payable_result = result['payable_account_result']
            assert payable_result is not None, 'payable_account_result 不应为空'
            assert payable_result['pay_list_resp'].status_code == 200
            assert payable_result['pay_list_data'].get('code') == 200
            assert payable_result['select_list'], f'select_list 不应为空'
            assert payable_result['submit_resp'].status_code == 200
            assert payable_result['submit_data'].get('code') == 200
            assert payable_result.get('pay_account_id')
            assert payable_result.get('pay_account_no')

        # ----- link20 确认应付对账 -----
        with allure.step('断言：确认应付对账成功'):
            confirm_result = result['confirm_payable_result']
            assert confirm_result is not None, 'confirm_payable_result 不应为空'
            assert confirm_result['pay_account_page_resp'].status_code == 200
            assert confirm_result['pay_account_page_data'].get('code') == 200
            assert confirm_result.get('pay_account_id')
            assert confirm_result['confirm_resp'].status_code == 200
            assert confirm_result['confirm_data'].get('code') == 200
            assert confirm_result['confirm_data'].get('msg') == '成功'

        # ---------- LINK21 发起应付开票批次申请断言 ----------

        with allure.step('断言：发起应付开票批次申请结果存在'):
            invoice_result = result['payable_invoice_apply_result']
            assert invoice_result is not None, 'payable_invoice_apply_result 不应为空'

        with allure.step('断言：financePayList（开票模式）查询成功'):
            pay_list_resp = invoice_result['pay_list_invoice_resp']
            pay_list_data = invoice_result['pay_list_invoice_data']
            assert pay_list_resp.status_code == 200
            assert pay_list_data.get('code') == 200
            assert pay_list_data.get('msg') == '成功'

        with allure.step('断言：main_id / pay_settle_object 已提取'):
            assert invoice_result.get('main_id'), f'main_id 不应为空: {invoice_result}'
            assert invoice_result.get('pay_settle_object'), f'pay_settle_object 不应为空'

        with allure.step('断言：getOrderInfoByFeeId 返回记录'):
            order_info_records = invoice_result['order_info_records']
            assert order_info_records, f'order_info_records 不应为空: {invoice_result["order_info_data"]}'
            for rec in order_info_records:
                assert rec.get('order_fee_real_id'), f'record 中 order_fee_real_id 不应为空: {rec}'
                assert rec.get('book_supplier_id'), f'record 中 book_supplier_id 不应为空: {rec}'

        with allure.step('断言：batchOrderEdit 应付开票批次提交成功'):
            submit_resp = invoice_result['submit_resp']
            submit_data = invoice_result['submit_data']
            assert submit_resp.status_code == 200
            assert submit_data.get('code') == 200
            assert submit_data.get('msg') == '成功', f'batchOrderEdit msg 不为"成功": {submit_data.get("msg")}'

        with allure.step('断言：bl_no 来自上游链路（未被覆盖）'):
            assert result['bl_no'] == bl_no

        with allure.step('断言：链路停在 payable_invoice_apply 阶段'):
            assert result['stop_at'] == 'payable_invoice_apply'
