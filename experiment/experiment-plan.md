# Pokémon Card PreGrader — Experiment Plan

## Research question

On 10–20 permissioned card photographs, how often does Gemini 3.8 Flash correctly identify visible corner wear, edge wear, surface scratches, bending/creases, and other visible issues such as stains or print defects, and how often does it invent a defect?

## Cases and labels

- One case is one card photo with a unique `image_id`.
- The planned dataset is 10–20 different cards, with varied but usable lighting and condition.
- Two reviewers should label visible reference defects before seeing model output; resolve disagreements and keep notes.
- `reference_defects.csv` must explicitly label all five categories on every image as `true`, `false`, or `uncertain`; uncertain pairs are omitted from metric denominators.
- For `card_bending`, label visible creases, folds, or warping only. Request angled and reverse-side views where possible; a straight-on front image cannot establish that a card is flat.
- For `other_visible_issue`, label only physical or print issues not already covered by the named categories; ordinary card design is not a defect.
- Centering is excluded from model assessment and reserved for code-based geometric measurement.

## Procedure

1. Create a 10–20-row `cases.csv` manifest and check that all photos show the whole card.
2. Agree and record reference labels before sending images to the API.
3. Run `run_experiment.py` with the Gemini API key supplied through the environment.
4. Save the raw category decisions, evidence, confidence, token counts, and latency in the generated predictions CSV.
5. Review errors and report TP, FP, FN, precision, and recall for every defect category.
6. Preserve the dataset version, prompt, model ID, date, and pricing assumptions with the result.

## Current status

The evaluator and offline tests are implemented, and ten photos plus five-category labels are present. The API experiment has not completed; the one-card ChatGPT pilot is separate and is described in the [experiment report](experiment_report.md).

## Limitations

Manual defect labels may still be subjective. A small convenience sample does not establish performance across all card types, conditions, or photo quality. Model confidence is self-reported and not calibrated. No vision output is an official grade.
