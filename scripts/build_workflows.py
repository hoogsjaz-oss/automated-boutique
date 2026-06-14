#!/usr/bin/env python3
"""Builds the importable n8n workflow JSON files for Automated Boutique.

Run:  python3 scripts/build_workflows.py
Writes: n8n/1-weekly-scheduler.json, n8n/2-customer-reply-bot.json,
        n8n/3-order-fulfilment.json

Keeping the workflows in a generator means the embedded JavaScript (Code nodes)
stays readable and the emitted JSON is always valid.
"""
import json
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "n8n")

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def node(id_, name, type_, type_version, position, parameters, extra=None):
    n = {
        "parameters": parameters,
        "id": id_,
        "name": name,
        "type": type_,
        "typeVersion": type_version,
        "position": position,
    }
    if extra:
        n.update(extra)
    return n


def gsheet_read(id_, name, position, sheet, doc_env="GSHEET_ID"):
    return node(
        id_, name, "n8n-nodes-base.googleSheets", 4.5, position,
        {
            "resource": "sheet",
            "operation": "read",
            "documentId": {"__rl": True, "value": "={{ $env." + doc_env + " }}", "mode": "id"},
            "sheetName": {"__rl": True, "value": sheet, "mode": "name"},
            "options": {},
        },
    )


def http(id_, name, position, method, url, headers, json_body=None, query=None):
    params = {
        "method": method,
        "url": url,
        "sendHeaders": True,
        "headerParameters": {"parameters": [{"name": k, "value": v} for k, v in headers]},
        "options": {},
    }
    if json_body is not None:
        params["sendBody"] = True
        params["specifyBody"] = "json"
        params["jsonBody"] = json_body
    if query is not None:
        params["sendQuery"] = True
        params["queryParameters"] = {"parameters": [{"name": k, "value": v} for k, v in query]}
    return node(id_, name, "n8n-nodes-base.httpRequest", 4.2, position, params)


def code(id_, name, position, js):
    return node(id_, name, "n8n-nodes-base.code", 2, position, {"jsCode": js})


def wf(name, nodes, connections):
    return {
        "name": name,
        "nodes": nodes,
        "connections": connections,
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
        "meta": {"templateId": "automated-boutique"},
    }


def write(filename, data):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print("wrote", os.path.relpath(path))


# Common header tuples
META_HEADERS = [("Authorization", "=Bearer {{ $env.META_ACCESS_TOKEN }}"),
                ("Content-Type", "application/json")]

# ===========================================================================
# WORKFLOW 1 — Weekly Scheduler / Multi-platform Poster
# ===========================================================================

filter_js = r"""
// Reads all Products rows and keeps the ones scheduled to post today.
// A product posts when: Active == TRUE and PostDay == today's weekday name.
// Builds a ready-to-use caption for each kept product.
const weekday = new Intl.DateTimeFormat('en-US', { weekday: 'long' })
  .format(new Date());                                  // e.g. "Monday"
const boutique = $env.BOUTIQUE_NAME || 'Our Boutique';

const out = [];
for (const item of $input.all()) {
  const p = item.json;
  const active = String(p.Active).toUpperCase() === 'TRUE';
  if (!active) continue;
  if (String(p.PostDay).trim().toLowerCase() !== weekday.toLowerCase()) continue;

  const stock = Number(p.Stock) || 0;
  const price = `${p.Currency || 'R'}${p.Price}`;
  const sizes = String(p.Sizes || '').split(',').map(s => s.trim()).filter(Boolean);
  const colours = String(p.Colours || '').split(',').map(s => s.trim()).filter(Boolean);

  const caption =
    `✨ ${p.Name} ✨\n\n` +
    `${p.Description || ''}\n\n` +
    `💰 Price: ${price}\n` +
    (sizes.length ? `📏 Sizes: ${sizes.join(', ')}\n` : '') +
    (colours.length ? `🎨 Colours: ${colours.join(', ')}\n` : '') +
    (stock > 0 ? `✅ In stock` : `⏳ Restocking soon`) + `\n\n` +
    `💬 WhatsApp us to order! — ${boutique}`;

  out.push({
    json: {
      sku: p.SKU,
      name: p.Name,
      price,
      sizes,
      colours,
      stock,
      imageUrl: p.ImageURL,
      caption,
      postDay: p.PostDay,
    },
  });
}

if (out.length === 0) {
  // Nothing scheduled today — stop the branch cleanly.
  return [];
}
return out;
""".strip()

