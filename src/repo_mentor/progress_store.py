"""RepoMentor 的 SQLite 学习进度持久化层。"""

from __future__ import annotations

import os
import sqlite3
import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from repo_mentor.models import (
    EvaluationResult,
    LearnerProfile,
    LearningRoadmap,
    LearningTask,
    MasteryProfile,
    ReplanDecision,
)


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS repositories (
    repository_id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_path TEXT NOT NULL UNIQUE,
    display_path TEXT NOT NULL,
    created_at TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS learner_profiles (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    repository_id INTEGER NOT NULL,
    profile_key TEXT NOT NULL,
    profile_json TEXT NOT NULL,
    created_at TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (repository_id, profile_key),
    FOREIGN KEY (repository_id)
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS plans (
    plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    repository_id INTEGER NOT NULL,
    profile_id INTEGER NOT NULL,
    roadmap_json TEXT NOT NULL,
    mastery_json TEXT,
    replan_decision_json TEXT,
    created_at TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (repository_id)
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    FOREIGN KEY (profile_id)
        REFERENCES learner_profiles(profile_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    task_kind TEXT NOT NULL CHECK (
        task_kind IN ('roadmap', 'supplemental')
    ),
    task_order INTEGER NOT NULL,
    task_json TEXT NOT NULL,
    created_at TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (plan_id, task_kind, task_order),
    FOREIGN KEY (plan_id)
        REFERENCES plans(plan_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS assessment_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    item_id TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (plan_id, item_id),
    FOREIGN KEY (plan_id)
        REFERENCES plans(plan_id)
        ON DELETE CASCADE
);
"""


@dataclass(frozen=True)
class StoredLearningProgress:
    """从 SQLite 恢复的一次完整学习进度。"""

    repository_id: int
    repository_path: str
    plan_id: int
    learner_profile: LearnerProfile
    roadmap: LearningRoadmap
    mastery: MasteryProfile | None
    replan_decision: ReplanDecision | None
    supplemental_tasks: list[LearningTask]
    assessment_results: list[EvaluationResult]
    saved_at: str


class SQLiteProgressStore:
    """管理 RepoMentor 的长期学习进度。"""

    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.initialize()


    @staticmethod
    def normalize_repository_path(
            repository_path: str | Path,
    ) -> str:
        """生成用于仓库隔离和唯一约束的规范路径。"""
        # 1. 转成 Path并展开用户目录并得到绝对规范路径，但不要求路径必须已经存在；
        path = (
            Path(repository_path)
            .expanduser()
            .resolve(strict=False)
        )
        # 2. 转成统一使用 / 的字符串；
        normalized = path.as_posix()
        # 3. Windows 路径使用 casefold()，避免大小写产生重复仓库。
        if os.name == "nt":
            normalized = normalized.casefold()

        return normalized

    def _connect(self) -> sqlite3.Connection:
        """创建启用外键并支持按列名读取的连接。"""
        # 1. 使用 sqlite3.connect() 连接 self.database_path；
        connection = sqlite3.connect(
            self.database_path
        )
        # 2. 设置 row_factory = sqlite3.Row；
        connection.row_factory = sqlite3.Row
        # 3. 执行 PRAGMA foreign_keys = ON；
        connection.execute(
            "PRAGMA foreign_keys = ON"
        )
        return connection

    @contextmanager
    def _session(
        self,
    ) -> Iterator[sqlite3.Connection]:
        """确保每次数据库操作结束后关闭连接。"""
        connection = self._connect()

        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        """首次运行时自动创建数据库表。"""
        with self._session() as connection:
            with connection:
                connection.executescript(SCHEMA_SQL)

    def register_repository(
        self,
        repository_path: str | Path,
    ) -> int:
        """幂等注册仓库并返回 repository_id。"""
        raw_path = str(repository_path).strip()

        if not raw_path:
            raise ValueError("repository_path 不能为空")

        canonical_path = self.normalize_repository_path(
            repository_path
        )
        display_path = str(
            Path(repository_path)
            .expanduser()
            .resolve(strict=False)
        )

        with self._session() as connection:
            # 外层会话负责关闭连接，
            # 内层 Connection 上下文负责提交或回滚。
            with connection:
                connection.execute(
                    """
                    INSERT INTO repositories (
                        canonical_path,
                        display_path
                    )
                    VALUES (?, ?)
                    ON CONFLICT(canonical_path)
                    DO UPDATE SET
                        display_path = excluded.display_path,
                        updated_at = strftime(
                            '%Y-%m-%dT%H:%M:%fZ',
                            'now'
                        )
                    """,
                    (
                        canonical_path,
                        display_path,
                    ),
                )
                row = connection.execute(
                    """
                    SELECT repository_id
                    FROM repositories
                    WHERE canonical_path = ?
                    """,
                    (canonical_path,),
                ).fetchone()

        if row is None:
            raise RuntimeError(
                "仓库注册后无法读取 repository_id"
            )

        return int(row["repository_id"])

    @staticmethod
    def _dump_model(model) -> str:
        """把 Pydantic 模型稳定序列化为 JSON。"""
        return json.dumps(
            model.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
        )

    def save_progress(
        self,
        *,
        repository_path: str | Path,
        learner_profile: LearnerProfile,
        roadmap: LearningRoadmap,
        mastery: MasteryProfile | None = None,
        replan_decision: ReplanDecision | None = None,
        supplemental_tasks: list[LearningTask] | None = None,
        assessment_results: list[EvaluationResult] | None = None,
        profile_key: str = "default",
    ) -> int:
        """在一个事务中保存完整学习进度快照。"""
        clean_profile_key = profile_key.strip()

        if not clean_profile_key:
            raise ValueError("profile_key 不能为空")

        learner = LearnerProfile.model_validate(
            learner_profile
        )
        validated_roadmap = LearningRoadmap.model_validate(
            roadmap
        )
        validated_mastery = (
            MasteryProfile.model_validate(mastery)
            if mastery is not None
            else None
        )
        validated_decision = (
            ReplanDecision.model_validate(replan_decision)
            if replan_decision is not None
            else None
        )
        validated_supplemental_tasks = [
            LearningTask.model_validate(task)
            for task in (supplemental_tasks or [])
        ]
        validated_results = [
            EvaluationResult.model_validate(result)
            for result in (assessment_results or [])
        ]

        repository_id = self.register_repository(
            repository_path
        )

        roadmap_tasks = [
            task
            for daily_plan in validated_roadmap.daily_plans
            for task in daily_plan.tasks
        ]

        with self._session() as connection:
            # learner_profile、plan、tasks 和 results
            # 共享一个事务边界。
            with connection:
                connection.execute(
                    """
                    INSERT INTO learner_profiles (
                        repository_id,
                        profile_key,
                        profile_json
                    )
                    VALUES (?, ?, ?)
                    ON CONFLICT(repository_id, profile_key)
                    DO UPDATE SET
                        profile_json = excluded.profile_json,
                        updated_at = strftime(
                            '%Y-%m-%dT%H:%M:%fZ',
                            'now'
                        )
                    """,
                    (
                        repository_id,
                        clean_profile_key,
                        self._dump_model(learner),
                    ),
                )
                profile_row = connection.execute(
                    """
                    SELECT profile_id
                    FROM learner_profiles
                    WHERE repository_id = ?
                      AND profile_key = ?
                    """,
                    (
                        repository_id,
                        clean_profile_key,
                    ),
                ).fetchone()

                if profile_row is None:
                    raise RuntimeError(
                        "学习者画像保存后无法读取 profile_id"
                    )

                cursor = connection.execute(
                    """
                    INSERT INTO plans (
                        repository_id,
                        profile_id,
                        roadmap_json,
                        mastery_json,
                        replan_decision_json
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        repository_id,
                        int(profile_row["profile_id"]),
                        self._dump_model(validated_roadmap),
                        (
                            self._dump_model(validated_mastery)
                            if validated_mastery is not None
                            else None
                        ),
                        (
                            self._dump_model(validated_decision)
                            if validated_decision is not None
                            else None
                        ),
                    ),
                )
                plan_id = int(cursor.lastrowid)

                connection.executemany(
                    """
                    INSERT INTO tasks (
                        plan_id,
                        task_kind,
                        task_order,
                        task_json
                    )
                    VALUES (?, 'roadmap', ?, ?)
                    """,
                    [
                        (
                            plan_id,
                            task_order,
                            self._dump_model(task),
                        )
                        for task_order, task
                        in enumerate(roadmap_tasks)
                    ],
                )
                connection.executemany(
                    """
                    INSERT INTO tasks (
                        plan_id,
                        task_kind,
                        task_order,
                        task_json
                    )
                    VALUES (?, 'supplemental', ?, ?)
                    """,
                    [
                        (
                            plan_id,
                            task_order,
                            self._dump_model(task),
                        )
                        for task_order, task
                        in enumerate(
                            validated_supplemental_tasks
                        )
                    ],
                )
                connection.executemany(
                    """
                    INSERT INTO assessment_results (
                        plan_id,
                        item_id,
                        result_json
                    )
                    VALUES (?, ?, ?)
                    """,
                    [
                        (
                            plan_id,
                            result.item_id,
                            self._dump_model(result),
                        )
                        for result in validated_results
                    ],
                )

        return plan_id

    def load_latest_progress(
        self,
        repository_path: str | Path,
        *,
        profile_key: str = "default",
    ) -> StoredLearningProgress | None:
        """按仓库和学习者恢复最新进度快照。"""
        clean_profile_key = profile_key.strip()

        if not clean_profile_key:
            raise ValueError("profile_key 不能为空")

        canonical_path = self.normalize_repository_path(
            repository_path
        )

        with self._session() as connection:
            row = connection.execute(
                """
                SELECT
                    r.repository_id,
                    r.display_path,
                    lp.profile_json,
                    p.plan_id,
                    p.roadmap_json,
                    p.mastery_json,
                    p.replan_decision_json,
                    p.created_at
                FROM repositories AS r
                JOIN learner_profiles AS lp
                  ON lp.repository_id = r.repository_id
                JOIN plans AS p
                  ON p.repository_id = r.repository_id
                 AND p.profile_id = lp.profile_id
                WHERE r.canonical_path = ?
                  AND lp.profile_key = ?
                ORDER BY p.plan_id DESC
                LIMIT 1
                """,
                (
                    canonical_path,
                    clean_profile_key,
                ),
            ).fetchone()

            if row is None:
                return None

            supplemental_rows = connection.execute(
                """
                SELECT task_json
                FROM tasks
                WHERE plan_id = ?
                  AND task_kind = 'supplemental'
                ORDER BY task_order
                """,
                (int(row["plan_id"]),),
            ).fetchall()
            result_rows = connection.execute(
                """
                SELECT result_json
                FROM assessment_results
                WHERE plan_id = ?
                ORDER BY result_id
                """,
                (int(row["plan_id"]),),
            ).fetchall()

        mastery_json = row["mastery_json"]
        decision_json = row["replan_decision_json"]

        return StoredLearningProgress(
            repository_id=int(row["repository_id"]),
            repository_path=str(row["display_path"]),
            plan_id=int(row["plan_id"]),
            learner_profile=LearnerProfile.model_validate(
                json.loads(row["profile_json"])
            ),
            roadmap=LearningRoadmap.model_validate(
                json.loads(row["roadmap_json"])
            ),
            mastery=(
                MasteryProfile.model_validate(
                    json.loads(mastery_json)
                )
                if mastery_json is not None
                else None
            ),
            replan_decision=(
                ReplanDecision.model_validate(
                    json.loads(decision_json)
                )
                if decision_json is not None
                else None
            ),
            supplemental_tasks=[
                LearningTask.model_validate(
                    json.loads(task_row["task_json"])
                )
                for task_row in supplemental_rows
            ],
            assessment_results=[
                EvaluationResult.model_validate(
                    json.loads(result_row["result_json"])
                )
                for result_row in result_rows
            ],
            saved_at=str(row["created_at"]),
        )

