# 5. Claude (Anthropic) setup

Claude powers the **customer reply bot** — it reads each incoming WhatsApp
message, looks at your live catalog, and writes a natural reply about price,
sizes, colours and stock. It also detects when a customer has confirmed an order
and emits a structured order line the fulfilment workflow picks up.

## A. Get an API key

1. Sign up at <https://console.anthropic.com>.
2. Add billing (the reply bot is pay-as-you-go).
3. **API Keys → Create Key**, copy it.
4. Set env var `ANTHROPIC_API_KEY`.

## B. Choose a model

Set `CLAUDE_MODEL`:

| Model | When to use | Notes |
|-------|-------------|-------|
| `claude-sonnet-4-6` | **Recommended default** | Fast + low cost, great for WhatsApp chat. |
| `claude-opus-4-8` | Maximum quality | Best reasoning; higher cost/latency. |
| `claude-haiku-4-5-20251001` | Highest volume / lowest cost | Cheapest, still capable for simple Q&A. |

For a boutique answering product questions, **`claude-sonnet-4-6`** is the sweet
spot. You can change it anytime via the env var — no workflow edit needed.

## C. How it's wired

Workflow 2 (`Build Claude Request` node) builds the call:

- **system prompt** = your boutique persona + rules + the **live catalog as
  JSON** (pulled fresh from the sheet on every message). The canonical prompt is
  in [`prompts/customer-reply-system-prompt.md`](../prompts/customer-reply-system-prompt.md).
- **user message** = the customer's WhatsApp text.

It calls `POST https://api.anthropic.com/v1/messages` with headers
`x-api-key` and `anthropic-version: 2023-06-01`.

Because the catalog is injected every call, **the bot is always current** — when
you change stock/price in the sheet, replies reflect it immediately. No
retraining, no redeploy.

## D. Order capture

When the customer has given product + size + colour + quantity + name + delivery
area **and confirms**, Claude appends a line like:

```
[[ORDER]] {"sku":"BTQ-001","name":"Floral Summer Dress","size":"M","colour":"Blue","qty":1,"customer_name":"Thandi","delivery_area":"Sandton","unit_price":450,"total_price":450}
```

The `Handle Reply` node strips this line out of the customer-facing message and
(if present) writes the order to the **Orders** tab — which then triggers the
fulfilment workflow.

## E. Tuning the personality

Edit the system prompt text in the `Build Claude Request` node (or update
[`prompts/customer-reply-system-prompt.md`](../prompts/customer-reply-system-prompt.md)
and mirror it into the node). You can adjust tone, languages (e.g. reply in the
customer's language), upsell behaviour, payment instructions, etc.

## F. Cost control

- `max_tokens` is capped at 1024 in the node — plenty for chat, keeps costs down.
- The catalog JSON is the bulk of input tokens; keep `Description` concise.
- Consider Haiku if volume gets high.

➡️ Back to the **[README](../README.md)** to finish wiring and go live.
