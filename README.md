# viotours.in — website (v1, static)

Built from the **viotours design system** — *Warm heritage* direction (terracotta + saffron gold,
Fraunces + Jost), **E1 Info pin** logo, the 23 line icons, and the *Povoma Oorgolam* theme music.

## What's here

| Path | What |
| --- | --- |
| `build.py` | Stdlib-only Python generator. `python3 build.py` → `dist/`; `--serve` previews on :8000 |
| `content/packages.json` | Packages, itineraries, prices, featured flag + position (top 3 on home) |
| `content/events.json`, `content/posts.json` | Events (past ones auto-hide) and journal posts |
| `css/site.css` | All styling, from the design-system tokens |
| `js/config.js` | **Edit me:** WhatsApp number, email, form endpoint, music, AED/USD rates — no rebuild needed |
| `js/site.js` | Menu, theme music, forms, package filters, currency hint |
| `server/enquiry_server.py` | Form endpoint: stores every lead in SQLite, optional email. `--list` shows leads |
| `deploy/` | nginx server block and systemd unit |
| `dist/` | The built site — this is what goes on the server |

Pages: home, packages (style + activity filters), 7 package pages, plan-my-trip enquiry, events,
journal + 3 posts, about & safety, contact (form + Google Maps), partner invitation, sign-in
(placeholder, not linked, noindex), 404, `sitemap.xml`, `robots.txt`.

## Before launch — must do

1. **Replace the sample content.** All 7 packages, prices, dates and the 3 events are placeholders.
   Then set `SAMPLE_CONTENT = False` in `build.py` to remove the "Preview site" banner.
2. **`js/config.js`:** real WhatsApp Business number and inbox (currently `910000000000` / `hello@viotours.in`).
3. **Photos:** drop images in `assets/img/` and set `"image": "assets/img/swiss.jpg"` per package.
   The illustrated scenes are stand-ins.
4. **Contact page map:** `build.py` points Google Maps at "Chennai, Tamil Nadu" — set your office address.
5. **Music rights:** the theme is a film composition; clear commercial use (or swap the file).
6. **Name check:** the design system flags "viotours" as close to giotours.com / geotours.in.

## Deploy — GitHub Pages (current)

Every push to `main` runs `.github/workflows/static.yml`: it runs `build.py` and publishes `dist/`
to GitHub Pages at the custom domain www.viotours.in. Pages is static-only, so `server/` isn't used
there and forms hand off to WhatsApp/email (`enquiryEndpoint: ""` in `js/config.js`).

DNS at your registrar:

| Type | Name | Value |
| --- | --- | --- |
| A | @ | 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153 |
| AAAA | @ | 2606:50c0:8000::153, 2606:50c0:8001::153, 2606:50c0:8002::153, 2606:50c0:8003::153 |
| CNAME | www | vikabot.github.io |

## Deploy — own VPS (alternative)

```bash
rsync -av --delete ./ user@server:/var/www/viotours/      # whole folder (dist + server)
sudo cp deploy/nginx.conf /etc/nginx/sites-available/viotours
sudo ln -s /etc/nginx/sites-available/viotours /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d viotours.in -d www.viotours.in
sudo cp deploy/viotours-enquiry.service /etc/systemd/system/   # fill SMTP vars first
sudo systemctl daemon-reload && sudo systemctl enable --now viotours-enquiry
```

If the endpoint is down, forms don't lose the visitor: they offer WhatsApp/email with the message pre-filled.

## Workflow

Edit `content/*.json` → `python3 build.py` → `rsync dist/` to the server.

## v1 rules kept from the design system

No "Book now" / "Pay" anywhere — only "Request this trip" / "Plan my trip". Prices per person with
what's included. No fake scarcity, no "100% safe". Music plays once on load at 35%, mute lasts the session.

## Next (Phase 3 / v2)

Accounts and the Traveller / Guide / Admin dashboards (Next.js + Supabase) replace `signin.html`
and the JSON files; v2 adds affiliate price feeds (Booking.com, Agoda, GetYourGuide) and the
price-comparison card.
