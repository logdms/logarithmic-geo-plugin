# Logarithmic GEO

Generative Engine Optimization (GEO) audits for any website, packaged as agent skills for Grok Build, Cursor and other hosts that load Agent Skills.

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

## Install

**Grok Build.** Once the plugin is listed in the xAI plugin marketplace, open `/plugins`, go to the Marketplace tab and install `logarithmic-geo`. To try a local checkout: `grok --plugin-dir /path/to/logarithmic-geo`.

**Cursor.** The repository includes a Cursor plugin manifest (`.cursor-plugin/plugin.json`).

## Use

Ask in plain words or call a skill directly:

- "Run a GEO audit of https://example.com"
- `/geo-audit https://example.com`
- `/geo crawlers https://example.com`
- `/geo-report-pdf` after an audit

The helper scripts in `skills/geo/scripts/` need Python 3 and four packages:

```bash
pip install -r skills/geo/requirements.txt   # requests, beautifulsoup4, lxml, reportlab
```

The PDF report needs them. The other checks can also run on the agent's own web fetching.

## Network access and data

- It requests only the site you ask it to audit: its pages, `robots.txt`, sitemaps and `llms.txt`. `fetch_page.py` repeats some of those requests with AI-crawler user-agent strings (GPTBot, ClaudeBot, PerplexityBot, Googlebot, Bingbot) to test how the site treats each crawler.
- `brand_scanner.py` calls the public Wikipedia and Wikidata search APIs with the brand name. It builds search links for YouTube, Reddit, LinkedIn and review sites without requesting them.
- No API keys, accounts or credentials are needed. There is no telemetry, and nothing is sent to Logarithmic.

## License

MIT. See [LICENSE](LICENSE), which keeps the original geo-seo-claude copyright notice alongside Logarithmic's.
