"""
链路测试 - 应付发票上传与登记（link22）

  link22 - 应付发票上传与登记（link21 + uploadFile + invoiceAdd + applyPage + allocationInvoiceFee）
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
# 链路22：新建...发起应付开票批次申请 → 应付发票上传与登记
# =============================================================================
@pytest.mark.link22
class TestLink22PayableInvoiceRegister:
    """链路22：新建 → ... → 发起应付开票批次申请 → 应付发票上传与登记"""

    @allure.feature("链路测试")
    @allure.story("链路22：发起应付开票批次申请 + 应付发票上传与登记")
    @allure.severity("critical")
    @allure.title("链路22：发起应付开票批次申请 → 应付发票上传与登记")
    def test_link22_payable_invoice_register(self):
        """验证：完整链路（LINK21 + 应付发票上传与登记），链路停在 payable_invoice_register 阶段"""
        bl_no = generate_bl_no(22)

        with allure.step('执行链路（新建→...→发起应付开票批次申请→应付发票上传与登记）'):
            result = OrderWorkflow.full_flow(
                stop_at='payable_invoice_register',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：前置链路（link21）全部成功'):
            _assert_link18_prerequisite_ok(result)
            _assert_payable_account_ok(result)
            _assert_confirm_payable_ok(result)
            _assert_payable_invoice_apply_ok(result)

        with allure.step('断言：应付发票上传与登记结果存在'):
            upload_result = result['payable_invoice_register_result']
            assert upload_result is not None, '应付发票上传与登记结果不应为空'

        with allure.step('断言：uploadFile 成功'):
            upload_resp = upload_result['upload_resp']
            assert upload_resp.status_code == 200, (
                f'uploadFile HTTP 状态码异常: {upload_resp.status_code}'
            )
            upload_data = upload_result['upload_data']
            assert upload_data.get('code') == 200, (
                f'uploadFile code 不为 200: {upload_data}'
            )
            uploaded_file_info = upload_result['uploaded_file_info']
            assert uploaded_file_info.get('file_id'), (
                f'uploadFile 未返回 file_id: {uploaded_file_info}'
            )

        with allure.step('断言：invoiceAdd 成功'):
            add_resp = upload_result['add_resp']
            assert add_resp.status_code == 200, (
                f'invoiceAdd HTTP 状态码异常: {add_resp.status_code}'
            )
            add_data = upload_result['add_data']
            assert add_data.get('code') == 200, (
                f'invoiceAdd code 不为 200: {add_data}'
            )
            pay_invoice_id = upload_result['pay_invoice_id']
            assert pay_invoice_id, f'invoiceAdd 未返回 pay_invoice_id: {upload_result}'

        with allure.step('断言：applyPage 成功'):
            apply_resp = upload_result['apply_page_resp']
            assert apply_resp.status_code == 200, (
                f'applyPage HTTP 状态码异常: {apply_resp.status_code}'
            )
            apply_data = upload_result['apply_page_data']
            assert apply_data.get('code') == 200, (
                f'applyPage code 不为 200: {apply_data}'
            )
            pay_invoice_apply_id = upload_result['pay_invoice_apply_id']
            assert pay_invoice_apply_id, (
                f'applyPage 未返回 pay_invoice_apply_id: {upload_result}'
            )

        with allure.step('断言：allocationInvoiceFee 成功'):
            alloc_resp = upload_result['alloc_resp']
            assert alloc_resp.status_code == 200, (
                f'allocationInvoiceFee HTTP 状态码异常: {alloc_resp.status_code}'
            )
            alloc_data = upload_result['alloc_data']
            assert alloc_data.get('code') == 200, (
                f'allocationInvoiceFee code 不为 200: {alloc_data}'
            )

        with allure.step('断言：链路停在 payable_invoice_register 阶段'):
            assert result['stop_at'] == 'payable_invoice_register'
