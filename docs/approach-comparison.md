# Candidate Approaches — Pokémon Card PreGrader

The comparison below contrasts two ways to build the defect-analysis component. Statements about model quality and speed are hypotheses until measured on the same labeled photos.

| Criterion | Hosted vision API (Gemini 3.8 Flash) | Custom computer-vision model |
|---|---|---|
| Output quality | Can describe visible wear without task-specific training. The one-card manual pilot matched 2 reference labels but also reported 2 extra labels; that is not enough evidence to trust it. | Could be tuned to the chosen defect categories and evaluated consistently, but quality depends on the dataset, labels, model, and training procedure. No evidence yet that it would outperform the API. |
| Cost per unit of work | Low marginal cost at current published rates: with the planning assumption of 2,000 input and 500 output tokens, about $0.003375 per analysis on the paid standard tier. The free tier is listed as free of charge, subject to its limits and data terms. | No per-token fee, but data labeling, training, deployment, monitoring, and hardware have upfront and ongoing costs. Cost per card is unknown until those are measured. |
| Latency | One network request; measure end-to-end response time in the experiment. Network and service load can vary. | Potentially low and predictable on suitable hardware, but preprocessing and hosting add work. Measure on the target device. |
| Data needed | Card photo for each request; no custom training set needed to start. Evaluation still needs 10–20 independently labeled photos for this pilot. | A substantially larger, representative labeled dataset for training, validation, and testing, including different defects, cards, and photo conditions. |
| Failure modes | Missed subtle wear, hallucinated defects, reflections mistaken for scratches, variable confidence, API errors, rate limits, and provider changes. Centering is deliberately measured from image geometry instead of delegated to the model. | Overfitting, label noise, class imbalance, missed unfamiliar cases, image-quality sensitivity, and model or hardware deployment failures. |
| Vendor lock-in / switching | Moderate: the provider API and response format are proprietary, but a small provider adapter and provider-neutral output schema should make changing APIs feasible. | Low to moderate if model weights, training code, and data stay portable; higher if deployment relies on provider-specific hardware or managed services. |

## Chosen approach for the MVP

Use Gemini 3.8 Flash through its hosted API for qualitative corner wear, edge wear, surface scratches, visible bends or creases, and other visible issues such as stains, dents, discoloration, or print defects. Measure centering separately with code. “Other visible issue” excludes ordinary card design and the four named defect types. A single front photo cannot rule out a bend that is not visible. Keep the provider behind an adapter and return a provider-neutral defect schema. This is a practical prototype choice, not a validated accuracy decision.

## Evidence and switching decision

The existing ChatGPT-interface pilot is not a Gemini API test. It recorded four observations against two reference defects: two matched, while centering and edge wear were not in the reference. If unlisted labels are treated as negatives, that is 2 true positives and 2 false positives (50% precision, 100% recall) on one card. The reference itself was created by one person, so those extra detections need independent adjudication.

Run the reproducible API experiment on 10–20 labeled photos and record per-defect true positives, false positives, false negatives, latency, and token usage. Reconsider the approach if false detections remain too frequent for reseller decisions, costs or latency exceed the team’s budget, privacy/availability terms become unsuitable, or a portable custom model demonstrates better performance on an independently labeled holdout set at an acceptable total cost.

## Sources

- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) and [Gemini 3.8 Flash model information](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash), checked 29 October 2026. See the [cost estimate](cost-estimate.md) for the dated arithmetic and free-tier caveat.
- The custom-model comparison is a project hypothesis, not a vendor quote or benchmark.
