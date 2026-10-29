# Approach Decision and MVP Plan

## Chosen approach

Use Gemini 3.8 Flash through a hosted API for qualitative corner wear, edge wear, and surface-scratch observations. Measure centering with image geometry in code. Keep the provider behind an adapter so another API or a custom model can replace it.

This is a provisional implementation choice because it avoids training a custom model before a suitable labeled dataset exists. It is not a claim that Gemini is accurate enough: the existing one-card manual pilot matched two reference labels and also reported two additional labels.

## Three limitations

1. **Photo and visibility limits:** Blur, glare, cropping, lighting, and viewing angle can hide wear or make reflections look like scratches. Unusable photos must be rejected with clear retake instructions.
2. **Weak validation and uncertainty:** The existing reference labels were made by one person on one card. The pilot cannot establish reliability, and model-reported confidence is not a calibrated probability.
3. **No official grade or guaranteed profit:** A photo-based grade range cannot reproduce all professional grading checks. Prices and grading outcomes are uncertain; show assumptions and never imply an official grade or financial guarantee.

## What would make us switch

Reconsider the hosted approach if:

- The 10–20-photo pilot and a larger, independently labeled follow-up show unacceptable false positives or missed defects for reseller decisions.
- Measured per-analysis cost or latency exceeds a budget agreed with interviewed resellers.
- Provider terms, privacy, outages, or rate limits make the service unsuitable.
- A custom model performs better on the same held-out images and can be trained, deployed, and maintained at an acceptable total cost.

Compare candidate approaches on the same images and labels. Keep the integration modular to reduce provider lock-in.

## Proposed MVP plan

Assignments are proposed based on repository contributors and need confirmation by the team. Dates are target dates after 29 October 2026, not completed work.

| Task | Owner | Target date |
|---|---|---|
| Collect permissioned photos of 10–20 cards and prepare reference defect labels; Thomas Schneider reviews disagreements | Mauro Pires | 3 November 2026 |
| Interview three Pokémon card resellers and record their decision thresholds | Thomas Schneider | 6 November 2026 |
| Run the API experiment and report per-defect TP/FP/FN, latency, and token usage | Thomas Schneider | 7 November 2026 |
| Add a photo-quality gate with clear blur, glare, and crop retake messages | Mauro Pires | 12 November 2026 |
| Measure centering from card/border geometry and report measurement uncertainty | Mauro Pires | 16 November 2026 |
| Build a result screen with marked defects, evidence, confidence, grade range, and disclaimer | Thomas Schneider | 19 November 2026 |
| Add the raw-versus-grading profit calculation and explicit send/sell recommendation | Thomas Schneider | 23 November 2026 |
| Test the complete flow with resellers and review the continue/switch criteria | Mauro Pires | 27 November 2026 |

## MVP acceptance checks

- A controlled, repeatable experiment has at least 10 labeled cases and reports false positives and missed defects by category.
- Poor photos are refused with a specific, actionable message rather than an analysis result.
- Centering is measured from image geometry, not delegated to the vision model.
- The result shows a marked-up image, possible defects with uncertainty/confidence, and a conservative grade range; it clearly says the estimate is not official.
- The profit comparison includes the raw-sale path, each grade in the estimated range, grading and shipping costs, sale values, and the final "send for grading" or "sell raw" recommendation.
- Interview evidence and the next approach decision are documented. Do not claim customer validation until interviews happen.
