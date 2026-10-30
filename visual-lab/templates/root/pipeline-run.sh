#!/bin/bash
# Deploys this project behind the Cloudflare tunnel: pulls the latest code, removes ALL
# containers on the host, starts the tunnel, then starts this project's compose stack.
# The tunnel routes to http://rixus-frontend:80 on the tunnel-net network.
set -e

cd "$(dirname "$0")"

# Project secrets live in the git-ignored .env, read by docker compose.
if [ ! -f .env ]; then
  echo "No .env found: creating one from .env.example."
  cp .env.example .env
  chmod 600 .env
fi

# Passwords the stack needs and nobody types (database, broker): generated here on first
# deploy, because docker-compose.yml gives them no fallback. List them, e.g.
# GENERATED_SECRETS=(DB_PASSWORD). A database keeps the password its volume was created
# with, so a value is never replaced once set.
GENERATED_SECRETS=()
for name in "${GENERATED_SECRETS[@]}"; do
  if ! grep -qE "^${name}=.+" .env; then
    echo "Generating ${name} in .env."
    value="$(openssl rand -hex 24)"
    if grep -qE "^${name}=" .env; then
      sed -i "s/^${name}=.*/${name}=${value}/" .env
    else
      echo "${name}=${value}" >> .env
    fi
    unset value
  fi
done

# TUNNEL_TOKEN is normally set globally (e.g. /etc/environment); fall back to .env.
# Only that one line is read, so nothing else from .env enters this shell.
if [ -z "${TUNNEL_TOKEN:-}" ]; then
  TUNNEL_TOKEN="$(grep -E '^TUNNEL_TOKEN=' .env | tail -n 1 | cut -d= -f2- | tr -d "\"'\r")"
  export TUNNEL_TOKEN
fi
: "${TUNNEL_TOKEN:?TUNNEL_TOKEN must be set globally on this server or in .env}"

echo "=== Pulling project ==="
bash ./git-pull-project.sh

echo "=== Stopping and removing all containers ==="
docker ps -aq | xargs -r docker rm -f

echo "=== Starting Cloudflare tunnel ==="
docker network inspect tunnel-net >/dev/null 2>&1 || docker network create tunnel-net
# -e TUNNEL_TOKEN passes the value from this shell, keeping it out of the command line
docker run -d --name cloudflared-tunnel --network tunnel-net --restart unless-stopped \
  -e TUNNEL_TOKEN cloudflare/cloudflared:latest tunnel --no-autoupdate run
echo "=== Starting apps ==="
docker compose up -d --build

echo "=== Pipeline complete ==="
