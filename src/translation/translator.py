from abc import ABC, abstractmethod
from itertools import cycle

from pydantic import BaseModel
import json
import time

import httpx
from ..models import TranscriptionSegment
from ..config import settings
from google import genai
from google.genai import errors, types


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
        # Retries are handled by RotatingTranslator
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(attempts=1)
            ),
        )
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


class RotatingTranslator(TranslatorLLM):
    def __init__(
        self,
        translators: list[TranslatorLLM],
        max_consecutive_errors: int,
        retry_delay: float,
    ):
        self.translators = list(enumerate(translators, start=1))
        self._next = cycle(self.translators)
        self.max_consecutive_errors = max_consecutive_errors
        self.retry_delay = retry_delay

    def translate(
        self, segments: list[TranscriptionSegment], target_language: str, context: str
    ):
        for attempt in range(1, self.max_consecutive_errors + 1):
            number, translator = next(self._next)
            try:
                return translator.translate(segments, target_language, context)
            except (errors.APIError, httpx.TransportError) as e:
                print(
                    f"Error en la traducción con la clave {number} "
                    f"(intento {attempt}/{self.max_consecutive_errors}): {e}"
                )
                if attempt < self.max_consecutive_errors:
                    time.sleep(self.retry_delay)

        print(
            f"Error: traducción fallida tras {self.max_consecutive_errors} errores "
            f"seguidos. Se mantiene el texto original."
        )
        apply_translation(segments, {})
        return None


class TranslatorFactory:
    _pattern = {"google": GoogleAITranslator}

    @classmethod
    def crear(cls) -> TranslatorLLM:
        provider = settings.llm_provider
        llm_model = settings.llm_model
        clase = cls._pattern.get(settings.llm_provider)

        if clase is None:
            raise ValueError(f"Provider '{provider}' not supported")
        if not settings.api_keys:
            raise ValueError("API_KEYS is empty")

        translators = [
            clase(api_key=api_key, model=llm_model) for api_key in settings.api_keys
        ]
        return RotatingTranslator(
            translators,
            max_consecutive_errors=settings.max_consecutive_errors,
            retry_delay=settings.retry_delay,
        )
