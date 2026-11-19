#!/bin/sh
# 用法: sh driver/run.sh <blueprint.json> <script.json> [body] [maxSec] [startAlt] [startVs] [fromStage] [startHs]
# 相对路径按仓库根目录解析
export PATH=/usr/lib/jvm/java-17-openjdk/bin:$PATH
DIR="$(cd "$(dirname "$0")" && pwd)"
exec java -cp "$HOME/workspace/ftp-pull/sfs-ai__sfsai.jar:$DIR/cls" com.sfsai.core.Fly "$@"
