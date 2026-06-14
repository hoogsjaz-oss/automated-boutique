# 2. WhatsApp Business setup (Cloud API)

This powers two things:
- **Broadcasting** weekly products to opted-in subscribers (workflow 1).
- **The reply bot** that answers customer questions (workflow 2).

We use the **WhatsApp Cloud API** (free to use, hosted by Meta). You need a
Meta/Facebook account and a phone number for the business.

## A. Create the app & get tokens

1. Go to <https://developers.facebook.com> → **My Apps → Create App** →
   type **Business**.
2. Add the **WhatsApp** product to the app.
3. In **WhatsApp → API Setup** you'll see:
   - A **temporary access token** (24h — fine for testing).
   - Your **Phone number ID** (`WHATSAPP_PHONE_NUMBER_ID`).
   - A test number you can send from immediately.
4. Set env vars:
   - `WHATSAPP_TOKEN` = the access token
   - `WHATSAPP_PHONE_NUMBER_ID` = the phone number ID

> **Production token:** the 24h token expires. For a permanent one, create a
> **System User** in **Business Settings → Users → System Users**, assign the
> app, and generate a token with `whatsapp_business_messaging` +
> `whatsapp_business_management` permissions. Use that as `WHATSAPP_TOKEN`.

## B. Connect the inbound webhook (for the reply bot)

The reply bot (workflow 2) exposes a webhook at:

```
https://<your-n8n-host>/webhook/whatsapp-inbound
```

1. Make sure workflow 2 is **Active** in n8n (so the webhook URL is live).
   Copy the **Production URL** from the *WhatsApp Webhook* node.
2. In the Meta app → **WhatsApp → Configuration → Webhook → Edit**:
   - **Callback URL:** the n8n production URL above.
   - **Verify token:** any string you choose — set the same value as
     `WHATSAPP_VERIFY_TOKEN`.
3. Click **Verify and Save**, then **Subscribe** to the **`messages`** field.

> ### Webhook verification (GET) handshake
> Meta first sends a **GET** request with `hub.challenge` to verify ownership.
> The provided workflow's webhook is POST-only. Add a quick verify endpoint one
> of two ways:
>
> **Easiest:** duplicate the *WhatsApp Webhook* node, set **HTTP Method = GET**
> and add a **Respond to Webhook** node returning
> `{{ $json.query['hub.challenge'] }}` (when `hub.verify_token` matches
> `WHATSAPP_VERIFY_TOKEN`). Wire GET → Respond.
>
> You only need this once during setup; Meta re-verifies occasionally.

## C. Opt-in & broadcasting rules (important)

- You may only message customers who **opted in**. Keep them in the
  `Subscribers` tab with `OptInStatus = OPTED_IN`.
- **Service replies** (answering someone who messaged you in the last 24h) can be
  free-form text — that's the reply bot, no template needed.
- **Marketing broadcasts** (the weekly poster pushing to subscribers) generally
  require a **pre-approved message template** if you're outside the 24-hour
  window. Create templates in **WhatsApp Manager → Message Templates**.
  - The workflow currently sends a free-form image message — fine for testing
    and within-window sends. For compliant marketing at scale, switch the
    *WhatsApp Send Broadcast* node body to a `type: "template"` payload
    referencing your approved template name.
- Marketing conversations are billed per Meta's WhatsApp pricing.

## D. Test

Send a WhatsApp message to your business/test number, e.g. *"What colours does
the silk scarf come in?"* — the bot should reply using your catalog within a few
seconds. Check the n8n execution log if not.

➡️ Next: **[Instagram + Facebook setup](03-instagram-facebook-setup.md)**
