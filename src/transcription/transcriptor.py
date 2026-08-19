from pathlib import Path
from ..models import Model, TranscriptionSegment
from faster_whisper import WhisperModel
from ..utils.utils import format_time
from faster_whisper.vad import VadOptions, get_speech_timestamps
from faster_whisper.audio import decode_audio


class Transcriptor(Model):
    def __init__(
        self, model_size: str = "large-v3", language: str | None = None
    ) -> None:
        self.model_size: str | None = model_size
        self.language: str | None = language
        self.vad_options = VadOptions(
            threshold=0.45,
            min_silence_duration_ms=500,
            speech_pad_ms=300,
            max_speech_duration_s=25,
            min_speech_duration_ms=250,
        )

    def load(self):
        self.model: WhisperModel = WhisperModel(
            self.model_size, device="cuda", compute_type="float16"
        )

    def transcribe(self, audio_path: Path | None) -> list[TranscriptionSegment]:
        audio = decode_audio(str(audio_path), sampling_rate=16000)
        vad_timestamps = [
            (t["start"] / 16000, t["end"] / 16000)
            for t in get_speech_timestamps(audio, self.vad_options)
        ]

        segments, _ = self.model.transcribe(
            str(audio_path),
            beam_size=10,
            word_timestamps=True,
            language=self.language,
            vad_filter=True,
            vad_parameters=self.vad_options,
        )

        result: list[TranscriptionSegment] = []

        for index, segment in enumerate(segments):
            start = segment.words[0].start if segment.words else segment.start
            end = segment.words[-1].end if segment.words else segment.end
            start, end = adjust_timestamps(start, end, vad_timestamps)
            result.append(
                TranscriptionSegment(
                    id=index + 1,
                    start=start,
                    end=end,
                    text=segment.text,
                    translated_text="",
                )
            )

        return result

    def free(self):
        del self.model


def adjust_timestamps(start, end, timestamps):
    overlapped = [
        (va, vb) for va, vb in timestamps if min(end, vb) - max(start, va) > 0
    ]
    if not overlapped:
        return start, end
    principal = max(overlapped, key=lambda t: min(end, t[1]) - max(start, t[0]))
    return max(start, principal[0]), min(end, overlapped[-1][1])
