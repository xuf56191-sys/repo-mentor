"""根据目标任务对真实仓库文件进行相关性排序。"""

from __future__ import annotations
import  re
from pathlib import Path

from repo_mentor.models import (
    RankedRepositoryFile,
    RepositoryEvidence,
    TargetTask,
)

from repo_mentor.repository_reader import (
    read_repository_onboarding_docs,
)

from repo_mentor.repository_service import (
    validate_repository_path,
)

from repo_mentor.repository_tree import (
    DEFAULT_IGNORED_NAMES,
    should_ignore,
)


TARGET_KEYWORD_MAP = {
    "工具": {
        "tool",
        "tools",
    },
    "调用": {
        "call",
        "invoke",
        "tool",
    },
    "工作流": {
        "graph",
        "workflow",
        "node",
        "nodes",
        "state",
    },
    "状态": {
        "state",
    },
    "目录树": {
        "tree",
        "repository_tree",
    },
    "扫描": {
        "tree",
        "scan",
        "repository",
    },
    "路径": {
        "path",
        "repository_service",
    },
    "读取": {
        "read",
        "reader",
    },
    "证据": {
        "evidence",
        "reader",
        "repository",
    },
    "路线": {
        "roadmap",
    },
    "学习路线": {
        "roadmap",
        "learning",
    },
    "提示词": {
        "prompt",
        "prompts",
    },
    "模型": {
        "model",
        "models",
        "llm",
    },
    "结构化": {
        "model",
        "models",
        "schema",
        "roadmap",
    },
    "配置": {
        "config",
        "settings",
        "pyproject",
        "requirements",
    },
    "测试": {
        "test",
        "tests",
        "pytest",
    },
    "文档": {
        "readme",
        "docs",
        "contributing",
    },
    "贡献": {
        "contributing",
        "issue",
        "test",
        "tests",
    },
}

def extract_target_keywords(
    target_task: TargetTask,
) -> set[str]:
    """从目标任务中提取用于路径匹配的关键词。"""

    target_text = " ".join(
        [
            target_task.title,
            target_task.description,
            target_task.expected_outcome,
        ]
    ).lower()

    keywords: set[str] = set()

    # 提取目标中直接存在的英文词。
    english_words = re.findall(
        r"[a-zA-Z][a-zA-Z0-9_-]*",
        target_text,
    )

    for word in english_words:
        if len(word) >= 2:
            keywords.add(word.lower())

    # 将常见中文目标词映射为文件路径关键词。
    for trigger, mapped_keywords in (
        TARGET_KEYWORD_MAP.items()
    ):
        if trigger.lower() in target_text:
            keywords.update(mapped_keywords)

    return keywords

def extract_target_keywords(
    target_task: TargetTask,
) -> set[str]:
    """从目标任务中提取用于路径匹配的关键词。"""

    target_text = " ".join(
        [
            target_task.title,
            target_task.description,
            target_task.expected_outcome,
        ]
    ).lower()

    keywords: set[str] = set()

    # 提取目标中直接存在的英文词。
    english_words = re.findall(
        r"[a-zA-Z][a-zA-Z0-9_-]*",
        target_text,
    )

    for word in english_words:
        if len(word) >= 2:
            keywords.add(word.lower())

    # 将常见中文目标词映射为文件路径关键词。
    for trigger, mapped_keywords in (
        TARGET_KEYWORD_MAP.items()
    ):
        if trigger.lower() in target_text:
            keywords.update(mapped_keywords)

    return keywords

ENTRY_FILE_NAMES = {
    "main.py",
    "app.py",
    "cli.py",
    "__main__.py",
}

CONFIG_FILE_NAMES = {
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "setup.cfg",
    "config.py",
}

ONBOARDING_FILE_NAMES = {
    "readme.md",
    "readme.rst",
    "contributing.md",
}

ENTRY_FILE_NAMES = {
    "main.py",
    "app.py",
    "cli.py",
    "__main__.py",
}

CONFIG_FILE_NAMES = {
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "setup.cfg",
    "config.py",
}

ONBOARDING_FILE_NAMES = {
    "readme.md",
    "readme.rst",
    "contributing.md",
}

def is_test_file(
    relative_path: str,
) -> bool:
    """判断路径是否属于测试文件。"""

    path = Path(relative_path)

    lower_parts = {
        part.lower()
        for part in path.parts
    }

    filename = path.name.lower()

    return (
        "tests" in lower_parts
        or "test" in lower_parts
        or filename.startswith("test_")
        or filename.endswith("_test.py")
    )

def find_readme_reference(
    readme_content: str,
    candidate_path: str,
) -> str | None:
    """寻找README中对候选文件的真实引用。"""

    candidate_lower = candidate_path.lower()

    filename = (
        Path(candidate_path)
        .name
        .lower()
    )

    for line in readme_content.splitlines():
        lower_line = line.lower()

        if (
            candidate_lower in lower_line
            or filename in lower_line
        ):
            cleaned_line = line.strip()

            if cleaned_line:
                return cleaned_line[:300]

    return None

