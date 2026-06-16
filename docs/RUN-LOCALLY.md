# ▶️ Run it locally

This runs the whole automation engine (**n8n** + the 3 workflows) on your own
machine with Docker. The workflows talk to external services (Google Sheets,
Claude, WhatsApp, Meta, TikTok, M-Pesa/Airtel), so those still need keys — but you can get
n8n up and the AI reply logic working with just **two** keys to start.

---

## What "the end product" is

There's no app to compile — the product is:

| Piece | Where |
|-------|-------|
| 3 automation workflows | [`n8n/*.json`](../n8n/) — imported into n8n |
| Your catalog / orders | a Google Sheet (created from [`google-sheet/*.csv`](../google-sheet/)) |
| The runtime engine | **n8n**, which you run locally via Docker |
| Secrets/config | [`.env`](../.env.example) |

When n8n is running and the workflows are **Active**, the system runs itself:
posts on schedule, replies to WhatsApp messages, and fulfils orders.

---

## Prerequisites

- **Docker** (Docker Desktop on Mac/Windows, or Docker Engine on Linux) —
  <https://docs.docker.com/get-docker/>
- A **Google Sheet** built from the templates (see
  [01-google-sheet-setup.md](01-google-sheet-setup.md)) and its `GSHEET_ID`.
- An **Anthropic API key** (for the reply bot) — see
  [05-claude-api-setup.md](05-claude-api-setup.md).
- (Optional, add later) WhatsApp / Meta / TikTok / M-Pesa/Airtel keys for live posting,
  messaging and payments.

---

## Fastest path (one command)

```bash
git clone https://github.com/hoogsjaz-oss/automated-boutique.git
cd automated-boutique
./scripts/run-local.sh
```

The script will:
1. create `.env` from the template (if missing),
2. start n8n in Docker,
3. wait for it to be healthy,
4. import the 3 workflows.

Then open **<http://localhost:5678>**, create your owner account, and finish the
credential setup below.

> Edit `.env` with your keys, then re-run `docker compose up -d` (or the script)
> so n8n picks them up.

---

## Manual path (if you prefer step by step)

```bash
# 1. Get the config file and add your keys
cp .env.example .env
#   open .env and set at least: BOUTIQUE_NAME, GSHEET_ID,
#   ANTHROPIC_API_KEY, CLAUDE_MODEL

# 2. Start n8n
docker compose up -d

# 3. (optional) import the workflows from the CLI
docker compose exec n8n n8n import:workflow --separate --input=/workflows
```

Open <http://localhost:5678>. If you skipped step 3, import the workflows in the
UI: **Workflows → Import from File →** select each file in `n8n/`.

---

## Finish setup in the n8n UI

1. **Create your account** on first visit (stored locally in the Docker volume).
2. **Google Sheets credential:** Credentials → New → *Google Sheets OAuth2* (or a
   service account). Then open each workflow and select it on every Google Sheets
   node. (See [01-google-sheet-setup.md](01-google-sheet-setup.md).)
3. **Email credential** (workflow 3): add a Gmail OAuth2 or SMTP credential on
   the email nodes — or delete those nodes if you don't want owner emails yet.
4. The HTTP nodes (WhatsApp / Meta / TikTok / Claude / M-Pesa/Airtel) read from `.env`, so
   no credential UI is needed — just make sure the env vars are set.
5. Toggle each workflow **Active** (top-right) when you're ready.

---

## Test locally without all the platform keys

You can validate the core pieces with minimal setup:

- **Weekly poster logic:** set one `Products` row's `PostDay` to today and run
  workflow 1 with **Test workflow**. The *Filter & Build Captions* node will show
  the generated caption even before the platform tokens exist. (Platform nodes
  will error until their tokens are set — that's expected.)
- **Claude reply logic:** open workflow 2, click the *Build Claude Request* and
  *Claude — Generate Reply* nodes and use **Test step** with a sample message —
  needs only `ANTHROPIC_API_KEY` + the Google Sheet.
- **Fulfilment + stock math:** add a row to the `Orders` tab; the *Compute New
  Stock* node runs with just the Google credential.

---

## Receiving WhatsApp messages locally (webhooks)

The reply bot needs Meta to reach your machine, so localhost must be exposed via
a tunnel:

```bash
npx localtunnel --port 5678      # or:  ngrok http 5678
```

Put the public `https://…` URL into `.env` as `WEBHOOK_URL`, re-run
`docker compose up -d`, then use
`https://<public-url>/webhook/whatsapp-inbound` as the callback in the Meta app
(see [02-whatsapp-setup.md](02-whatsapp-setup.md)). The scheduler and fulfilment
workflows don't need a tunnel — only the inbound webhook does.

---

## Everyday commands

```bash
docker compose up -d        # start (or apply .env changes)
docker compose logs -f n8n  # watch logs
docker compose down         # stop, keep data
docker compose down -v      # stop and DELETE the n8n data volume
```

➡️ Back to the **[README](../README.md)**.
