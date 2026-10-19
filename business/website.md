# beardshomeservices.com

- Domain migrated from **beardsservices.com → beardshomeservices.com** (Aug 2026). Contact email is now `brianb@beardshomeservices.com`.
- Hosting: Cloudflare Pages (static assets, `wrangler.jsonc`), mail via Zoho Mail.
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
