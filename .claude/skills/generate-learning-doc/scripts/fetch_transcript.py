#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["youtube-transcript-api>=1.2.4,<2"]
# ///
"""Fetch a YouTube video's transcript as plain text (no timestamps).

Usage:
  uv run fetch_transcript.py <url|video-id> [-l vi [en ...]] [--translate LANG] [-o raw.txt]

-l takes language codes in priority order; the first one the video has is used.
A code also matches its regional variants (vi → vi-VN), and uploaded captions win over auto-generated ones.
--translate asks YouTube to machine-translate that transcript (what downsub.com shows).
Without -o the text goes to stdout. The video title and channel are printed to stderr as `SOURCE:`.
"""
import argparse
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from requests import RequestException, Session
from youtube_transcript_api import CouldNotRetrieveTranscript, YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
PATH_PREFIXES = ("shorts", "embed", "live", "v")
OEMBED_URL = "https://www.youtube.com/oembed"
TIMEOUT_SECONDS = 30


class TimeoutSession(Session):
    def request(self, *args, **kwargs):
        kwargs.setdefault("timeout", TIMEOUT_SECONDS)
        return super().request(*args, **kwargs)


def video_id_from(value: str) -> str:
    value = value.strip()
    if VIDEO_ID.match(value):
        return value
    url = urlparse(value if "://" in value else f"https://{value}")
    host = (url.hostname or "").removeprefix("www.").removeprefix("m.")
    parts = [p for p in url.path.split("/") if p]
    candidate = ""
    if host == "youtu.be" and parts:
        candidate = parts[0]
    elif host == "youtube.com" or host.endswith(".youtube.com"):
        query = parse_qs(url.query)
        if "v" in query:
            candidate = query["v"][0]
        elif len(parts) >= 2 and parts[0] in PATH_PREFIXES:
            candidate = parts[1]
    if not VIDEO_ID.match(candidate):
        sys.exit(f"ERROR: cannot find a YouTube video id in {value!r}")
    return candidate


def pick_transcript(transcripts, codes):
    for code in codes:
        matches = [t for t in transcripts if t.language_code == code or t.language_code.startswith(f"{code}-")]
        if matches:
            return min(matches, key=lambda t: (t.is_generated, t.language_code != code))
    return transcripts.find_transcript(codes)


def video_source(session: Session, video_id: str) -> str:
    try:
        resp = session.get(OEMBED_URL, params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"})
        resp.raise_for_status()
        data = resp.json()
        return f"{data['title']} · {data['author_name']}"
    except (RequestException, ValueError, KeyError):
        return "unknown"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", help="YouTube URL or 11-character video id")
    ap.add_argument("-l", "--languages", nargs="+", default=["vi"], help="language codes by priority (default: vi)")
    ap.add_argument("--translate", metavar="LANG", help="translate the transcript to this language code")
    ap.add_argument("-o", "--out", type=Path, help="write to this file instead of stdout")
    args = ap.parse_args()

    video_id = video_id_from(args.video)
    session = TimeoutSession()
    try:
        transcript = pick_transcript(YouTubeTranscriptApi(http_client=session).list(video_id), args.languages)
        if args.translate:
            transcript = transcript.translate(args.translate)
        text = TextFormatter().format_transcript(transcript.fetch()) + "\n"
    except (CouldNotRetrieveTranscript, RequestException) as e:
        sys.exit(f"ERROR: {type(e).__name__}: {e}")

    print(f"SOURCE: {video_source(session, video_id)}", file=sys.stderr)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        kind = "generated" if transcript.is_generated else "manual"
        print(
            f"OK {args.out} — {transcript.language_code} ({kind}), "
            f"{len(text.splitlines())} lines, {len(text.split())} words",
            file=sys.stderr,
        )
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
