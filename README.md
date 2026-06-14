# finance-news

Proyecto de investigación para construir un agente semanal de finanzas con foco en Argentina y mercados internacionales.

## Pipeline inicial

1. Instalar herramientas locales:

```bash
brew install yt-dlp ffmpeg whisper-cpp
```

2. Descargar la playlist del podcast:

```bash
./scripts/download_podcast.sh
```

Los audios, metadatos y thumbnails quedan en `data/audio/`. El archivo `data/download-archive.txt` permite retomar sin duplicar descargas.

El downloader conserva el audio nativo de YouTube (`m4a` o `webm`) para evitar transcodificación innecesaria. Whisper lo puede leer a través de `ffmpeg`.

3. Transcribir con `mlx-whisper` en Apple Silicon:

```bash
./scripts/transcribe_mlx_whisper.sh
```

Por defecto usa `mlx-community/whisper-small-mlx` y escribe `.txt`, `.json`, `.srt`, `.vtt` y `.tsv` en `data/transcripts/`.

4. Alternativa/fallback con `whisper.cpp`: descargar un modelo GGML compatible en `models/`, por ejemplo `models/ggml-medium.bin`.

Luego ejecutar:

```bash
WHISPER_MODEL=models/ggml-medium.bin ./scripts/transcribe_whisper_cpp.sh
```

Las transcripciones quedan en `data/transcripts/` como `.txt`, `.srt` y `.json`.

5. Ver inventario:

```bash
./scripts/inventory.py
```
