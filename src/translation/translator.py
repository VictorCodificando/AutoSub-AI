from abc import ABC, abstractmethod

from pydantic import BaseModel
import json

from ..models import TranscriptionSegment
from ..config import settings
from google import genai


class TranslatedLine(BaseModel):
    id: int
    text: str


class TranslatedBatch(BaseModel):
    lines: list[TranslatedLine]


class TranslatorLLM(ABC):
    @abstractmethod
    def translate(
        self, segments: list[TranscriptionSegment], target_language: str, context: str
    ):
        pass


class GoogleAITranslator(TranslatorLLM):
    def __init__(self, api_key: str, model: str):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def translate(
        self, segments: list[TranscriptionSegment], target_language: str, context: str
    ):
        payload = json.dumps(
            [{"id": s.id, "text": s.text} for s in segments], ensure_ascii=False
        )
        prompt = f"""Translate into {target_language} the following subtitles.
        Return with an object per received id. Do not fuse or ommit lines.
        Keep the ids just like that.
        
        PreviousContext(Do not translate):
        {context}
        
        Subtitles:
        {payload}
        """

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": TranslatedBatch,
            },
        )
        missing = apply_translation(segments, parse_response(response))
        if missing:
            print(
                f"Warning: the model did not return {len(missing)} lines "
                f"(ids {missing[:10]}...). Keeping original text."
            )

        return None


def parse_response(response) -> dict[int, str]:
    # parsed is None when the output does not match the schema (truncated JSON, blocked)
    batch: TranslatedBatch | None = getattr(response, "parsed", None)
    if batch is None:
        return {}

    return {line.id: line.text.strip() for line in batch.lines if line.text.strip()}


def apply_translation(
    segments: list[TranscriptionSegment], translations: dict[int, str]
) -> list[int]:
    missing: list[int] = []
    for segment in segments:
        text = translations.get(segment.id)
        if text:
            segment.translated_text = text
        else:
            segment.translated_text = segment.text
            segment.translation_failed = True
            missing.append(segment.id)

    return missing


class TranslatorFactory:
    _pattern = {"google": GoogleAITranslator}

    @classmethod
    def crear(cls) -> TranslatorLLM:
        provider = settings.llm_provider
        api_key = settings.api_key
        llm_model = settings.llm_model
        clase = cls._pattern.get(settings.llm_provider)

        if clase is None:
            raise ValueError(f"Provider '{provider}' not supported")

        return clase(api_key=api_key, model=llm_model)
