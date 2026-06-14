# 1. Google Sheet setup

The Google Sheet is your **single source of truth**: products, orders, and
subscribers. You'll edit it weekly; n8n reads and writes it automatically.

## Create the sheet

1. Go to [sheets.new](https://sheets.new) and name it e.g. **Boutique Catalog**.
2. Create **three tabs** (rename the bottom tabs): `Products`, `Orders`,
   `Subscribers`.
3. For each tab, paste the matching template:
   - [`google-sheet/Products-template.csv`](../google-sheet/Products-template.csv)
   - [`google-sheet/Orders-template.csv`](../google-sheet/Orders-template.csv)
   - [`google-sheet/Subscribers-template.csv`](../google-sheet/Subscribers-template.csv)

   Easiest: **File → Import → Upload** each CSV into its tab, choosing *"Replace
   current sheet"*. Or just copy the header row from the CSV into row 1.

> The **column headers must match exactly** (including capitalisation) — the
> workflows reference them by name.

## Get the Sheet ID

From the URL:

```
https://docs.google.com/spreadsheets/d/1AbCdEf...XyZ/edit#gid=0
                                        └──────┬──────┘
                                          this is GSHEET_ID
```

Put it in your n8n env var `GSHEET_ID`.

## Connect Google to n8n

In n8n you'll add a **Google Sheets credential** (OAuth2 is simplest):

1. n8n → **Credentials → New → Google Sheets OAuth2 API**.
2. Follow n8n's wizard (it links you to a Google Cloud OAuth client). n8n's docs:
   <https://docs.n8n.io/integrations/builtin/credentials/google/>.
3. Authorise with the Google account that owns the sheet.
4. When you open each Google Sheets node in the imported workflows, pick this
   credential from the dropdown.

> Self-hosting n8n? You can instead use a **Service Account**: create one in
> Google Cloud, download the JSON key, and **share the sheet with the service
> account's email** (as Editor). Then use the *Service Account* auth type in the
> n8n Google credential.

## Column reference

### Products
| Column | Meaning |
|--------|---------|
| `SKU` | Unique product code (e.g. `BTQ-001`). Used to match orders → stock. |
| `Name`, `Description` | Shown in posts and replies. |
| `Price`, `Currency` | Number + currency code (e.g. `450`, `ZAR`). |
| `Sizes`, `Colours` | Comma-separated (e.g. `S,M,L`). |
| `Stock` | Units available. Hits 0 → bot says sold out; fulfilment won't go negative. |
| `ImageURL` | **Public** image link used for posting. |
| `PostDay` | Weekday name (`Monday`…`Sunday`) — the scheduler posts it that day. |
| `Active` | `TRUE`/`FALSE` — only `TRUE` rows are eligible to post. |
| `Category` | Optional grouping. |
| `LastPostedAt` | Optional, for your own tracking. |

### Orders
Auto-populated by the reply bot and fulfilment workflow. `Status` flows
`NEW → PROCESSING → …`; `PaymentStatus` is yours to manage.

### Subscribers
WhatsApp customers who **opted in** to broadcasts. Only `OptInStatus =
OPTED_IN` rows receive the weekly WhatsApp broadcast.

➡️ Next: **[n8n setup](06-n8n-setup.md)**
