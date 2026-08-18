# Profound Signal → Marketing Skill Routing

Use this table after pulling Profound MCP reports. Pick **one primary** and
**zero–two supporting** skills per task — avoid running unrelated skills.

## By Profound report

### `get_visibility_report`

| Signal | Skills | Actions |
| --- | --- | --- |
| Low share of voice on prompt cluster | `ai-seo`, `content-strategy` | Map fan-out queries; plan topical coverage |
| Single prompt invisible | `copywriting`, `ai-seo` | Draft answer-first block for that prompt |
| Model-specific gap (e.g. ChatGPT vs Perplexity) | `ai-seo` | Apply platform-specific patterns from references |
| Category-wide weakness | `marketing-plan`, `content-strategy` | Prioritize page/topic backlog |

### `get_citations_report`

| Signal | Skills | Actions |
| --- | --- | --- |
| Competitor URL cited, Vixxo not | `competitors`, `competitor-profiling`, `ai-seo` | Gap analysis; differentiation copy |
| Vixxo path cited but thin content | `copy-editing`, `seo-audit` | Expand answer blocks on cited page |
| No vixxo.com citations for topic | `hubspot-page-aeo`, `copywriting` | Revamp or new FAQ/intros on clone |
| Third-party sources cited (Reddit, G2) | `public-relations`, `ai-seo` | Earned media / review strategy |

### `get_prompt_answers`

| Signal | Skills | Actions |
| --- | --- | --- |
| AI answer omits Vixxo | `copywriting`, `ai-seo` | Match answer structure; add entity-rich intro |
| AI answer is wrong about category | `copy-editing`, `marketing-psychology` | Correct misconceptions in FAQ |
| Answer lists competitors only | `competitors`, `product-marketing` | Positioning refresh |
| Good answer but no link | `schema`, `seo-audit` | Structured data + internal links |

### `get_sentiment_report`

| Signal | Skills | Actions |
| --- | --- | --- |
| Positive theme underused | `copywriting`, `marketing-psychology` | Reinforce in hero and FAQ |
| Negative theme attached to brand | `copy-editing`, `public-relations` | Counter-narrative copy |
| Neutral/indifferent sentiment | `marketing-psychology`, `offers` | Sharpen value prop |

### `get_bots_report` / `get_referrals_report`

| Signal | Skills | Actions |
| --- | --- | --- |
| Crawl gaps | `seo-audit`, `site-architecture` | Indexability, robots, sitemap |
| AI referral traffic to specific paths | `analytics`, `attribution` | Measure AEO impact |
| Low agent crawl on new clones | `schema`, `ai-seo` | llms.txt, FAQ schema, clear HTML |

---

## By task type

| Task | Start with | Then |
| --- | --- | --- |
| Weekly tracker row revamp | Profound snapshot → `hubspot-page-aeo` | `seo-audit`, `copywriting` as needed |
| New page from topic | Profound visibility on topic → `hubspot-page-content` | `ai-seo`, `schema` |
| Blog/email/social bundle | Profound prompts → `hubspot-content` | `social`, `emails`, `copywriting` |
| Competitive AEO brief | `get_citations_report` → `competitors` | `competitor-profiling`, `ai-seo` |
| Site-wide AEO audit | Full Profound pull → `ai-seo` | `seo-audit`, `site-architecture`, `content-strategy` |
| Scale under-cited topics | Citation gaps → `programmatic-seo` | `content-strategy`, `schema` |

---

## Skills that rarely need Profound (skip unless asked)

`ab-testing`, `ad-creative`, `ads`, `aso`, `churn-prevention`, `co-marketing`,
`cold-email`, `directory-submissions`, `free-tools`, `image`, `influencer-marketing`,
`launch`, `lead-magnets`, `marketing-council`, `marketing-ideas`, `marketing-loops`,
`onboarding`, `paywalls`, `popups`, `pricing`, `prospecting`, `referrals`,
`revops`, `sales-enablement`, `signup`, `sms`, `video`

These can still consume Profound **outputs** (e.g. ad copy from sentiment themes)
but do not pull Profound data themselves.
