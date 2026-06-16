#!/usr/bin/env bash
# One-shot local launcher for the Automated Boutique stack.
# Starts n8n in Docker, waits for it, and imports the 3 workflows.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v docker >/dev/null 2>&1; then
  echo "❌ Docker is required. Install it: https://docs.docker.com/get-docker/"
  exit 1
fi

# Pick the right compose invocation (plugin vs legacy binary).
if docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose"
else
  echo "❌ Docker Compose not found. Install Docker Desktop or the compose plugin."
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "📝 Created .env from .env.example."
  echo "   Edit .env to add your keys (at minimum GSHEET_ID + ANTHROPIC_API_KEY)."
fi

echo "🚀 Pulling n8n image & starting…"
$COMPOSE up -d

printf "⏳ Waiting for n8n to be ready"
for _ in $(seq 1 60); do
  if curl -sf http://localhost:5678/healthz >/dev/null 2>&1; then
    printf " ready\n"; break
  fi
  printf "."; sleep 2
done

echo "📥 Importing workflows…"
if $COMPOSE exec -T n8n n8n import:workflow --separate --input=/workflows >/dev/null 2>&1; then
  echo "   ✅ Imported 3 workflows."
else
  echo "   ⚠️  CLI import skipped — import manually in the UI (Workflows → Import from File → n8n/*.json)."
fi

cat <<'EOF'

✅ n8n is running at  http://localhost:5678

Next steps:
  1. Open the URL and create your owner account (first run only).
  2. Open each imported "Boutique — …" workflow and:
       • pick your Google Sheets credential on the Google Sheets nodes
       • pick a Gmail (or SMTP) credential on the email nodes (workflow 3)
  3. Make sure .env has your keys, then restart:  docker compose up -d
  4. Toggle each workflow Active.

Test the reply bot's webhook from the internet? Run a tunnel:
     npx localtunnel --port 5678     (or: ngrok http 5678)
  then put the public https URL in .env as WEBHOOK_URL and re-run this script.

Stop everything:   docker compose down        (data is kept)
Wipe everything:   docker compose down -v      (deletes the n8n volume)
EOF
