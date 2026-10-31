# beardshomeservices.com

- Domain migrated from **beardsservices.com → beardshomeservices.com** (Aug 2026). Contact email is now `brianb@beardshomeservices.com`.
- Hosting: Cloudflare Pages (static assets, `wrangler.jsonc`), mail is Cloudflare Email Routing (the domain's mail records point there, not Zoho; checked 31 Oct 2026).
- Previously on SiteGround/Tucows (domain expired once — now resolved).
- Repo: `beardsservices-png/beardsservices-site`. Plain static HTML/CSS/JS — no build step. Shared look comes from `shared-styles.css` + `site.js` (loaded on every page); per-page content is hand-authored HTML.
- Multi-page SEO expansion: homepage + 6 service pages (concrete, roofing, decks, bathroom-remodel, flooring, handyman) + blog, sitemap submitted to Search Console. Canonical URLs are extensionless.
- Brand: original `LOGO.png` (light background) still used site-wide; transparent brand assets live in `brand/` (`bhs-mark.png`, horizontal logos).

## PWA + mobile (Aug 2026)

- Installable PWA: `manifest.webmanifest` (standalone, theme `#1a3a5c`, app shortcuts), service worker `sw.js` (network-first pages, cache-first images, stale-while-revalidate assets), `offline.html` fallback. Icon set generated from the logo under `icons/` (any + maskable + apple-touch + favicons).
- Mobile nav is now a real hamburger + slide-in drawer (previously the links were just `display:none` with no fallback). Drawer clones each page's nav links, so all pages get it from `site.js`.
- Sticky bottom action bar on phones (Call / Text / Quote), back-to-top button, lightbox swipe.
- Quote form: labels + service dropdown + progressive-enhancement handler that builds a reliable `mailto`. Still `mailto`-based (no backend) — a form service could be wired up later if Brian wants submissions to land automatically.
- Accessibility: skip links, `main` landmark, focus-visible styles, `prefers-reduced-motion` respected.

## Blog + indexing (Oct 2026)

- One blog post per month. Jul–Oct 2026 added 29 Oct (LVP vs laminate, tub surround vs remodel, fall gutters/drainage, deck winter prep). Blog index is newest-first. Posts are hand-built from the existing template: `BlogPosting` JSON-LD with image, extensionless canonical and `og:url`, one site photo on top. Never put customer names or addresses in a post.
- When adding a post: add the card to `blog/index.html`, the URL to `sitemap.xml`, the line to `llms.txt`, then ping IndexNow (below). Google needs a Search Console sitemap resubmit / URL inspection by hand (Claude in Chrome).
- `llms.txt` at the root lists services and every post for AI assistants. `robots.txt` explicitly allows GPTBot, ClaudeBot, PerplexityBot, Google-Extended etc.
- IndexNow (Bing, Yandex): key file `/6a8017912acfc8b0a619e17fe0375be3.txt` at the site root. POST `https://api.indexnow.org/indexnow` with `{host, key, keyLocation, urlList}` — 202 = accepted.
- Pushing `main` deploys the site via Cloudflare (live within ~1 minute).
