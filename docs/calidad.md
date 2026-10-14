# Calidad

## Qué se mide

Al terminar cada ejecución, `main.py` evalúa los subtítulos generados. No compara con un subtítulo de referencia: comprueba reglas de legibilidad que cualquier subtítulo profesional debería cumplir.

Por cada subtítulo:

- **Duración.** Ni tan corto que no dé tiempo a leerlo ni tanto que se quede en pantalla en silencio.
- **Caracteres por segundo (CPS).** Velocidad de lectura necesaria.
- **Caracteres por línea (CPL)** y número de líneas.
- **Vacío.** Subtítulos sin letras ni números.
- **Tiempos invertidos.** Fin anterior al inicio.

Entre subtítulos consecutivos:

- **Solape** y **separación mínima** entre uno y el siguiente.
- **Desorden.** Un subtítulo que empieza antes que el anterior.
- **Duplicado.** El mismo texto dos veces seguidas, una señal típica de que Whisper se ha repetido.

Sobre el archivo completo:

- Mediana, percentil 90, mínimo y máximo de duración y CPS.
- **Ocupación.** Fracción del tiempo, entre el primer y el último subtítulo, que tiene texto en pantalla.
- **Traducciones fallidas.** Porcentaje de líneas que el LLM no devolvió y se quedaron en el idioma original.

Cada incumplimiento es un aviso o un error según lo lejos que esté del límite.

## Umbrales

Están basados en la guía de estilo de Netflix, con algo de margen en los avisos.

| Regla | Aviso | Error |
|---|---|---|
| Duración mínima | < 1 s | < 0,833 s (5/6 s) |
| Duración máxima | > 6 s | > 7 s |
| CPS | > 17 | > 21 |
| CPL | > 37 | > 42 |
| Líneas | | > 2 |
| Separación mínima | < 0,083 s (2 frames a 24 fps) | |

Japonés, chino y coreano se leen por carácter y tienen límites propios:

| Idioma | CPS aviso / error | CPL aviso / error |
|---|---|---|
| Japonés | 4 / 5 | 13 / 16 |
| Chino | 9 / 11 | 16 / 20 |
| Coreano | 12 / 15 | 16 / 20 |

El preset se elige según el idioma de destino de la traducción.

## Evaluar cualquier subtítulo

`scripts/evaluate.py` aplica el mismo informe a archivos `.srt`, `.ass` o `.vtt`, generados o no por AutoSub-AI. Sirve para comparar ejecuciones o tomar como referencia subtítulos profesionales.

```bash
python -m scripts.evaluate output/*.srt --lang default --run vad-065 --details
python -m scripts.evaluate subs_ja.ass --lang ja --styles Default --json informes/
```

- `--lang`: preset de umbrales (`default`, `ja`, `zh`, `ko`).
- `--run`: etiqueta para distinguir ejecuciones al comparar.
- `--styles`: en `.ass`, estilos a evaluar (para ignorar carteles y karaoke).
- `--details`: muestra el peor caso de cada regla.
- `--json`: guarda un informe JSON por archivo.

## Qué no mide

El informe no sabe si el texto es correcto. Un subtítulo bien cronometrado con una transcripción equivocada o una mala traducción pasa todas las reglas. Para eso hace falta revisión manual o un subtítulo de referencia, que se usarán en los estudios de la [hoja de ruta](hoja_de_ruta.md).

Tampoco detecta frases perdidas. `coverage` (qué parte de la voz detectada tiene subtítulo) está implementada pero no se usa todavía en el pipeline.

## Resultados

Todavía no hay resultados publicados. Aquí irán las comparativas de los estudios de la 1.0.
