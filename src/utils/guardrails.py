from guardrails import AsyncGuard
from guardrails.hub import DetectJailbreak, SecretsPresent, ToxicLanguage

from src.models.guardrails_models import GuardRailConfig, GuardrailResult, load_guardrails_from_yaml
from src.utils.config import settings


class GuardrailValidator:
    def __init__(self, config: GuardRailConfig):
        self.config = config

    async def check_jailbreak(self, text: str) -> GuardrailResult:
        cfg = self.config.jailbreak
        guard = AsyncGuard()
        return await guard.use(DetectJailbreak, threshold=cfg["threshold"], on_fail=cfg["on_fail"]).validate(text)

    async def check_toxicity(self, text: str) -> GuardrailResult:
        cfg = self.config.toxicity
        guard = AsyncGuard()
        return await guard.use(
            ToxicLanguage, threshold=cfg["threshold"], validation_method=cfg["validation_method"], on_fail=cfg["on_fail"]
        ).validate(text)

    async def check_secrets(self, text: str) -> GuardrailResult:
        cfg = self.config.secrets
        guard = AsyncGuard()
        return await guard.use(SecretsPresent, on_fail=cfg["on_fail"]).validate(text)


guard_config = load_guardrails_from_yaml(settings.GUARDRAILS_CONFIG)
guardrail_validator = GuardrailValidator(config=guard_config)
