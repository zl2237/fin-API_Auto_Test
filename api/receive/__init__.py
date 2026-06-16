"""API 层 - 应收（Receive）子包

应收链路 4 域：
  billing_api          应收对账（financeApi 类的同义文件）
  invoice_batch_api    应收开票批次
  invoice_upload_api   应收发票上传与登记
  receive_writeoff_api 应收核销

⚠ 历史说明：billing_api 内的类名仍叫 `FinanceApi`（与文件名不匹配），
    是从 api/finance_api.py 整体迁过来的，保留类名以确保外部调用兼容。
    如需后续重命名为 BillingApi，可全局搜索替换。
"""
