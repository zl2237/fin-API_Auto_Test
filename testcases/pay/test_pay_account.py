"""
链路测试 - 应付对账（link19 / link20）

  link19 - 发起应付对账批次（link18 + financePayList + orderPayAccountEdit）
  link20 - 确认应付对账（link19 + payAccountPage + accountConfirm）
"""
import allure
import pytest

from data.order import BookRealAmountData, generate_bl_no
from workflows.order_workflow import OrderWorkflow
from testcases.pay.helpers import _build_fee_config, _assert_link18_prerequisite_ok, _assert_payable_account_ok, _assert_confirm_payable_ok


# =============================================================================
# 链路19：新建...应收核销 → 发起应付对账批次
# =============================================================================
@pytest.mark.link19
class TestLink19PayableAccount:
    """链路19：新建 → ... → 应收核销 → 发起应付对账批次"""

    @allure.feature("链路测试")
    @allure.story("链路19：发起应付对账批次")
    @allure.severity("critical")
    @allure.title("链路19：应收核销 → 发起应付对账批次（financePayList + orderPayAccountEdit）")
    def test_link19_payable_account(self):
        """验证：完整链路（LINK18 + 发起应付对账批次），链路停在 payable 阶段"""
        bl_no = generate_bl_no(19)

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→...→应收核销→发起应付对账批次）'):
            result = OrderWorkflow.full_flow(
                stop_at='payable',
                bl_no=bl_no,
                fee_configs=[fee_config],
            )

        # ---------- LINK18 前置步骤断言（全部通过才执行 LK19） ----------
        with allure.step('断言：LINK18 前置链路全部成功'):
            _assert_link18_prerequisite_ok(result)

        # ---------- LINK19 发起应付对账批次断言 ----------

        with allure.step('断言：应付对账批次结果存在'):
            payable_result = result['payable_account_result']
            assert payable_result is not None, 'payable_account_result 不应为空'

        with allure.step('断言：financePayList 查询应付项列表成功'):
            pay_list_resp = payable_result['pay_list_resp']
            pay_list_data = payable_result['pay_list_data']
            assert pay_list_resp.status_code == 200, f'HTTP 状态码异常: {pay_list_resp.status_code}'
            assert pay_list_data.get('code') == 200, f'financePayList 查询失败: {pay_list_data}'
            assert pay_list_data.get('msg') == '成功', f'financePayList msg 不为"成功": {pay_list_data.get("msg")}'

        with allure.step('断言：select_list 非空（来自 financePayList 响应）'):
            select_list = payable_result['select_list']
            assert select_list, f'select_list 不应为空: {pay_list_data}'

        with allure.step('断言：amount_list_flat 包含 order_fee_real_id'):
            amount_list_flat = payable_result.get('amount_list_flat', [])
            assert amount_list_flat, f'amount_list_flat 不应为空（financePayList 响应: {pay_list_data}）'
            for item in amount_list_flat:
                assert item.get('order_fee_real_id'), f'amount_list 中存在 order_fee_real_id 为空的项: {item}'

        with allure.step('断言：orderPayAccountEdit 发起应付对账批次成功'):
            submit_resp = payable_result['submit_resp']
            submit_data = payable_result['submit_data']
            assert submit_resp.status_code == 200, f'HTTP 状态码异常: {submit_resp.status_code}'
            assert submit_data.get('code') == 200, f'orderPayAccountEdit 失败: {submit_data}'
            assert submit_data.get('msg') == '成功', f'orderPayAccountEdit msg 不为"成功": {submit_data.get("msg")}'

        with allure.step('断言：pay_account_id 和 pay_account_no 非空'):
            assert payable_result.get('pay_account_id'), f'pay_account_id 不应为空: {payable_result}'
            assert payable_result.get('pay_account_no'), f'pay_account_no 不应为空: {payable_result}'

        with allure.step('断言：bl_no 来自上游 link18（未被覆盖）'):
            assert result['bl_no'] == bl_no, f'bl_no 应为链路生成的: {bl_no}，实际: {result["bl_no"]}'

        with allure.step('断言：链路停在 payable 阶段'):
            assert result['stop_at'] == 'payable'


