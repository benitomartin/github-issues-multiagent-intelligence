import yaml
from pydantic import BaseModel


class ErrorSpan(BaseModel):
    start: int
    end: int
    reason: str


class ValidationSummary(BaseModel):
    type: str
    score: float | None = None
    error_spans: list[ErrorSpan] | None = None
    failure_reason: str | None = None
    validator_name: str | None = None


class GuardrailResult(BaseModel):
    validation_passed: bool
    validation_summaries: list[ValidationSummary]
    validated_output: str | None = None


class GuardRailConfig(BaseModel):
    jailbreak: dict
    toxicity: dict
    secrets: dict


def load_guardrails_from_yaml(path: str) -> GuardRailConfig:
    with open(path) as f:
        data = yaml.safe_load(f)
    return GuardRailConfig(**data)


repositories = load_guardrails_from_yaml("src/config/guardrails.yaml")
