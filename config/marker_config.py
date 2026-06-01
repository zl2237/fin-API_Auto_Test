"""
pytest 标记配置加载器

功能：
1. 从 YAML 文件读取标记开关配置
2. 动态注册标记到 pytest
3. 提供运行时条件过滤支持

使用方式：
1. 配置文件 config/markers.yaml 定义开关
2. conftest.py 自动加载并注册标记
3. 运行 pytest -m <marker> 选择性执行
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Set


class MarkerConfig:
    """pytest 标记配置管理类"""

    _instance = None
    _config: Dict[str, Any] = {}
    _markers: Set[str] = set()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """从 YAML 文件加载配置"""
        config_path = Path(__file__).parent / "markers.yaml"

        if not config_path.exists():
            self._config = self._get_default_config()
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load markers.yaml: {e}")
            self._config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            "test_type": {
                "smoke": True,
                "regression": True,
                "full_flow": True
            },
            "order_operations": {
                "order_query": True,
                "order_create": True,
                "order_distribute": True,
                "order_submit": True,
                "order_workflow": True
            },
            "api_modules": {
                "entrusted_order": True,
                "business_order": True,
                "data_validation": True
            },
            "priority": {
                "critical": True,
                "normal": True,
                "minor": False
            }
        }

    def get_enabled_markers(self) -> Set[str]:
        """
        获取所有已启用的标记

        Returns:
            启用标记的集合
        """
        enabled = set()

        for category, markers in self._config.items():
            if isinstance(markers, dict):
                for marker, enabled_flag in markers.items():
                    if enabled_flag:
                        enabled.add(marker)

        return enabled

    def is_marker_enabled(self, marker: str) -> bool:
        """
        检查某个标记是否启用

        Args:
            marker: 标记名称

        Returns:
            是否启用
        """
        return marker in self.get_enabled_markers()

    def get_marker_description(self, marker: str) -> str:
        """
        获取标记的描述信息

        Args:
            marker: 标记名称

        Returns:
            标记描述
        """
        descriptions = {
            # 测试类型
            "smoke": "冒烟测试 - 核心功能快速验证",
            "regression": "回归测试 - 完整功能验证",
            "full_flow": "完整流程测试 - 端到端测试",

            # 订单操作
            "order_query": "查询类测试",
            "order_create": "新增订单测试",
            "order_distribute": "分发订单测试",
            "order_submit": "提交订单测试",
            "order_workflow": "完整流程测试（新增→分发→提交）",

            # 接口模块
            "entrusted_order": "委托订单相关",
            "business_order": "业务订单相关",
            "data_validation": "数据验证相关",

            # 优先级
            "critical": "P0 - 核心业务流程",
            "normal": "P1 - 重要功能",
            "minor": "P2 - 一般功能",
        }
        return descriptions.get(marker, marker)

    def get_all_markers(self) -> Set[str]:
        """获取所有定义的标记（包括禁用和启用的）"""
        if self._markers:
            return self._markers

        markers = set()
        for category, category_markers in self._config.items():
            if isinstance(category_markers, dict):
                markers.update(category_markers.keys())

        self._markers = markers
        return markers

    def reload(self):
        """重新加载配置"""
        self._load_config()


# 全局实例
_marker_config = None


def get_marker_config() -> MarkerConfig:
    """获取标记配置实例"""
    global _marker_config
    if _marker_config is None:
        _marker_config = MarkerConfig()
    return _marker_config


def is_marker_enabled(marker: str) -> bool:
    """检查标记是否启用（便捷函数）"""
    return get_marker_config().is_marker_enabled(marker)


def get_enabled_markers() -> Set[str]:
    """获取所有启用标记（便捷函数）"""
    return get_marker_config().get_enabled_markers()


def print_marker_config():
    """打印当前标记配置（调试用）"""
    config = get_marker_config()
    print("\n" + "=" * 50)
    print("当前 pytest 标记配置")
    print("=" * 50)

    for category, markers in config._config.items():
        if isinstance(markers, dict):
            print(f"\n[{category}]")
            for marker, enabled in markers.items():
                status = "✓" if enabled else "✗"
                desc = config.get_marker_description(marker)
                print(f"  {status} {marker}: {desc}")

    print("\n" + "=" * 50)
    print(f"总计: {len(config.get_enabled_markers())} 个标记已启用")
    print("=" * 50 + "\n")
