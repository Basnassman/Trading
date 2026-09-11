#!/usr/bin/env bash
set -euo pipefail

# --- Manual Docker Compose v2 plugin install (user-local, no root needed) ---
DOCKER_CONFIG="${DOCKER_CONFIG:-$HOME/.docker}"
mkdir -p "$DOCKER_CONFIG/cli-plugins"

PLUGIN="$DOCKER_CONFIG/cli-plugins/docker-compose"
TARGET_VERSION="${1:-v5.5.0}"   # pass a version as $1 if you want a specific one

# Only re-download if the plugin isn't already present or doesn't match the requested version
if [ -x "$PLUGIN" ] && "$PLUGIN" version 2>/dev/null | grep -q "$TARGET_VERSION"; then
  echo "docker-compose plugin already installed at $TARGET_VERSION"
else
  echo "Downloading Docker Compose $TARGET_VERSION ..."
  curl -SL "https://github.com/docker/compose/releases/download/$TARGET_VERSION/docker-compose-linux-x86_64" \
    -o "$PLUGIN"
  chmod +x "$PLUGIN"
fi

# --- Verify ---
echo "---"
docker --version
docker compose version
