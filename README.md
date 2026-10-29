# Pokémon Card PreGrader

An AI-assisted prototype concept for identifying possible visible defects in Pokémon cards and helping collectors and resellers decide whether professional grading may be worthwhile.

## Problem

Assessing card condition takes time, and professional grading costs money. This project explores whether vision AI can provide useful preliminary observations about centering, corner wear, edge wear, surface scratches, visible card bending or creases, and other visible condition issues such as stains or print defects.

## Project status

This is an early-stage experiment, not a production application. The manual one-card pilot matched two reference labels but also reported two extra categories, giving 50% precision and 100% recall under the pilot's one-person labels. This is not evidence of general accuracy. A reproducible Gemini API experiment is implemented with ten card photos and five reference categories. The API run has not completed yet after transient service timeouts.

## Repository structure

- [Approach comparison](docs/approach-comparison.md) — architecture, cost estimate, MVP plan, and submission summary.
- [`experiment/`](experiment/README.md) — experiment notebook, reference labels, recorded predictions, and report.

## Main documents

- [Submission summary](docs/submission-summary.md)
- [Approach comparison](docs/approach-comparison.md)
- [Architecture sketch](docs/architecture.md)
- [Cost estimate](docs/cost-estimate.md)
- [Decision and MVP plan](docs/decision-and-mvp-plan.md)

## Experiment

### Start the experiment (Windows / PowerShell)

From the repository root, install the image-display dependency:

```powershell
python -m pip install -r requirements.txt
```

Confirm `experiment\cases.csv` lists 10–20 photos and `experiment\reference_defects.csv` has reviewed labels for each photo. Put your Gemini key in the ignored root `.env` file:

```text
API_KEY=your-gemini-api-key
```

Then run:

```powershell
python experiment\measure_centering.py --manifest experiment\cases.csv
python experiment\run_experiment.py --manifest experiment\cases.csv --references experiment\reference_defects.csv --centering-measurements experiment\centering_measurements.csv --overwrite
```

The centering tool asks you to mark the four card corners and four visible inner-border corners. It rectifies perspective and calculates left:right and top:bottom border ratios without using AI. Cards without a clearly measurable inner border can be skipped. The measurements are saved to `experiment\centering_measurements.csv` and attached to each prediction. The API runner prints each request/retry and saves progress after every card to `experiment\gemini_predictions.csv`; per-category metrics go to `experiment\gemini_predictions_metrics.csv`. For each prediction it also prints a prototype condition score and recommends "DO NOT BUY" below 6, "SELL RAW" from 6 to below 9, or "SUBMIT FOR GRADING" at 9 or above. This is a fixed-weight heuristic, not an official grade or profit calculation. Do not commit or share the `.env` file. For key setup, reruns, troubleshooting, and metric definitions, see the [detailed experiment instructions](experiment/README.md).

The notebook was developed in Google Colab; its earlier manual ChatGPT-interface result was not an API experiment.

## Limitations

The pilot uses one card and reference labels created by one person. Photo quality, glare, and viewing angle can affect observations. The app cannot guarantee a professional grade, card authenticity, or resale value.

## Next steps

- Interview resellers and record their decision thresholds.
- Gather permissioned card photos and independently agree reference labels.
- Run the API experiment and record defect counts, latency, and token usage.
- Extend the manual centering prototype into automatic boundary detection, then build the photo-quality gate, marked-up result, grade range, and profit recommendation.
- See the [named-owner MVP plan](docs/decision-and-mvp-plan.md) for target dates.

## Disclaimer

This project provides preliminary educational experimentation only. It does not provide official grading, authentication, or financial guarantees.
