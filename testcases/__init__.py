"""Testcases 层 - 测试用例根包

按业务域平铺 8 个 test_*.py 文件（不再有 test_link/ 子目录）：
  test_order_basic.py        订单基础
  test_fee.py                录费用
  test_fee_notice_confirm.py 费用通知单/确认单
  test_audit.py              审批流
  test_billing.py            应收对账（link13/14）
  test_invoice.py            应收发票（link15/16/17）
  test_writeoff.py           应收核销（link18）

历史说明：原 testcases/test_link/ + testcases/test_link/receive/ 双重子目录
已展平到 testcases/ 根——"test_link" 这个名字太具体，限制后续扩展；
平铺后所有测试用例通过文件名就能直观看出所属业务域。

API 层对应：api/order/ + api/receive/
"""
