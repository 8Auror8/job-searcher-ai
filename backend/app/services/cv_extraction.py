"""CV → structured profile with Claude, plus a grounding check against the source text.

The grounding check is our guarantee that the AI does not invent data (RNF-11): every skill,
company, institution and certification in the AI output must literally appear in the CV text.
Items that don't are removed from the profile and reported to the user as `unverified`.
"""

import re
import time
import unicodedata
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any, Protocol

import anthropic
import structlog

from app.core.config import Settings
from app.core.errors import AppError
from app.schemas.cv import CvProfile, ExtractedProfile

log = structlog.get_logger()

PROMPT_VERSION = "cv_extraction_v1"
_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class AiUnavailable(AppError):
    status_code, code = 503, "ai_unavailable"
    message = "The AI service is not available right now. Try again or fill in the profile by hand."


class AiQuotaExceeded(AppError):
    status_code, code, message = 429, "ai_quota_exceeded", "Daily AI limit reached."


@dataclass
class ExtractionResult:
    profile: CvProfile
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    unverified: list[dict[str, str]] = field(default_factory=list)


class CvExtractor(Protocol):
    model: str

    async def extract(self, text: str, origin: str) -> ExtractionResult: ...


@cache
def load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def build_user_message(text: str, origin: str) -> str:
    source = "LinkedIn profile PDF" if origin == "linkedin_pdf" else "CV file"
    # Escape anything that could close our delimiter early (prompt-injection hardening).
    safe = text.replace("</cv_document>", "</ cv_document>")
    return (
        f'<cv_document source="{source}">\n{safe}\n</cv_document>\n\n'
        "Extract the candidate profile from the document above."
    )


class ClaudeCvExtractor:
    def __init__(self, settings: Settings, client: anthropic.AsyncAnthropic | None = None) -> None:
        self.model = settings.ai_model_extraction
        self.client = client or anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key, max_retries=2, timeout=60
        )

    async def extract(self, text: str, origin: str) -> ExtractionResult:
        started = time.perf_counter()
        try:
            response = await self.client.messages.parse(
                model=self.model,
                max_tokens=16000,
                system=load_prompt(PROMPT_VERSION),
                messages=[{"role": "user", "content": build_user_message(text, origin)}],
                output_format=ExtractedProfile,
            )
        except anthropic.RateLimitError as exc:
            log.warning("ai_rate_limited", feature="cv_extraction")
            raise AiUnavailable("The AI service is busy. Try again in a minute.") from exc
        except (anthropic.APIConnectionError, anthropic.APIStatusError) as exc:
            log.error("ai_call_failed", feature="cv_extraction", error=type(exc).__name__)
            raise AiUnavailable() from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        if response.stop_reason in {"refusal", "max_tokens"} or response.parsed_output is None:
            log.error("ai_bad_stop", feature="cv_extraction", stop_reason=response.stop_reason)
            raise AiUnavailable("The AI could not process this CV. Fill in the profile by hand.")

        profile = CvProfile.model_validate(response.parsed_output.model_dump())
        return ExtractionResult(
            profile=profile,
            model=self.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_ms=latency_ms,
        )


# ── Grounding check ────────────────────────────────────────────────────


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9+#]+", " ", value.casefold()).strip()


def _present(value: str, haystack: str) -> bool:
    needle = _norm(value)
    return bool(needle) and f" {needle} " in haystack


def ground_profile(profile: CvProfile, source_text: str) -> tuple[CvProfile, list[dict[str, str]]]:
    """Drop items that don't literally appear in the CV text and report them."""
    haystack = f" {_norm(source_text)} "
    unverified: list[dict[str, str]] = []

    def keep(field_name: str, value: str | None) -> bool:
        if not value or _present(value, haystack):
            return True
        unverified.append({"field": field_name, "value": value})
        return False

    data: dict[str, Any] = profile.model_dump()
    data["skills"] = [s for s in profile.skills if keep("skills", s)]
    data["certifications"] = [c for c in profile.certifications if keep("certifications", c)]
    for exp in data["experience"]:
        if not keep("experience.company", exp["company"]):
            exp["company"] = None
    for edu in data["education"]:
        if not keep("education.institution", edu["institution"]):
            edu["institution"] = None
    return CvProfile.model_validate(data), unverified
