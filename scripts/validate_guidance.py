#!/usr/bin/env python3
"""Doc validation for the GEO playbooks. Standard library only.

    python3 scripts/validate_guidance.py              # check the repo
    python3 scripts/validate_guidance.py --self-test  # also prove each check fails on a mutated copy

What it catches (the failure cases, written before the guidance):
- a scoring weight, formula or band in geo / geo-audit changes, or legacy
  scoring text elsewhere is edited (scores must stay exactly as shipped);
- the PDF JSON contract in geo-report-pdf gains or loses a key;
- any of the nine advisories (A1-A9) loses a safeguard clause listed in REQUIRED;
- a copy of the destructive-action guard loses a GUARD_CLAUSES part of the
  noindex and URL-change rule on the same line as its A6 rule;
- the advisory playbook hardcodes a year, quotes a percentage or money figure,
  or brings in keyword density, content scores or toxic-backlink checks;
- a skill that should apply an advisory stops linking to the playbook or stops
  naming the advisory IDs it applies;
- a local Markdown link or #anchor no longer resolves.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADV = "skills/geo/references/advisories.md"

# Exact legacy scoring text. Pre-existing discrepancies between files are kept on purpose.
SCORING = {
    "skills/geo/SKILL.md": [
        "| AI Citability & Visibility | 25% |",
        "| Brand Authority Signals | 20% |",
        "| Content Quality & E-E-A-T | 20% |",
        "| Technical Foundations | 15% |",
        "| Structured Data | 10% |",
        "| Platform Optimization | 10% |",
    ],
    "skills/geo-audit/SKILL.md": [
        "| **AI Citability** | 25% |",
        "| **Brand Authority** | 20% |",
        "| **Content E-E-A-T** | 20% |",
        "| **Technical GEO** | 15% |",
        "| **Schema & Structured Data** | 10% |",
        "| **Platform Optimization** | 10% |",
        "GEO_Score = (Citability * 0.25) + (Brand * 0.20) + (EEAT * 0.20) + (Technical * 0.15) + (Schema * 0.10) + (Platform * 0.10)",
        "| 90-100 | Excellent |",
        "| 75-89 | Good |",
        "| 60-74 | Fair |",
        "| 40-59 | Poor |",
        "| 0-39 | Critical |",
    ],
    "skills/geo-report/SKILL.md": [
        "GEO Score = (Platform Score * 0.25) + (Content Score * 0.25) + (Technical Score * 0.20) + (Schema Score * 0.15) + (Brand Score * 0.15)",
        "| 85-100 | Excellent |",
        "| 70-84 | Good |",
        "| 55-69 | Moderate |",
        "| 40-54 | Below Average |",
        "| 0-39 | Needs Attention |",
    ],
    "skills/geo-brand-mentions/SKILL.md": [
        "Brand_Authority_Score = (YouTube * 0.25) + (Reddit * 0.25) + (Wikipedia * 0.20) + (LinkedIn * 0.15) + (Other * 0.15)",
    ],
    "skills/geo-technical/SKILL.md": [
        "- **90-100**: Excellent",
        "- **70-89**: Good",
        "- **50-69**: Needs Work",
        "- **30-49**: Poor",
        "- **0-29**: Critical",
    ],
    "skills/geo-platform-optimizer/SKILL.md": [
        "Status thresholds: Strong = 70+, Moderate = 40-69, Weak = 0-39",
    ],
    "skills/geo-report-pdf/SKILL.md": [
        "green (80+), blue (60-79), yellow (40-59), red (below 40)",
    ],
}

PDF_KEYS = {
    "url", "brand_name", "date", "geo_score", "scores", "platforms", "executive_summary",
    "findings", "quick_wins", "medium_term", "strategic", "crawler_access",
}

# Each advisory section must keep every clause below (case-insensitive regex).
REQUIRED = {
    "A1": [
        ("counts incoming links", r"incoming"),
        ("in-body links only", r"in-body"),
        ("same-topic sources", r"same-topic"),
        ("not sitemap", r"not[^.]*sitemap"),
        ("not nav", r"navigation|\bnav\b"),
        ("not footer", r"footer"),
        ("not outgoing totals", r"outgoing"),
        ("stated minimum 3-5", r"minimum[^.]*\b[345]\b"),
        ("reports observed count and threshold", r"observed count[^.]*threshold"),
        ("crawl coverage", r"crawl coverage"),
        ("incomplete evidence", r"incomplete"),
        ("normalized anchor text", r"normali[sz]ed anchor"),
        ("distinct canonical targets", r"distinct canonical"),
        ("source and target evidence", r"source[^.]*target"),
        ("collapse URL variants only on evidence", r"only[^.]*(redirect|canonical)[^.]*confirm"),
        ("otherwise keep distinct", r"otherwise[^.]*distinct"),
    ],
    "A2": [
        ("keyword leads title", r"lead(s)? the title"),
        ("year-sensitive page types", r"best[^.]*comparison[^.]*review[^.]*ranking"),
        ("current audit year", r"current audit year"),
        ("year from audit date", r"audit date"),
        ("unknown not failure", r"unknown[^.]*not[^.]*fail"),
        ("unknown brand", r"brand"),
        ("missing metadata", r"metadata"),
    ],
    "A3": [
        ("publisher-owned best-X list", r"best[- ]x"),
        ("own brand #1", r"#1"),
        ("own brand", r"own (brand|product)"),
        ("page evidence", r"page url"),
        ("entry evidence", r"entry"),
        ("assistant discount", r"discount"),
        ("no invented penalty", r"no[^.]*penalty"),
        ("no guarantee", r"no[^.]*guarantee|guarantee[^.]*no"),
    ],
    "A4": [
        ("earned mentions", r"earned"),
        ("editorial barter", r"editorial barter"),
        ("third-party rankings", r"rankings"),
        ("reviews", r"reviews"),
        ("forums", r"forums"),
        ("YouTube", r"youtube"),
        ("never paid placement", r"never[^.]*paid placement"),
        ("no automatic outreach/posting/submission", r"no automatic outreach, posting or submission"),
        ("3-5 real buyer prompts", r"3[-–]5 real buyer prompts"),
        ("weekly", r"week"),
        ("private window", r"private[^.]*window"),
        ("log fields", r"date[^.]*platform[^.]*prompt[^.]*cited url"),
        ("yes/no from observed answer", r"yes/no[^.]*observed"),
        ("no fabricated rates", r"never[^.]*(fabricat|invent|estimat)[^.]*rate"),
    ],
    "A5": [
        ("Bing Webmaster Tools", r"bing webmaster tools"),
        ("AI Performance report", r"ai performance"),
        ("IndexNow", r"indexnow"),
        ("sitemap submission", r"sitemap submission"),
        ("advice only", r"advice only"),
        ("no account registration", r"never registers"),
        ("no secrets", r"secret"),
        ("no ping or submit", r"ping[^.]*submit|submit[^.]*ping"),
    ],
    "A6": [
        ("600-word floor", r"600\+? main-content words"),
        ("delete/merge/redirect", r"delet[^.]*merg[^.]*redirect"),
        ("never recommend", r"never recommend"),
        ("unknown word count holds", r"unknown word count[^.]*hold"),
        ("irreversible needs human approval", r"irreversible[^.]*human approval"),
        ("advises only, never executes", r"never executes"),
        ("overrides legacy advice", r"overrides?[^.]*legacy"),
    ],
    "A7": [
        ("90-day window", r"90 days"),
        ("WAIT verdict", r"\bWAIT\b"),
        ("last-modified evidence", r"last[- ]modified"),
        ("recheck date", r"recheck date"),
        ("day 90 eligible for review", r"day 90[^.]*eligible for review"),
        ("not forced edit", r"not[^.]*(forced|required) edit"),
        ("unknown dates hold", r"unknown[^.]*hold"),
        ("no invented date", r"never invent"),
        ("workflow policy", r"workflow policy"),
        ("not a Google guarantee", r"not[^.]*google"),
        ("applies to quick wins/plans/reports/freshness", r"quick wins[^.]*plans[^.]*reports[^.]*freshness"),
    ],
    "A8": [
        ("separate script", r"separate script"),
        ("live URL response", r"live"),
        ("explicit sitemap membership", r"sitemap membership"),
        ("sitemap index children", r"index children|child sitemap"),
        ("re-crawl incoming in-body links", r"re-crawl"),
        ("timestamp", r"timestamp"),
        ("command", r"command"),
        ("raw evidence", r"raw"),
        ("partial/error is unverified", r"(?-i:UNVERIFIED)[^.]*(partial|error)|(partial|error)[^.]*(?-i:UNVERIFIED)"),
        ("no self-certification", r"self-certif"),
        ("uses existing fetch tool", r"fetch_page\.py"),
        ("offline verifier fails closed", r"fails closed"),
        ("no grep regex matching", r"^(?![\s\S]*\bgrep\b)"),
    ],
    "A9": [
        ("same intent", r"same intent"),
        ("same intent AND same angle", r"same intent and the same angle"),
        ("shared query not enough", r"shared query[^.]*not enough"),
        ("page evidence", r"page evidence"),
        ("missing either not flagged", r"not flagged"),
        ("no automatic consolidation", r"no automatic consolidation"),
        ("obeys 600-word guard", r"A6"),
    ],
}

FORBIDDEN = [
    ("hardcoded year", r"\b(19|20)\d\d\b"),
    ("percentage figure", r"\d\s?%"),
    ("money figure", r"\$\s?\d"),
    ("keyword density", r"keyword density"),
    ("content score", r"content score"),
    ("toxic backlinks", r"toxic|disavow"),
]

# Which skills must link to the playbook, and which advisories each one names.
INTEGRATION = {
    "skills/geo/SKILL.md": ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9"],
    "skills/geo-audit/SKILL.md": ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9"],
    "skills/geo-content/SKILL.md": ["A1", "A2", "A3", "A6", "A7", "A8", "A9"],
    "skills/geo-technical/SKILL.md": ["A1", "A5", "A6", "A8"],
    "skills/geo-brand-mentions/SKILL.md": ["A3", "A4"],
    "skills/geo-platform-optimizer/SKILL.md": ["A4", "A5", "A7"],
    "skills/geo-report/SKILL.md": ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9"],
    "skills/geo-report-pdf/SKILL.md": ["A6", "A7", "A8"],
}

# Skill-specific clauses that keep legacy text from contradicting the playbook.
LOCAL = {
    "skills/geo-content/SKILL.md": [
        ("internal linking counts incoming links per A1", r"### Internal Linking[^#]*incoming[^#]*A1"),
        ("freshness defers to A7", r"### Freshness Scoring[^#]*A7"),
    ],
    "skills/geo-technical/SKILL.md": [
        ("redirect advice yields to A6", r"### 4\.3 Redirect Chains[^#]*A6"),
        ("IndexNow is advice per A5", r"### Implementation Check[^#]*A5"),
    ],
    "skills/geo-platform-optimizer/SKILL.md": [
        ("Bing checklist is advice per A5", r"## Platform 5: Bing Copilot[\s\S]*?A5[\s\S]*?### Scoring Rubric"),
    ],
    "skills/geo-audit/SKILL.md": [
        ("advisories do not change scores", r"advisor[^.]*not change[^.]*score"),
        ("separate advisory report section", r"## Advisory Checks"),
    ],
    "skills/geo-report/SKILL.md": [
        ("advisories carry no projections", r"advisor[^.]*no[^.]*(projection|estimate)"),
        ("separate advisory section", r"Advisory Checks"),
    ],
    "skills/geo-report-pdf/SKILL.md": [
        ("Markdown companion", r"GEO-ADVISORIES\.md"),
        ("JSON contract unchanged", r"JSON[^.]*(unchanged|contract)"),
    ],
    "README.md": [
        ("links advisory playbook", re.escape(ADV)),
        ("scores unchanged", r"advisor[^.]*not change[^.]*score"),
    ],
    "CHANGELOG.md": [
        ("unreleased advisory entry", r"## Unreleased[^#]*advisor"),
    ],
}

# Every copy of the A6 guard states each GUARD_CLAUSES part on the line named by its anchor.
GUARD_CLAUSES = [
    ("noindex needs a human decision", r"noindex[^.]*human decision"),
    ("URL change needs a human decision", r"URL changes?[^.]*human decision"),
    ("at any word count", r"(any|regardless of|irrespective of|whatever the) word count"),
    ("URL change covers slug and path", r"URL changes?[^.]*(slug[^.]*path|path[^.]*slug)"),
    ("labelled Needs human approval", r"(?-i:Needs human approval)"),
    ("never executed", r"never execut"),
]
# Reference wording used in the guidance; the self-test mutates it.
GUARD = ("Noindex and URL changes need a human decision at any word count. "
         "A URL change includes any slug or path change. "
         "Label each one `Needs human approval` and never execute it.")
GUARD_SITES = [
    ("README.md", "a person approves and carries out every irreversible change"),
    (ADV, "**Human approval.**"),
    (ADV, "Any merge or redirect obeys A6"),
    ("skills/geo/SKILL.md", "A6 and A7 override any older advice"),
    ("skills/geo-audit/SKILL.md", "Action Plan item through A6 and A7"),
    ("skills/geo-content/SKILL.md", "Before advising pruning, merging or redirecting, apply A6"),
    ("skills/geo-technical/SKILL.md", "A6 overrides redirect, noindex"),
    ("skills/geo-technical/SKILL.md", "Any new redirect, merge or page removal follows"),
    ("skills/geo-report/SKILL.md", "Before an action enters Section 10, apply A6"),
    ("skills/geo-report-pdf/SKILL.md", "drop any item that A6"),
]


def read(root, rel):
    p = root / rel
    return p.read_text(encoding="utf-8") if p.exists() else None


def sections(text):
    """Map advisory ID -> section body, split on '## A<n>.' headings."""
    parts = re.split(r"^## (A\d)\b.*$", text, flags=re.M)
    return dict(zip(parts[1::2], parts[2::2]))


def slug(heading):
    s = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return s.replace(" ", "-")


def strip_fences(text):
    return re.sub(r"^```.*?^```", "", text, flags=re.M | re.S)


def check_scoring(root):
    errs = []
    for rel, needles in SCORING.items():
        text = read(root, rel) or ""
        errs += [f"{rel}: missing scoring text {n!r}" for n in needles if n not in text]
    return errs


def check_pdf_contract(root):
    text = read(root, "skills/geo-report-pdf/SKILL.md") or ""
    m = re.search(r"```json\n(.*?)```", text, re.S)
    if not m:
        return ["geo-report-pdf: JSON schema block missing"]
    keys = set(json.loads(m.group(1)))
    return [] if keys == PDF_KEYS else [f"geo-report-pdf: JSON keys changed: {sorted(keys ^ PDF_KEYS)}"]


def check_advisory(aid):
    def run(root):
        text = read(root, ADV)
        if text is None:
            return [f"{ADV} missing"]
        body = sections(text).get(aid)
        if body is None:
            return [f"{aid}: section missing"]
        return [f"{aid}: lost clause '{label}'" for label, rx in REQUIRED[aid] if not re.search(rx, body, re.I)]
    return run


def check_forbidden(root):
    text = read(root, ADV)
    if text is None:
        return [f"{ADV} missing"]
    return [f"{ADV}: contains {label}: {m.group(0)!r}"
            for label, rx in FORBIDDEN for m in [re.search(rx, text, re.I)] if m]


def check_integration(root):
    errs = []
    for rel, ids in INTEGRATION.items():
        text = read(root, rel) or ""
        if "references/advisories.md" not in text:
            errs.append(f"{rel}: no link to the advisory playbook")
        errs += [f"{rel}: does not name {i}" for i in ids if not re.search(rf"\b{i}\b", text)]
    for rel, rules in LOCAL.items():
        text = read(root, rel) or ""
        errs += [f"{rel}: lost '{label}'" for label, rx in rules if not re.search(rx, text, re.I)]
    return errs


def check_guard(root):
    errs = []
    for rel, anchor in GUARD_SITES:
        lines = [l for l in (read(root, rel) or "").splitlines() if anchor in l]
        if not lines:
            errs.append(f"{rel}: guard rule {anchor!r} missing")
        errs += [f"{rel}: {anchor!r} lost '{label}'" for label, rx in GUARD_CLAUSES
                 for l in lines if not re.search(rx, l, re.I)]
    return errs


def check_links(root):
    errs = []
    files = [root / "README.md", root / "CHANGELOG.md", *sorted((root / "skills").rglob("*.md"))]
    for f in files:
        for target in re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", strip_fences(f.read_text(encoding="utf-8"))):
            if re.match(r"[a-z]+:", target) or target == "URL":
                continue
            path, _, anchor = target.partition("#")
            dest = (f.parent / path).resolve() if path else f
            rel = f.relative_to(root)
            if not dest.exists():
                errs.append(f"{rel}: broken link {target}")
            elif anchor and dest.suffix == ".md":
                heads = re.findall(r"^#+ (.+)$", strip_fences(dest.read_text(encoding="utf-8")), re.M)
                if anchor not in {slug(h) for h in heads}:
                    errs.append(f"{rel}: missing anchor {target}")
    return errs


def a8_cases():
    """(name, expected exit code, file overrides, manifest overrides, files to drop)."""
    t = "https://example.com/tools/invoice-template/"
    ns = 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
    idx_url, pages_url = "https://example.com/sitemap_index.xml", "https://example.com/sitemap-pages.xml"

    def live(**kw):
        return json.dumps({"url": t, "status_code": 200, "redirect_chain": [], "canonical": t, "errors": [], **kw})

    good = f'<body><nav><a href="{t}">nav</a></nav><main><p>Use the <a href="/tools/invoice-template/#x">invoice template</a>.</p></main></body>'
    files = {
        "live.json": live(),
        "index.xml": f'<?xml version="1.0"?><sitemapindex {ns}><sitemap><loc>\n  {pages_url}  \n</loc></sitemap></sitemapindex>',
        "pages.xml": f'<urlset {ns}><url><loc> https://example.com/ </loc></url><url><loc>\n{t}\n</loc></url></urlset>',
        "s1.html": good, "s2.html": good, "s3.html": good,
    }
    sources = [{"url": f"https://example.com/blog/post-{i}/", "html": f"s{i}.html",
                "same_topic_reason": "invoicing post"} for i in (1, 2, 3)]
    manifest = {"target": t, "collected_at": "fixture", "commands": ["fixture"], "live": "live.json",
                "sitemap_roots": [idx_url], "sitemap_files": {idx_url: "index.xml", pages_url: "pages.xml"},
                "sources": sources, "min_links": 3}
    no_reason = [dict(sources[0], same_topic_reason=""), *sources[1:]]
    cases = [
        ("done", 0, {}, {}, []),
        ("missing live evidence", 2, {}, {}, ["live.json"]),
        ("live 404", 1, {"live.json": live(status_code=404)}, {}, []),
        ("sitemap absent", 1, {"pages.xml": f'<urlset {ns}><url><loc>https://example.com/</loc></url></urlset>'}, {}, []),
        ("link deficit", 1, {}, {"sources": sources[:2]}, []),
        ("index child not fetched", 2, {}, {"sitemap_files": {idx_url: "index.xml"}}, []),
        ("body unproven", 2, {"s3.html": f'<body><p><a href="{t}">x</a></p></body>'}, {}, []),
        ("canonical missing", 2, {"live.json": live(canonical=None)}, {}, []),
        ("unexpected redirect", 1, {"live.json": live(redirect_chain=[{"url": t[:-1], "status": 301}])}, {}, []),
        ("nav and unproven variant not counted", 1,
         {"s3.html": f'<main><nav><a href="{t}">x</a></nav><p><a href="{t[:-1]}">x</a></p></main>'}, {}, []),
        ("no timestamp", 2, {}, {"collected_at": ""}, []),
        ("fetch error", 2, {"live.json": live(status_code=None, canonical=None, errors=["Connection error: x"])}, {}, []),
        ("same-topic reason missing", 2, {}, {"sources": no_reason}, []),
        ("threshold below A1 range", 2, {}, {"min_links": 1}, []),
        ("index child missing although target found", 2,
         {"index.xml": f'<sitemapindex {ns}><sitemap><loc>{pages_url}</loc></sitemap>'
                       f'<sitemap><loc>https://example.com/sitemap-posts.xml</loc></sitemap></sitemapindex>'}, {}, []),
        ("extra source missing although 3 found", 2, {},
         {"sources": [*sources, dict(sources[0], url="https://example.com/blog/post-4/", html="s4.html")]}, []),
        ("live 200 with fetch errors", 2, {"live.json": live(errors=["Invalid JSON-LD detected"])}, {}, []),
        ("sitemap root is not urlset or index", 2, {"pages.xml": f"<html><loc>{t}</loc></html>"}, {}, []),
        ("external-host source", 2, {}, {"sources": [*sources[:2], dict(sources[2], url="https://other.example/x/")]}, []),
        ("self-link source", 2, {}, {"sources": [*sources[:2], dict(sources[2], url=t)]}, []),
        ("fragment duplicates count once", 1, {},
         {"sources": [dict(sources[0], url=sources[0]["url"] + f"#{c}") for c in "abc"]}, []),
        ("article inside aside is not body", 2, {"s3.html": f'<aside><article><a href="{t}">x</a></article></aside>'}, {}, []),
        ("live evidence is for another URL", 2, {"live.json": live(url="https://example.com/other/")}, {}, []),
        ("target only in image:loc extension", 1,
         {"pages.xml": f'<urlset {ns} xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
                       f'<url><loc>https://example.com/</loc><image:image><image:loc>{t}</image:loc></image:image></url></urlset>'},
         {}, []),
        ("article inside nav outside main not counted", 1,
         {"s3.html": f'<nav><article><a href="{t}">x</a></article></nav><main><p>none</p></main>'}, {}, []),
    ]
    return files, manifest, cases


def check_a8_verifier(root):
    text = read(root, ADV)
    body = sections(text).get("A8", "") if text else ""
    m = re.search(r"```python\n(.*?)```", body, re.S)
    if not m:
        return ["A8: no python verifier snippet"]
    files, manifest, cases = a8_cases()
    errs = []
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "verify_done.py"
        script.write_text(m.group(1), encoding="utf-8")
        for name, code, f_over, m_over, drop in cases:
            case = Path(tmp) / re.sub(r"\W+", "-", name)
            case.mkdir()
            for fname, content in {**files, **f_over}.items():
                if fname not in drop:
                    (case / fname).write_text(content, encoding="utf-8")
            (case / "evidence.json").write_text(json.dumps({**manifest, **m_over}), encoding="utf-8")
            r = subprocess.run([sys.executable, "-I", str(script), str(case / "evidence.json")],
                               capture_output=True, text=True, timeout=30)
            want = {0: "DONE", 1: "NOT DONE", 2: "UNVERIFIED"}[code]
            try:
                got = json.loads(r.stdout).get("verdict")
            except ValueError:
                got = None
            if r.returncode != code or got != want:
                errs.append(f"A8 case '{name}': want {want}/{code}, got {got}/{r.returncode} {r.stderr.strip()[-200:]}")
    return errs


CHECKS = [("scoring text preserved", check_scoring), ("PDF JSON contract", check_pdf_contract)]
CHECKS += [(f"advisory {aid}", check_advisory(aid)) for aid in REQUIRED]
CHECKS += [("A8 verifier fixtures", check_a8_verifier),
           ("advisory forbidden content", check_forbidden),
           ("skill integration", check_integration),
           ("noindex and URL-change guard", check_guard),
           ("local markdown links", check_links)]


def run_checks(root, quiet=False):
    failed = 0
    for name, fn in CHECKS:
        errs = fn(root)
        failed += bool(errs)
        if not quiet:
            print(("FAIL " if errs else "PASS ") + name)
            for e in errs:
                print("    " + e)
    if not quiet:
        print(f"{len(CHECKS) - failed} passed, {failed} failed, {len(CHECKS)} checks")
    return failed


# (file, old, new, check that must fail). Each removes or corrupts one safeguard.
MUTATIONS = [
    ("skills/geo-audit/SKILL.md", "(Citability * 0.25)", "(Citability * 0.30)", "scoring text preserved"),
    ("skills/geo-audit/SKILL.md", "| 75-89 | Good |", "| 70-89 | Good |", "scoring text preserved"),
    ("skills/geo-report-pdf/SKILL.md", '"strategic": [', '"advisories": [], "strategic": [', "PDF JSON contract"),
    (ADV, "in-body", "body", "advisory A1"),
    (ADV, "current audit year", "year", "advisory A2"),
    (ADV, "#1", "first", "advisory A3"),
    (ADV, "never as paid placement", "or paid placement", "advisory A4"),
    (ADV, "never registers", "registers", "advisory A5"),
    (ADV, "600+ main-content words", "1,500+ main-content words", "advisory A6"),
    (ADV, "WAIT", "RE-EDIT", "advisory A7"),
    (ADV, "UNVERIFIED", "DONE", "advisory A8"),
    (ADV, "and the same angle", "or the same angle", "advisory A9"),
    (ADV, "current audit year", "current audit year (e.g. 2026)", "advisory forbidden content"),
    ("skills/geo-technical/SKILL.md", "../geo/references/advisories.md", "advisories.md", "skill integration"),
    ("README.md", "](LICENSE)", "](LICENCE)", "local markdown links"),
    (ADV, 'if live.get("status_code") not in (None, 200):', 'if live.get("status_code") == 500:', "A8 verifier fixtures"),
    (ADV, "raise ValueError(\"no <main>", "print(\"no <main>", "A8 verifier fixtures"),
    (ADV, "    unverified += gaps\n", "", "A8 verifier fixtures"),
    (ADV, 'if live.get("url") != target:', "if False:", "A8 verifier fixtures"),
    (ADV, "for loc in e if", "for loc in e.iter() if", "A8 verifier fixtures"),
    (ADV, "linked.add(src)", "linked.add(s[\"url\"])", "A8 verifier fixtures"),
    (ADV, "self.has_body |= tag in self.BODY and not open_tags & self.SKIP", "self.has_body |= tag in self.BODY", "A8 verifier fixtures"),
    (ADV, "Noindex and URL changes need", "URL changes need", "noindex and URL-change guard"),
    (ADV, "every one needs human approval. " + GUARD, "every one needs human approval.", "noindex and URL-change guard"),
    ("README.md", "Noindex and URL changes need", "Noindex changes need", "noindex and URL-change guard"),
    ("skills/geo/SKILL.md", "decision at any word count.", "decision.", "noindex and URL-change guard"),
    ("skills/geo-audit/SKILL.md", "any slug or path change", "any path change", "noindex and URL-change guard"),
    ("skills/geo-content/SKILL.md", "`Needs human approval`", "`Pending`", "noindex and URL-change guard"),
    ("skills/geo-technical/SKILL.md", "human approval. " + GUARD, "human approval.", "noindex and URL-change guard"),
    ("skills/geo-technical/SKILL.md", "category below. " + GUARD, "category below.", "noindex and URL-change guard"),
    ("skills/geo-report/SKILL.md", "at any word count", "for 600+ main-content words", "noindex and URL-change guard"),
    ("skills/geo-report-pdf/SKILL.md", "never execute it", "execute it", "noindex and URL-change guard"),
]


def self_test():
    ok = 0
    for rel, old, new, expect in MUTATIONS:
        with tempfile.TemporaryDirectory() as tmp:
            dst = Path(tmp)
            shutil.copytree(ROOT / "skills", dst / "skills")
            for name in ("README.md", "CHANGELOG.md", "LICENSE"):
                shutil.copy(ROOT / name, dst / name)
            p = dst / rel
            text = p.read_text(encoding="utf-8")
            if old not in text:
                print(f"FAIL mutation setup: {old!r} not found in {rel}")
                continue
            p.write_text(text.replace(old, new), encoding="utf-8")
            caught = bool(dict(CHECKS)[expect](dst))
            ok += caught
            print(("PASS" if caught else "FAIL") + f" mutation caught by '{expect}': {rel} {old!r} -> {new!r}")
    print(f"{ok} passed, {len(MUTATIONS) - ok} failed, {len(MUTATIONS)} mutations")
    return len(MUTATIONS) - ok


if __name__ == "__main__":
    bad = run_checks(ROOT)
    if "--self-test" in sys.argv:
        bad += self_test()
    sys.exit(1 if bad else 0)
