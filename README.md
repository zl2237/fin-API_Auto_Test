# PR Study - 接口自动化测试框架 + Web 测试平台

基于 pytest + requests 的接口自动化测试框架，用于物流管理系统的全流程接口测试，覆盖从新建订单到付款单核销的 25 条链路。

**核心能力：**
- 25 条链路（link1~link25），按依赖顺序递增，link25 隐含 link1~link24
- workflows 层自动处理步骤间数据依赖（order_id、审批ID 等自动传递）
- 所有业务配置参数集中存储于 YAML，Python 代码零硬编码
- data 层按环境自动加载 `*_tidb.yaml` 或 `*_pre.yaml`，通过 `.env` 中的 `TEST_ENV` 切换
- Web 平台：环境管理、一键执行、实时日志、执行历史
- CI 环境自动企微机器人通知

---

## 目录结构

```
pr_study/
├── api/                        # API 层（按业务域组织）
│   ├── order/                  # 订单域
│   │   ├── order_api.py        # 订单 CRUD + 分发
│   │   └── audit_api.py        # 资产推送审批
│   ├── receive/               # 应收域
│   │   ├── receive_account_api.py
│   │   ├── receive_apply_api.py
│   │   ├── receive_invoice_register_api.py
│   │   └── receive_writeoff_api.py
│   └── pay/                    # 付款域
│       ├── pay_account_api.py
│       ├── pay_apply_api.py
│       ├── pay_demand_api.py
│       ├── pay_demand_audit_api.py
│       ├── pay_invoice_register_api.py
│       ├── pay_writeoff_api.py
│       └── payable_api.py
│
├── config/
│   └── settings.py            # 全局配置（.env 加载）
│
├── core/
│   └── http_client.py         # HTTP 客户端
│
├── data/                       # 数据层（YAML 配置 + 数据类）
│   ├── env.py                 # YAML 加载器，按 TEST_ENV 加载 *_tidb.yaml 或 *_pre.yaml
│   ├── order/                 # 订单基础、费用、审批流、费用通知单、费用确认单
│   │   ├── order_tidb.yaml / order_pre.yaml
│   │   ├── audit_tidb.yaml / audit_pre.yaml
│   │   ├── fee_tidb.yaml / fee_pre.yaml
│   │   ├── fee_notice_tidb.yaml / fee_notice_pre.yaml
│   │   └── fee_confirm_tidb.yaml / fee_confirm_pre.yaml
│   ├── receive/               # 应收对账、开票、核销
│   │   ├── receive_account_tidb.yaml / receive_account_pre.yaml
│   │   ├── receive_invoice_tidb.yaml / receive_invoice_pre.yaml       # 开票批次 + 审核
│   │   ├── receive_invoice_upload_tidb.yaml / receive_invoice_upload_pre.yaml
│   │   └── receive_writeoff_tidb.yaml / receive_writeoff_pre.yaml
│   └── pay/                   # 应付对账、开票、付款需求、核销
│       ├── pay_account_tidb.yaml / pay_account_pre.yaml
│       ├── payable_invoice_tidb.yaml / payable_invoice_pre.yaml        # 应付开票申请
│       ├── payable_invoice_register_tidb.yaml / payable_invoice_register_pre.yaml
│       ├── pay_demand_tidb.yaml / pay_demand_pre.yaml
│       ├── pay_demand_audit_tidb.yaml / pay_demand_audit_pre.yaml
│       └── pay_writeoff_tidb.yaml / pay_writeoff_pre.yaml
│
├── testcases/                 # 测试用例层
│   ├── conftest.py            # pytest 全局配置（登录、JSON 摘要）
│   ├── order/                 # 链路 1~12
│   │   ├── test_order_basic.py
│   │   ├── test_fee.py
│   │   ├── test_audit.py
│   │   └── test_fee_notice_confirm.py
│   ├── receive/               # 链路 13~18
│   │   ├── test_receive_account.py
│   │   ├── test_receive_writeoff.py
│   │   ├── test_receive_invoice_batch.py
│   │   ├── test_receive_invoice_batch_audit.py
│   │   └── test_receive_invoice_upload.py
│   └── pay/                   # 链路 19~25
│       ├── test_pay_account.py
│       ├── test_pay_apply.py
│       ├── test_pay_invoice_register.py
│       └── test_pay_demand.py
│
├── workflows/                 # 流程编排层
│   ├── order_workflow.py      # 全流程编排入口
│   ├── order/                 # 订单域步骤
│   │   ├── order_steps.py
│   │   ├── audit_steps.py
│   │   └── fee_steps.py
│   ├── receive/               # 应收域步骤
│   │   ├── receive_account_steps.py
│   │   ├── receive_writeoff_steps.py
│   │   ├── receive_apply_steps.py
│   │   └── receive_invoice_register_steps.py
│   └── pay/                   # 付款域步骤
│       ├── pay_account_steps.py
│       ├── pay_apply_steps.py
│       ├── pay_invoice_register_steps.py
│       ├── pay_demand_steps.py
│       ├── pay_demand_audit_steps.py
│       └── pay_writeoff_steps.py
│
├── platform/                  # 🆕 Web 测试平台
│   ├── backend/               # Flask 后端 API
│   │   ├── run.py             # 启动入口
│   │   ├── requirements.txt   # Python 依赖
│   │   ├── app/
│   │   │   ├── api/           # 路由：auth / environments / exec
│   │   │   ├── core/          # config / db
│   │   │   ├── models/
│   │   │   ├── services/
│   │   │   └── utils/
│   │   └── static/            # Vue 构建产物（开发模式由 Vite 托管）
│   └── frontend/              # Vue 3 前端
│       ├── package.json
│       ├── vite.config.js
│       ├── index.html
│       └── src/
│           ├── api/           # axios 接口封装
│           ├── views/         # 页面组件
│           ├── components/    # 公共组件
│           ├── stores/        # Pinia 状态管理
│           └── utils/         # request 拦截器
│
├── notify.py                  # 企微机器人通知
├── pytest.ini                 # pytest 配置（标记定义）
├── conftest.py                # pytest 根配置（redirect）
├── .env.example               # 环境变量模板
└── requirements.txt           # Python 依赖
```

