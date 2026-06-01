# PR Study - 接口自动化测试框架

基于 pytest + requests 的接口自动化测试框架，用于物流管理系统的全流程接口测试。

## 项目简介

本项目是一套面向物流管理系统的接口自动化测试框架，采用分层设计（API 层、数据层、用例层），支持订单的新增、查询、分发、提交等全流程测试。

**核心能力：**
- 完整的订单生命周期测试（新增 → 分发 → 提交）
- 支持多种运行方式（全部运行、按标记运行、单独运行）
- 自动生成 Allure 测试报告
- 全局登录会话管理

---

## 目录结构

```
pr_study/
├── api/                          # API 层
│   └── order.py                  # 订单相关接口封装
│
├── config/                       # 配置层
│   ├── __init__.py              # 包初始化
│   ├── settings.py               # 全局配置（加载 .env）
│   ├── marker_config.py          # 标记配置加载器
│   └── markers.yaml              # 标记开关配置文件
│
├── core/                         # 核心模块
│   └── http_client.py            # HTTP 客户端封装
│
├── data/                         # 数据层
│   ├── __init__.py              # 包初始化
│   └── order_data.py             # 订单测试数据（字段分层设计）
│
├── testcases/                    # 测试用例层
│   └── test_order.py             # 订单接口测试用例
│
├── utils/                        # 工具模块
│   ├── logger.py                # 日志工具
│   └── file_util.py             # 文件操作工具
│
├── .env.example                  # 环境变量模板（上传 Git）
├── .env                          # 环境变量（不上传，敏感数据）
├── conftest.py                   # pytest 全局配置（登录、报告生成）
├── pytest.ini                    # pytest 配置文件
├── requirements.txt              # Python 依赖
└── README.md                     # 项目文档
```

### 分层说明

| 层级 | 目录 | 职责 |
|------|------|------|
| **用例层** | `testcases/` | 测试用例定义，断言逻辑 |
| **API 层** | `api/` | 接口封装，请求发送 |
| **数据层** | `data/` | 测试数据管理，字段分层 |
| **配置层** | `config/` | 环境配置，账号信息 |
| **核心层** | `core/` | HTTP 客户端，日志等基础设施 |
| **工具层** | `utils/` | 通用工具函数 |

---

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| pytest | ≥7.4.0 | 测试框架 |
| requests | ≥2.31.0 | HTTP 客户端 |
| loguru | ≥0.7.2 | 日志记录 |
| allure-pytest | ≥2.13.2 | 测试报告 |
| python-dotenv | ≥1.0.0 | 环境变量（可选） |

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

#### 方式一：使用 .env 文件（推荐，保护敏感数据）

```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env，填入你的真实配置
```

#### 方式二：直接修改 settings.py（不推荐，敏感数据可能泄露）

编辑 `config/settings.py` 中的默认值。

#### 配置说明

| 配置项 | 说明 | 敏感程度 |
|--------|------|----------|
| `BASE_URL` | API 基础域名 | 低 |
| `USERNAME` | 登录账号 | 高 |
| `PASSWORD` | 登录密码 | 高 |
| `TOKEN_FIELD` | Token 字段路径 | 低 |
| `ORDER_CREATE_ID` | 操作员用户ID | 中 |

> **注意**：`.env` 文件已被 `.gitignore` 忽略，不会推送到仓库。

### 3. 运行测试

```bash
# 运行全部测试
pytest

# 运行指定测试类
pytest testcases/test_order.py::TestEntrustedOrder

# 运行指定测试用例
pytest testcases/test_order.py::TestEntrustedOrder::test_entrust_order_normal

# 运行带特定标记的测试（见标记使用章节）
pytest -m order
pytest -m "order_create and not order_submit"
```

### 4. 查看报告

测试完成后会自动打开 Allure 报告（需确保 allure 命令可用）：

```bash
# 手动生成报告
allure generate report/allure-results -o report/allure-html --clean
allure open report/allure-html
```

---

## 数据层设计

### 字段分层架构

```
BaseOrderData (基础字段)
    │
    ├── 新增订单：直接使用基础字段
    │       └── AddOrderData.get_add_payload(bl_no)
    │
    ├── 分发订单：基础字段 + order_info
    │       └── DistributeOrderData.get_distribute_payload(order_info, bl_no)
    │
    └── 提交订单：基础字段 + SubmitRequiredFields (提交必填字段)
            └── SubmitOrderData.get_submit_payload(order_info, bl_no)
```

