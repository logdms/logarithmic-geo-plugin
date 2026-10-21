# GEO Advisory Checks (A1–A9)

Every GEO skill that crawls pages, plans fixes or writes a report applies these nine checks. They are advice. They add no points, remove no points and change no score, weight, formula or band. They do not replace E-E-A-T, citability or any other scored check.

Source: Paul Vengeons, "How to use Opus 5.5 + Jev for SEO" (https://x.com/VengeonsP/status/2112114728596070486). Only the SEO method is used here. No model judge, API key or paid tool is involved.

## How to apply them

- **Code counts, the agent advises.** Counts, dates and word totals come from fetched HTML or script output, never from memory or estimates.
- **Every result is one of four verdicts:** `FLAG`, `OK`, `UNKNOWN` or `WAIT`. A6 and A7 can also give `HOLD`. Missing or partial evidence gives `UNKNOWN`, never a guessed `FLAG`.
- **Every `FLAG` cites evidence:** page URL, the observed value, the threshold or rule, and how the value was obtained.
- **No invented numbers.** No projected traffic, citation lift, score gain or ranking date is attached to an advisory.
- **The plugin advises and never acts.** It does not edit, delete, redirect, publish, submit, register or contact anyone.
- **Output.** Advisories go in their own `Advisory Checks` section, separate from the score tables. The PDF path writes them to a Markdown companion, `GEO-ADVISORIES.md`, and leaves the PDF JSON as it is (see [geo-report-pdf](../../geo-report-pdf/SKILL.md)).

Use one row per finding:

| ID | Page | Verdict | Observed | Rule / threshold | Evidence (source, command, fetch time) |
|---|---|---|---|---|---|

Tools: `python3 <plugin>/skills/geo/scripts/fetch_page.py <url> page` returns `status_code`, `title`, `canonical`, `word_count` and `internal_links`. It strips `nav`, `header` and `footer` elements before it counts words and collects links. `<plugin>` is the plugin root folder.

## A1. Internal link coverage

Count **incoming in-body** internal links to each key page. Count only links that sit in the body text of crawled same-topic source pages. Do not count sitemap entries, navigation menus, footer links, or the page's own outgoing totals. Those say nothing about how other pages support it.

- Build the count from the crawl. Run `fetch_page.py <source> page` on each crawled page and match `internal_links` to the target's canonical URL. Drop fragments. Treat two URL variants (scheme, `www`, trailing slash) as one page only when a fetched redirect or canonical tag confirms they are the same. Otherwise keep them as distinct pages.
- Same-topic means the source page covers the target's topic, judged from its title and H1. Record the reason in one line.
- Default minimum: 3 incoming in-body links from same-topic pages. The playbook range is 3–5. An audit may set 4 or 5, but the report must state the threshold it used.
- Below the minimum: `FLAG`. Report the observed count and the threshold, and list the source URLs found.
- State crawl coverage: pages crawled against pages known, and whether the crawl cap was hit. If the crawl was incomplete, a fetch failed, or the theme puts links in sidebars that cannot be told apart from the body, the count is a floor. In those cases report `UNKNOWN` (incomplete evidence) rather than `FLAG`.
- Anchor conflicts: `FLAG` when the same normalized anchor text (lowercase, trimmed, whitespace collapsed) points to two or more distinct canonical target pages. List each source URL, anchor and target URL.

## A2. Title lead and year

- **Keyword lead.** When the target keyword for a page is known, check whether it leads the title: it comes first, word for word, ignoring case. If no keyword was supplied, report `UNKNOWN`. Do not infer the keyword from the title.
- **Year.** For best, comparison, review and ranking pages, check whether the title holds the current audit year. Take that year from the audit date at run time (`date +%Y`); never write it into a template. A missing year or an older year is a `FLAG`.
- **Unknowns.** If the title, page type, audit date or other metadata could not be fetched, the result is `UNKNOWN`, not a fail. The same applies when text before the keyword might be the brand but the brand is not confirmed.

## A3. Self-ranking in own best-X lists

`FLAG` a publisher-owned best-X, top-X or ranking list on the audited site when the site's own brand or own product holds the #1 entry.

- Evidence: page URL, list heading, and the #1 entry text exactly as shown. If the brand cannot be matched to the entry, report `UNKNOWN`.
- Why it matters: practitioners report that AI assistants discount self-ranked lists and cite the second or third entry instead. State that as a reported pattern. Give no penalty size, no lost-citation figure and no guarantee that a rewrite restores citations.
- Advice: rank the list on stated criteria, or move the own product into a disclosed note outside the ranking. The owner decides.

## A4. Third-party presence and prompt tracking

- **Where to get mentioned.** Recommend earned mentions in other people's rankings, reviews, forums and YouTube videos. Editorial barter is acceptable when each side would list the other on merit. Get listed on merit, never as paid placement.
- **No outreach.** The plugin may draft a pitch for the owner to edit and send. It does no automatic outreach, posting or submission.
- **Tracking.** The owner tracks 3–5 real buyer prompts each week in a private browser window on each AI platform. Log the date, platform, prompt, cited URL (or none) and yes/no for whether the brand was cited. The yes/no is taken from the observed answer as shown.
- Never estimate, invent or fabricate a citation rate or a visibility score from prompts nobody ran.

## A5. Bing tools

Recommend these to the site owner:

- Verify the site in Bing Webmaster Tools and read its AI Performance report. That report shows how the site appears in Microsoft AI answers.
- Set up IndexNow so new and changed URLs are announced.
- Use sitemap submission in Bing Webmaster Tools.

This is advice only. The plugin never registers accounts, never creates keys or secrets, and never pings IndexNow or submits sitemaps. It may fetch public files, such as a published IndexNow key file, to check what already exists.

## A6. Destructive-action guard

- **600-word floor.** Never recommend deleting, merging or redirecting a page that has 600+ main-content words. Take the count from `word_count` in `fetch_page.py` output. For such pages, recommend improving or differentiating them instead.
- **Unknown count.** An unknown word count means `HOLD`. This covers a failed fetch, client-rendered content, or boilerplate that cannot be stripped. Hold any destructive advice until the word count is evidenced.
- **Human approval.** Any irreversible action on any page needs human approval. That covers delete, merge, redirect, noindex, URL change, publish and sending. Label each such item `Needs human approval`. The plugin advises and never executes it.
- **Precedence.** This guard overrides legacy advice in any skill: technical redirect and duplicate-URL fixes, index-bloat cleanup, cannibalization merges and content pruning. Plain redirect hygiene that removes no page, such as collapsing a chain into one hop, still needs human approval.

## A7. 90-day wait on re-edits

Before recommending a re-edit of an existing page, find its last change date. Use the visible updated date, `dateModified`, sitemap `<lastmod>` or an owner-supplied change log, and record which source was used. Count days from that date to the audit date with code, not by eye.

- **Under 90 days since the last change:** verdict `WAIT`. Show the last-modified evidence and the recheck date (last change + 90 days). Do not give re-edit advice.
- **Day 90 and later:** the page is eligible for review. That is not a forced edit or a required edit.
- **Unknown date:** the result is `UNKNOWN` and the edit is on hold until the owner supplies the date. Never invent a date or assume one from the crawl date.
- This is a workflow policy based on practitioner experience that rankings settle over about three months after a real change. It is not a documented Google rule, and it carries no ranking guarantee.
- It applies everywhere a page edit is advised: quick wins, plans, reports, rechecks and freshness advice. Freshness scoring stays as it is; only the edit advice waits.

## A8. Done verification

A fix is `DONE` only after a separate script run verifies it. The writer's own report never counts; no self-certification. Three conditions must hold:

1. **Live URL.** The target URL returns 200 without a redirect, and its canonical tag names the target URL itself.
2. **Explicit sitemap membership.** The exact target URL appears as the direct `<url><loc>` of a fetched sitemap. Image and video `loc` extensions do not count. When the sitemap is an index, the child sitemaps are fetched too. `fetch_page.py <url> sitemap` stops at a page cap, so a miss there proves nothing.
3. **Incoming links.** A fresh re-crawl of the source pages finds at least the A1 minimum of same-topic pages linking to the target inside `<main>` or `<article>`, outside any nested `nav`, `header`, `footer` or `aside`.

**Collect** the evidence into one folder, outside the site's repo:

```bash
date -u +%Y-%m-%dT%H:%M:%SZ                                          # collected_at
python3 <plugin>/skills/geo/scripts/fetch_page.py "$URL" page > live.json
python3 <plugin>/skills/geo/scripts/fetch_page.py "$URL" robots     # read the sitemaps list
curl -sSf -o sitemap-1.xml "$SITEMAP"      # each root sitemap and each child of an index
curl -sSf -o src-1.html "$SOURCE"          # each same-topic source page, raw HTML
```

Then write `evidence.json`. File paths are relative to it:

```json
{
  "target": "https://example.com/page/",
  "collected_at": "<UTC timestamp from the date command>",
  "commands": ["<every command run, verbatim>"],
  "live": "live.json",
  "sitemap_roots": ["https://example.com/sitemap_index.xml"],
  "sitemap_files": {"https://example.com/sitemap_index.xml": "sitemap-1.xml"},
  "sources": [{"url": "https://example.com/blog/a/", "html": "src-1.html", "same_topic_reason": "<one line>"}],
  "min_links": 3
}
```

**Verify** offline with the script below, saved as `verify_done.py`: `python3 verify_done.py evidence.json`. It reads only the files the manifest names. It prints a JSON verdict and exits with 0 for `DONE`, 1 for `NOT DONE` and 2 for `UNVERIFIED`. It fails closed. Any missing, partial or erroring evidence gives `UNVERIFIED`, never `DONE`, even when the other evidence looks complete. That covers a fetch error, an absent canonical, an unfetched child sitemap, a sitemap file that is not a `urlset` or `sitemapindex`, a source without `<main>` or `<article>` outside skipped regions, an external-host or self-link source, and a missing same-topic reason. A source URL counts once after its fragment is dropped. URL matching is exact string equality after resolving relative links and dropping fragments. A variant URL (scheme, `www`, trailing slash) never counts as the target. `min_links` must be 3-5, per A1. `fetch_page.py` also lists invalid JSON-LD and suspected client-side rendering under `errors`. The verifier treats any error as incomplete evidence, so fix those first or check the page by hand.

```python
import json, sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlsplit


class BodyLinks(HTMLParser):
    """Links inside <main>/<article> with no nav/header/footer/aside ancestor."""
    BODY, SKIP = {"main", "article"}, {"nav", "header", "footer", "aside"}

    def __init__(self):
        super().__init__()
        self.stack, self.has_body, self.hrefs = [], False, []

    def handle_starttag(self, tag, attrs):
        open_tags = set(self.stack)
        if tag in self.BODY | self.SKIP:
            self.stack.append(tag)
            self.has_body |= tag in self.BODY and not open_tags & self.SKIP
        elif tag == "a" and open_tags & self.BODY and not open_tags & self.SKIP and dict(attrs).get("href"):
            self.hrefs.append(dict(attrs)["href"])

    def handle_endtag(self, tag):
        if tag in self.stack:
            while self.stack.pop() != tag:
                pass


def local(tag):
    return tag.rsplit("}", 1)[-1]


def verify(manifest_path):
    base = Path(manifest_path).parent
    failed, unverified, links = [], [], 0
    m = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    target = m["target"]
    read = lambda name: (base / name).read_text(encoding="utf-8")
    if not m.get("collected_at") or not m.get("commands"):
        unverified.append("manifest lacks collected_at or commands")
    try:
        live = json.loads(read(m["live"]))
        if live.get("url") != target:
            unverified.append(f"live evidence is for {live.get('url')}, not the target")
        if live.get("status_code") is None or live.get("errors"):
            unverified.append(f"live fetch incomplete: {live.get('status_code')} {live.get('errors')}")
        if live.get("status_code") not in (None, 200):
            failed.append(f"live status {live['status_code']}")
        if live.get("redirect_chain"):
            failed.append(f"redirected: {live['redirect_chain']}")
        if live.get("status_code") is not None and not live.get("canonical"):
            unverified.append("no canonical tag: identity unproven")
        elif live.get("canonical") and urljoin(target, live["canonical"]) != target:
            failed.append(f"canonical is {live['canonical']}")
    except Exception as e:
        unverified.append(f"live evidence: {e!r}")
    locs, gaps, queue, seen = set(), [], list(m.get("sitemap_roots") or []), set()
    if not queue:
        gaps.append("no sitemap roots")
    while queue:
        url = queue.pop()
        if url in seen:
            continue
        seen.add(url)
        try:
            tree = ET.fromstring(read(m["sitemap_files"][url]))
            if local(tree.tag) not in ("urlset", "sitemapindex"):
                raise ValueError(f"root <{local(tree.tag)}> is not a sitemap")
            entry = "sitemap" if local(tree.tag) == "sitemapindex" else "url"
            found = [loc.text.strip() for e in tree if local(e.tag) == entry
                     for loc in e if local(loc.tag) == "loc" and loc.text]
            (queue.extend if local(tree.tag) == "sitemapindex" else locs.update)(found)
        except Exception as e:
            gaps.append(f"sitemap {url}: {e!r}")
    unverified += gaps
    if target not in locs:
        failed.append("target not in fetched sitemaps")
    linked = set()
    for s in m.get("sources") or []:
        try:
            src = urldefrag(s["url"])[0]
            if urlsplit(src).netloc != urlsplit(target).netloc or src == target:
                raise ValueError("external-host or self-link source")
            if not s.get("same_topic_reason"):
                raise ValueError("same-topic reason missing")
            p = BodyLinks()
            p.feed(read(s["html"]))
            if not p.has_body:
                raise ValueError("no <main> or <article>: body links unproven")
            if any(urldefrag(urljoin(s["url"], h))[0] == target for h in p.hrefs):
                linked.add(src)
        except Exception as e:
            unverified.append(f"source {s.get('url')}: {e}")
    links, need = len(linked), int(m.get("min_links", 3))
    if not 3 <= need <= 5:
        unverified.append(f"min_links {need} is outside the A1 range 3-5")
    if links < need:
        failed.append(f"{links} confirmed in-body links, need {need}")
    verdict = "UNVERIFIED" if unverified else "NOT DONE" if failed else "DONE"
    return verdict, {"target": target, "collected_at": m.get("collected_at"), "verdict": verdict,
                     "in_body_links": links, "failed": failed, "unverified": unverified}


if __name__ == "__main__":
    try:
        verdict, report = verify(sys.argv[1])
    except Exception as e:
        verdict, report = "UNVERIFIED", {"verdict": "UNVERIFIED", "unverified": [repr(e)]}
    print(json.dumps(report, indent=2))
    sys.exit({"DONE": 0, "NOT DONE": 1}.get(verdict, 2))
```

Keep the timestamp, commands, raw files and the verifier output together as the record. The verdicts mean:

- `DONE`: all three conditions passed.
- `NOT DONE`: the evidence is complete and a condition failed.
- `UNVERIFIED`: any evidence is partial, timed out or returned an error.

## A9. Cannibalization

Flag a pair of pages only when both have the same intent and the same angle, confirmed by page evidence. Same angle means the same reader, question and answer. A shared query in Search Console or a rank tracker is not enough.

- Evidence for each page: URL, title, H1, page type and opening paragraph, with one line each on intent and angle.
- If intent or angle differs, the pair is not flagged. If evidence for either is missing, the pair is not flagged and is reported as `UNKNOWN`.
- No automatic consolidation. The owner chooses the fix. Any merge or redirect obeys A6: none for a page with 600+ main-content words or an unknown count, and every one needs human approval.
