#!/usr/bin/env bash
set -euo pipefail

AUDIO_DIR="${AUDIO_DIR:-data/audio}"
TRANSCRIPT_DIR="${TRANSCRIPT_DIR:-data/transcripts}"
MODEL="${MLX_WHISPER_MODEL:-mlx-community/whisper-small-mlx}"
LANGUAGE="${LANGUAGE:-es}"

mkdir -p "$TRANSCRIPT_DIR"

shopt -s nullglob
for audio in "$AUDIO_DIR"/*.m4a "$AUDIO_DIR"/*.mp3 "$AUDIO_DIR"/*.webm; do
  stem="$(basename "$audio")"
  stem="${stem%.*}"

  if [[ -s "$TRANSCRIPT_DIR/$stem.txt" && -s "$TRANSCRIPT_DIR/$stem.json" ]]; then
    echo "Skipping existing transcript: $stem"
    continue
  fi

  echo "Transcribing: $audio"
  uvx --from mlx-whisper mlx_whisper "$audio" \
    --model "$MODEL" \
    --language "$LANGUAGE" \
    --output-dir "$TRANSCRIPT_DIR" \
    --output-name "$stem" \
    --output-format all \
    --verbose False
done