whatsapp_broadcast_js = r"""
// Cross-joins today's products with opted-in subscribers so each subscriber
// receives each scheduled product as a WhatsApp image message.
// WhatsApp policy: only message users who have opted in. For marketing
// outside the 24h window you should use an approved message template.
const products = $items('Filter & Build Captions').map(i => i.json);
const subs = $items('Read Subscribers')
  .map(i => i.json)
  .filter(s => String(s.OptInStatus).toUpperCase() === 'OPTED_IN');

const out = [];
for (const s of subs) {
  for (const p of products) {
    out.push({
      json: {
        to: String(s.Phone).replace(/[^0-9]/g, ''),
        name: s.Name,
        imageUrl: p.imageUrl,
        caption: p.caption,
        sku: p.sku,
      },
    });
  }
}
return out;
""".strip()

ig_publish_js = r"""
// Instagram publishing is two calls: create a media container, then publish it.
// This node just passes the creation_id from the previous (container) node
// through together with the IG user id so the Publish node can use it.
return $input.all().map(i => ({
  json: { creation_id: i.json.id }
}));
""".strip()

w1_nodes = [
    node("c9e6d42a-4133-4961-9ada-b114fbec5d14", "Weekly Schedule",
         "n8n-nodes-base.scheduleTrigger", 1.2, [-660, 300],
         {"rule": {"interval": [{"field": "cronExpression", "expression": "0 9 * * *"}]}}),

    gsheet_read("60d48eb2-4179-4539-96ee-9ad265f0b323", "Read Products", [-440, 300], "Products"),

    code("ef48734d-144f-40be-96f7-af822d61a51b", "Filter & Build Captions", [-220, 300], filter_js),

    # ---- Facebook Page photo post ----
    http("726fdcbc-1aa1-429d-b5d9-69c61d7fb7d3", "Facebook Page Post", [40, 40],
         "POST", "=https://graph.facebook.com/v20.0/{{ $env.FB_PAGE_ID }}/photos",
         META_HEADERS,
         json_body="={{ JSON.stringify({ url: $json.imageUrl, caption: $json.caption }) }}"),

    # ---- Instagram: create container then publish ----
    http("f5a4b093-a034-4ccb-83a8-e6c7664b27e6", "Instagram Create Container", [40, 240],
         "POST", "=https://graph.facebook.com/v20.0/{{ $env.IG_USER_ID }}/media",
         META_HEADERS,
         json_body="={{ JSON.stringify({ image_url: $json.imageUrl, caption: $json.caption }) }}"),
    code("af1de3d8-8cb4-40e6-8975-1c462b09359d", "Pass creation_id", [260, 240], ig_publish_js),
    http("e6077d76-bf06-420b-9db4-49b60e2eecc7", "Instagram Publish", [480, 240],
         "POST", "=https://graph.facebook.com/v20.0/{{ $env.IG_USER_ID }}/media_publish",
         META_HEADERS,
         json_body="={{ JSON.stringify({ creation_id: $json.creation_id }) }}"),

    # ---- TikTok content posting (photo, PULL_FROM_URL) ----
    http("3f2d8156-81a0-4f18-9f0f-d29ae560aac1", "TikTok Init Post", [40, 440],
         "POST", "https://open.tiktokapis.com/v2/post/publish/content/init/",
         [("Authorization", "=Bearer {{ $env.TIKTOK_ACCESS_TOKEN }}"),
          ("Content-Type", "application/json; charset=UTF-8")],
         json_body="={{ JSON.stringify({"
                   " post_info: { title: $json.name, description: $json.caption,"
                   " disable_comment: false, privacy_level: 'PUBLIC_TO_EVERYONE' },"
                   " source_info: { source: 'PULL_FROM_URL', photo_cover_index: 0,"
                   " photo_images: [$json.imageUrl] }, post_mode: 'DIRECT_POST',"
                   " media_type: 'PHOTO' }) }}"),

    # ---- WhatsApp broadcast to opted-in subscribers ----
    gsheet_read("239526e3-9af4-4f60-bd32-7ba16ec723e7", "Read Subscribers", [40, 640], "Subscribers"),
    code("9b04b24e-9d96-4bd9-a593-21335fd49922", "Build WhatsApp Messages", [260, 640], whatsapp_broadcast_js),
    http("d39232eb-d15c-4a11-bb25-ce95de11a1be", "WhatsApp Send Broadcast", [480, 640],
         "POST", "=https://graph.facebook.com/v20.0/{{ $env.WHATSAPP_PHONE_NUMBER_ID }}/messages",
         [("Authorization", "=Bearer {{ $env.WHATSAPP_TOKEN }}"),
          ("Content-Type", "application/json")],
         json_body="={{ JSON.stringify({ messaging_product: 'whatsapp', to: $json.to,"
                   " type: 'image', image: { link: $json.imageUrl, caption: $json.caption } }) }}"),
]

