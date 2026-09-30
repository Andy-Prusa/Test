# Hosting the page on Cloudflare Pages

The deployable folder is **`site/`**. It contains exactly two files:

| file | what |
|---|---|
| `index.html` | the whole simulator, 91 KB, a single self-contained file |
| `_headers` | HTTP headers Cloudflare Pages applies to everything it serves |

**There is no build step and no dependency to install.** `index.html` is one
file with the model, the styles and the markup inlined. It fetches nothing —
no scripts, no stylesheets, no fonts, no images, no analytics — and makes no
network request of any kind once it has loaded. That is checked, not assumed:
the page is loaded in a real browser over HTTP with the `_headers` rules
applied and asserted to issue **zero** external requests.

## Deploy it

Any one of these works. The first is the least trouble.

**1. Drag and drop.** In the Cloudflare dashboard go to *Workers & Pages* →
*Create* → *Pages* → *Upload assets*, name the project, and drag the `site`
folder in. Done; you get a `*.pages.dev` address straight away.

**2. Wrangler, from this directory.**

```sh
npx wrangler pages deploy site --project-name apnoea
```

**3. Connect the Git repository.** *Workers & Pages* → *Create* → *Pages* →
*Connect to Git*, pick the repo and branch, then set:

- **Build command:** leave empty
- **Build output directory:** `site`

`site/` is committed, so Cloudflare has nothing to build. Every push to the
chosen branch redeploys.

## After a change to the model

`site/index.html` is a copy, and a copy rots the moment the page is rebuilt and
the copy is not. Regenerate both:

```sh
python3 build_page.py      # rebuild the page from model.js
python3 build_site.py      # refresh site/ from the page
```

The pre-commit hook runs `build_page.py --check` and `build_site.py --check`,
so a stale deployment folder fails a commit instead of quietly serving an old
model.

## The headers, and what they assume

```
Content-Security-Policy: default-src 'none'; script-src 'unsafe-inline';
  style-src 'unsafe-inline'; img-src 'self' data:; font-src 'self';
  base-uri 'none'; form-action 'none'
```

`default-src 'none'` denies everything, and only inline script and style are
allowed back — which is the page itself. This is only tight enough to be worth
setting *because* the page is self-contained. **If you ever add an external
script, stylesheet or font, this policy will block it** and the page will break
on the deployed domain while still working from a local file. Change the policy
in `build_site.py` in the same commit, not afterwards.

**Framing is deliberately left open.** There is no `X-Frame-Options` and no
`frame-ancestors`, so the page can be embedded in teaching material and in
sandboxed embeds. If you do not want that, add `frame-ancestors 'self'` to the
policy in `build_site.py`.

## Two things to decide before you make the link public

1. **The footer states the licence**: "© 2026 A. M. B. Heard. All rights
   reserved. Unpublished research model — not a medical device, not for patient
   care." A public URL is publication in the ordinary sense even if the page
   says unpublished, so check that wording says what you want it to say to
   whoever finds it.
2. **Cloudflare Pages projects are public by default.** See below.

## Making it private

Checked 2026-09-30. `developers.cloudflare.com` is unreachable from the build
container, so this came from search results and a third-party write-up rather
than Cloudflare's own docs: the mechanism is stable but Cloudflare renames
dashboard menus often, so treat the click-path as a guide and confirm as you go.

**THE TRAP. There is a toggle at *Workers & Pages* → the project → *Settings* →
*General* → *Enable access policy*, and it is NOT the answer.** It protects
only the randomly generated PREVIEW deployments — the
`373f31e2.project.pages.dev` hash URLs. It does **not** protect the
`*.pages.dev` production URL and does **not** protect a custom domain. Turning
it on and assuming the site is private leaves the link everyone actually uses
wide open.

**What does work** is Cloudflare Access (under Zero Trust / Cloudflare One,
free to 50 users), as a **Self-hosted application** over the hostname being
served:

1. *Zero Trust* → *Access* → *Applications* → *Add an application* →
   *Self-hosted*.
2. Set the domain to the hostname you publish — the custom domain, or the Pages
   domain with subdomain `*` to cover production and previews at once.
3. Add a policy: **Allow** / **Include** / `Emails` for a named list, or
   `Emails ending in` for a whole organisation.
4. *Zero Trust* → *Settings* → *Authentication* → *Login methods*: make sure
   **One-time PIN** is enabled, so people get in with an emailed code instead
   of needing a Cloudflare account.

The most dependable arrangement is to serve the page on a **custom domain
already in your Cloudflare account** and protect that, rather than trying to
lock down the bare `pages.dev` hostname: Access applications are built around
domains you hold.

**A failure mode that wastes an afternoon**: if the policy says "emails ending
in @yourdomain" and someone signs in with a Gmail address, Access denies them
SILENTLY and never sends the PIN. It reads as a broken mail system rather than
a refused login.

**Not discoverable is not the same as private.** An unguessable URL, or a
`X-Robots-Tag: noindex` header, keeps the page out of search results. Only
Access stops someone who has the link.
