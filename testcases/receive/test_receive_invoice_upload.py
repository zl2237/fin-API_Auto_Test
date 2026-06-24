"""
链路测试 - 应收发票（link17）

  link17 - 发票上传与登记（link16 + uploadFile + invoiceAdd + applyPage + allocationInvoiceFee）
"""
import allure
import pytest

from data.order import BookRealAmountData, generate_bl_no
from workflows.order_workflow import OrderWorkflow
from testcases.receive.helpers import _build_fee_config, _assert_audit_and_fee_doc_ok


# =============================================================================
# 链路17：新建...审核生成开票申请 → 发票上传与登记
# =============================================================================
@pytest.mark.link17
class TestLink17InvoiceUpload:
    """链路17：新建 → ... → 审核生成开票申请 → 发票上传与登记"""

    @allure.feature("链路测试")
    @allure.story("链路17：发票上传与登记")
    @allure.severity("critical")
    @allure.title("链路17：审核生成开票申请 → 发票上传与登记")
    def test_link17_invoice_upload(self):
        """验证：完整链路（LINK16 + 发票上传与登记），链路停在 invoice_upload 阶段"""
        bl_no = generate_bl_no(17)

        with allure.step('执行链路（新建→...→审核生成开票申请→发票上传与登记）'):
            result = OrderWorkflow.full_flow(
                stop_at='invoice_upload',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：LINK14 之前所有步骤成功'):
            _assert_audit_and_fee_doc_ok(result)

        with allure.step('断言：审核生成开票申请成功'):
            audit_result = result['invoice_batch_audit_result']
            assert audit_result is not None, 'invoice_batch_audit_result 不应为空'
            audit_query_data = audit_result['audit_query_data']
            assert audit_result['audit_query_resp'].status_code == 200
            assert audit_query_data.get('code') == 200, f'auditPage 查询失败: {audit_query_data}'
            assert audit_result.get('audit_id'), f'audit_id 不应为空: {audit_result}'
            audit_execute_data = audit_result['audit_execute_data']
            assert audit_result['audit_execute_resp'].status_code == 200
            assert audit_execute_data.get('code') == 200, f'auditExecute 审批失败: {audit_execute_data}'
            assert '成功' in audit_execute_data.get('msg', ''), f'auditExecute msg 不含"成功": {audit_execute_data.get("msg")}'

        with allure.step('断言：发票上传与登记结果存在'):
            upload_result = result['invoice_upload_result']
            assert upload_result is not None, 'invoice_upload_result 不应为空'

        with allure.step('断言：invoiceAdd 上传发票成功'):
            add_data = upload_result['add_data']
            assert upload_result['add_resp'].status_code == 200
            assert add_data.get('code') == 200, f'invoiceAdd 上传失败: {add_data}'
            assert add_data.get('msg') == '成功', f'invoiceAdd msg 不为"成功": {add_data.get("msg")}'
            assert upload_result.get('receive_invoice_id'), f'receive_invoice_id 不应为空: {upload_result}'

        with allure.step('断言：applyPage 获取发票申请ID成功'):
            apply_page_data = upload_result['apply_page_data']
            assert upload_result['apply_page_resp'].status_code == 200
            assert apply_page_data.get('code') == 200, f'applyPage 查询失败: {apply_page_data}'
            assert apply_page_data.get('msg') == '成功', f'applyPage msg 不为"成功": {apply_page_data.get("msg")}'
            assert upload_result.get('receive_invoice_apply_id'), f'receive_invoice_apply_id 不应为空: {upload_result}'

        with allure.step('断言：allocationInvoiceFee 登记发票成功'):
            alloc_data = upload_result['alloc_data']
            assert upload_result['alloc_resp'].status_code == 200
            assert alloc_data.get('code') == 200, f'allocationInvoiceFee 登记失败: {alloc_data}'
            assert alloc_data.get('msg') == '成功', f'allocationInvoiceFee msg 不为"成功": {alloc_data.get("msg")}'

        with allure.step('断言：链路停在 invoice_upload 阶段'):
            assert result['stop_at'] == 'invoice_upload'

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
                '查询应收开票批次审批ID',
                '审批通过应收开票批次',
                '上传应收发票',
                '获取发票申请ID',
                '登记发票到申请',
            ]:
                assert name in step_names, f'steps 缺少: {name}'