w1_connections = {
    "Weekly Schedule": {"main": [[{"node": "Read Products", "type": "main", "index": 0}]]},
    "Read Products": {"main": [[{"node": "Filter & Build Captions", "type": "main", "index": 0}]]},
    "Filter & Build Captions": {"main": [[
        {"node": "Facebook Page Post", "type": "main", "index": 0},
        {"node": "Instagram Create Container", "type": "main", "index": 0},
        {"node": "TikTok Init Post", "type": "main", "index": 0},
        {"node": "Read Subscribers", "type": "main", "index": 0},
    ]]},
    "Instagram Create Container": {"main": [[{"node": "Pass creation_id", "type": "main", "index": 0}]]},
    "Pass creation_id": {"main": [[{"node": "Instagram Publish", "type": "main", "index": 0}]]},
    "Read Subscribers": {"main": [[{"node": "Build WhatsApp Messages", "type": "main", "index": 0}]]},
    "Build WhatsApp Messages": {"main": [[{"node": "WhatsApp Send Broadcast", "type": "main", "index": 0}]]},
}

write("1-weekly-scheduler.json", wf("Boutique — 1. Weekly Scheduler & Poster", w1_nodes, w1_connections))

# ===========================================================================
# WORKFLOW 2 — Customer Reply Bot (WhatsApp webhook -> Claude -> reply)
# ===========================================================================

parse_msg_js = r"""
// Parses an incoming WhatsApp Cloud API webhook payload into a simple shape.
// Ignores status callbacks (delivery/read receipts) which have no message.
const body = $input.first().json.body || $input.first().json;
let entry, change, value, msg;
try {
  entry = body.entry[0];
  change = entry.changes[0];
  value = change.value;
  msg = value.messages && value.messages[0];
} catch (e) { msg = null; }

if (!msg || msg.type !== 'text') {
  // Not a text message we can answer — end quietly.
  return [];
}

const contactName = (value.contacts && value.contacts[0] &&
  value.contacts[0].profile && value.contacts[0].profile.name) || '';

return [{
  json: {
    from: msg.from,                 // customer phone (wa id)
    text: msg.text.body,            // the question
    customerName: contactName,
    messageId: msg.id,
  },
}];
""".strip()

