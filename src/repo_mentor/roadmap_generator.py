"""生成并导出结构化RepoMentor学习路线。"""

from __future__ import annotations

import json
from fileinput import filename
from pathlib import Path

from pydantic import ValidationError

from repo_mentor.llm_service import create_llm
from repo_mentor.models import LearningRoadmap
from repo_mentor.prompts import FINAL_ROADMAP_PROMPT
from repo_mentor.prompt_experiment import PROJECT_ROOT

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DEMO_REPO = PROJECT_ROOT / "data" / "demo_repo"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
JSON_OUTPUT_FILE = OUTPUTS_DIR / "roadmap.json"
MARKDOWN_OUTPUT_FILE = OUTPUTS_DIR /"roadmap.md"

def load_json_file(filename: str) -> dict:
    """读取演示JSON数据。"""
    file_path = DATA_DEMO_REPO / filename

    if not file_path.exists():
        raise FileNotFoundError(f"找不到JSON文件：{file_path}")

    content = file_path.read_text(
        encoding="utf-8"
    ).strip()

    if not content:
        raise ValueError(f"JSON文件为空：{file_path}")

    return json.loads(content) #把 JSON 格式的字符串 → 转成 Python 对象（dict /list）

def load_text_file(filname:str) -> dict:
    """读取演示文本数据"""
    file_path = DATA_DEMO_REPO / filname

    if not file_path.exists():
        raise FileNotFoundError(f"找不到文本文件{file_path}")

    content = file_path.read_text(encoding='utf-8').strip()
    if not content:
        raise ValidationError(f"文本文件为空：{file_path}")
    return content

def build_prompt_inputs() -> dict[str,str]:
    """组装正式学习路线Prompt的输入。"""
    user_profile = load_json_file("user_profile.json")
    target_task = load_json_file("target_task.json")
    repository_readme = load_text_file("README.md")
    repository_tree = load_text_file("tree.txt")

    return {
        "user_profile":json.dumps(
            user_profile,
            ensure_ascii=False,
            indent=2,
        ),
        "target_task": json.dumps(
            target_task,
            ensure_ascii=False,
            indent=2,
        ),
        "repository_readme":repository_readme,
        "repository_tree": repository_tree
    }



def generate_structured_roadmap(
    user_profile: dict,
    target_task: dict,
    repository_readme: str,
    repository_tree: str,
    retrieval_context: str = "",
) -> LearningRoadmap:
    """根据指定输入生成结构化学习路线。"""
    llm = create_llm(
        thinking_enabled=False,
    )

    structured_llm = llm.with_structured_output(
        LearningRoadmap,
        method="function_calling",
        include_raw=True,
    )

    # prompt_inputs = build_prompt_inputs()

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
        "repository_readme": (
            repository_readme
            + (
                "\n\n## 当前学习模块检索证据\n"
                + retrieval_context
                if retrieval_context.strip()
                else ""
            )
        ),
        "repository_tree": repository_tree,
    }

    messages = FINAL_ROADMAP_PROMPT.format_messages(
        **prompt_inputs
    )

    result = structured_llm.invoke(messages)

    # parsed：解析后的 Pydantic 对象，成功就有，失败为None。
    # parsing_error：解析时产生的错误对象，失败才有，成功为None。
    # 两个变量配合，用来区分 “结构化输出是否正常工作”，方便调试大模型输出的问题。
    parsing_error = result.get("parsing_error")
    parsed = result.get("parsed")

    if parsing_error is not None:
        raise ValueError(
            "模型返回内容无法解析为LearningRoadmap："
            f"{parsing_error}"
        )

    if parsed is None:
        raise ValueError(
            "模型没有返回可用的LearningRoadmap对象。"
        )

    #isinstance(变量, 类)：检查变量是不是这个类的实例对象。
    if not isinstance(parsed, LearningRoadmap):
        raise TypeError(
            "结构化输出类型错误，"
            f"预期LearningRoadmap，"
            f"实际为{type(parsed).__name__}。"
        )

    return parsed

