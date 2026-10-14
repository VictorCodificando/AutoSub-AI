import argparse
import json
from pathlib import Path

from src.evaluation.cues import from_file
from src.evaluation.display import format_details, format_table
from src.evaluation.report import evaluate
from src.evaluation.rules import PRESETS


def main() -> None:
    parser = argparse.ArgumentParser(description="Evalúa ficheros de subtítulos sin referencia.")
    parser.add_argument("paths", nargs="+", type=Path, help="Ficheros .srt, .ass o .vtt")
    parser.add_argument("--lang", default="default", choices=sorted(PRESETS), help="Umbrales según el idioma del texto")
    parser.add_argument("--styles", help="Estilos ASS a conservar, separados por comas")
    parser.add_argument("--run", help="Etiqueta de la ejecución")
    parser.add_argument("--json", type=Path, help="Directorio donde escribir un JSON por fichero")
    parser.add_argument("--details", action="store_true", help="Muestra el peor caso de cada regla")
    args = parser.parse_args()

    styles = set(args.styles.split(",")) if args.styles else None
    thresholds = PRESETS[args.lang]

    reports = []
    for path in args.paths:
        try:
            cues = from_file(path, styles=styles)
        except Exception as e:
            print(f"No se pudo leer {path}: {e}")
            continue
        reports.append(evaluate(cues, name=path.name, thresholds=thresholds, run=args.run))

    if not reports:
        return

    print(format_table(reports))

    if args.details:
        for report in reports:
            print()
            print(format_details(report))

    if args.json:
        args.json.mkdir(parents=True, exist_ok=True)
        for report in reports:
            target = args.json / f"{Path(report.file).stem}.json"
            target.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nInformes JSON en {args.json}")


if __name__ == "__main__":
    main()