build_claude_js = r"""
// Builds the Anthropic request: turns the live catalog into JSON, injects it
// into the system prompt, and passes the customer's question as the user turn.
const products = $items('Read Catalog').map(i => {
  const p = i.json;
  return {
    sku: p.SKU,
    name: p.Name,
    description: p.Description,
    price: Number(p.Price),
    currency: p.Currency,
    sizes: String(p.Sizes || '').split(',').map(s => s.trim()).filter(Boolean),
    colours: String(p.Colours || '').split(',').map(s => s.trim()).filter(Boolean),
    stock: Number(p.Stock) || 0,
    category: p.Category,
  };
}).filter(p => String(p.sku || '').length > 0);

const incoming = $items('Parse Message')[0].json;
const boutique = $env.BOUTIQUE_NAME || 'Our Boutique';

const systemPrompt =
`You are the friendly, professional sales assistant for ${boutique}, an online fashion boutique replying to customers on WhatsApp.

Answer using ONLY the live catalog (JSON) below. Customers ask about price, sizes, colours, and whether items are in stock, and may want to order.

LIVE CATALOG:
${JSON.stringify(products)}

RULES:
1. Use only the catalog data. Never invent products, prices, sizes, colours or stock.
2. If stock is 0, say it's sold out and offer a similar in-stock item.
3. Quote prices with currency (e.g. "R450").
4. Keep replies short and warm for WhatsApp. Use the customer's name if known${incoming.customerName ? ' (' + incoming.customerName + ')' : ''}.
5. To place an order you need: product, size, colour, quantity, customer name and delivery area. Confirm the total before finalising.
6. When ALL order details are gathered AND the customer confirms, append a final line on its own:
[[ORDER]] {"sku":"...","name":"...","size":"...","colour":"...","qty":1,"customer_name":"...","delivery_area":"...","unit_price":000,"total_price":000}
Only emit [[ORDER]] after confirmation; otherwise omit it.`;

return [{
  json: {
    model: $env.CLAUDE_MODEL || 'claude-sonnet-4-6',
    system: systemPrompt,
    userText: incoming.text,
    from: incoming.from,
    customerName: incoming.customerName,
  },
}];
""".strip()

handle_reply_js = r"""
// Extracts Claude's text, splits off any [[ORDER]] machine line, and prepares
// the WhatsApp reply + an optional order record for the fulfilment step.
const resp = $input.first().json;
let fullText = '';
try { fullText = resp.content.map(c => c.text || '').join('').trim(); } catch (e) { fullText = ''; }
if (!fullText) fullText = "Thanks for your message! A team member will get back to you shortly. 💬";

const meta = $items('Build Claude Request')[0].json;

let reply = fullText;
let order = null;
const idx = fullText.indexOf('[[ORDER]]');
if (idx !== -1) {
  reply = fullText.slice(0, idx).trim();
  const jsonPart = fullText.slice(idx + '[[ORDER]]'.length).trim();
  try { order = JSON.parse(jsonPart); } catch (e) { order = null; }
}

return [{
  json: {
    to: meta.from,
    reply: reply || "Got it! 💬",
    hasOrder: !!order,
    order: order || {},
    customerPhone: meta.from,
    customerName: meta.customerName,
  },
}];
""".strip()

append_order_js = r"""
// Shapes a confirmed order from the bot into an Orders-sheet row.
const o = $json.order || {};
const phone = $json.customerPhone;
const id = 'ORD-' + Date.now();
return [{
  json: {
    OrderID: id,
    Timestamp: new Date().toISOString(),
    CustomerName: o.customer_name || $json.customerName || '',
    Phone: phone,
    SKU: o.sku || '',
    ProductName: o.name || '',
    Size: o.size || '',
    Colour: o.colour || '',
    Qty: o.qty || 1,
    UnitPrice: o.unit_price || '',
    TotalPrice: o.total_price || '',
    Currency: 'ZAR',
    Status: 'NEW',
    FulfilmentNotes: 'Delivery area: ' + (o.delivery_area || ''),
    PaymentStatus: 'UNPAID',
  },
}];
""".strip()

