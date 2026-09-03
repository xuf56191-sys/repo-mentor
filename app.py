"""RepoMentor Streamlit 入口：`streamlit run app.py`。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from repo_mentor.contribution_models import TargetIssue
from repo_mentor.models import LearnerProfile
from repo_mentor.ui_service import (
    analyze_ui_request,
    evaluate_ui_answers,
    save_ui_progress,
)


PROJECT_ROOT = Path(__file__).resolve().parent


def main() -> None:
    try:
        import streamlit as st
    except ImportError as error:
        raise RuntimeError(
            "尚未安装 Streamlit，请先安装 requirements-ui.txt"
        ) from error

    st.set_page_config(page_title="RepoMentor", page_icon="🧭", layout="wide")
    st.title("RepoMentor：目标 Issue 驱动的贡献学习助手")
    st.caption("限定本地仓库与当前学习任务，不是任意全仓聊天。")

    with st.sidebar:
        st.header("学习者与目标")
        repository_path = st.text_input("本地仓库路径", value=str(PROJECT_ROOT))
        current_level = st.selectbox(
            "当前水平", ["beginner", "intermediate", "advanced"]
        )
        known_skills_text = st.text_input("已掌握技能（逗号分隔）", value="Python, pytest")
        learning_goal = st.text_input("学习目标", value="完成第一个开源贡献")
        daily_hours = st.number_input("每天可投入小时", 0.5, 12.0, 2.0, 0.5)
        available_days = st.number_input("可用天数", 1, 90, 7)
        issue_title = st.text_input("Issue 标题")
        issue_description = st.text_area("Issue 描述")
        labels_text = st.text_input("Labels（逗号分隔）")
        expected_outcome = st.text_area("预期结果")
        deadline = st.date_input("截止日期（可选）", value=None)
        analyze = st.button("生成贡献学习路线", type="primary")

    if analyze:
        try:
            learner = LearnerProfile(
                current_level=current_level,
                known_skills=[
                    item.strip() for item in known_skills_text.split(",") if item.strip()
                ],
                learning_goal=learning_goal,
                daily_hours=float(daily_hours),
                available_days=int(available_days),
            )
            issue = TargetIssue(
                title=issue_title,
                description=issue_description,
                labels=[item.strip() for item in labels_text.split(",") if item.strip()],
                expected_outcome=expected_outcome,
                deadline=deadline if isinstance(deadline, date) else None,
            )
            st.session_state["bundle"] = analyze_ui_request(
                repository_path, learner, issue
            )
            st.session_state.pop("evaluation", None)
            st.success("已基于本地证据生成路线；未读取或显示任何 API Key。")
        except Exception as error:
            st.error(f"生成失败：{error}")

    bundle = st.session_state.get("bundle")
    if bundle is None:
        st.info("请在左侧填写仓库和目标 Issue，然后生成路线。")
        return

    route_tab, evidence_tab, assessment_tab, readiness_tab = st.tabs(
        ["每日路线", "证据与问答", "测验与掌握度", "贡献准备度"]
    )
    with route_tab:
        for plan in bundle.roadmap.daily_plans:
            st.subheader(f"Day {plan.day} · {plan.theme}")
            for task in plan.tasks:
                st.checkbox(task.title, key=f"task-{plan.day}-{task.title}")
                st.write(task.objective)
                st.caption(f"预计 {task.estimated_hours} 小时")

    with evidence_tab:
        st.dataframe(
            [
                {
                    "文件": chunk.source_path,
                    "行号": f"{chunk.line_start}-{chunk.line_end}",
                    "符号/标题": chunk.heading_or_symbol or "",
                }
                for chunk in bundle.evidence_layer.chunks
            ],
            use_container_width=True,
        )
        question = st.text_input("只询问当前学习任务", key="grounded-question")
        if st.button("基于证据回答") and question.strip():
            answer = bundle.evidence_layer.answer(question)
            if answer.evidence_sufficient:
                st.write(answer.answer)
                for citation in answer.citations:
                    st.code(
                        f"{citation.source_path}:{citation.line_start}-{citation.line_end}\n"
                        + citation.excerpt
                    )
            else:
                st.warning(answer.answer)

    with assessment_tab:
        answers: dict[str, str] = {}
        for question_item in bundle.assessment.questions:
            st.markdown(f"**{question_item.question_type}** · {question_item.prompt}")
            answers[question_item.question_id] = st.text_area(
                "你的回答", key=f"answer-{question_item.question_id}"
            )
        practice = bundle.assessment.practice_task
        st.markdown(f"**practice** · {practice.instructions}")
        answers[practice.practice_id] = st.text_area(
            "实践提交说明", key=f"answer-{practice.practice_id}"
        )
        if st.button("离线评估"):
            st.session_state["evaluation"] = evaluate_ui_answers(bundle, answers)

        evaluation = st.session_state.get("evaluation")
        if evaluation:
            results, mastery = evaluation
            st.metric("掌握度", f"{mastery.overall_score:.0%}")
            st.write("薄弱点：", mastery.weak_points or ["尚无可靠评分的薄弱点"])
            for result in results:
                st.write(
                    f"{result.item_id}: {result.status} · "
                    f"{result.score if result.score is not None else '待复核'} / {result.max_score}"
                )
                st.caption(result.feedback)
            if st.button("保存学习进度"):
                try:
                    plan_id = save_ui_progress(
                        PROJECT_ROOT / "data" / "repomentor.db",
                        repository_path,
                        bundle,
                        results,
                        mastery,
                    )
                    st.success(f"进度已保存，plan_id={plan_id}")
                except Exception as error:
                    st.error(f"保存失败：{error}")

    with readiness_tab:
        st.metric("贡献准备度", f"{bundle.gap.readiness_score:.1f}/100")
        st.progress(bundle.gap.readiness_score / 100)
        st.write(bundle.gap.interpretation)
        st.write("已掌握：", bundle.gap.mastered_skills or ["暂无已验证项"])
        st.write("待补知识：", bundle.gap.missing_knowledge or ["无"])
        st.dataframe(
            [item.model_dump(mode="json") for item in bundle.gap.readiness_components],
            use_container_width=True,
        )
        st.subheader("openEuler/openGauss 贡献清单")
        for item in bundle.contribution_plan.checklist:
            st.write(f"{item.status} · {item.category} · {item.item}")
        st.caption(bundle.contribution_plan.scope_statement)


if __name__ == "__main__":
    main()
