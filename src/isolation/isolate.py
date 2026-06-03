from pathlib import Path
from audio_separator.separator import Separator


def isolate_voice(audio_path: Path) -> Path:
    separator = Separator(output_dir=str(audio_path.parent))

    model = "model_bs_roformer_ep_368_sdr_12.9628.ckpt"
    separator.load_model(model)

    output_files = separator.separate(str(audio_path))
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
        print(f"La pista de voz {file_path.name} del ha sido generada")
        return vocal_file