def score_candidate_file(
    relative_path: str,
    target_task: TargetTask,
    target_keywords: set[str],
    readme_path: str | None,
    readme_content: str | None,
) -> RankedRepositoryFile | None:
    """根据目标任务计算一个真实文件的相关性。"""

    path_lower = relative_path.lower()
    filename_lower = (
        Path(relative_path)
        .name
        .lower()
    )

    score = 0.0
    reasons: list[str] = []
    evidence: list[RepositoryEvidence] = []

    # -------------------------------------------------
    # 规则1：路径与目标关键词匹配
    # -------------------------------------------------

    matched_keywords = sorted(
        keyword
        for keyword in target_keywords
        if keyword in path_lower
    )

    if matched_keywords:
        keyword_score = min(
            len(matched_keywords) * 2.0,
            6.0,
        )

        score += keyword_score

        reason = (
            "文件路径与目标关键词匹配："
            + ", ".join(matched_keywords)
        )

        reasons.append(reason)

        evidence.append(
            RepositoryEvidence(
                source_path=relative_path,
                snippet=None,
                reason=(
                    "该文件真实存在，且路径名称"
                    "与目标关键词存在匹配。"
                ),
                confidence=0.75,
            )
        )

    # -------------------------------------------------
    # 规则2：README明确引用这个文件
    # -------------------------------------------------

    if (
        readme_content is not None
        and readme_path is not None
    ):
        snippet = find_readme_reference(
            readme_content,
            relative_path,
        )

        if snippet is not None:
            score += 3.0

            reasons.append(
                "README明确引用了该文件"
            )

            evidence.append(
                RepositoryEvidence(
                    source_path=readme_path,
                    snippet=snippet,
                    reason=(
                        "README中存在对该候选文件"
                        "的真实引用。"
                    ),
                    confidence=0.95,
                )
            )

    # -------------------------------------------------
    # 规则3：入口文件
    # -------------------------------------------------

    if filename_lower in ENTRY_FILE_NAMES:
        score += 0.75

        reasons.append(
            "该文件属于常见项目入口文件"
        )

        evidence.append(
            RepositoryEvidence(
                source_path=relative_path,
                snippet=None,
                reason=(
                    "真实文件名属于常见入口文件名称，"
                    "但尚未读取源码确认具体职责。"
                ),
                confidence=0.55,
            )
        )

    # -------------------------------------------------
    # 规则4：配置文件
    # -------------------------------------------------

    target_text = (
        f"{target_task.title} "
        f"{target_task.description} "
        f"{target_task.expected_outcome}"
    ).lower()

    if filename_lower in CONFIG_FILE_NAMES:
        config_score = (
            2.0
            if "配置" in target_text
            else 0.5
        )

        score += config_score

        reasons.append(
            "该文件属于项目配置或依赖文件"
        )

        evidence.append(
            RepositoryEvidence(
                source_path=relative_path,
                snippet=None,
                reason=(
                    "该路径真实存在，并属于常见"
                    "配置或依赖文件。"
                ),
                confidence=0.60,
            )
        )

    # -------------------------------------------------
    # 规则5：测试文件
    # -------------------------------------------------

    if is_test_file(relative_path):
        test_score = 0.5

        if (
            "测试" in target_text
            or target_task.task_type
            in {
                "add_feature",
                "add_test",
                "solve_issue",
            }
        ):
            test_score = 2.0

        score += test_score

        reasons.append(
            "该文件属于测试路径"
        )

        evidence.append(
            RepositoryEvidence(
                source_path=relative_path,
                snippet=None,
                reason=(
                    "该文件真实存在于测试目录"
                    "或符合测试文件命名规则。"
                ),
                confidence=0.70,
            )
        )

    # -------------------------------------------------
    # 规则6：README / CONTRIBUTING
    # -------------------------------------------------

    if filename_lower in ONBOARDING_FILE_NAMES:
        score += 0.5

        reasons.append(
            "该文件属于仓库入门或贡献资料"
        )

        evidence.append(
            RepositoryEvidence(
                source_path=relative_path,
                snippet=None,
                reason=(
                    "该文件真实存在，并属于"
                    "常见仓库说明资料。"
                ),
                confidence=0.75,
            )
        )

    # 完全没有任何相关性时，不推荐。
    if score <= 0:
        return None

    # 当前只有README等入门资料真正读取过内容。
    content_status = (
        "verified"
        if filename_lower
        in ONBOARDING_FILE_NAMES
        else "needs_confirmation"
    )

    return RankedRepositoryFile(
        file_path=relative_path,
        score=round(score, 2),
        reasons=reasons,
        evidence=evidence,
        content_status=content_status,
    )

