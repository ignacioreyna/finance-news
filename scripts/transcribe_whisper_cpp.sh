#!/usr/bin/env bash
set -euo pipefail

AUDIO_DIR="${AUDIO_DIR:-data/audio}"
TRANSCRIPT_DIR="${TRANSCRIPT_DIR:-data/transcripts}"
MODEL="${WHISPER_MODEL:-models/ggml-medium.bin}"
WHISPER_BIN="${WHISPER_BIN:-whisper-cli}"
LANGUAGE="${LANGUAGE:-es}"

mkdir -p "$TRANSCRIPT_DIR"

if ! command -v "$WHISPER_BIN" >/dev/null 2>&1; then
  echo "Missing Whisper binary: $WHISPER_BIN" >&2
  echo "Install whisper.cpp or set WHISPER_BIN to the executable path." >&2
  exit 1
fi

if [[ ! -f "$MODEL" ]]; then
  echo "Missing model file: $MODEL" >&2
  echo "Set WHISPER_MODEL or download a whisper.cpp ggml model into models/." >&2
  exit 1
fi

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

shopt -s nullglob
for audio in "$AUDIO_DIR"/*.m4a "$AUDIO_DIR"/*.mp3 "$AUDIO_DIR"/*.webm; do
  stem="$(basename "$audio")"
  stem="${stem%.*}"
  out_base="$TRANSCRIPT_DIR/$stem"

  if [[ -s "$out_base.txt" && -s "$out_base.json" ]]; then
    echo "Skipping existing transcript: $stem"
    continue
  fi

  echo "Transcribing: $audio"
  wav="$TMP_DIR/$stem.wav"
  ffmpeg -nostdin -y -v error -i "$audio" -ar 16000 -ac 1 -c:a pcm_s16le "$wav"

  "$WHISPER_BIN" \
    -m "$MODEL" \
    -f "$wav" \
    -l "$LANGUAGE" \
    -otxt \
    -osrt \
    -oj \
    -of "$out_base"
done
