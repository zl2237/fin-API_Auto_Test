"""
链路测试 - 应收（Receive）域公共辅助函数

适用于 link15 ~ link17 的共享断言逻辑。
"""
from data.order import BookRealAmountData


def _build_fee_config():
    return {
        'to_customer_fees': BookRealAmountData.get_customer_standard_fees(),
        'to_supplier_fees': BookRealAmountData.get_supplier_standard_fees(),
    }


def _assert_audit_and_fee_doc_ok(result):
    """link15 前置链路（link14）断言"""
    assert result['create_data']['code'] == 200, f'新建失败: {result["create_data"]}'
    assert result['distribute_data']['code'] == 200, f'分发失败: {result["distribute_data"]}'
    gen_data = result['generate_sub_data']
    assert gen_data['code'] == 200, f'生成子订单失败: {gen_data}'
    assert len(result['record_fee_results']) == 1
    fee_1 = result['record_fee_results'][0]
    assert fee_1['resp'].status_code == 200
    assert fee_1['data']['code'] == 200
    assert fee_1.get('audit_send_resp') is not None
    assert fee_1['audit_send_resp'].status_code == 200
    assert fee_1['audit_send_data']['code'] == 200
    assert fee_1.get('audit_id')
    assert fee_1['audit_approve_resp'].status_code == 200
    assert fee_1['audit_approve_data']['code'] == 200

    lock_result = result['order_lock_result']
    assert lock_result is not None
    assert lock_result['container']
    assert lock_result['send_resp'].status_code == 200
    assert lock_result['send_data']['code'] == 200
    assert lock_result.get('audit_id')
    assert lock_result['approve_resp'].status_code == 200
    assert lock_result['approve_data']['code'] == 200

    invoice_result = result['invoice_apply_result']
    assert invoice_result is not None
    assert invoice_result['send_resp'].status_code == 200
    assert invoice_result['send_data']['code'] == 200
    assert invoice_result.get('audit_id')
    assert invoice_result['approve_resp'].status_code == 200
    assert invoice_result['approve_data']['code'] == 200

    advance_result = result['supplier_advance_result']
    assert advance_result is not None
    assert advance_result['send_resp'].status_code == 200
    assert advance_result['send_data']['code'] == 200
    assert advance_result.get('audit_id')
    assert advance_result['approve_resp'].status_code == 200
    assert advance_result['approve_data']['code'] == 200

    notice_result = result['fee_notice_result']
    assert notice_result is not None
    assert notice_result['resp'].status_code == 200
    assert notice_result['data']['code'] == 200

    fee_confirm_result = result['fee_confirm_result']
    assert fee_confirm_result is not None
    assert fee_confirm_result['resp'].status_code == 200
    assert fee_confirm_result['data']['code'] == 200

    receive_result = result['receive_account_result']
    assert receive_result is not None
    assert receive_result['put_list_resp'].status_code == 200
    assert receive_result['put_list_data'].get('code') == 200
    assert receive_result['check_resp'].status_code == 200
    assert receive_result['check_data'].get('code') == 200
    assert receive_result['submit_resp'].status_code == 200
    assert receive_result['submit_data'].get('code') == 200
    assert receive_result['submit_data'].get('msg') == '成功'
    assert receive_result['receive_account_id']
    assert receive_result['receive_account_no'].startswith('YSDZPC')

    confirm_result = result['confirm_account_result']
    assert confirm_result is not None
    assert confirm_result['detail_resp'].status_code == 200
    assert confirm_result['detail_data'].get('code') == 200
    assert confirm_result['confirm_list_resp'].status_code == 200
    assert confirm_result['confirm_list_data'].get('code') == 200
    confirm_list = confirm_result['confirm_list']
    assert confirm_list is not None
    assert isinstance(confirm_list, list)
    assert len(confirm_list) > 0
    assert confirm_result['submit_resp'].status_code == 200
    assert confirm_result['submit_data'].get('code') == 200
    assert confirm_result['submit_data'].get('msg') == '成功'
    assert confirm_result['page_resp'].status_code == 200
    assert confirm_result['page_data'].get('code') == 200


def _assert_invoice_batch_ok(result):
    invoice_batch_result = result['invoice_batch_result']
    assert invoice_batch_result is not None, 'invoice_batch_result 不应为空'
    put_list_data = invoice_batch_result['put_list_data']
    assert invoice_batch_result['put_list_resp'].status_code == 200
    assert put_list_data.get('code') == 200, f'查询应收款项列表失败: {put_list_data}'
    rate_data = invoice_batch_result['rate_data']
    assert invoice_batch_result['rate_resp'].status_code == 200
    assert rate_data.get('code') == 200, f'获取汇率失败: {rate_data}'
    assert invoice_batch_result.get('exchange_rate'), '汇率为空'
    sell_info_data = invoice_batch_result['sell_info_data']
    assert invoice_batch_result['sell_info_resp'].status_code == 200
    assert sell_info_data.get('code') == 200, f'获取开票方信息失败: {sell_info_data}'
    invoice_submit_data = invoice_batch_result['invoice_submit_data']
    assert invoice_batch_result['invoice_submit_resp'].status_code == 200
    assert invoice_submit_data.get('code') == 200, f'提交应收开票批次申请失败: {invoice_submit_data}'
    assert invoice_submit_data.get('msg') == '成功', f'提交应收开票批次申请 msg 不为"成功": {invoice_submit_data.get("msg")}'
    page_data = invoice_batch_result['page_data']
    assert invoice_batch_result['page_resp'].status_code == 200
    assert page_data.get('code') == 200, f'验证批次查询失败: {page_data}'
    assert page_data.get('msg') == '成功', f'批次查询 msg 不为"成功": {page_data.get("msg")}'
    return invoice_batch_result