---

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 测试框架 | pytest | >=7.4.0 |
| HTTP 客户端 | requests | >=2.31.0 |
| 日志记录 | loguru | >=0.7.2 |
| YAML 配置 | PyYAML | >=6.0 |
| 后端框架 | Flask | >=3.0.0 |
| 数据库 | SQLite | 3.x（无需额外服务） |
| 前端框架 | Vue 3 + Vite | ^3.4 / ^5.0 |
| UI 组件库 | Element Plus | ^2.4.0 |

---

## 快速开始

### 1. 克隆项目

```bash
git clone http://172.16.18.55:88/root/pr_study.git
cd pr_study
```

### 2. 安装依赖

**后端（Python）：**

```bash
cd platform/backend
pip install -r requirements.txt
```

**前端（Node.js）：**

```bash
cd platform/frontend
npm install
```

### 3. 配置环境

**命令行 pytest 环境变量：**

```bash
cp .env.example .env
# 编辑 .env，关键变量：
#   BASE_URL / LOGIN_URL / USERNAME / PASSWORD   -- 被测系统地址和登录凭据
#   TEST_ENV=tidb                               -- 指定 data 层加载 tidb/pre 专属 YAML
```

Web 测试平台的启动与部署说明见 `platform/README.md`。

---

## 直接运行 pytest（命令行模式）

保留原有的 pytest 命令行能力，不依赖 Web 平台：

```bash
# 配置被测系统
cp .env.example .env
# 编辑 .env 填入 BASE_URL、USERNAME、PASSWORD

# 运行
pytest -v                          # 全部
pytest -m link1                    # 仅链路1
pytest -m "link11 or link12"       # 多条链路
pytest -m link25                   # 全流程
```

---

## 链路一览（25 条）

| 链路 | 停止阶段 | 链路 | 停止阶段 |
|------|----------|------|----------|
| link1 | 新建 | link14 | 确认应收对账 |
| link2 | 分发 | link15 | 发起应收开票批次审批 |
| link3 | 暂存 | link16 | 审核生成开票申请 |
| link4 | 提交 | link17 | 发票上传与登记 |
| link5 | 生成子订单 | link18 | 应收核销 |
| link6 | 录费用 | link19 | 发起应付对账批次 |
| link7 | 资产推送审批 | link20 | 确认应付对账 |
| link8 | 订单锁定审批 | link21 | 发起应付开票批次申请 |
| link9 | 未放款开票申请审批 | link22 | 应付发票上传与登记 |
| link10 | 供应商垫付申请审批 | link23 | 发起付款需求 |
| link11 | 生成费用通知单 | link24 | 审核生成付款单 |
| link12 | 生成费用确认单 | link25 | 付款单核销 |
| link13 | 发起应收对账批次 | | |

> 链路按依赖顺序递增，link25 隐含 link1~link24 的全部步骤。

---

## 快捷方法

`OrderWorkflow` 提供 `run_until_xxx` 系列方法：

```python
from workflows.order_workflow import OrderWorkflow

OrderWorkflow.run_until_distribute()                # link2
OrderWorkflow.run_until_stash()                    # link3
OrderWorkflow.run_until_generate_sub_order()        # link5
OrderWorkflow.run_until_record_fee(...)             # link6
OrderWorkflow.run_until_record_audit()              # link7
OrderWorkflow.run_until_order_lock()                # link8
OrderWorkflow.run_until_invoice_apply()             # link9
OrderWorkflow.run_until_supplier_advance()          # link10
OrderWorkflow.run_until_fee_notice()                # link11
OrderWorkflow.run_until_fee_confirm()               # link12
OrderWorkflow.run_until_receive_account()           # link13
OrderWorkflow.run_until_confirm_account()           # link14
OrderWorkflow.run_until_invoice_batch()             # link15
OrderWorkflow.run_until_invoice_batch_audit()      # link16
OrderWorkflow.run_until_invoice_upload()            # link17
OrderWorkflow.run_until_receive_writeoff()          # link18
OrderWorkflow.run_until_payable_account()           # link19
OrderWorkflow.run_until_confirm_payable()           # link20
OrderWorkflow.run_until_payable_invoice_apply()     # link21
OrderWorkflow.run_until_pay_demand()                # link23
OrderWorkflow.run_until_pay_demand_audit()          # link24
OrderWorkflow.run_until_pay_writeoff()              # link25
```

---

## 安全提示

- `.env` 文件包含敏感凭据，已加入 `.gitignore`
- 生产部署请修改 `ADMIN_PASSWORD` 和 `SECRET_KEY`
- 如仅内网使用，`TOKEN_EXPIRE_SECONDS` 可设为 `0`（永不过期）
- 建议在 Nginx 前配置 HTTPS（Let's Encrypt）