w2_nodes = [
    node("0604373e-c00d-4d98-b14d-70a9a90968db", "WhatsApp Webhook",
         "n8n-nodes-base.webhook", 2, [-720, 300],
         {"httpMethod": "POST", "path": "whatsapp-inbound", "responseMode": "responseNode",
          "options": {}},
         extra={"webhookId": "whatsapp-inbound"}),

    code("1dd3cd3d-c7c0-458e-b45d-2635bef3cb1a", "Parse Message", [-500, 300], parse_msg_js),

    gsheet_read("107879db-3ced-4771-8fd0-7ee7fbe47db4", "Read Catalog", [-280, 300], "Products"),

    code("b8fa1041-2eb1-4d72-9fd1-39e04c5f5352", "Build Claude Request", [-60, 300], build_claude_js),

    http("53a64c2c-283a-441b-a647-b13187160355", "Claude — Generate Reply", [160, 300],
         "POST", "https://api.anthropic.com/v1/messages",
         [("x-api-key", "={{ $env.ANTHROPIC_API_KEY }}"),
          ("anthropic-version", "2023-06-01"),
          ("Content-Type", "application/json")],
         json_body="={{ JSON.stringify({ model: $json.model, max_tokens: 1024,"
                   " system: $json.system,"
                   " messages: [{ role: 'user', content: $json.userText }] }) }}"),

    code("0889f51f-1e9a-4b0e-b33d-c8f4b1634523", "Handle Reply", [380, 300], handle_reply_js),

    http("d8e2b4a1-d67d-4221-b5de-4822252af188", "Send WhatsApp Reply", [600, 200],
         "POST", "=https://graph.facebook.com/v20.0/{{ $env.WHATSAPP_PHONE_NUMBER_ID }}/messages",
         [("Authorization", "=Bearer {{ $env.WHATSAPP_TOKEN }}"),
          ("Content-Type", "application/json")],
         json_body="={{ JSON.stringify({ messaging_product: 'whatsapp', to: $json.to,"
                   " type: 'text', text: { body: $json.reply } }) }}"),

    node("a1da927b-c8a6-4eb0-ba3f-f26e813999d6", "Respond 200",
         "n8n-nodes-base.respondToWebhook", 1.1, [820, 200],
         {"respondWith": "text", "responseBody": "EVENT_RECEIVED", "options": {}}),

    node("b9964c77-911b-4e16-a187-f1211562af18", "Order detected?",
         "n8n-nodes-base.if", 2, [600, 440],
         {"conditions": {"options": {"caseSensitive": True, "typeValidation": "loose"},
                          "combinator": "and",
                          "conditions": [{"id": "ord1",
                                          "leftValue": "={{ $json.hasOrder }}",
                                          "rightValue": True,
                                          "operator": {"type": "boolean", "operation": "true", "singleValue": True}}]}}),

    code("6b5f41bb-f41a-4158-a4dd-75a033ddecf9", "Shape Order Row", [820, 440], append_order_js),

    node("d332fc39-9106-483f-9098-8326b390fabc", "Append Order to Sheet",
         "n8n-nodes-base.googleSheets", 4.5, [1040, 440],
         {"resource": "sheet", "operation": "append",
          "documentId": {"__rl": True, "value": "={{ $env.GSHEET_ID }}", "mode": "id"},
          "sheetName": {"__rl": True, "value": "Orders", "mode": "name"},
          "columns": {"mappingMode": "autoMapInputData", "value": {}, "matchingColumns": []},
          "options": {}}),
]

w2_connections = {
    "WhatsApp Webhook": {"main": [[{"node": "Parse Message", "type": "main", "index": 0}]]},
    "Parse Message": {"main": [[{"node": "Read Catalog", "type": "main", "index": 0}]]},
    "Read Catalog": {"main": [[{"node": "Build Claude Request", "type": "main", "index": 0}]]},
    "Build Claude Request": {"main": [[{"node": "Claude — Generate Reply", "type": "main", "index": 0}]]},
    "Claude — Generate Reply": {"main": [[{"node": "Handle Reply", "type": "main", "index": 0}]]},
    "Handle Reply": {"main": [[
        {"node": "Send WhatsApp Reply", "type": "main", "index": 0},
        {"node": "Order detected?", "type": "main", "index": 0},
    ]]},
    "Send WhatsApp Reply": {"main": [[{"node": "Respond 200", "type": "main", "index": 0}]]},
    "Order detected?": {"main": [[{"node": "Shape Order Row", "type": "main", "index": 0}], []]},
    "Shape Order Row": {"main": [[{"node": "Append Order to Sheet", "type": "main", "index": 0}]]},
}