def collect_repository_files(
    repository_path: str | Path,
    *,
    max_depth: int = 4,
    max_files: int = 300,
) -> list[str]:
    """收集仓库中真实存在的文件路径。"""

    repository_info = validate_repository_path(
        repository_path
    )

    repository_root = (
        repository_info.absolute_path
    )

    collected_files: list[str] = []

    def walk(
        directory: Path,
        current_depth: int,
    ) -> None:
        if current_depth > max_depth:
            return

        if len(collected_files) >= max_files:
            return

        try:
            children = sorted(
                directory.iterdir(),
                key=lambda path: path.name.lower(),
            )
        except OSError:
            return

        for child in children:
            if len(collected_files) >= max_files:
                return

            if should_ignore(
                child,
                DEFAULT_IGNORED_NAMES,
            ):
                continue

            if child.is_symlink():
                continue

            try:
                if child.is_dir():
                    walk(
                        child,
                        current_depth + 1,
                    )

                elif child.is_file():
                    relative_path = (
                        child
                        .relative_to(repository_root)
                        .as_posix()
                    )

                    collected_files.append(
                        relative_path
                    )

            except OSError:
                continue

    walk(
        repository_root,
        current_depth=0,
    )

    return collected_files

def rank_target_files(
    repository_path: str | Path,
    target_task: TargetTask,
    *,
    top_n: int = 8,
) -> list[RankedRepositoryFile]:
    """返回与目标任务最相关的Top-N真实文件。"""

    if top_n < 1:
        raise ValueError(
            "top_n必须大于等于1。"
        )

    repository_info = validate_repository_path(
        repository_path
    )

    repository_files = collect_repository_files(
        repository_info.absolute_path
    )

    target_keywords = extract_target_keywords(
        target_task
    )

    onboarding_result = (
        read_repository_onboarding_docs(
            repository_info.absolute_path
        )
    )

    readme_path: str | None = None
    readme_content: str | None = None

    for document in onboarding_result.documents:
        if document.document_type == "readme":
            readme_path = document.relative_path
            readme_content = document.content
            break

    ranked_files: list[RankedRepositoryFile] = []

    for relative_path in repository_files:
        ranked_file = score_candidate_file(
            relative_path=relative_path,
            target_task=target_task,
            target_keywords=target_keywords,
            readme_path=readme_path,
            readme_content=readme_content,
        )

        if ranked_file is not None:
            ranked_files.append(
                ranked_file
            )

    ranked_files.sort(
        key=lambda item: (
            -item.score,
            item.file_path.lower(),
        )
    )

    return ranked_files[:top_n]

def print_ranked_files(
    target_task: TargetTask,
    ranked_files: list[RankedRepositoryFile],
) -> None:
    """打印目标相关文件排序结果。"""

    print("\n" + "=" * 70)
    print(f"目标：{target_task.title}")
    print("=" * 70)

    if not ranked_files:
        print(
            "没有找到具有明确规则依据的相关文件。"
        )
        return

    for index, item in enumerate(
        ranked_files,
        start=1,
    ):
        print(
            f"\n{index}. {item.file_path}"
        )
        print(
            f"   分数：{item.score}"
        )
        print(
            f"   内容状态：{item.content_status}"
        )

        print("   推荐理由：")

        for reason in item.reasons:
            print(f"   - {reason}")

        print("   证据：")

        for evidence in item.evidence:
            print(
                f"   - 来源："
                f"{evidence.source_path}"
            )
            print(
                f"     理由："
                f"{evidence.reason}"
            )
            print(
                f"     可信度："
                f"{evidence.confidence}"
            )

            if evidence.snippet:
                print(
                    f"     片段："
                    f"{evidence.snippet}"
                )

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

TARGET_A = TargetTask(
    title="理解RepoMentor的本地仓库目录树扫描流程",
    description=(
        "理解仓库路径校验、目录遍历、"
        "忽略规则和目录树生成之间的关系"
    ),
    task_type="understand_module",
    expected_outcome=(
        "能够说明从仓库路径校验"
        "到目录树生成的完整流程"
    ),
    reference=None,
)

TARGET_B = TargetTask(
    title="理解RepoMentor的结构化学习路线生成流程",
    description=(
        "理解Prompt、数据模型、"
        "结构化输出和学习路线生成之间的关系"
    ),
    task_type="understand_module",
    expected_outcome=(
        "能够说明从Prompt输入"
        "到LearningRoadmap输出的流程"
    ),
    reference=None,
)

def main() -> None:
    """运行目标相关文件排序演示。"""

    first_result = rank_target_files(
        repository_path=PROJECT_ROOT,
        target_task=TARGET_A,
        top_n=6,
    )

    second_result = rank_target_files(
        repository_path=PROJECT_ROOT,
        target_task=TARGET_B,
        top_n=6,
    )

    print_ranked_files(
        TARGET_A,
        first_result,
    )

    print_ranked_files(
        TARGET_B,
        second_result,
    )


if __name__ == "__main__":
    main()