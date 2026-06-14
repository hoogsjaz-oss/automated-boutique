# 3. Instagram + Facebook setup (Meta Graph API)

Instagram and Facebook posting both go through the **Meta Graph API** with one
access token. Posting requires:

- A **Facebook Page** for your boutique.
- An **Instagram professional account** (Business or Creator) **linked to that
  Page**.

## A. Link Instagram to your Facebook Page

1. Convert your IG account to **Professional** (IG app → Settings → Account type).
2. In the Facebook Page settings → **Linked accounts**, connect the Instagram
   account. (Or do it via Meta Business Suite.)

## B. Create the app & token

1. <https://developers.facebook.com> → reuse the app from the WhatsApp step (or
   create a **Business** app).
2. Add the **Facebook Login** and **Instagram Graph API** products.
3. Use the **Graph API Explorer** (Tools menu) to generate a **User access
   token** with these permissions:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
   - `instagram_basic`
   - `instagram_content_publish`
   - `business_management`
4. **Exchange for a long-lived token** (60 days) — see
   <https://developers.facebook.com/docs/facebook-login/guides/access-tokens/#long-lived>.
   For a non-expiring **Page token**, fetch it via `/me/accounts` using the
   long-lived user token. Use that as `META_ACCESS_TOKEN`.

## C. Get the IDs

Run these in Graph API Explorer:

- **Facebook Page ID:**
  ```
  GET /me/accounts
  ```
  → copy the `id` of your Page → `FB_PAGE_ID`.

- **Instagram User ID:**
  ```
  GET /{FB_PAGE_ID}?fields=instagram_business_account
  ```
  → copy `instagram_business_account.id` → `IG_USER_ID`.

Set env vars: `META_ACCESS_TOKEN`, `FB_PAGE_ID`, `IG_USER_ID`.

## D. How the workflow posts

- **Facebook** → single call: `POST /{FB_PAGE_ID}/photos` with `url` + `caption`.
- **Instagram** → two calls (handled by two nodes):
  1. `POST /{IG_USER_ID}/media` with `image_url` + `caption` → returns a
     `creation_id`.
  2. `POST /{IG_USER_ID}/media_publish` with that `creation_id`.

> The `ImageURL` in your sheet must be a **public** URL Meta can fetch (no login,
> direct image link, https). Large images: keep under IG's limits (JPEG, < 8 MB).

## E. App Review (for going beyond your own accounts)

While your app is in **Development mode** you can post to Pages/IG accounts you
own/admin — perfect for a single boutique. If you ever manage others' accounts,
submit `instagram_content_publish` + `pages_manage_posts` for **App Review**.

## F. Test

In n8n, run workflow 1 with one product scheduled for today. Watch the
**Facebook Page Post** and **Instagram Publish** nodes turn green, then check
the Page and IG profile.

➡️ Next: **[TikTok setup](04-tiktok-setup.md)**
