# First Cost Estimate — Pokémon Card PreGrader

**Price checked:** 29 October 2026
**Chosen service:** Gemini 3.8 Flash API, standard paid tier
**Official sources:** [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) and [Gemini 3.8 Flash model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash)

The official pricing page lists Gemini 3.8 Flash standard paid rates through 31 December 2026 of **$0.75 per 1 million input tokens** and **$3.75 per 1 million output tokens**. It lists free-of-charge input/output on the free tier, subject to model availability and usage limits; the free-tier terms state that submitted content may be used to improve Google's products. Confirm terms and rates before using real customer photos or launching.

## Estimated cost for one user action

One action is one photo analysis. For a planning estimate, assume 2,000 total input tokens (image plus instructions) and 500 output tokens (structured findings). These are assumptions, not measured usage.

| Item | Arithmetic | Estimated cost |
|---|---:|---:|
| Input | 2,000 ÷ 1,000,000 × $0.75 | $0.001500 |
| Output | 500 ÷ 1,000,000 × $3.75 | $0.001875 |
| **Total per analysis** | $0.001500 + $0.001875 | **$0.003375** |

That is about **0.34 US cents per analysis**. The same token assumptions at the published rates starting 1 January 2027 ($1.50 input and $7.50 output per million tokens) give **$0.00675** per analysis.

| Analyses | Current-rate estimate |
|---:|---:|
| 100 | $0.34 |
| 1,000 | $3.38 |
| 10,000 | $33.75 |

The experiment script records token usage returned by the API and request latency for each photo. Replace the assumed token counts with actual API usage before using this estimate for a business decision.

## Exclusions

This estimate excludes hosting, image storage, development, human review, taxes, and market-data fees. It also excludes any costs arising from retries. The model’s tokenization of an image depends on the image and API processing, so 2,000 input tokens is not a guarantee or limit.