def save_roadmap_json(roadmap:LearningRoadmap) ->None:
    """将学习路线保存为JSON"""
    OUTPUTS_DIR.mkdir(parents=True,exist_ok=True)
    json_text = json.dumps(
        roadmap.model_dump(mode="json"),
        ensure_ascii=False,
        indent=2,
    )
    JSON_OUTPUT_FILE.write_text(
        json_text,
        encoding='utf-8'
    )

def load_saved_roadmap()->LearningRoadmap:
    """重新读取JSON，并再次使用Pydantic校验。"""
    if not JSON_OUTPUT_FILE.exists():
        raise FileNotFoundError(f"找不到已生成的路线文件：{JSON_OUTPUT_FILE}")
    raw_data = json.loads(
        JSON_OUTPUT_FILE.read_text(encoding='utf-8')
    )
    return  LearningRoadmap.model_validate(raw_data)

def roadmap_to_markdown(roadmap: LearningRoadmap) -> str:
    """将LearningRoadmap转换为可阅读的Markdown。"""
    lines: list[str] = []

    lines.append("# RepoMentor 个性化学习路线")
    lines.append("")

    lines.append("## 学习者分析")
    lines.append("")
    lines.append(roadmap.learner_summary)
    lines.append("")

    lines.append("### 当前已掌握技能")
    lines.append("")
    for skill in roadmap.learner_profile.known_skills:
        lines.append(f"- {skill}")

    lines.append("")
    lines.append("### 当前能力差距")
    lines.append("")
    for gap in roadmap.skill_gaps:
        lines.append(f"- {gap}")

    lines.append("")
    lines.append("## 目标任务")
    lines.append("")
    lines.append(f"**标题：** {roadmap.target_task.title}")
    lines.append("")
    lines.append(
        f"**任务说明：** {roadmap.target_task.description}"
    )
    lines.append("")
    lines.append(
        f"**预期结果：** {roadmap.target_task.expected_outcome}"
    )
    lines.append("")

    lines.append("## 每日学习计划")
    lines.append("")

    for daily_plan in roadmap.daily_plans:
        lines.append(
            f"### 第{daily_plan.day}天：{daily_plan.theme}"
        )
        lines.append("")

        for task_index, task in enumerate(
            daily_plan.tasks,
            start=1,
        ):
            lines.append(
                f"#### 任务{task_index}：{task.title}"
            )
            lines.append("")
            lines.append(f"**学习目标：** {task.objective}")
            lines.append("")
            lines.append(
                f"**阅读任务：** {task.reading_task}"
            )
            lines.append("")
            lines.append(
                f"**代码定位任务：** {task.code_location_task}"
            )
            lines.append("")
            lines.append(
                f"**实践任务：** {task.practice_task}"
            )
            lines.append("")
            lines.append(
                f"**预计时间：** {task.estimated_hours}小时"
            )
            lines.append("")

            lines.append("**仓库证据：**")
            lines.append("")

            for evidence in task.evidence_sources:
                lines.append(
                    f"- `{evidence.file_path}`："
                    f"{evidence.reason}"
                    f"（证据类型：{evidence.evidence_type}，"
                    f"可信度：{evidence.confidence}）"
                )

            lines.append("")
            lines.append("**完成标准：**")
            lines.append("")

            for criterion in task.completion_criteria:
                lines.append(f"- [ ] {criterion}")

            lines.append("")

        lines.append(
            f"**当天预期成果：** {daily_plan.daily_outcome}"
        )
        lines.append("")

    lines.append("## 风险与待确认信息")
    lines.append("")

    if roadmap.risks_and_uncertainties:
        for risk in roadmap.risks_and_uncertainties:
            lines.append(f"- {risk}")
    else:
        lines.append("- 当前没有记录风险。")

    lines.append("")
    lines.append(
        f"**预计总学习时间："
        f"{roadmap.total_estimated_hours}小时**"
    )
    lines.append("")

    return "\n".join(lines)


def save_roadmap_markdown(
    roadmap: LearningRoadmap,
) -> None:
    """将学习路线保存为Markdown。"""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    markdown_text = roadmap_to_markdown(roadmap)

    MARKDOWN_OUTPUT_FILE.write_text(
        markdown_text,
        encoding="utf-8",
    )

