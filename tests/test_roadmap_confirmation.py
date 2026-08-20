import pytest
from pydantic import ValidationError

from repo_mentor.models import RoadmapConfirmation


def test_confirmation_accepts_approval():
    confirmation = RoadmapConfirmation.model_validate({
        "action": "approve",
    })

    assert confirmation.action == "approve"
    assert confirmation.target_updates == {}
    assert confirmation.learner_updates == {}


def test_confirmation_accepts_target_revision():
    confirmation = RoadmapConfirmation.model_validate({
        "action": "revise",
        "target_updates": {
            "title": "理解 checkpoint",
        },
    })

    assert confirmation.action == "revise"
    assert confirmation.target_updates == {
        "title": "理解 checkpoint",
    }


def test_approval_rejects_revision_payload():
    with pytest.raises(
        ValidationError,
        match="批准路线时不能同时提交修改内容",
    ):
        RoadmapConfirmation.model_validate({
            "action": "approve",
            "target_updates": {
                "title": "不应该出现",
            },
        })


def test_revision_requires_updates():
    with pytest.raises(
        ValidationError,
        match="请求修改时必须提供目标或学习者更新",
    ):
        RoadmapConfirmation.model_validate({
            "action": "revise",
        })


def test_confirmation_rejects_unknown_action():
    with pytest.raises(ValidationError):
        RoadmapConfirmation.model_validate({
            "action": "skip",
        })