write("2-customer-reply-bot.json", wf("Boutique — 2. Customer Reply Bot (Claude)", w2_nodes, w2_connections))

# ===========================================================================
# WORKFLOW 3 — Order Fulfilment
# ===========================================================================

decrement_js = r"""
// Given a new order, find the matching product row and compute the new stock.
// Outputs the row number + new stock so the next node can update the sheet.
const order = $items('New Order Trigger')[0].json;
const products = $items('Read Products for Stock');

let match = null;
let rowNumber = null;
products.forEach((it, i) => {
  if (String(it.json.SKU).trim() === String(order.SKU).trim()) {
    match = it.json;
    // Google Sheets node exposes the spreadsheet row via row_number when read.
    rowNumber = it.json.row_number || (i + 2); // +2: header row + 1-based
  }
});

if (!match) {
  return [{ json: { ok: false, reason: 'SKU not found', sku: order.SKU, order } }];
}

const qty = Number(order.Qty) || 1;
const current = Number(match.Stock) || 0;
const newStock = Math.max(0, current - qty);

return [{
  json: {
    ok: true,
    sku: order.SKU,
    rowNumber,
    newStock,
    lowStock: newStock <= 2,
    order,
    productName: match.Name,
  },
}];
""".strip()

owner_notice_js = r"""
// Composes the owner notification (email body) for a new paid/new order.
const d = $json;
const o = d.order || {};
const subject = `🛍️ New order ${o.OrderID || ''} — ${d.productName || o.ProductName || ''}`;
const lines = [
  `New order received:`,
  ``,
  `Order: ${o.OrderID || ''}`,
  `Customer: ${o.CustomerName || ''} (${o.Phone || ''})`,
  `Item: ${o.ProductName || d.productName} | Size ${o.Size || ''} | ${o.Colour || ''} | Qty ${o.Qty || 1}`,
  `Total: ${o.Currency || 'ZAR'} ${o.TotalPrice || ''}`,
  `Delivery: ${o.FulfilmentNotes || ''}`,
  ``,
  `Stock now: ${d.newStock}${d.lowStock ? '  ⚠️ LOW STOCK' : ''}`,
];
return [{ json: { subject, body: lines.join('\n'), to: $env.OWNER_EMAIL } }];
""".strip()