### 核心数据类

| 类名 | 用途 | 说明 |
|------|------|------|
| `BaseOrderData` | 基础字段 | 所有订单操作都需要的公共字段 |
| `SubmitRequiredFields` | 提交必填字段 | 仅提交时需要的业务字段，新增/分发时默认置空 |
| `AddOrderData` | 新增订单数据 | 基于 BaseOrderData |
| `DistributeOrderData` | 分发订单数据 | 基于 BaseOrderData + order_info |
| `SubmitOrderData` | 提交订单数据 | BaseOrderData + SubmitRequiredFields 合并 |

### 使用示例

```python
from data.order_data import (
    AddOrderData,
    DistributeOrderData,
    SubmitOrderData,
    BaseOrderData,
    SubmitRequiredFields,
    generate_bl_no
)

# ============== 新增订单 ==============
# 方式1: 仅基础字段（提交必填字段为空）
payload = AddOrderData.get_add_payload()

# 方式2: 基础字段 + 预填部分提交字段
payload = AddOrderData.get_add_payload_with_submit_fields(
    trade_term="FOB",
    carrier="MSC"
)

# 方式3: 完全自定义
payload = BaseOrderData.get_base_payload_with_overrides(
    trade_term="CIF",
    customer_id="12345"
)

# ============== 提交订单 ==============
# 标准提交
payload = SubmitOrderData.get_submit_payload(order_info, bl_no)

# 自定义部分提交字段
payload = SubmitOrderData.get_submit_payload_with_overrides(
    order_info,
    bl_no,
    trade_term="FOB",
    shipper="自定义发货人"
)
```

---

## pytest 标记使用

### 预定义标记

| 标记 | 说明 | 使用场景 |
|------|------|----------|
| `smoke` | 冒烟测试 | 核心功能快速验证 |
| `regression` | 回归测试 | 完整回归验证 |
| `full_flow` | 完整流程测试 | 端到端测试 |
| `order_query` | 查询类测试 | 委托/业务订单列表查询 |
| `order_create` | 新增订单测试 | 新增委托订单 |
| `order_distribute` | 分发订单测试 | 订单分发功能 |
| `order_submit` | 提交订单测试 | 订单提交功能 |
| `order_workflow` | 完整流程测试 | 新增→分发→提交全流程 |
| `entrusted_order` | 委托订单相关 | 委托订单模块 |
| `business_order` | 业务订单相关 | 业务订单模块 |
| `data_validation` | 数据验证相关 | 数据完整性验证 |
| `critical` | P0 - 核心业务流程 | 必须通过的核心用例 |
| `normal` | P1 - 重要功能 | 重要功能用例 |

### 标记配置文件

在 `config/markers.yaml` 中定义标记开关：

```yaml
# config/markers.yaml
test_type:
  smoke: true           # 冒烟测试开关
  regression: true      # 回归测试开关
  full_flow: true      # 完整流程开关

order_operations:
  order_query: true     # 查询类测试
  order_create: true   # 新增订单
  order_distribute: true # 分发订单
  order_submit: true   # 提交订单
  order_workflow: true # 全流程
```

### 运行方式（重点）

**核心规则：命令行 `-m` 参数 > YAML 配置文件**

| 运行命令 | 是否使用 YAML | 实际行为 |
|---------|-------------|---------|
| `pytest` | ✅ 使用 | 只跑 YAML 中标记为 `true` 的测试 |
| `pytest -m smoke` | ❌ 忽略 | 只跑冒烟测试，忽略 YAML |
| `pytest -m regression` | ❌ 忽略 | 只跑回归测试，忽略 YAML |
| `pytest -m order_workflow` | ❌ 忽略 | 只跑全流程测试，忽略 YAML |
| `pytest -m "smoke or regression"` | ❌ 忽略 | 跑冒烟或回归，忽略 YAML |
| `pytest -m "order and not order_submit"` | ❌ 忽略 | 跑订单测试（排除提交） |
| `pytest -m critical` | ❌ 忽略 | 只跑 P0 核心用例 |

**常用运行场景：**

