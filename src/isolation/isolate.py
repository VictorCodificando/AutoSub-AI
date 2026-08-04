from pathlib import Path
from audio_separator.separator import Separator
from ..models import Model


class Isolator(Model):
    def __init__(
        self, model: str = "model_bs_roformer_ep_368_sdr_12.9628.ckpt"
    ) -> None:
        self.separator: Separator | None = None
        self.model = model

    def load(self):
        self.separator = Separator(model_file_dir="models")
        self.separator.load_model(self.model)

    def isolate_voice(self, audio_path: Path | None) -> Path:
        self.separator.output_dir = str(audio_path.parent)
        output_files = self.separator.separate(str(audio_path))
        vocal_file = None
        for file in output_files:
            file_path = Path(f"{audio_path.parent}/{file}")
            if "Vocals" in file or "vocals" in file:
                vocal_file = file_path
            else:
                file_path.unlink(missing_ok=True)

        if vocal_file is None:
            raise Exception("No se ha generado ninguna pista de voz")
        else:
            print(f"La pista de voz {vocal_file.name} ha sido generada")
            return vocal_file

    def free(self):
        del self.separator
