from pathlib import Path
from ..models import Model, TranscriptionSegment
from faster_whisper import WhisperModel
from faster_whisper.vad import VadOptions, get_speech_timestamps
from faster_whisper.audio import decode_audio

SAMPLE_RATE = 16000


class Transcriptor(Model):
    def __init__(
        self, model_size: str = "large-v3", language: str | None = None
    ) -> None:
        self.model_size: str | None = model_size
        self.language: str | None = language
        self.vad_options = VadOptions(
            threshold=0.65,
            min_speech_duration_ms=250,
            min_silence_duration_ms=500,
            speech_pad_ms=100,
            max_speech_duration_s=25,
        )

        self.short_region_s = 2.0
        self.context_s = 1.0

    def load(self):
        self.model: WhisperModel = WhisperModel(
            self.model_size, device="cuda", compute_type="float16"
        )

    def transcribe(self, audio_path: Path | None) -> list[TranscriptionSegment]:
        audio = decode_audio(str(audio_path), sampling_rate=SAMPLE_RATE)
        regions = [
            (t["start"] / SAMPLE_RATE, t["end"] / SAMPLE_RATE)
            for t in get_speech_timestamps(audio, self.vad_options)
        ]

        language = self.language
        if language is None:
            language, _, _ = self.model.detect_language(
                audio, vad_filter=True, vad_parameters=self.vad_options
            )
            print(f"Language detected: {language}")

        result: list[TranscriptionSegment] = []
        for start, end in regions:
            result.extend(self._transcribe_region(audio, start, end, language))

        for index, segment in enumerate(result):
            segment.id = index + 1

        return result

    def _transcribe_region(
        self, audio, start: float, end: float, language: str
    ) -> list[TranscriptionSegment]:
        context = self.context_s if end - start < self.short_region_s else 0.0
        low = max(0.0, start - context)
        high = min(len(audio) / SAMPLE_RATE, end + context)
        chunk = audio[int(low * SAMPLE_RATE) : int(high * SAMPLE_RATE)]

        segments, _ = self.model.transcribe(
            chunk,
            beam_size=10,
            word_timestamps=True,
            language=language,
            condition_on_previous_text=False,
            vad_filter=False,
        )

        found: list[TranscriptionSegment] = []
        for segment in segments:
            if segment.no_speech_prob > 0.8:
                continue
            first = segment.words[0].start if segment.words else segment.start
            last = segment.words[-1].end if segment.words else segment.end
            first, last = low + first, low + last

            if min(last, end) - max(first, start) <= 0:
                continue
            first, last = clamp(first, start, end), clamp(last, start, end)
            if last - first < 0.05:
                continue
            found.append(
                TranscriptionSegment(
                    id=1,
                    start=first,
                    end=last,
                    text=segment.text
                )
            )
        return found

    def free(self):
        del self.model


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))
