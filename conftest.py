import pytest
import os
import shutil
import subprocess
from pathlib import Path

from utils.logger import log
from core.http_client import http
from config.settings import LOGIN_URL, USERNAME, PASSWORD, TOKEN_FIELD, TOKEN_TYPE, AUTH_HEADER
from config.marker_config import get_marker_config, print_marker_config

# Allure 命令路径（确保能找到）
ALLURE_CMD = os.environ.get("ALLURE_BIN", "D:\\CODE\\allure-2.35.1\\bin\\allure.bat")


# ==========================
# 工具函数：嵌套取值
# ==========================
def get_nested_value(data, key: str):
    """
    从嵌套字典中获取值，支持路径如 "data.token"

    Args:
        data: 字典
        key: 点分隔的路径，如 "data.token"

    Returns:
        嵌套的值，如果路径不存在返回 None
    """
    if not isinstance(data, dict):
        return None

    keys = key.split(".")
    result = data
    for k in keys:
        if not isinstance(result, dict):
            return None
        result = result.get(k)
        if result is None:
            return None
    return result


# ==========================
# 标记配置加载（session 级别）
# ==========================
@pytest.fixture(scope="session", autouse=True)
def marker_config_loader():
    """加载并注册标记配置"""
    config = get_marker_config()
    log.info("===== pytest 标记配置已加载 =====")

    if os.environ.get("DEBUG_MARKER_CONFIG"):
        print_marker_config()

    yield config

    log.info("===== 测试会话结束 =====")


# ==========================
# 全局登录（session级别，仅一次）
# ==========================
@pytest.fixture(scope="session", autouse=True)
def global_login():
    log.info("===== 全局登录开始（仅一次） =====")

    login_data = {"username": USERNAME, "password": PASSWORD}
    resp = http.post(
        LOGIN_URL,
        json=login_data,
        headers={"Authorization": "lele_auth"},
    )

    assert resp.status_code == 200, "登录接口请求失败"
    resp_json = resp.json()

    token = get_nested_value(resp_json, TOKEN_FIELD)
    assert token is not None, f"无法提取token：{TOKEN_FIELD}"

    auth_value = f"{TOKEN_TYPE} {token}" if TOKEN_TYPE else token
    http.session.headers.update({AUTH_HEADER: auth_value})
    log.info("✅ 登录成功，token已注入session")

    yield

    log.info("===== 全局登录fixture结束 =====")


# ==========================
# 用例结果钩子（用于后续获取用例状态）
# ==========================
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, "rep_" + report.when, report)


# ==========================
# pytest_collection_modifyitems - 动态标记过滤
# ==========================
def pytest_collection_modifyitems(items, config):
    """
    在测试收集后、运行前修改测试用例
    支持基于配置文件的标记过滤

    优先级规则：
    1. 命令行 -m 参数 > YAML 配置文件
       - 如果命令行指定了 -m，则完全使用命令行过滤
       - 如果没有指定 -m，则使用 YAML 配置过滤

    使用场景：
    - pytest              → 按 YAML 配置运行
    - pytest -m smoke    → 只跑冒烟测试（忽略 YAML）
    - pytest -m order_workflow  → 只跑全流程测试（忽略 YAML）
    """
    # 检查命令行是否指定了 -m 参数
    m_option = config.getoption("-m", default=None)

    # 如果命令行指定了 -m，完全跳过 YAML 过滤逻辑
    if m_option:
        log.info(f"📋 使用命令行 -m 过滤: {m_option}")
        return

    # 没有指定 -m，使用 YAML 配置过滤
    config_loader = get_marker_config()
    skip_markers = set()

    for category, markers in config_loader._config.items():
        if isinstance(markers, dict):
            for marker, enabled in markers.items():
                if not enabled:
                    skip_markers.add(marker)

    if not skip_markers:
        log.info("📋 YAML 配置中所有标记均为启用状态")
        return

    skipped = 0
    skipped_details = []

    for item in items:
        item_markers = {m.name for m in item.iter_markers()}

        for disabled_marker in skip_markers:
            if disabled_marker in item_markers:
                item.add_marker(pytest.mark.skip(reason=f"标记 [{disabled_marker}] 在 YAML 配置中被禁用"))
                skipped += 1
                skipped_details.append(f"  - {item.name} (禁用原因: {disabled_marker})")
                break

    if skipped > 0:
        log.info(f"📋 根据 YAML 配置，已跳过 {skipped} 个测试用例:")
        for detail in skipped_details:
            log.info(detail)


# ==========================
# ✅ 修复：session结束生成报告
# ==========================
def pytest_sessionfinish(session, exitstatus):
    """测试结束生成 Allure 报告"""

    allure_dir = session.config.getoption("--alluredir")

    if not allure_dir:
        log.warning("⚠️ 未配置 --alluredir，allure 插件未激活，跳过报告生成")
        log.warning("💡 请在 pytest.ini 中添加：--alluredir=report/allure-results")
        return

    allure_path = Path(allure_dir)

    if not allure_path.exists() or not any(allure_path.iterdir()):
        log.warning(f"⚠️ {allure_dir} 为空，可能原因：")
        log.warning("   1. 没有测试用例被执行")
        log.warning("   2. allure-pytest 未安装：pip install allure-pytest")
        log.warning("   3. 测试在收集阶段就失败了")
        return

    html_dir = Path("report/allure-html")
    try:
        log.info(f"📊 正在生成 Allure 报告（来源：{allure_dir}）...")
        result = subprocess.run(
            [ALLURE_CMD, "generate", str(allure_dir), "-o", str(html_dir), "--clean"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            log.error(f"❌ allure generate 失败: {result.stderr}")
            return

        log.info(f"✅ Allure 报告生成成功: {html_dir}")

        try:
            log.info("🌐 正在打开 Allure 报告...")
            subprocess.Popen(
                [ALLURE_CMD, "open", str(html_dir)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            log.info("✅ 浏览器已启动")
        except Exception as e:
            log.warning(f"⚠️ 自动打开浏览器失败，请手动访问: {html_dir}")

    except FileNotFoundError:
        log.error(f"❌ 未找到 allure 命令: {ALLURE_CMD}")
        log.info("💡 请确保 allure 已安装: npm install -g allure-commandline")
    except Exception as e:
        log.error(f"❌ 报告生成失败: {str(e)}")


# ==========================
# 自定义命令行选项
# ==========================
def pytest_addoption(parser):
    """添加自定义命令行选项"""
    parser.addoption(
        "--debug-markers",
        action="store_true",
        default=False,
        help="打印标记配置并退出（调试用）"
    )


def pytest_configure(config):
    """pytest 配置钩子"""
    if config.getoption("--debug-markers"):
        print_marker_config()
