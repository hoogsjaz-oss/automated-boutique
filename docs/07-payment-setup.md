# 7. Payment setup (M-Pesa / Airtel Money / Bank transfer)

The fulfilment workflow takes payment using **one** of three methods, chosen by
the `PAYMENT_METHOD` env var:

| `PAYMENT_METHOD` | How it works | Customer experience |
|------------------|--------------|---------------------|
| `mpesa` | **M-Pesa STK Push** (Safaricom Daraja) | Gets a PIN prompt on their phone |
| `airtel` | **Airtel Money** collection request | Approves a prompt on their phone |
| `bank` | **Bank transfer** instructions (manual) | Receives your bank details + reference |

For every method the workflow:
1. Decrements stock.
2. Runs the **Prepare Payment** node (computes amount, formats the phone, builds
   the customer message; for M-Pesa it also builds the Daraja timestamp/password).
3. Routes through the **Payment Method?** switch to the right branch.
4. Sends the customer a WhatsApp message (the pay prompt or bank details).
5. Emails you the order, marks it `Status=PROCESSING`, `PaymentStatus=PENDING`,
   and stores the reference in the `PaymentRef` column of the `Orders` tab.

> Switching method is just changing `PAYMENT_METHOD` in `.env` — no workflow edit.

---

## Option 1 — M-Pesa (Safaricom Daraja)

1. Create an app at <https://developer.safaricom.co.ke> and add the **Lipa na
   M-Pesa Online (STK Push)** product.
2. From the app, copy the **Consumer Key** and **Consumer Secret**.
3. Get your **Business ShortCode** (Paybill/Till) and the **Lipa na M-Pesa
   Passkey** (sandbox values are provided in the portal for testing).
4. Set env vars:
   ```
   PAYMENT_METHOD=mpesa
   MPESA_ENV=sandbox            # switch to production when live
   MPESA_CONSUMER_KEY=...
   MPESA_CONSUMER_SECRET=...
   MPESA_SHORTCODE=...
   MPESA_PASSKEY=...
   MPESA_TX_TYPE=CustomerPayBillOnline   # or CustomerBuyGoodsOnline for a Till
   MPESA_CALLBACK_URL=https://<public-url>/webhook/mpesa-callback
   ```
5. **Callback:** Daraja POSTs the payment result to `MPESA_CALLBACK_URL`. To mark
   orders `PAID` automatically, add a small webhook workflow that listens there
   and updates the `Orders` row (see "Auto-confirming payment" below). Until then
   you confirm payments manually in the sheet.

**How it's wired:** `M-Pesa Get Token` (Basic auth → OAuth token) →
`M-Pesa STK Push` (`/mpesa/stkpush/v1/processrequest`). The phone is normalised
to `2547XXXXXXXX`; amount comes from the order's `TotalPrice`.

> Sandbox testing uses Safaricom's test MSISDNs and credentials from the portal.
> Move `MPESA_ENV` to `production` only after you've been granted Go-Live.

---

## Option 2 — Airtel Money

1. Register at <https://developers.airtel.africa> and create an app with the
   **Collection** product.
2. Copy the **Client ID** and **Client Secret**.
3. Set env vars:
   ```
   PAYMENT_METHOD=airtel
   AIRTEL_ENV=sandbox           # switch to production when live
   AIRTEL_CLIENT_ID=...
   AIRTEL_CLIENT_SECRET=...
   AIRTEL_COUNTRY=KE            # KE, TZ, UG, …
   AIRTEL_CURRENCY=KES
   AIRTEL_COUNTRY_CODE=254      # used to strip the dialing prefix from the phone
   ```

**How it's wired:** `Airtel Get Token` (`/auth/oauth2/token`) →
`Airtel Request Payment` (`/merchant/v1/payments/`). This pushes a USSD/app
prompt to the customer to approve. The `msisdn` is the local number (country
code stripped).

> Airtel also supports a **transaction status** call and callbacks for
> confirmation — wire those the same way as the M-Pesa callback if you want
> automatic `PAID` updates.

---

## Option 3 — Bank transfer (manual)

No API needed — best when you'd rather reconcile payments yourself.

```
PAYMENT_METHOD=bank
BANK_DETAILS=Bank: Equity Bank | Account name: Your Boutique | Account no: 0123456789 | Branch: Nairobi
```

The customer gets a WhatsApp message with your `BANK_DETAILS` and is asked to use
the **Order ID as the reference** and reply with proof of payment. You then mark
the order `PAID` in the sheet (or via the reply bot conversation).

---

## Auto-confirming payment (optional, recommended for mpesa/airtel)

Mobile-money providers notify you of completed payments via a **callback**. To
flip `PaymentStatus → PAID` automatically, add a 4th workflow:

```
Webhook (mpesa-callback / airtel-callback)
  → parse result (success? amount? order ref?)
  → Google Sheets: update Orders row by OrderID → PaymentStatus = PAID
  → WhatsApp: "Payment received — your order is on the way! 🎉"
```

Point `MPESA_CALLBACK_URL` (and the Airtel callback) at this webhook. I can
generate this workflow for you on request.

---

## Test

1. Set `PAYMENT_METHOD` and the matching sandbox credentials.
2. Add a row to the `Orders` tab (or let the reply bot create one).
3. Within a minute the fulfilment workflow runs:
   - **mpesa/airtel:** the token + push nodes go green; check the test phone for
     the prompt.
   - **bank:** the customer WhatsApp message contains your `BANK_DETAILS`.
4. Confirm the `Orders` row shows `Status=PROCESSING`, `PaymentStatus=PENDING`,
   and a value in `PaymentRef`.

➡️ Back to the **[README](../README.md)**.
