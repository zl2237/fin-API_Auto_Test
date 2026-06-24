"""
链路测试 - 应收发票（link16）

  link16 - 审核生成开票申请（link15 + auditPage + auditExecute）
"""
import allure
import pytest

from data.order import BookRealAmountData, generate_bl_no
from workflows.order_workflow import OrderWorkflow
from testcases.receive.helpers import _build_fee_config, _assert_audit_and_fee_doc_ok, _assert_invoice_batch_ok


# =============================================================================
# 链路16：新建...发起应收开票批次审批 → 审核生成开票申请
# =============================================================================
@pytest.mark.link16
class TestLink16InvoiceBatchAudit:
    """链路16：新建 → ... → 发起应收开票批次审批 → 审核生成开票申请"""

    @allure.feature("链路测试")
    @allure.story("链路16：审核生成开票申请")
    @allure.severity("critical")
    @allure.title("链路16：发起应收开票批次审批 → 审核生成开票申请")
    def test_link16_invoice_batch_audit(self):
        """验证：完整链路（LINK15 + 审核生成开票申请），链路停在 invoice_batch_audit 阶段"""
        bl_no = generate_bl_no(16)

        with allure.step('执行链路（新建→...→发起应收开票批次审批→审核生成开票申请）'):
            result = OrderWorkflow.full_flow(
                stop_at='invoice_batch_audit',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：LINK14 之前所有步骤成功'):
            _assert_audit_and_fee_doc_ok(result)

        with allure.step('断言：发起应收开票批次审批成功'):
            invoice_batch_result = _assert_invoice_batch_ok(result)
            assert invoice_batch_result.get('batch_id'), f'batch_id 不应为空: {invoice_batch_result}'

        with allure.step('断言：审核生成开票申请结果存在'):
            audit_result = result['invoice_batch_audit_result']
            assert audit_result is not None, 'invoice_batch_audit_result 不应为空'

        with allure.step('断言：auditPage 查询审批ID成功'):
            audit_query_data = audit_result['audit_query_data']
            assert audit_result['audit_query_resp'].status_code == 200
            assert audit_query_data.get('code') == 200, f'auditPage 查询失败: {audit_query_data}'
            assert audit_result.get('audit_id'), f'audit_id 不应为空: {audit_result}'

        with allure.step('断言：auditExecute 审批通过成功'):
            audit_execute_data = audit_result['audit_execute_data']
            assert audit_result['audit_execute_resp'].status_code == 200
            assert audit_execute_data.get('code') == 200, f'auditExecute 审批失败: {audit_execute_data}'
            assert '成功' in audit_execute_data.get('msg', ''), f'auditExecute msg 不含"成功": {audit_execute_data.get("msg")}'

        with allure.step('断言：链路停在 invoice_batch_audit 阶段'):
            assert result['stop_at'] == 'invoice_batch_audit'

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
            ]:
                assert name in step_names, f'steps 缺少: {name}'
