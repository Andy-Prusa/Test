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
2. **Cloudflare Pages projects are public by default.** If you want it limited
   to named people, put Cloudflare Access in front of the project (*Settings* →
   *Access policy*) rather than relying on the URL being hard to guess.