# =============================================================================
# 链路20：新建...发起应付对账批次 → 确认应付对账
# =============================================================================
@pytest.mark.link20
class TestLink20ConfirmPayable:
    """链路20：新建 → ... → 发起应付对账批次 → 确认应付对账"""

    @allure.feature("链路测试")
    @allure.story("链路20：确认应付对账")
    @allure.severity("critical")
    @allure.title("链路20：发起应付对账批次 → 确认应付对账（payAccountPage + accountConfirm）")
    def test_link20_confirm_payable(self):
        """验证：完整链路（LINK19 + 确认应付对账），链路停在 confirm_payable 阶段"""
        bl_no = generate_bl_no(20)

        customer_fees = BookRealAmountData.get_customer_standard_fees()
        supplier_fees = BookRealAmountData.get_supplier_standard_fees()

        fee_config = {
            'to_customer_fees': customer_fees,
            'to_supplier_fees': supplier_fees,
        }

        with allure.step('执行链路（新建→...→发起应付对账批次→确认应付对账）'):
            result = OrderWorkflow.full_flow(
                stop_at='confirm_payable',
                bl_no=bl_no,
                fee_configs=[fee_config],
            )

        # ---------- LINK19 前置步骤断言 ----------
        with allure.step('断言：LINK19 前置链路全部成功'):
            _assert_link18_prerequisite_ok(result)

        # ----- link19 发起应付对账 -----
        with allure.step('断言：发起应付对账批次成功'):
            payable_result = result['payable_account_result']
            assert payable_result is not None, 'payable_account_result 不应为空'
            pay_list_data = payable_result['pay_list_data']
            assert payable_result['pay_list_resp'].status_code == 200
            assert pay_list_data.get('code') == 200
            select_list = payable_result['select_list']
            assert select_list, f'select_list 不应为空: {pay_list_data}'
            assert payable_result['submit_resp'].status_code == 200
            assert payable_result['submit_data'].get('code') == 200
            assert payable_result.get('pay_account_id')
            assert payable_result.get('pay_account_no')

        # ---------- LINK20 确认应付对账断言 ----------

        with allure.step('断言：确认应付对账结果存在'):
            confirm_result = result['confirm_payable_result']
            assert confirm_result is not None, 'confirm_payable_result 不应为空'

        with allure.step('断言：payAccountPage 查询应付对账批次成功'):
            page_resp = confirm_result['pay_account_page_resp']
            page_data = confirm_result['pay_account_page_data']
            assert page_resp.status_code == 200, f'HTTP 状态码异常: {page_resp.status_code}'
            assert page_data.get('code') == 200, f'payAccountPage 查询失败: {page_data}'
            assert page_data.get('msg') == '成功', f'payAccountPage msg 不为"成功": {page_data.get("msg")}'

        with allure.step('断言：pay_account_id 非空'):
            assert confirm_result.get('pay_account_id'), f'pay_account_id 不应为空: {confirm_result}'
            assert confirm_result.get('pay_account_no'), f'pay_account_no 不应为空: {confirm_result}'

        with allure.step('断言：accountConfirm 确认应付对账成功'):
            confirm_resp = confirm_result['confirm_resp']
            confirm_data = confirm_result['confirm_data']
            assert confirm_resp.status_code == 200, f'HTTP 状态码异常: {confirm_resp.status_code}'
            assert confirm_data.get('code') == 200, f'accountConfirm 失败: {confirm_data}'
            assert confirm_data.get('msg') == '成功', f'accountConfirm msg 不为"成功": {confirm_data.get("msg")}'

        with allure.step('断言：bl_no 来自上游链路（未被覆盖）'):
            assert result['bl_no'] == bl_no

        with allure.step('断言：链路停在 confirm_payable 阶段'):
            assert result['stop_at'] == 'confirm_payable'
