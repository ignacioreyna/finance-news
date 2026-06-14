#!/usr/bin/env bash
set -euo pipefail

PLAYLIST_URL="${1:-https://www.youtube.com/watch?v=TC0fGSsymUk&list=PLECBfekwHIv06RCZuq9gLAZU0DjL8q3T2}"
OUT_DIR="${OUT_DIR:-data/audio}"
ARCHIVE_FILE="${ARCHIVE_FILE:-data/download-archive.txt}"

mkdir -p "$OUT_DIR" "$(dirname "$ARCHIVE_FILE")"

yt-dlp \
  --ignore-errors \
  --yes-playlist \
  --download-archive "$ARCHIVE_FILE" \
  --format "bestaudio[ext=m4a]/bestaudio" \
  --write-info-json \
  --write-thumbnail \
  --convert-thumbnails jpg \
  --restrict-filenames \
  --paths "$OUT_DIR" \
  --output "%(playlist_index)03d-%(upload_date>%Y-%m-%d)s-%(title).180B [%(id)s].%(ext)s" \
  "$PLAYLIST_URL"
