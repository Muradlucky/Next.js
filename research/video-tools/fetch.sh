#!/usr/bin/env bash
# Download the analysed video-tool repositories at pinned release tags.
# Download only: nothing is built, installed or executed.
#
# Usage: ./fetch.sh [destination]   (default: ./vendor next to this script, git-ignored)
set -euo pipefail

DEST="${1:-$(cd "$(dirname "$0")" && pwd)/vendor}"
mkdir -p "$DEST"

# HyperFrames keeps ~240 MB of regression-test videos in Git LFS; we only need sources.
export GIT_LFS_SKIP_SMUDGE=1

clone() { # <url> <tag> <dir>
  if [ -d "$DEST/$3/.git" ]; then
    echo "skip: $3 already exists"
    return
  fi
  echo "fetch: $3 @ $2"
  git clone --quiet --depth 1 --branch "$2" --filter=blob:limit=5m "$1" "$DEST/$3"
}

clone https://github.com/yt-dlp/yt-dlp.git          2026.10.26 yt-dlp
clone https://github.com/FFmpeg/FFmpeg.git          n9.0.2     FFmpeg
clone https://github.com/ggml-org/whisper.cpp.git   v1.9.5     whisper.cpp
clone https://github.com/remotion-dev/remotion.git  v4.0.541   remotion
clone https://github.com/heygen-com/hyperframes.git v0.9.15    hyperframes

echo "done: $DEST"
