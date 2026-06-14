#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


audio_dir = Path("data/audio")
transcript_dir = Path("data/transcripts")

episodes = []
for info_file in sorted(audio_dir.glob("*.info.json")):
    with info_file.open("r", encoding="utf-8") as f:
        info = json.load(f)

    title = info.get("title") or info_file.stem
    video_id = info.get("id") or ""
    upload_date = info.get("upload_date") or ""
    duration = info.get("duration") or 0
    url = info.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}"
    transcript = next(transcript_dir.glob(f"*[{video_id}].txt"), None)

    episodes.append(
        {
            "upload_date": upload_date,
            "title": title,
            "video_id": video_id,
            "duration_minutes": round(duration / 60, 1) if duration else None,
            "url": url,
            "transcribed": transcript is not None and transcript.stat().st_size > 0,
        }
    )

print(json.dumps(episodes, ensure_ascii=False, indent=2))
