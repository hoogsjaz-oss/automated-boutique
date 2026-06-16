# 🛍️ Automated Boutique

Automate your online boutique end-to-end with **n8n** + a **Google Sheet** +
**Claude**:

1. **📅 Scheduled posting** — every week your products auto-post to **WhatsApp
   Business, Instagram, Facebook, and TikTok**, driven by a Google Sheet.
2. **💬 Smart customer replies** — Claude reads incoming WhatsApp messages and
   answers questions about **price, sizes, colours, and stock** from your live
   catalog, and captures orders.
3. **📦 Order fulfilment + payment** — confirmed orders update stock and take
   payment by **M-Pesa, Airtel Money, or bank transfer**, send the customer a
   WhatsApp confirmation, notify you, and move the order through statuses.

You edit one Google Sheet each week. Everything else runs itself.

---

## How it works

```
                       ┌──────────────────────────┐
                       │   Google Sheet (catalog)  │
                       │  Products · Orders · Subs  │
                       └───────────┬──────────────┘
                                   │  (source of truth)
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                           │
┌───────▼────────┐      ┌──────────▼──────────┐      ┌─────────▼─────────┐
│ 1. Weekly       │      │ 2. Customer Reply   │      │ 3. Order          │
│    Scheduler    │      │    Bot (Claude)     │      │    Fulfilment     │
│                 │      │                     │      │                   │
│ cron → read     │      │ WhatsApp webhook →  │      │ new Orders row →  │
│ today's items → │      │ Claude (catalog) →  │      │ decrement stock → │
│ post to:        │      │ reply on WhatsApp → │      │ M-Pesa/Airtel/bank│
│ WA·IG·FB·TikTok │      │ capture order       │      │ confirm + email   │
└─────────────────┘      └─────────────────────┘      └───────────────────┘
```

All three are **n8n workflows** in [`n8n/`](n8n/). Import them, add your
credentials, and switch them on.

---

## Repository layout

| Path | What it is |
|------|------------|
| [`n8n/1-weekly-scheduler.json`](n8n/1-weekly-scheduler.json) | Weekly multi-platform poster |
| [`n8n/2-customer-reply-bot.json`](n8n/2-customer-reply-bot.json) | WhatsApp → Claude → reply + order capture |
| [`n8n/3-order-fulfilment.json`](n8n/3-order-fulfilment.json) | Stock update + M-Pesa/Airtel/bank payment + notifications |
| [`google-sheet/`](google-sheet/) | CSV templates for the `Products`, `Orders`, `Subscribers` tabs |
| [`prompts/`](prompts/) | The Claude system prompt used by the reply bot |
| [`docs/`](docs/) | Step-by-step setup for the sheet, each platform, Claude and n8n |
| [`.env.example`](.env.example) | All the environment variables/secrets n8n needs |
| [`docker-compose.yml`](docker-compose.yml) | Runs n8n locally (mounts workflows for import) |
| [`scripts/run-local.sh`](scripts/run-local.sh) | One-command local launcher |
| [`scripts/build_workflows.py`](scripts/build_workflows.py) | Regenerates the workflow JSON (edit logic here) |

---

## Run it locally (Docker, one command)

```bash
git clone https://github.com/hoogsjaz-oss/automated-boutique.git
cd automated-boutique
./scripts/run-local.sh        # starts n8n + imports the workflows
```

Then open **<http://localhost:5678>**, create your account, add your Google +
keys, and toggle the workflows Active. Full walkthrough (including testing with
just an Anthropic key, and exposing the WhatsApp webhook via a tunnel):
**[docs/RUN-LOCALLY.md](docs/RUN-LOCALLY.md)**.

## Quick start (≈ 1–2 hrs the first time)

Follow the docs in order — each is short and self-contained:

1. **[Google Sheet setup](docs/01-google-sheet-setup.md)** — create the sheet from the CSV templates.
2. **[n8n setup](docs/06-n8n-setup.md)** — install/sign up for n8n, add env vars, import the 3 workflows.
3. **[WhatsApp Business setup](docs/02-whatsapp-setup.md)** — Cloud API number, token, webhook.
4. **[Instagram + Facebook setup](docs/03-instagram-facebook-setup.md)** — Meta Graph token, Page & IG IDs.
5. **[TikTok setup](docs/04-tiktok-setup.md)** — Content Posting API access.
6. **[Claude setup](docs/05-claude-api-setup.md)** — Anthropic API key + model choice.
7. **[Payment setup](docs/07-payment-setup.md)** — M-Pesa, Airtel Money, or bank transfer.

Then in n8n: open each workflow, attach the Google credential, and toggle it
**Active**. Add a row to `Products` with today's weekday in `PostDay` and run
the scheduler manually to test.

---

## The Google Sheet (your weekly control panel)

Three tabs. Each week you mostly touch **Products** (set `PostDay`, update
`Stock`, flip `Active`).

**Products** — `SKU, Name, Description, Price, Currency, Sizes, Colours, Stock,
ImageURL, PostDay, Active, Category, LastPostedAt`

**Orders** — auto-filled by the bot/fulfilment: `OrderID, Timestamp,
CustomerName, Phone, SKU, ProductName, Size, Colour, Qty, UnitPrice,
TotalPrice, Currency, Status, FulfilmentNotes, PaymentStatus, PaymentRef`

**Subscribers** — opted-in WhatsApp customers for broadcasts: `Name, Phone,
OptInStatus, OptInDate, Tags`

> **`ImageURL` must be a public link** (Google Drive "anyone with link" direct
> link, Cloudinary, S3, etc.). Instagram/WhatsApp/TikTok all fetch the image
> from this URL, so it must be reachable without a login.

---

## Important notes & compliance

- **WhatsApp opt-in:** only broadcast to customers who opted in. For marketing
  messages outside the 24-hour customer-service window, Meta requires an
  **approved message template**. The reply bot (answering people who message
  *you*) is fine; the *broadcast* needs opt-in + templates. See the WhatsApp doc.
- **TikTok:** unaudited apps can only post in **private/SELF_ONLY** mode until
  your app passes TikTok's audit. Details in the TikTok doc.
- **Costs:** n8n (free self-hosted or paid cloud), Anthropic API (pay per
  message — Sonnet is cheap for chat), Meta/TikTok APIs are free, WhatsApp has
  per-conversation pricing for marketing.
- **Secrets:** put real keys in n8n env vars, never in git. `.env` is gitignored.

---

## Editing the workflows

The JSON files are generated from [`scripts/build_workflows.py`](scripts/build_workflows.py)
so the embedded JavaScript stays readable. Change logic there and run:

```bash
python3 scripts/build_workflows.py
```

You can also edit nodes visually in n8n and re-export — both are fine.
