#!/bin/sh
# 编译驱动：依赖 ftp-pull 里的官方 jar
set -e
cd "$(dirname "$0")"
export PATH=/usr/lib/jvm/java-17-openjdk/bin:$PATH
javac -cp "$HOME/workspace/ftp-pull/sfs-ai__sfsai.jar" -d cls src/com/sfsai/core/*.java
echo BUILD_OK
