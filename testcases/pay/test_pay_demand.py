"""
链路测试 - 应付付款需求（link23 / link24 / link25）

  link23 - 发起付款需求（link22 + financePayList + paymentList + demandEditByOrder）
  link24 - 审核生成付款单（link23 + auditPage + auditExecute）
  link25 - 付款单核销（link24 + formPage + writeoffPayFormList + orderFeePage + writeoffBatch）
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
# 链路23：新建...应付发票上传与登记 → 发起付款需求
# =============================================================================
@pytest.mark.link23
class TestLink23PayDemand:
    """链路23：新建 → ... → 应付发票上传与登记 → 发起付款需求"""

    @allure.feature("链路测试")
    @allure.story("链路23：发起付款需求")
    @allure.severity("critical")
    @allure.title("链路23：应付发票上传与登记 → 发起付款需求")
    def test_link23_pay_demand(self):
        """验证：完整链路（LINK22 + 发起付款需求），链路停在 pay_demand 阶段"""
        bl_no = generate_bl_no(23)

        with allure.step('执行链路（新建→...→应付发票上传与登记→发起付款需求）'):
            result = OrderWorkflow.full_flow(
                stop_at='pay_demand',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：前置链路（link22）全部成功'):
            _assert_link18_prerequisite_ok(result)
            _assert_payable_account_ok(result)
            _assert_confirm_payable_ok(result)
            _assert_payable_invoice_apply_ok(result)

        with allure.step('断言：应付发票上传与登记结果存在'):
            upload_result = result.get('payable_invoice_register_result')
            assert upload_result is not None, '应付发票上传与登记结果不应为空'

        with allure.step('断言：发起付款需求结果存在'):
            demand_result = result['pay_demand_result']
            assert demand_result is not None, 'pay_demand_result 不应为空'

        with allure.step('断言：financePayList 查询应付费用列表成功'):
            pay_list_resp = demand_result['pay_list_resp']
            pay_list_data = demand_result['pay_list_data']
            assert pay_list_resp.status_code == 200, (
                f'financePayList HTTP 状态码异常: {pay_list_resp.status_code}'
            )
            assert pay_list_data.get('code') == 200, (
                f'financePayList 查询失败: {pay_list_data}'
            )
            assert pay_list_data.get('msg') == '成功', (
                f'financePayList msg 不为"成功": {pay_list_data.get("msg")}'
            )

        with allure.step('断言：select_list 非空'):
            select_list = demand_result.get('select_list', [])
            assert select_list, f'select_list 不应为空: {pay_list_data}'

        with allure.step('断言：cost_usd / cost_cny 已计算'):
            cost_usd = demand_result.get('cost_usd')
            cost_cny = demand_result.get('cost_cny')
            assert cost_usd, f'cost_usd 不应为空: {demand_result}'
            assert cost_cny is not None, f'cost_cny 不应为空: {demand_result}'
            assert float(cost_usd) > 0, f'cost_usd 应大于 0: {cost_usd}'

        with allure.step('断言：paymentList 付款需求预览成功'):
            payment_resp = demand_result['payment_list_resp']
            payment_data = demand_result['payment_list_data']
            assert payment_resp.status_code == 200, (
                f'paymentList HTTP 状态码异常: {payment_resp.status_code}'
            )
            assert payment_data.get('code') == 200, (
                f'paymentList 失败: {payment_data}'
            )

        with allure.step('断言：payment_list 非空'):
            payment_list = demand_result.get('payment_list', [])
            assert payment_list, f'payment_list 不应为空: {payment_data}'

        with allure.step('断言：demandEditByOrder 提交付款需求成功'):
            submit_resp = demand_result['submit_resp']
            submit_data = demand_result['submit_data']
            assert submit_resp.status_code == 200, (
                f'demandEditByOrder HTTP 状态码异常: {submit_resp.status_code}'
            )
            assert submit_data.get('code') == 200, (
                f'demandEditByOrder 失败: {submit_data}'
            )
            assert submit_data.get('msg') == '成功', (
                f'demandEditByOrder msg 不为"成功": {submit_data.get("msg")}'
            )

        with allure.step('断言：bl_no 来自上游链路（未被覆盖）'):
            assert result['bl_no'] == bl_no

        with allure.step('断言：链路停在 pay_demand 阶段'):
            assert result['stop_at'] == 'pay_demand'


# =============================================================================
# 链路24：新建...发起付款需求 → 审核生成付款单
# =============================================================================
@pytest.mark.link24
class TestLink24PayDemandAudit:
    """链路24：新建 → ... → 发起付款需求 → 审核生成付款单"""

    @allure.feature("链路测试")
    @allure.story("链路24：审核生成付款单")
    @allure.severity("critical")
    @allure.title("链路24：发起付款需求 → 审核生成付款单")
    def test_link24_pay_demand_audit(self):
        """验证：完整链路（LINK23 + 审核生成付款单），链路停在 pay_demand_audit 阶段"""
        bl_no = generate_bl_no(24)

        with allure.step('执行链路（新建→...→发起付款需求→审核生成付款单）'):
            result = OrderWorkflow.full_flow(
                stop_at='pay_demand_audit',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：前置链路（link23）全部成功'):
            _assert_link18_prerequisite_ok(result)
            _assert_payable_account_ok(result)
            _assert_confirm_payable_ok(result)
            _assert_payable_invoice_apply_ok(result)

        with allure.step('断言：应付发票上传与登记结果存在'):
            upload_result = result.get('payable_invoice_register_result')
            assert upload_result is not None, '应付发票上传与登记结果不应为空'

        with allure.step('断言：发起付款需求结果存在'):
            demand_result = result.get('pay_demand_result')
            assert demand_result is not None, 'pay_demand_result 不应为空'

        with allure.step('断言：审核生成付款单结果存在'):
            audit_result = result['pay_demand_audit_result']
            assert audit_result is not None, 'pay_demand_audit_result 不应为空'

        with allure.step('断言：auditPage 查询待审核列表成功'):
            audit_page_resp = audit_result['audit_page_resp']
            audit_page_data = audit_result['audit_page_data']
            assert audit_page_resp.status_code == 200, (
                f'auditPage HTTP 状态码异常: {audit_page_resp.status_code}'
            )
            assert audit_page_data.get('code') == 200, (
                f'auditPage 查询失败: {audit_page_data}'
            )

        with allure.step('断言：audit_records 非空'):
            audit_records = audit_result.get('audit_records', [])
            assert audit_records, f'audit_records 不应为空: {audit_page_data}'

        with allure.step('断言：audit_id 非空'):
            audit_id = audit_result.get('audit_id')
            assert audit_id, f'audit_id 不应为空: {audit_result}'

        with allure.step('断言：audit_type 为 payDemand'):
            audit_type = audit_result.get('audit_type')
            assert audit_type == 'payDemand', f'audit_type 应为 payDemand: {audit_type}'

        with allure.step('断言：auditExecute 执行审批成功'):
            audit_execute_resp = audit_result['audit_execute_resp']
            audit_execute_data = audit_result['audit_execute_data']
            assert audit_execute_resp.status_code == 200, (
                f'auditExecute HTTP 状态码异常: {audit_execute_resp.status_code}'
            )
            assert audit_execute_data.get('code') == 200, (
                f'auditExecute 失败: {audit_execute_data}'
            )

        with allure.step('断言：bl_no 来自上游链路（未被覆盖）'):
            assert result['bl_no'] == bl_no

        with allure.step('断言：链路停在 pay_demand_audit 阶段'):
            assert result['stop_at'] == 'pay_demand_audit'


# =============================================================================
# 链路25：新建...审核生成付款单 → 付款单核销
# =============================================================================
@pytest.mark.link25
class TestLink25PayWriteoff:
    """链路25：新建 → ... → 审核生成付款单 → 付款单核销"""

    @allure.feature("链路测试")
    @allure.story("链路25：付款单核销")
    @allure.severity("critical")
    @allure.title("链路25：审核生成付款单 → 付款单核销")
    def test_link25_pay_writeoff(self):
        """验证：完整链路（LINK24 + 付款单核销），链路停在 pay_writeoff 阶段"""
        bl_no = generate_bl_no(25)

        with allure.step('执行链路（新建→...→审核生成付款单→付款单核销）'):
            result = OrderWorkflow.full_flow(
                stop_at='pay_writeoff',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：前置链路（link24）全部成功'):
            _assert_link18_prerequisite_ok(result)
            _assert_payable_account_ok(result)
            _assert_confirm_payable_ok(result)
            _assert_payable_invoice_apply_ok(result)

        with allure.step('断言：应付发票上传与登记结果存在'):
            upload_result = result.get('payable_invoice_register_result')
            assert upload_result is not None, '应付发票上传与登记结果不应为空'

        with allure.step('断言：发起付款需求结果存在'):
            demand_result = result.get('pay_demand_result')
            assert demand_result is not None, 'pay_demand_result 不应为空'

        with allure.step('断言：审核生成付款单结果存在'):
            audit_result = result.get('pay_demand_audit_result')
            assert audit_result is not None, 'pay_demand_audit_result 不应为空'

        with allure.step('断言：付款单核销结果存在'):
            writeoff_result = result['pay_writeoff_result']
            assert writeoff_result is not None, 'pay_writeoff_result 不应为空'

        with allure.step('断言：formPage 查询付款单列表成功'):
            form_page_resp = writeoff_result['form_page_resp']
            form_page_data = writeoff_result['form_page_data']
            assert form_page_resp.status_code == 200, (
                f'formPage HTTP 状态码异常: {form_page_resp.status_code}'
            )
            assert form_page_data.get('code') == 200, (
                f'formPage 查询失败: {form_page_data}'
            )

        with allure.step('断言：pay_form_records 非空'):
            pay_form_records = writeoff_result.get('pay_form_records', [])
            assert pay_form_records, f'pay_form_records 不应为空: {form_page_data}'

        with allure.step('断言：pay_form_id 非空'):
            pay_form_id = writeoff_result.get('pay_form_id')
            assert pay_form_id, f'pay_form_id 不应为空: {writeoff_result}'

        with allure.step('断言：writeoffPayFormList 成功'):
            writeoff_pay_form_list_resp = writeoff_result['writeoff_pay_form_list_resp']
            writeoff_pay_form_list_data = writeoff_result['writeoff_pay_form_list_data']
            assert writeoff_pay_form_list_resp.status_code == 200, (
                f'writeoffPayFormList HTTP 状态码异常: {writeoff_pay_form_list_resp.status_code}'
            )
            assert writeoff_pay_form_list_data.get('code') == 200, (
                f'writeoffPayFormList 失败: {writeoff_pay_form_list_data}'
            )

        with allure.step('断言：orderFeePage 查询成功'):
            order_fee_page_resp = writeoff_result['order_fee_page_resp']
            order_fee_page_data = writeoff_result['order_fee_page_data']
            assert order_fee_page_resp.status_code == 200, (
                f'orderFeePage HTTP 状态码异常: {order_fee_page_resp.status_code}'
            )
            assert order_fee_page_data.get('code') == 200, (
                f'orderFeePage 失败: {order_fee_page_data}'
            )

        with allure.step('断言：writeoffBatch 执行核销成功'):
            writeoff_batch_resp = writeoff_result['writeoff_batch_resp']
            writeoff_batch_data = writeoff_result['writeoff_batch_data']
            assert writeoff_batch_resp.status_code == 200, (
                f'writeoffBatch HTTP 状态码异常: {writeoff_batch_resp.status_code}'
            )
            assert writeoff_batch_data.get('code') == 200, (
                f'writeoffBatch 失败: {writeoff_batch_data}'
            )

        with allure.step('断言：bl_no 来自上游链路（未被覆盖）'):
            assert result['bl_no'] == bl_no

        with allure.step('断言：链路停在 pay_writeoff 阶段'):
            assert result['stop_at'] == 'pay_writeoff'
