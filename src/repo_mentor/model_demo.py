"""验证RepoMentor数据模型。"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from models import (
    DailyPlan,
    EvidenceSource,
    LearnerProfile,
    LearningRoadmap,
    LearningTask,
    TargetTask,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_FILE = PROJECT_ROOT / "outputs" / "sample_roadmap.json"


def build_sample_roadmap() -> LearningRoadmap:
    """构造一份合法的演示学习路线。"""
    learner = LearnerProfile(
        current_level="会Python基础，但没有完成过Agent项目",
        known_skills=["Python基础语法", "函数与类"],
        unfamiliar_skills=["Agent工具调用", "LangGraph"],
        learning_goal="理解简单Agent项目的工具调用流程",
        daily_hours=2,
        available_days=7,
    )

    target = TargetTask(
        title="理解Demo Agent的工具调用流程",
        description="理解Agent如何选择并调用搜索工具或计算器工具",
        task_type="understand_module",
        expected_outcome="能够说明从用户输入到工具执行的完整数据流",
        reference=None,
    )

    evidence = EvidenceSource(
        file_path="agent/graph.py",
        evidence_type="source",
        reason="目录结构显示该文件可能负责Agent工作流组织",
        excerpt=None,
        confidence=0.7,
    )

    learning_task = LearningTask(
        title="理解Agent工作流入口",
        objective="找到Agent处理用户请求的主要执行路径",
        evidence_sources=[evidence],
        reading_task="阅读agent/graph.py，并记录主要节点和连接关系",
        code_location_task="找到决定是否调用工具的代码位置",
        practice_task="用文字画出用户输入到工具执行的数据流",
        completion_criteria=[
            "能够说明工作流从哪里开始",
            "能够指出工具调用的判断位置",
            "能够画出完整数据流",
        ],
        estimated_hours=2,
    )

    first_day = DailyPlan(
        day=1,
        theme="理解Agent工作流",
        tasks=[learning_task],
        daily_outcome="能够解释Agent工作流入口和工具调用路径",
    )

    return LearningRoadmap(
        learner_profile=learner,
        target_task=target,
        learner_summary="用户具备Python基础，但缺少Agent工作流实践经验",
        skill_gaps=[
            "工具调用流程",
            "Agent状态传递",
            "工作流节点连接",
        ],
        daily_plans=[first_day],
        risks_and_uncertainties=[
            "当前只有目录树，尚未读取graph.py真实内容",
        ],
        total_estimated_hours=2,
    )


def test_valid_model() -> None:
    """验证合法数据可以创建和导出。"""
    roadmap = build_sample_roadmap()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    output_text = json.dumps(
        roadmap.model_dump(),
        ensure_ascii=False,
        indent=2,
    )
    OUTPUT_FILE.write_text(output_text, encoding="utf-8")

    print("测试1通过：合法数据可以创建LearningRoadmap")
    print(f"示例JSON已保存：{OUTPUT_FILE}")


def test_invalid_daily_hours() -> None:
    """验证错误学习时间会触发校验。"""
    try:
        LearnerProfile(
            current_level="Python初学者",
            known_skills=["Python基础"],
            unfamiliar_skills=["Agent"],
            learning_goal="学习Agent",
            daily_hours=0,
            available_days=7,
        )
    except ValidationError as error:
        print("测试2通过：daily_hours=0被正确拒绝")
        print(error)
    else:
        raise AssertionError("测试2失败：错误的daily_hours没有被拒绝")


def test_extra_field() -> None:
    """验证未定义字段会触发校验。"""
    try:
        TargetTask(
            title="理解工具调用",
            description="理解Agent如何调用工具",
            task_type="understand_module",
            expected_outcome="能够说明完整工具调用流程",
            reference=None,
            unknown_field="不应该存在的字段",
        )
    except ValidationError as error:
        print("测试3通过：未知字段被正确拒绝")
        print(error)
    else:
        raise AssertionError("测试3失败：未知字段没有被拒绝")


def main() -> None:
    print("=" * 60)
    print("开始验证RepoMentor数据模型")
    print("=" * 60)

    test_valid_model()

    print("\n" + "=" * 60)
    test_invalid_daily_hours()

    print("\n" + "=" * 60)
    test_extra_field()

    print("\n" + "=" * 60)
    print("全部模型测试通过")
    print("=" * 60)


if __name__ == "__main__":
    main()