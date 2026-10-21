# Logarithmic GEO

Generative Engine Optimization (GEO) audits for any website, packaged as agent skills for Claude Code, Grok Build, Cursor and other hosts that load Agent Skills.

Give it a URL and it checks how ready the site is for AI search:

- which AI crawlers can reach it (robots.txt, meta tags, HTTP headers)
- whether it has a useful `llms.txt`, and drafts one if not
- schema.org structured data, with ready-to-paste JSON-LD
- how quotable the content is for AI answers (citability)
- brand signals on the sources AI models lean on
- readiness for Google AI Overviews, ChatGPT, Perplexity, Gemini and Bing Copilot

A full audit scores the site from 0 to 100, lists fixes in priority order, and can produce a client-ready report in Markdown or PDF.

Built by [Logarithmic](https://logarithmic.com). Based on the open-source [geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) skills by Zubair Trabzada (MIT), with the changes Logarithmic made while running them in production. Not affiliated with or endorsed by the original author.

## Skills

| Skill | Use it for |
| --- | --- |
| `geo` | Entry point. `/geo <command> <url>` routes to the skills below, and adds a single-page analysis and a quick snapshot |
| `geo-audit` | Full audit: runs the checks in parallel and computes an overall GEO score (0–100) |
| `geo-citability` | How likely AI systems are to quote passages from a page |
| `geo-crawlers` | Which AI crawlers can access the site, and which to allow |
| `geo-llmstxt` | Validate or generate `llms.txt` |
| `geo-brand-mentions` | Brand presence on the sources AI models cite (Wikipedia, Reddit, YouTube and others) |
| `geo-platform-optimizer` | Readiness for each AI search platform |
| `geo-schema` | Detect, validate and generate schema.org JSON-LD |
| `geo-technical` | Technical SEO with GEO-specific checks (server rendering, crawlability, performance) |
| `geo-content` | Content quality and E-E-A-T |
| `geo-report` | Client-facing report in Markdown |
| `geo-report-pdf` | The same report as a PDF with charts |

## Advisory checks

Audits, plans and reports also apply nine advisory checks from [skills/geo/references/advisories.md](skills/geo/references/advisories.md): incoming internal links, title keyword and year, self-ranking lists, third-party mentions and prompt tracking, Bing tools, a guard against destructive changes, a 90-day wait before re-edits, scripted done verification, and strict cannibalization. The advisories do not change any score, weight or band. The plugin advises; a person approves and carries out every irreversible change. Noindex and URL changes need a human decision at any word count. A URL change includes any slug or path change. Label each one `Needs human approval` and never execute it.

Check the playbooks after editing them (Python 3, no packages): `python3 scripts/validate_guidance.py --self-test`.

## Install

**Claude Code.** In Claude Code, the plugin is `geo-by-logarithmic`, shown as GEO by Logarithmic. Add the Logarithmic marketplace and install it from your shell:

```bash
claude plugin marketplace add logdms/logarithmic-geo-plugin
claude plugin install geo-by-logarithmic@logarithmic
```

Inside a session, `/plugin marketplace add logdms/logarithmic-geo-plugin` and `/plugin install geo-by-logarithmic@logarithmic` do the same. To try a local checkout: `claude --plugin-dir /path/to/logarithmic-geo-plugin`.

The plugin also connects Claude Code to the Logarithmic GEO service, a remote MCP server named `geo` at `https://geo-mcp.logarithmic.com/mcp`. The plugin ships no token or key. When the service asks you to sign in, run `/mcp`, pick `geo` and complete the sign-in in your browser. If the browser does not open, copy the URL that Claude Code prints. If the `geo` tools stop working or `/mcp` shows that `geo` needs authentication, open `/mcp`, pick `geo` and choose **Re-authenticate**. **Clear authentication** in the same menu signs you out. The skills still run without the service; see [Network access and data](#network-access-and-data).

**Grok Build.** Once the plugin is listed in the xAI plugin marketplace, open `/plugins`, go to the Marketplace tab and install `logarithmic-geo`. To try a local checkout: `grok --plugin-dir /path/to/logarithmic-geo`.

**Cursor.** The repository includes a Cursor plugin manifest (`.cursor-plugin/plugin.json`).

## Use

Ask in plain words or call a skill directly:

- "Run a GEO audit of https://example.com"
- `/geo-audit https://example.com`
- `/geo crawlers https://example.com`
- `/geo-report-pdf` after an audit

Claude Code puts every plugin skill under the plugin name, so there the commands read `/geo-by-logarithmic:geo-audit https://example.com` and `/geo-by-logarithmic:geo crawlers https://example.com`. The other skills follow the same pattern.

The helper scripts in `skills/geo/scripts/` need Python 3 and four packages:

```bash
pip install -r skills/geo/requirements.txt   # requests, beautifulsoup4, lxml, reportlab
```

The PDF report needs them. The other checks can also run on the agent's own web fetching.

## Network access and data

The plugin reaches the network in two ways: through local skill scripts and through the remote Logarithmic GEO service.

**Local skills and scripts.** These run on your machine:

- They request only the site you ask them to audit: its pages, `robots.txt`, sitemaps and `llms.txt`. `fetch_page.py` repeats some of those requests with AI-crawler user-agent strings (GPTBot, ClaudeBot, PerplexityBot, Googlebot, Bingbot) to test how the site treats each crawler.
- `brand_scanner.py` calls the public Wikipedia and Wikidata search APIs with the brand name. It builds search links for YouTube, Reddit, LinkedIn and review sites without requesting them.
- The local scripts need no API keys, accounts or credentials, send no telemetry, and send nothing to Logarithmic.

**Remote Logarithmic GEO service (Claude Code).** The Claude Code plugin declares the `geo` MCP server at `https://geo-mcp.logarithmic.com/mcp`. When Claude calls one of its tools, the service gets the tool arguments, including the site URL you ask about. After you sign in, it also gets the account identity from that sign-in. The service stores the audits and reports it produces.

To avoid sending audit data to Logarithmic, turn the service off before you run the skills: run `/mcp`, pick `geo` and choose **Disable**. Claude Code records this per project, so repeat it in each project. While `geo` is disabled, Claude Code does not connect to the service. The existing skills remain available with the local scripts and the agent's own web fetching. To turn it back on, toggle `geo` on again in `/mcp`.

Logarithmic's general [Privacy Policy](https://logarithmic.com/privacy-policy) applies to Logarithmic. This README describes what the GEO service receives. Questions: office@logarithmic.com or https://logarithmic.com/contact.

## License

MIT. See [LICENSE](LICENSE), which keeps the original geo-seo-claude copyright notice alongside Logarithmic's.
