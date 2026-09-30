# Copyright (c) 2026 A. M. B. Heard. All rights reserved.
# Unpublished research software. See LICENSE: use in any publication
# requires prior written permission. Cite as in CITATION.cff.
"""Build `site/`, a static folder ready to host on Cloudflare Pages.

    python3 build_page.py      # first: rebuild the page from model.js
    python3 build_site.py      # then: assemble the deployable folder

WHY THIS IS A SCRIPT AND NOT A HAND-COPIED FOLDER. `site/index.html` is a COPY
of `airway_scenario.html`, and a copy rots the moment the page is rebuilt and
the copy is not. This regenerates it, and `--check` fails if the two have
drifted, so a stale deployment is a failed check rather than a silent
difference between what is tested and what is served.

WHAT IS SERVED. The page is a single self-contained file: no scripts,
stylesheets, fonts or images are fetched from anywhere, and it makes no network
request of any kind once loaded. That is a deliberate property (see the comment
at the top of the HTML) and it is what makes the Content-Security-Policy below
as tight as it is -- everything is denied except inline script and style, which
are the page itself.

FRAMING IS DELIBERATELY LEFT OPEN. No X-Frame-Options and no frame-ancestors,
because the page is meant to be embeddable in teaching material and in
sandboxed embeds. Add `frame-ancestors 'self'` to the CSP if that is not
wanted.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, 'airway_scenario.html')
SITE = os.path.join(HERE, 'site')

# Cloudflare Pages reads _headers from the root of the published directory.
HEADERS = """\
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: no-referrer
  Cross-Origin-Opener-Policy: same-origin
  Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=()
  Content-Security-Policy: default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'self' data:; font-src 'self'; base-uri 'none'; form-action 'none'
"""

FILES = {'_headers': HEADERS}


def build(check=False):
    if not os.path.exists(PAGE):
        print("airway_scenario.html does not exist; run: python3 build_page.py")
        return 1
    page = open(PAGE, encoding='utf-8').read()
    want = dict(FILES)
    want['index.html'] = page

    if check:
        stale = []
        for name, body in want.items():
            path = os.path.join(SITE, name)
            if not os.path.exists(path):
                stale.append(f"{name} is missing")
            elif open(path, encoding='utf-8').read() != body:
                stale.append(f"{name} differs")
        if stale:
            print("STALE: site/ does not match the built page.")
            for s in stale:
                print(f"  {s}")
            print("Run: python3 build_page.py && python3 build_site.py")
            return 1
        print(f"up to date: site/ matches {os.path.basename(PAGE)}")
        return 0

    os.makedirs(SITE, exist_ok=True)
    for name, body in want.items():
        with open(os.path.join(SITE, name), 'w', encoding='utf-8') as fh:
            fh.write(body)
    kb = len(page.encode('utf-8')) / 1024.0
    print(f"built {SITE}/")
    print(f"  index.html  {kb:.0f} KB, self-contained, no external requests")
    print(f"  _headers    security headers for Cloudflare Pages")
    print()
    print("Deploy (either way -- see DEPLOY.md):")
    print("  npx wrangler pages deploy site --project-name apnoea")
    print("  or point Cloudflare Pages at this repo, output directory: site")
    return 0


if __name__ == '__main__':
    sys.exit(build(check='--check' in sys.argv))
