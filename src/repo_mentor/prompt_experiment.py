"""对比三版RepoMentor学习路线Prompt。"""

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

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    llm = create_llm()

    for version_name, prompt_template in ROADMAP_PROMPTS.items():
        print("=" * 60)
        print(f"正在运行Prompt：{version_name}")
        print("=" * 60)

        try:
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