w3_nodes = [
    node("bc2d3984-fdff-4952-b1b4-200d65e60da4", "New Order Trigger",
         "n8n-nodes-base.googleSheetsTrigger", 1, [-680, 300],
         {"documentId": {"__rl": True, "value": "={{ $env.GSHEET_ID }}", "mode": "id"},
          "sheetName": {"__rl": True, "value": "Orders", "mode": "name"},
          "event": "rowAdded",
          "pollTimes": {"item": [{"mode": "everyMinute"}]},
          "options": {}}),

    gsheet_read("20ddcf3e-95b4-4097-9bae-d93d512cd279", "Read Products for Stock", [-460, 300], "Products"),

    code("61b75c75-6b90-45c0-b868-9c1c0c111cce", "Compute New Stock", [-240, 300], decrement_js),

    node("36cd3498-c52a-4e2d-a20c-65c09d5bdb6f", "Stock found?",
         "n8n-nodes-base.if", 2, [-20, 300],
         {"conditions": {"options": {"caseSensitive": True, "typeValidation": "loose"},
                          "combinator": "and",
                          "conditions": [{"id": "ok1",
                                          "leftValue": "={{ $json.ok }}",
                                          "rightValue": True,
                                          "operator": {"type": "boolean", "operation": "true", "singleValue": True}}]}}),

    node("c1e9a155-55c4-47bc-b485-33137dce4cef", "Update Stock",
         "n8n-nodes-base.googleSheets", 4.5, [220, 200],
         {"resource": "sheet", "operation": "update",
          "documentId": {"__rl": True, "value": "={{ $env.GSHEET_ID }}", "mode": "id"},
          "sheetName": {"__rl": True, "value": "Products", "mode": "name"},
          "columns": {"mappingMode": "defineBelow", "matchingColumns": ["SKU"],
                       "value": {"SKU": "={{ $json.sku }}", "Stock": "={{ $json.newStock }}"}},
          "options": {}}),

    code("8cd4ef35-7430-48f5-9d9d-f31f9d82cf1c", "Build Owner Email", [440, 200], owner_notice_js),

    node("6452c481-394d-4d96-bae7-24a1ff8915c8", "Email Owner",
         "n8n-nodes-base.gmail", 2.1, [660, 120],
         {"resource": "message", "operation": "send",
          "sendTo": "={{ $json.to }}", "subject": "={{ $json.subject }}",
          "emailType": "text", "message": "={{ $json.body }}", "options": {}}),

    http("4151bfef-627e-4a72-9201-09c80fa2c2a7", "WhatsApp Confirm to Customer", [660, 280],
         "POST", "=https://graph.facebook.com/v20.0/{{ $env.WHATSAPP_PHONE_NUMBER_ID }}/messages",
         [("Authorization", "=Bearer {{ $env.WHATSAPP_TOKEN }}"),
          ("Content-Type", "application/json")],
         json_body="={{ JSON.stringify({ messaging_product: 'whatsapp',"
                   " to: $('New Order Trigger').item.json.Phone.replace(/[^0-9]/g,''),"
                   " type: 'text', text: { body: 'Thank you for your order ' +"
                   " ($('New Order Trigger').item.json.OrderID || '') + '! 🎉 We are preparing it"
                   " and will share payment + delivery details shortly. — ' +"
                   " ($env.BOUTIQUE_NAME || 'Our Boutique') } }) }}"),

    node("ac555c24-dbb7-4a8c-ab6c-f4141f105612", "Mark PROCESSING",
         "n8n-nodes-base.googleSheets", 4.5, [880, 280],
         {"resource": "sheet", "operation": "update",
          "documentId": {"__rl": True, "value": "={{ $env.GSHEET_ID }}", "mode": "id"},
          "sheetName": {"__rl": True, "value": "Orders", "mode": "name"},
          "columns": {"mappingMode": "defineBelow", "matchingColumns": ["OrderID"],
                       "value": {"OrderID": "={{ $('New Order Trigger').item.json.OrderID }}",
                                  "Status": "PROCESSING"}},
          "options": {}}),

    node("ad4fea4e-edb0-41ef-ac3a-c27c22d135e2", "Flag: SKU not found",
         "n8n-nodes-base.gmail", 2.1, [220, 440],
         {"resource": "message", "operation": "send",
          "sendTo": "={{ $env.OWNER_EMAIL }}",
          "subject": "=⚠️ Order needs attention — SKU not found ({{ $json.sku }})",
          "emailType": "text",
          "message": "={{ 'An order came in but the SKU was not found in Products: ' + JSON.stringify($json.order) }}",
          "options": {}}),
]

w3_connections = {
    "New Order Trigger": {"main": [[{"node": "Read Products for Stock", "type": "main", "index": 0}]]},
    "Read Products for Stock": {"main": [[{"node": "Compute New Stock", "type": "main", "index": 0}]]},
    "Compute New Stock": {"main": [[{"node": "Stock found?", "type": "main", "index": 0}]]},
    "Stock found?": {"main": [
        [{"node": "Update Stock", "type": "main", "index": 0}],
        [{"node": "Flag: SKU not found", "type": "main", "index": 0}],
    ]},
    "Update Stock": {"main": [[{"node": "Build Owner Email", "type": "main", "index": 0}]]},
    "Build Owner Email": {"main": [[
        {"node": "Email Owner", "type": "main", "index": 0},
        {"node": "WhatsApp Confirm to Customer", "type": "main", "index": 0},
    ]]},
    "WhatsApp Confirm to Customer": {"main": [[{"node": "Mark PROCESSING", "type": "main", "index": 0}]]},
}

write("3-order-fulfilment.json", wf("Boutique — 3. Order Fulfilment", w3_nodes, w3_connections))

print("done")
