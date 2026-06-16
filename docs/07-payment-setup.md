# 7. Payment setup (Yoco)

When the fulfilment workflow processes a new order it now:

1. Decrements stock.
2. **Creates a hosted payment link** via the **Yoco Checkout API**.
3. Sends the customer a WhatsApp message with the order total **and the pay
   link**.
4. Emails you the order details + link.
5. Marks the order `Status = PROCESSING`, `PaymentStatus = PENDING`, and stores
   the link in the new `PaymentLink` column of the `Orders` tab.

Yoco is used because it's a great fit for **South African (ZAR)** boutiques and
its API returns a ready-to-share payment URL. Swapping providers is one node —
see the bottom of this page.

## A. Get your Yoco key

1. Sign up / log in at <https://www.yoco.com> and open the **Yoco Dashboard**.
2. Go to **Developers → API keys** (or **Sell online → Payment Gateway**).
3. Copy your **Secret key**. Use the **test** key (`sk_test_...`) while you set
   things up; switch to the **live** key when ready to take real money.
4. Set env var `YOCO_SECRET_KEY` in n8n.

## B. How the node calls Yoco

`POST https://payments.yoco.com/api/checkouts`
Header: `Authorization: Bearer <YOCO_SECRET_KEY>`

```json
{
  "amount": 45000,            // total in CENTS (R450.00 → 45000)
  "currency": "ZAR",
  "metadata": { "orderId": "ORD-...", "sku": "BTQ-001" }
}
```

The response contains **`redirectUrl`** — that's the payment link sent to the
customer. (Amount is taken from the order's `TotalPrice` × 100.)

> **Optional but recommended:** set `successUrl` / `cancelUrl` and configure a
> **webhook** in Yoco so a separate small workflow can flip `PaymentStatus` to
> `PAID` automatically when the customer pays. Without it, you mark orders paid
> manually in the sheet. Yoco webhook docs:
> <https://developer.yoco.com/online/api-reference/webhooks>.

## C. Test

1. Use a `sk_test_...` key.
2. Add a test row to the `Orders` tab (or let the bot create one).
3. Within a minute the fulfilment workflow runs — check that the **Create
   Payment Link** node returns a `redirectUrl`, the customer WhatsApp message
   contains it, and the `Orders` row shows `PaymentStatus = PENDING` with the
   link in `PaymentLink`.
4. Open the link and complete a **test** payment.

## D. Using Stripe or PayFast instead

Only the **Create Payment Link** node changes — everything downstream just reads
`redirectUrl`.

**Stripe Payment Links** — `POST https://api.stripe.com/v1/payment_links`
(Bearer `sk_...`), or create a Price + Payment Link. Map the response `url` to
`redirectUrl` (add a tiny Set/Code node, or rename references to `.url`).

**PayFast** — link-based redirect with an MD5 signature rather than a JSON API.
Build the URL in a Code node:
`https://www.payfast.co.za/eng/process?merchant_id=...&merchant_key=...&amount=...&item_name=...&signature=...`
and output it as `redirectUrl`. See <https://developers.payfast.co.za>.

In all cases, keep the output field name `redirectUrl` (or update the two
references in the **WhatsApp Confirm to Customer**, **Build Owner Email**, and
**Mark PROCESSING** nodes) so the rest of the flow keeps working.

➡️ Back to the **[README](../README.md)**.
