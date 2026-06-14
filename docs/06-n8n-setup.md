# 6. n8n setup

n8n is the engine that runs all three workflows. You can use **n8n Cloud**
(hosted, easiest) or **self-host** (free).

## Option A — n8n Cloud (recommended to start)

1. Sign up at <https://n8n.io> and create a workspace.
2. Skip to **[Add environment variables](#add-environment-variables)**.

## Option B — Self-host (free)

Quickest with Docker:

```bash
docker volume create n8n_data
docker run -d --name n8n -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  --env-file ./.env \
  docker.n8n.io/n8nio/n8n
```

Open <http://localhost:5678>. For webhooks (the WhatsApp bot) to be reachable
from the internet you need a public URL — either deploy on a server with a
domain, or for testing use a tunnel:

```bash
npx localtunnel --port 5678      # or ngrok http 5678
```

Set `WEBHOOK_URL` to that public URL so n8n generates correct webhook links.

## Add environment variables

All secrets live as env vars (see [`.env.example`](../.env.example)). The
workflows read them via `{{ $env.NAME }}`.

- **Self-hosted:** put them in `.env` / pass with `--env-file` (as above), or
  export them in the host environment, then restart n8n.
- **n8n Cloud:** add them under **Variables** in your workspace settings, or
  store the sensitive ones inside each node's **Credential**.

Minimum to get started: `BOUTIQUE_NAME`, `GSHEET_ID`, `ANTHROPIC_API_KEY`,
`CLAUDE_MODEL`. Add the platform tokens as you complete each platform's doc.

## Import the workflows

For each file in [`n8n/`](../n8n/):

1. n8n → **Workflows → Import from File** (top-right menu).
2. Select `1-weekly-scheduler.json`, then repeat for `2-` and `3-`.

After import, open each workflow and:

- Click every **Google Sheets** node → choose your Google credential.
- Click the **Gmail** nodes (in workflow 3) → choose a Gmail credential (or
  swap for the plain *Send Email*/SMTP node if you prefer).
- The **HTTP Request** nodes already use `{{ $env.* }}` tokens, so they need no
  credential — just make sure the env vars are set.

## Connect the credentials you'll need

| Credential | Used by | Doc |
|------------|---------|-----|
| Google Sheets OAuth2 | all 3 workflows | [01](01-google-sheet-setup.md) |
| Gmail OAuth2 (or SMTP) | fulfilment emails | n8n Gmail docs |
| (env var) Anthropic key | reply bot | [05](05-claude-api-setup.md) |
| (env var) WhatsApp token | poster, bot, fulfilment | [02](02-whatsapp-setup.md) |
| (env var) Meta token | poster (IG + FB) | [03](03-instagram-facebook-setup.md) |
| (env var) TikTok token | poster | [04](04-tiktok-setup.md) |

## Test each workflow

1. **Weekly Scheduler:** set one `Products` row's `PostDay` to **today** and
   `Active = TRUE`, then open workflow 1 and click **Test workflow**. Watch each
   platform node — green = posted. (Start with just Facebook to confirm the
   pipeline, then enable the rest.)
2. **Reply Bot:** after the WhatsApp webhook is connected (doc 02), message your
   business number "how much is the floral dress?" — you should get a reply.
3. **Fulfilment:** add a test row to the `Orders` tab → within a minute you
   should get the owner email and stock should decrement.

## Go live

Toggle each workflow **Active** (top-right switch). The scheduler then runs on
its cron (default **09:00 daily**, posting only items whose `PostDay` is today).
Adjust the time in the **Weekly Schedule** node.

➡️ Next: **[WhatsApp setup](02-whatsapp-setup.md)**