```bash
# 场景1: 直接运行，按 YAML 配置过滤
pytest

# 场景2: 只跑冒烟测试（忽略 YAML）
pytest -m smoke

# 场景3: 只跑完整流程测试（忽略 YAML）
pytest -m order_workflow

# 场景4: 只跑新增+分发，不跑提交（忽略 YAML）
pytest -m "order_create and not order_submit"

# 场景5: 同时运行冒烟和回归
pytest -m "smoke or regression"

# 场景6: 只跑 P0 核心用例
pytest -m critical

# 场景7: 指定测试类运行
pytest testcases/test_order.py::TestEntrustedOrder

# 场景8: 指定测试用例运行
pytest testcases/test_order.py::TestEntrustedOrder::test_entrust_order_normal
```

**简化理解：**
- **不带 `-m`** → 用 `config/markers.yaml` 控制哪些跑、哪些不跑
- **带 `-m`** → 命令行说了算，完全忽略 YAML 配置

这样设计的好处：
- 不改代码，只改 YAML 配置就能切换默认行为
- 需要临时跑特定测试时，直接 `-m` 覆盖

---

## API 接口说明

### 订单 API (`api/order.py`)

| 方法 | 接口 | 说明 |
|------|------|------|
| `get_entrust_order_list()` | GET /api/order/orderEntrust/orderPage | 委托订单列表 |
| `get_business_order_list()` | GET /api/order/order/orderPage | 业务订单列表 |
| `get_order_by_bl_no()` | - | 按提单号查询订单 |
| `add_order()` | POST /api/order/orderEntrust/orderAdd | 新增订单 |
| `distribute_order()` | POST /api/order/orderEntrust/orderAdd | 分发订单 |
| `submit_order()` | POST /api/order/order/orderAdd | 提交订单 |

### 使用示例

```python
from api.order import OrderApi

# 查询委托订单列表
resp = OrderApi.get_entrust_order_list(page_no=1, page_size=20)

# 新增订单
resp = OrderApi.add_order(bl_no="TEST_BL_001")

# 按提单号查询
order_info = OrderApi.get_order_by_bl_no("TEST_BL_001")

# 分发订单
resp = OrderApi.distribute_order(order_info, bl_no="TEST_BL_001")

# 提交订单
resp = OrderApi.submit_order(order_info, bl_no="TEST_BL_001")
```

---

## 测试用例说明

### 用例类列表

| 类名 | 测试范围 |
|------|----------|
| `TestEntrustedOrder` | 委托订单列表查询、分页、排序 |
| `TestBusinessOrder` | 业务订单列表查询、分页、排序 |
| `TestOrderDataValidation` | 订单数据完整性验证 |
| `TestAddOrder` | 新增订单接口测试 |
| `TestAddAndDistribute` | 新增并分发流程测试 |
| `TestSubmitOrder` | 提交订单接口测试 |
| `TestFullWorkflow` | 完整订单流程测试 |

---

## 日志与报告

### 日志输出

- 位置：`report/logs/auto_test_YYYYMMDD_HHMMSS.log`
- 保留天数：7 天

### Allure 报告

- 结果目录：`report/allure-results/`
- HTML 报告：`report/allure-html/`
- 测试完成后自动打开浏览器

---

## 常见问题

### Q: 如何配置登录账号密码？

**方式一（推荐）：.env 文件**
```bash
cp .env.example .env
# 编辑 .env 填入真实配置
```

**方式二：直接修改 settings.py**

编辑 `config/settings.py` 中的默认值。

### Q: `.env` 文件会泄露吗？

不会。该文件已被 `.gitignore` 忽略，不会推送到仓库。

### Q: 如何修改测试数据？
编辑 `data/order_data.py` 中对应数据类的常量，或在调用时传入自定义参数。

### Q: 如何跳过登录？
`conftest.py` 中的 `global_login` fixture 负责登录，可根据需要修改。

### Q: 如何添加新的接口？
1. 在 `api/` 下创建新的 API 类
2. 在 `data/` 下创建对应的测试数据类
3. 在 `testcases/` 下编写测试用例

### Q: Allure 报告未自动生成？
确保：
1. allure-pytest 已安装
2. allure 命令可用（Windows: `allure.bat`，Linux/Mac: `allure`）
3. pytest.ini 中已配置 `--alluredir`

---

## License

MIT
