"""对比三版RepoMentor学习路线Prompt。"""

#类型先存为字符串，延后解析，解决「类还没定义完成就引用自己」的报错。
#只和类型提示有关，不改变程序运行结果。
from __future__ import annotations

import json
from pathlib import Path

from llm_service import create_llm
from prompts import ROADMAP_PROMPTS


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_DATA_DIR = PROJECT_ROOT / "data" / "demo_repo"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "prompt_experiments"


def load_json_file(filename: str) -> dict:
    """读取演示JSON文件。"""
    file_path = DEMO_DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"找不到JSON文件：{file_path}")

    content = file_path.read_text(encoding="utf-8").strip()

    if not content:
        raise ValueError(f"JSON文件为空：{file_path}")

    return json.loads(content)


def load_text_file(filename: str) -> str:
    """读取演示文本文件。"""
    file_path = DEMO_DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"找不到文本文件：{file_path}")

    return file_path.read_text(encoding="utf-8")

#content: object = 这个参数可以传入任意类型的数据，不限制。
def normalize_response_content(content: object) -> str:
    """将模型返回内容转换为文本。"""
    if isinstance(content, str):
        return content

    return str(content)


def run_experiments() -> None:
    """使用相同输入依次运行三版Prompt。"""
    user_profile = load_json_file("user_profile.json")
    target_task = load_json_file("target_task.json")
    repository_readme = load_text_file("README.md")
    repository_tree = load_text_file("tree.txt")

    r"""
    json.dumps(数据) = 把 Python 对象（dict/list）转成格式化 JSON 字符串
    参数说明：
    ensure_ascii=False
    ❗关键：中文不转成 \uXXXX 编码，直接显示汉字。
    如果开默认 True，中文会变成 "\u4e2d\u6587"，LLM 阅读体验差。
    indent=2
    换行 + 缩进 2 空格，输出美观、分行的 JSON 文本，方便人 / AI 阅读；
    不加 indent 就是挤成一行。
    """


    prompt_inputs = {
        "user_profile": json.dumps(
            user_profile,
            ensure_ascii=False,
            indent=2,
        ),
        "target_task": json.dumps(
            target_task,
            ensure_ascii=False,
            indent=2,
        ),
        "repository_readme": repository_readme,
        "repository_tree": repository_tree,
    }
    #parents=True：如果上级文件夹不存在，一并创建（多层目录一次性建好）exist_ok=True：文件夹已经存在也不会报错
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    llm = create_llm()

    #.items() 是字典自带方法：把字典里所有【键 和 值】成对拿出来。
    for version_name, prompt_template in ROADMAP_PROMPTS.items():
        print("=" * 60)
        print(f"正在运行Prompt：{version_name}")
        print("=" * 60)

        try:
            #format_messages()：把占位符填充完毕，组装成大模型要求的对话消息格式 [{},{}]
            #**prompt_inputs 字典解包，把里面所有内容送入模板，填充模板里的占位符
            messages = prompt_template.format_messages(**prompt_inputs)
            response = llm.invoke(messages)
            answer = normalize_response_content(response.content)

            output_file = OUTPUT_DIR / f"{version_name}.md"
            output_file.write_text(answer, encoding="utf-8")

            print(answer)
            print(f"\n结果已保存：{output_file}")

        except Exception as error:
            print(f"{version_name}运行失败：{error}")


def main() -> None:
    try:
        run_experiments()
    except FileNotFoundError as error:
        print(f"文件读取失败：{error}")
    except json.JSONDecodeError as error:
        print(
            f"JSON格式错误：第{error.lineno}行，"
            f"第{error.colno}列，{error.msg}"
        )
    except ValueError as error:
        print(f"数据内容错误：{error}")


if __name__ == "__main__":
    main()