def review_roadmap(
    roadmap: LearningRoadmap,
) -> list[str]:
    """对生成路线进行基础质量检查。"""
    warnings: list[str] = []

    expected_days = roadmap.learner_profile.available_days
    actual_days = len(roadmap.daily_plans)

    if actual_days != expected_days:
        warnings.append(
            f"计划天数不一致：用户可用{expected_days}天，"
            f"模型生成{actual_days}天。"
        )

    daily_limit = roadmap.learner_profile.daily_hours
    calculated_total_hours = 0.0
    actual_day_numbers: list[int] = []

    for daily_plan in roadmap.daily_plans:
        actual_day_numbers.append(daily_plan.day)

        daily_total = sum(
            task.estimated_hours
            for task in daily_plan.tasks
        )

        calculated_total_hours += daily_total

        if daily_total > daily_limit:
            warnings.append(
                f"第{daily_plan.day}天预计{daily_total}小时，"
                f"超过用户每天可用的{daily_limit}小时。"
            )

        if len(daily_plan.tasks) != 1:
            warnings.append(
                f"第{daily_plan.day}天生成了"
                f"{len(daily_plan.tasks)}个LearningTask，"
                "当前版本建议每天只生成1个完整任务。"
            )

    expected_day_numbers = list(
        range(1, expected_days + 1)
    )

    if actual_day_numbers != expected_day_numbers:
        warnings.append(
            "计划中的day编号不连续或顺序错误："
            f"{actual_day_numbers}"
        )

    declared_total = roadmap.total_estimated_hours

    if abs(declared_total - calculated_total_hours) > 0.01:
        warnings.append(
            "模型填写的总时间与每日任务之和不一致："
            f"模型填写{declared_total}小时，"
            f"实际计算{calculated_total_hours}小时。"
        )

    maximum_total = daily_limit * expected_days

    if calculated_total_hours > maximum_total:
        warnings.append(
            f"整份计划预计{calculated_total_hours}小时，"
            f"超过用户最多可投入的{maximum_total}小时。"
        )

    return warnings

def main() -> None:
    """生成、导出并重新验证学习路线。"""

    try:
        print("=" * 60)
        print("正在生成结构化学习路线")
        print("=" * 60)

        user_profile = load_json_file("user_profile.json")
        target_task = load_json_file("target_task.json")
        repository_readme = load_text_file("README.md")
        repository_tree = load_text_file("tree.txt")

        roadmap = generate_structured_roadmap(
            user_profile=user_profile,
            target_task=target_task,
            repository_readme=repository_readme,
            repository_tree=repository_tree,
        )

        print("结构化输出成功")
        print(f"返回类型：{type(roadmap).__name__}")

        save_roadmap_json(roadmap)
        save_roadmap_markdown(roadmap)

        reloaded_roadmap = load_saved_roadmap()

        print("\nJSON重新读取成功")
        print(
            "重新读取后的类型："
            f"{type(reloaded_roadmap).__name__}"
        )

        warnings = review_roadmap(reloaded_roadmap)

        if warnings:
            print("\n质量检查警告：")
            for warning in warnings:
                print(f"- {warning}")
        else:
            print("\n基础质量检查通过")

        print("\n生成文件：")
        print(JSON_OUTPUT_FILE)
        print(MARKDOWN_OUTPUT_FILE)

    except FileNotFoundError as error:
        print(f"文件读取失败：{error}")

    except json.JSONDecodeError as error:
        print(
            f"JSON格式错误：第{error.lineno}行，"
            f"第{error.colno}列，{error.msg}"
        )

    except ValidationError as error:
        print("Pydantic数据校验失败：")
        print(error)

    except ValueError as error:
        print(f"结构化输出失败：{error}")

    except TypeError as error:
        print(f"类型错误：{error}")

    except OSError as error:
        print(f"文件系统错误：{error}")

    except Exception as error:
        print(
            "模型调用或未知错误："
            f"{type(error).__name__}: {error}"
        )


if __name__ == "__main__":
    main()
