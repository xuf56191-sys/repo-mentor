from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# config.py 位于：
# repo-mentor/src/repo_mentor/config.py
#
# parents[0] = repo_mentor
# parents[1] = src
# parents[2] = repo-mentor
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class ConfigError(RuntimeError):
    """项目配置错误。"""


@dataclass(frozen=True)
class Settings:
    """RepoMentor运行所需的模型配置。"""

    model_provider: str
    model_name: str
    model_api_key: str
    model_base_url: str | None
    temperature: float


def require_environment_variable(variable_name: str) -> str:
    """
    读取必填环境变量。

    如果变量不存在或内容为空，抛出清晰的配置异常。
    """
    value = os.getenv(variable_name, "").strip()

    if not value:
        raise ConfigError(
            f"缺少配置项 {variable_name}，"
            "请检查项目根目录下的 .env 文件。"
        )

    return value


def parse_temperature() -> float:
    """读取并校验模型temperature配置。"""
    raw_value = os.getenv("TEMPERATURE", "0.2").strip()

    try:
        temperature = float(raw_value)
    except ValueError as error:
        raise ConfigError(
            f"TEMPERATURE 必须是数字，当前内容为：{raw_value!r}"
        ) from error

    if not 0.0 <= temperature <= 2.0:
        raise ConfigError(
            "TEMPERATURE 必须在 0.0 到 2.0 之间。"
        )

    return temperature


def load_settings() -> Settings:
    """
    从项目根目录的.env文件加载配置。

    返回经过基本检查的Settings对象。
    """
    if not ENV_FILE.exists():
        raise ConfigError(
            "项目根目录中不存在 .env 文件。"
            "请复制 .env.example 并创建本地 .env。"
        )

    load_dotenv(dotenv_path=ENV_FILE)

    base_url = os.getenv("MODEL_BASE_URL", "").strip()

    return Settings(
        model_provider=require_environment_variable("MODEL_PROVIDER"),
        model_name=require_environment_variable("MODEL_NAME"),
        model_api_key=require_environment_variable("MODEL_API_KEY"),
        model_base_url=base_url or None,
        temperature=parse_temperature(),
    )


def main() -> None:
    """单独运行config.py时检查配置是否正确。"""
    try:
        settings = load_settings()
    except ConfigError as error:
        print("=" * 50)
        print("配置检查失败")
        print("=" * 50)
        print(error)
        raise SystemExit(1) from error

    print("=" * 50)
    print("配置检查成功")
    print("=" * 50)
    print(f"模型提供商：{settings.model_provider}")
    print(f"模型名称：{settings.model_name}")
    print(
        "自定义接口地址："
        f"{settings.model_base_url or '未设置，使用平台默认地址'}"
    )
    print(f"Temperature：{settings.temperature}")
    print("API Key：已读取，但不会显示具体内容")


if __name__ == "__main__":
    main()