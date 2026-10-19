# Approach Decision and MVP Plan

## Chosen approach

For the first MVP, use a hosted vision AI model through a provider API. This avoids the initial cost and complexity of training a custom computer-vision model. Keep the model provider behind a separate adapter so it can be replaced later.

The experiment so far is only a one-card pilot using ChatGPT's vision interface, not a controlled comparison of model providers or a direct API test. The choice is therefore provisional.

## Three key limitations

1. **Visual uncertainty:** Glare, blur, lighting, and camera angle may hide defects or make reflections look like scratches.
2. **Limited validation:** The initial pilot covers one card and uses one person's visual judgments as reference labels. The result cannot establish general accuracy.
3. **No official grade prediction:** Visible-image analysis cannot reliably assess every factor used by professional graders. Results must be presented as preliminary observations, not a guaranteed grade or resale value.

## Criteria for reconsidering the approach

Re-evaluate the hosted-model choice if:
- A test set of at least 30 varied cards shows that defect detection is not reliable enough for the intended use.
- Measured API cost or response time exceeds the product's agreed budget.
- A custom model can demonstrate better performance on independently labeled cards at an acceptable development and operating cost.
- Privacy, provider availability, or provider terms make the hosted approach unsuitable.

Compare alternatives using the same images, reference labels, prompts where applicable, and evaluation metrics.

## MVP task plan

Dates below are proposed planning targets, not completed work.

| Task | Owner | Target date |
|---|---|---|
| Review and improve the initial experiment labels | Project owner | 21 Oct 2026 |
| Test at least 10 varied card photos and record results | Project owner | 24 Oct 2026 |
| Compare hosted-model options and verify API pricing | Project owner | 27 Oct 2026 |
| Build a minimal photo-upload and results prototype | Project owner | 3 Nov 2026 |
| Test image-quality warnings and document limitations | Project owner | 7 Nov 2026 |
| Review results and decide whether to continue or switch approach | Project owner | 10 Nov 2026 |

## MVP success criteria

The prototype should accept a card photo, return a structured list of possible visible defects with evidence and uncertainty, and explain the limitations. Before claiming reliable performance, evaluate it against independently reviewed reference labels from multiple cards.
