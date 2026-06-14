# 4. TikTok setup (Content Posting API)

TikTok posting uses the **Content Posting API**. The workflow posts a **photo**
(your product image, pulled from `ImageURL`) with the caption as the title.

> ⚠️ TikTok has the strictest access rules of the four platforms. Expect this one
> to take the longest to fully enable. You can launch the other 3 platforms first
> and add TikTok later — just leave `TIKTOK_ACCESS_TOKEN` blank and the TikTok
> node will simply fail/skip without affecting the rest.

## A. Create a developer app

1. Register at <https://developers.tiktok.com> and **create an app**.
2. Add the **Content Posting API** product to the app.
3. Add the **Login Kit** so you can authorise your TikTok account.
4. Request the scopes:
   - `video.publish` and/or `photo.publish`
   - `user.info.basic`

## B. Authorise & get an access token

TikTok uses OAuth 2.0. Easiest inside n8n: there is a community/credential flow,
but the simplest reliable path is:

1. Complete TikTok's OAuth flow to get an **access token + refresh token** for
   your boutique's TikTok account (see
   <https://developers.tiktok.com/doc/oauth-user-access-token-management>).
2. Put the access token in `TIKTOK_ACCESS_TOKEN`.

> Access tokens expire (~24h) and must be refreshed with the refresh token. For
> production, add a small n8n sub-workflow (Schedule → HTTP refresh →
> store) or use n8n's OAuth2 credential to auto-refresh. For first tests, paste a
> fresh token.

## C. Audit / unaudited mode (important)

Until your app passes TikTok's **audit**, posts are restricted to
**`SELF_ONLY`** (private — only you can see them). The workflow currently sets
`privacy_level: 'PUBLIC_TO_EVERYONE'`, which **only works after audit**.

- **Before audit:** change `privacy_level` to `SELF_ONLY` in the
  *TikTok Init Post* node so test posts succeed (privately).
- **After audit:** switch it back to `PUBLIC_TO_EVERYONE`.

Submit for audit in the TikTok developer portal once you're posting reliably.

## D. How the workflow posts

`POST https://open.tiktokapis.com/v2/post/publish/content/init/` with:

```json
{
  "post_info": { "title": "<caption>", "privacy_level": "...", "disable_comment": false },
  "source_info": { "source": "PULL_FROM_URL", "photo_cover_index": 0, "photo_images": ["<ImageURL>"] },
  "post_mode": "DIRECT_POST",
  "media_type": "PHOTO"
}
```

> For `PULL_FROM_URL`, the image's domain must be **verified** in your TikTok app
> (Developer portal → URL properties). Otherwise use the `FILE_UPLOAD` source
> flow instead.

## E. Test

With a fresh `TIKTOK_ACCESS_TOKEN` and `privacy_level: SELF_ONLY`, run workflow 1
and confirm the *TikTok Init Post* node returns a `publish_id`. Check the post in
your TikTok account (it'll be private until audited).

➡️ Next: **[Claude setup](05-claude-api-setup.md)**
