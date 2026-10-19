# First Cost Estimate — Pokémon Card PreGrader

**Pricing checked:** 19 October 2026  
**Proposed model:** Gemini 3.8 Flash, standard paid tier  
**Source:** [Official Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)

## Estimated cost for one card analysis

For an initial planning estimate, assume one analysis uses:
- 2,000 input tokens, including the image and instructions
- 500 output tokens for the structured defect report

These token counts are assumptions, not measured usage. Actual image token usage and output length may differ.

| Item | Calculation | Estimated cost |
|---|---|---:|
| Input | 2,000 ÷ 1,000,000 × $0.75 | $0.0015 |
| Output | 500 ÷ 1,000,000 × $3.75 | $0.001875 |
| **Total per analysis** | Input + output | **$0.003375** |

This is approximately **0.34 US cents per analysis**, before any other operating costs.

From 1 January 2027, the standard paid rates are $1.50 per million input tokens and $7.50 per million output tokens. With the same assumed token usage, the estimated cost becomes $0.00675 per analysis.

## Estimated usage scenarios

| Analyses | Estimated AI cost |
|---:|---:|
| 100 | $0.34 |
| 1,000 | $3.38 |
| 10,000 | $33.75 |

Figures are rounded and assume the same token usage and prices for every analysis.

## Important exclusions and assumptions

- This estimate covers model input and output only.
- It excludes hosting, storage, development, taxes, and other services.
- The estimate assumes paid-tier pricing; free-tier eligibility and conditions may differ.
- Actual usage must be measured in a real API experiment before this estimate is used for business decisions.
- Pricing may change, so it should be checked again before launch.

The existing experiment used ChatGPT's vision interface, not the Gemini API. Therefore, it provides no measured Gemini API cost or latency.
