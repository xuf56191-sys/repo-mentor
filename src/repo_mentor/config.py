from __future__ import annotations  #自由使用 |（联合类型）和后续定义的类作为类型提示，

#操作系统接口
import os

#数据类装饰器
from dataclasses import dataclass

#面向对象的路径处理
from pathlib import Path

#加载 .env 文件
from dotenv import load_dotenv


# config.py 位于：
# repo-mentor/src/repo_mentor/config.py
#
# parents[0] = repo_mentor
# parents[1] = src
# parents[2] = repo-mentor

"""
__file__：当前文件（即 config.py）的路径。

.resolve()：将相对路径解析为绝对路径（消除 .. 或符号链接）。

.parents[2]：向上回溯 2 级父目录。
ENV_FILE：使用 / 运算符拼接路径，得到 PROJECT_ROOT 下的 .env 文件完整路径。
\后续配合 load_dotenv(ENV_FILE) 就能精准加载配置，不依赖当前运行目录。
"""
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class ConfigError(RuntimeError):
    """项目配置错误。"""

"""
@ 是 Python 提供的“语法糖”，用于简化高阶函数的调用。

没有 @ 时：必须写成 类名 = 装饰器(类名)。

有 @ 时：直接放在类或函数定义的上方，Python 解释器会自动将下面定义的类/函数作为参数，传入 @ 后面的函数中，并将返回值重新赋值给原来的名字。

# 写法一（使用 @ 语法糖）
@dataclass
class Student:
    name: str

# 写法二（不使用 @，手动调用）
class Student:
    name: str
Student = dataclass(Student)  # 装饰器接收类，返回新的类
"""
@dataclass(frozen=True)
class Settings:
    """RepoMentor运行所需的模型配置。"""
    model_name: str
    model_api_key: str
    model_base_url: str | None
    temperature: float


"""
raise作用：
触发条件：当 value 不存在（not value 为 True）时。

执行动作：立刻创建一个 ConfigError 异常对象（通常继承自 Exception），并用 raise 把它“扔”出去。

结果：函数立即终止，底下的 return value 完全不会执行。程序的正常流程被彻底打断。

.strep()作用：移除字符串首尾两端的空白字符（包括空格、制表符 \t、换行符 \n 等），并返回处理后的新字符串。
"""
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


"""
try:：Python 说“我进去执行里面的代码了”。
temperature = float(raw_value)：尝试把字符串（比如 "36.5"）转成小数。
如果成功了：跳过 except 块，继续往下走。
如果失败了（比如 raw_value 是 "abc"）：float() 会立刻抛出一个 ValueError 异常。
此时，try 块里的代码立即停止，程序跳转到 except ValueError as error: 这一行去执行。
"""

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