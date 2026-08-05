"""运行PepoMentor v0.2差异化评测"""

from __future__ import annotations
import json
from pathlib import Path
from roadmap_generator import (
    generate_structured_roadmap,
    review_roadmap,
    roadmap_to_markdown,
)
from src.repo_mentor.config import PROJECT_ROOT
from src.repo_mentor.main import DEMO_DATA_DIR

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_DATA_DIR = PROJECT_ROOT / "data" / "demo_repo"
PROFILE_DIR = PROJECT_ROOT/ "data" / "evaluation" / "learner_profiles"
TASK_DIR = PROJECT_ROOT/ "data" / "evaluation" / "target_tasks"
OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "evaluation"
)
PROFILE_FILES = [
    "beginner.json",
    "intermediate.json",
    "limited_time.json"
]
TASK_FILES = [
    "understand_tool_calling.json",
    "prepare_new_tool.json",
]

def load_json_file(file_path:Path)->dict:
    """读取JSON文件。"""
    if not file_path.exists():
        raise FileNotFoundError(f"找不到JSON文件：{file_path}")

    content = file_path.read_text(
        encoding="utf-8"
    ).strip()

    if not content :
        raise ValueError(f"JSON文件为空：{file_path}")
    return  json.loads(content)  #把 JSON 格式的字符串 → 转成 Python 对象（dict /list）

def load_text_file(file_path:Path)->str:
    """读取text文件"""
    if not file_path.exists():
        raise FileNotFoundError(f"找不到TEXT文件：{file_path}")

    content = file_path.read_text(encoding="utf-8").strip()

    if not content:
        raise  ValueError(f"TEXT文件为空：{file_path}")
    return content

def save_evaluation_result(
        case_name:str,
        roadmap,
)->None:
    """保存单个评测案例的JSON和Markdown。"""
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)

    json_file = OUTPUT_DIR / f"{case_name}.json"
    markdown_file = OUTPUT_DIR / f"{case_name}.md"

    #model_dump()：把 Pydantic 实例 → 转成 Python 字典。
    #mode="json"：把里面特殊类型自动转换成适合 JSON 输出的类型：比如日期、UUID，会转成字符串；普通 str/int 保持原样。
    json_file.write_text(
        json.dumps(
            roadmap.model_dump(mode="json")
        )
    )
    markdown_file.write_text(
        roadmap_to_markdown(roadmap),
        encoding="utf-8",
    )

def run_evaluation() -> None:
    """运行3类学习者和2个目标任务的组合实验。"""
    repository_readme = load_text_file(
        DEMO_DATA_DIR / "README.md"
    )
    repository_tree = load_text_file(
        DEMO_DATA_DIR / "tree.txt"
    )

    total_cases = len(PROFILE_FILES) * len(TASK_FILES)
    current_case = 0

    for profile_filename in PROFILE_FILES:
        for task_filename in TASK_FILES:
            current_case += 1

            profile_path = PROFILE_DIR / profile_filename
            task_path = TASK_DIR  / task_filename

            user_profile = load_json_file(profile_path)
            target_task = load_json_file(task_path)

            profile_name = profile_path.stem  #.stem 是 Pathlib 的属性，作用：拿到文件名，去掉后缀。
            task_name = task_path.stem
            case_name = f"{profile_name}_{task_name}"

            print("\n" + "=" * 60)
            print(
                f"案例{current_case}/{total_cases}："
                f"{case_name}"
            )
            print("=" * 60)

            try:
                roadmap = generate_structured_roadmap(
                    user_profile = user_profile,
                    target_task = target_task,
                    repository_readme = repository_readme,
                    repository_tree = repository_tree
                )
                warnings = review_roadmap(roadmap)

                save_evaluation_result(
                    case_name,
                    roadmap,
                )

                print("结构化路线生成成功")
                print(f"计划天数："
                    f"{len(roadmap.daily_plans)}"
                )

                print(
                    f"预计总时间："
                    f"{roadmap.total_estimated_hours}小时"
                )

                if warnings:
                    print("质量警告：")
                    for warning in warnings:
                        print(f"- {warning}")
                else:
                    print("基础质量检查通过")

            except Exception as error:
                print(
                    f"案例生成失败："
                    f"{type(error).__name__}: {error}"
                )

def main() -> None:
    run_evaluation()

    print("\n" + "=" * 60)
    print("V0.2差异化评测运行结束")
    print(f"输出目录：{OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()

