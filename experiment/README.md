# Pokémon Card PreGrader — Reproducible Experiment

## Question and protocol

Can Gemini 3.8 Flash identify visible corner wear, edge wear, surface scratches, card bending, and other visible issues in card photos? The script sends one image per API request and records the model response, latency, and token usage. For bending, it assesses only visible creases, folds, or warping; a straight-on front photo cannot rule out a hidden bend. “Other visible issue” is for stains, dents, discoloration, print defects, or similar issues not covered by the named defect categories; ordinary card artwork and holographic patterns are not defects. Centering is excluded from model labels and is intended to be measured with image geometry in the application.

Use 10–20 permissioned card photos. Two people should inspect each photo and agree on visible reference defects before running the model. The reference CSV lists positive labels; an omitted category for an image is treated as absent. Keep photos sharp, well-lit, and showing the complete card, while recording any remaining glare or angle issues in notes.

## Prepare the dataset

1. Keep card photos in a local folder, for example `experiment\images\`. Do not commit photos without permission.
2. Copy `cases_template.csv` to `cases.csv`.
3. Add 10–20 rows to `cases.csv`, matching `image_id` to an image and using paths relative to `cases.csv`, for example `images\card_01.jpg`.
4. Fill `reference_defects.csv` with all image/category pairs. The file should have columns `image_id,defect,present,notes`. Allowed categories are `corner_wear`, `edge_wear`, `surface_scratch`, `card_bending`, and `other_visible_issue`; for bending, only label visible folds, creases, or warping. For `other_visible_issue`, label only other physical/printing defects and do not duplicate a named category. `present` must be `true`, `false`, or `uncertain`. Use `uncertain` when glare, cropping, lack of angled/back-side views, or image quality prevents a fair judgment. Use image IDs exactly as listed in `cases.csv`.
5. Review the labels before running. The existing `card_01` entries are from the earlier single-person pilot and are not an independently reviewed multi-card dataset.

Required CSV columns:

```csv
image_id,image_path
card_01,images\card_01.jpg
```

Reference labels use `image_id,defect,present,notes`. Supply exactly 50 rows for ten photos (one row for each of the five categories on every photo). `uncertain` cases are excluded from that category's metrics and counted in the output.

## Run on Windows

Python 3.10 or later is required; the script uses only the standard library. The runner reads `GEMINI_API_KEY` from the process environment or from a repository-root `.env` file. It accepts both `GEMINI_API_KEY=...` and `API_KEY=...`; an environment variable takes precedence. Keep `.env` out of version control.

You can keep the key in an ignored repository-root `.env` file:

```text
API_KEY=your-key-here
```

Or set it in the current PowerShell session:

```powershell
$env:GEMINI_API_KEY = Read-Host "Gemini API key"
python experiment\run_experiment.py --manifest experiment\cases.csv --references experiment\reference_defects.csv
```

The script prints each validation step, request attempt, retry, response time, and saved image. Output is flushed as it runs, so progress appears during slow requests. It writes one row per photo to `experiment\gemini_predictions.csv` and per-defect counts to `experiment\gemini_predictions_metrics.csv`. Requests time out after 180 seconds by default; adjust with `--timeout SECONDS`. Each completed prediction is saved immediately. If the predictions file already exists, choose another `--output` or pass `--overwrite`.

Recalculate metrics without making API calls:

```powershell
python experiment\run_experiment.py --manifest experiment\cases.csv --references experiment\reference_defects.csv --output experiment\gemini_predictions.csv --evaluate-only
```

The Gemini free tier is listed as free of charge but has limits and different data-use terms from the paid tier; check the current terms before submitting photos. The script does not store the API key in its output.

## Metric

For each defect category, the script reports:

- **True positives (TP):** model said present and the reference label is present.
- **False positives (FP):** model said present but the reference label is absent.
- **False negatives (FN):** the reference label is present but the model missed it.
- **Uncertain pairs:** reference judgments marked uncertain; excluded from TP/FP/FN.
- **Precision:** TP ÷ (TP + FP); the share of model detections supported by the reference.
- **Recall:** TP ÷ (TP + FN); the share of reference defects detected.

It also reports micro-aggregated counts across the five defect types. If a category has no reference positives or no model detections, the corresponding rate is shown as N/A rather than zero. Self-reported model confidence is recorded but not treated as calibrated.

## Prototype score and recommendation

After each card prediction, the script prints a **heuristic condition score** and recommendation. It starts at 10 and subtracts a fixed penalty for each defect the model marks present:

| Detected defect     | Penalty |
| ------------------- | ------: |
| Corner wear         |     0.5 |
| Edge wear           |    0.75 |
| Surface scratch     |     1.5 |
| Card bending        |     3.5 |
| Other visible issue |     2.5 |

The score is clamped to 1–10 and shown to one decimal place. A score **below 6.0** gives **DO NOT BUY**; a score from **6.0 to below 9.0** gives **SELL RAW**; a score of **9.0 or above** gives **SUBMIT FOR GRADING**. Penalties stack when multiple defect types are detected. The score uses the model's present/absent flags, not its confidence, because that confidence has not been calibrated.

These are transparent starting weights for a prototype, not coefficients learned from professional grade outcomes or official grading deductions. The result is not an official grade and is not a profit calculation: it does not account for card-specific raw/graded sale prices, grading fees, shipping, marketplace fees, or risk. Calibrate or replace the rule using independently graded cards and reseller feedback before relying on it for real purchase decisions.

Run the offline metric and response parsing tests with:

```powershell
python -m unittest experiment.test_run_experiment
```

## Evidence so far

The previous manual ChatGPT-interface pilot covered one card with two recorded reference defects. Its response listed all four categories: corner wear, surface scratches, centering, and edge wear. Under the pilot convention that unlisted defects are absent:

| Category        | Reference present | Pilot response present |  TP |  FP |  FN |
| --------------- | ----------------: | ---------------------: | --: | --: | --: |
| Corner wear     |                 1 |                      1 |   1 |   0 |   0 |
| Surface scratch |                 1 |                      1 |   1 |   0 |   0 |
| Edge wear       |                 0 |                      1 |   0 |   1 |   0 |
| Centering       |                 0 |                      1 |   0 |   1 |   0 |

That is 2 TP and 2 FP among 4 reported observations (50% precision), with 2/2 reference defects found (100% recall) on **one card only**. The manual labels came from one person; the two extra categories are unverified and the result is not general accuracy evidence. Centering is not included in the new Gemini experiment because it should be measured from geometry.

Ten card photos are listed in `cases.csv`, and their five-category reference labels are in `reference_defects.csv`. The API experiment has not completed yet; follow the run instructions above to generate predictions and metrics.
