# Web 测试平台

基于 Vue 3 + Flask 的自动化测试执行平台，支持登录认证、环境管理、一键执行、实时日志和结果展示。

## 项目结构

```
platform/
├── backend/               # Flask 后端
│   ├── run.py             # Flask 启动入口
│   ├── requirements.txt   # Python 依赖
│   ├── .env.example       # 平台环境变量示例
│   └── app/               # 应用包
│       ├── api/           # 路由：auth / environments / exec
│       ├── core/          # config / db
│       ├── models/
│       ├── services/
│       └── utils/
├── frontend/              # Vue 3 前端（Vite + Element Plus）
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── api/           # axios 接口封装
│       ├── views/         # 页面组件
│       ├── components/    # 公共组件
│       ├── stores/        # Pinia 状态管理
│       └── utils/         # request 拦截器
└── README.md
```

## 环境要求

- Python >= 3.10
- Node.js >= 18
- Ubuntu 22.04+（生产部署）

## 本地启动

### 1. 安装后端依赖

```bash
cd platform/backend
pip install -r requirements.txt
```

### 2. 配置平台环境变量

```bash
cp platform/backend/.env.example platform/backend/.env
# 编辑 .env，填入管理员账号和被测系统配置
```

### 3. 启动后端

```bash
cd platform/backend
python run.py
```

服务运行在 `http://localhost:5000`。

### 4. 启动前端（开发模式）

```bash
cd platform/frontend
npm install
npm run dev
```

访问 `http://localhost:3000`（Vite 开发服务器，API 代理到 `http://localhost:5000`）。

## 生产部署（Ubuntu VM）

### 前置条件

- Ubuntu 22.04+，已安装 Python 3.10+、Node.js 18+
- 开放 5000（Flask）端口；若加 Nginx 则还需开放 80

### 步骤 1：上传项目

```bash
# 通过 scp / git clone 上传到 /opt/pr_study
cd /opt/pr_study
git clone http://172.16.18.55:88/root/pr_study.git  # 或 scp -r
```

### 步骤 2：安装后端依赖

```bash
cd platform/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 步骤 3：构建前端

```bash
cd platform/frontend
npm install
npm run build
```

### 步骤 4：复制前端产物到 backend/static

```bash
mkdir -p platform/backend/static
cp -r platform/frontend/dist/* platform/backend/static/
```

### 步骤 5：配置 Systemd

```bash
# /etc/systemd/system/pr_study.service
[Unit]
Description=PR Study Platform
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/pr_study/platform/backend
Environment="PATH=/opt/pr_study/platform/backend/.venv/bin"
ExecStart=/opt/pr_study/platform/backend/.venv/bin/python run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now pr_study
journalctl -u pr_study -f  # 查看日志
```

### 步骤 6：访问

浏览器打开 `http://172.16.18.55:90/`，使用 `admin / admin123` 登录。

> 当前环境通过端口转发将虚拟机 5000 映射到主机 `172.16.18.55:90`，因此无需暴露虚拟机 IP。

---

### 可选：使用 Nginx 反向代理（推荐用于生产）

如果你希望统一域名/端口、做静态资源缓存、HTTPS 或负载均衡，可以在 Systemd 部署完成后继续加 Nginx。

#### Nginx 配置

```bash
# /etc/nginx/sites-available/pr_study
server {
    listen 80;
    server_name <your-domain-or-ip>;

    client_max_body_size 10M;

    location / {
        root /opt/pr_study/platform/backend/static;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/pr_study /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

启用 Nginx 后，可直接访问 `http://<your-ip>`。

---

## 平台默认账号

| 账号  | 密码     |
|-------|----------|
| admin | admin123 |

在 `platform/backend/.env` 中修改 `ADMIN_USERNAME` / `ADMIN_PASSWORD`。

## 主要功能

| 功能 | 说明 |
|------|------|
| 登录认证 | 账号密码，会话级有效；错误时给出明确提示 |
| 环境配置 | 通过 Web 页面管理被测系统环境 |
| 链路选择 | 通过 pytest marker 筛选 link1 ~ link25 |
| 循环执行 | 支持指定循环次数 |
| 实时日志 | SSE 流式推送 pytest 输出到前端，自动滚动 |
| 结果汇总 | 通过 / 失败 / 跳过数量 + 失败用例详情 |
