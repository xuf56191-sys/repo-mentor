from repo_mentor.repository_safeguards import (
    EvidenceBudget,
    invoke_with_retry,
    redact_for_log,
)

def test_redact_for_log_hides_sensitive_values():
    secret = "sk-super-secret"

    data = {
        "MODEL_API_KEY": secret,
        "nested": {
            "password": "123456",
            "max_depth": 4,
        },
    }

    safe = redact_for_log(data)

    assert (
        safe["MODEL_API_KEY"]
        == "***REDACTED***"
    )

    assert (
        safe["nested"]["password"]
        == "***REDACTED***"
    )

    assert (
        safe["nested"]["max_depth"]
        == 4
    )

    assert secret not in str(safe)

def test_redact_for_log_hides_sensitive_values():
    secret = "sk-super-secret"

    data = {
        "MODEL_API_KEY": secret,
        "nested": {
            "password": "123456",
            "max_depth": 4,
        },
    }

    safe = redact_for_log(data)

    assert (
        safe["MODEL_API_KEY"]
        == "***REDACTED***"
    )

    assert (
        safe["nested"]["password"]
        == "***REDACTED***"
    )

    assert (
        safe["nested"]["max_depth"]
        == 4
    )

    assert secret not in str(safe)

def test_budget_stops_at_file_limit():
    budget = EvidenceBudget(
        max_files=2,
        max_chars=10_000,
    )

    budget.consume(
        file_count=1,
        char_count=100,
    )

    assert budget.stopped is False

    budget.consume(
        file_count=1,
        char_count=100,
    )

    assert budget.used_files == 2
    assert budget.stopped is True

    assert "文件预算" in (
        budget.stop_reason
        or ""
    )

def test_budget_stops_at_file_limit():
    budget = EvidenceBudget(
        max_files=2,
        max_chars=10_000,
    )

    budget.consume(
        file_count=1,
        char_count=100,
    )

    assert budget.stopped is False

    budget.consume(
        file_count=1,
        char_count=100,
    )

    assert budget.used_files == 2
    assert budget.stopped is True

    assert "文件预算" in (
        budget.stop_reason
        or ""
    )

class FakeInvalidTool:
    name = "fake_invalid_tool"

    def __init__(self):
        self.call_count = 0

    def invoke(
        self,
        args,
    ):
        self.call_count += 1

        raise ValueError(
            "invalid argument"
        )

class FakeFlakyTool:
    name = "fake_flaky_tool"

    def __init__(self):
        self.call_count = 0

    def invoke(
        self,
        args,
    ):
        self.call_count += 1

        if self.call_count == 1:
            raise TimeoutError(
                "temporary timeout"
            )

        return {
            "ok": True,
            "value": "success",
        }

def test_retry_once_then_success():
    tool = FakeFlakyTool()

    execution = invoke_with_retry(
        tool,
        {},
        max_retries=1,
    )

    assert tool.call_count == 2
    assert execution.attempts == 2

    assert (
        execution.result["ok"]
        is True
    )

    assert (
        execution.result["value"]
        == "success"
    )

    assert (
        execution.elapsed_seconds
        >= 0
    )



def test_non_retryable_error_runs_once():
    tool = FakeInvalidTool()

    execution = invoke_with_retry(
        tool,
        {},
        max_retries=1,
    )

    assert tool.call_count == 1
    assert execution.attempts == 1

    assert (
        execution.result["ok"]
        is False
    )

    assert (
        execution.result[
            "error_type"
        ]
        == "ValueError"
    )

import logging


def test_log_does_not_expose_api_key(
    caplog,
):
    secret = "sk-this-must-not-appear"

    safe_args = redact_for_log(
        {
            "MODEL_API_KEY": secret,
            "repository_path": "D:/repo",
        }
    )

    with caplog.at_level(
        logging.DEBUG
    ):
        logging.getLogger(
            "repo_mentor.test"
        ).debug(
            "args=%s",
            safe_args,
        )

    assert secret not in caplog.text

    assert (
        "***REDACTED***"
        in caplog.text
    )

