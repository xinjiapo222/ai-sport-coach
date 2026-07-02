#!/bin/bash
set -e
cd "$(dirname "$0")"
export AI_SPORT_CAMERA="${AI_SPORT_CAMERA:-20}"
export AI_SPORT_POSE_MODEL="${AI_SPORT_POSE_MODEL:-$PWD/models/movenet-lightning.onnx}"
export AI_SPORT_ORT_THREADS="${AI_SPORT_ORT_THREADS:-8}"
export AI_SPORT_FONT="${AI_SPORT_FONT:-/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc}"
exec python3 main.py "$@"
