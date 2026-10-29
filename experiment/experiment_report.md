# Pokémon Card PreGrader — Experiment Report

## Existing manual pilot

The repository's initial pilot used one Pokémon card photo and manually recorded two reference defects: corner wear and surface scratches. The recorded ChatGPT vision response marked four categories present: corner wear, surface scratches, centering, and edge wear. Card bending was not assessed in that older pilot.

| Category | Reference | Response | TP | FP | FN |
|---|---:|---:|---:|---:|---:|
| Corner wear | 1 | 1 | 1 | 0 | 0 |
| Surface scratch | 1 | 1 | 1 | 0 | 0 |
| Centering | 0 | 1 | 0 | 1 | 0 |
| Edge wear | 0 | 1 | 0 | 1 | 0 |
| **All four categories** | **2** | **4** | **2** | **2** | **0** |

**One-card precision:** 2 ÷ (2 + 2) = **50%**.
**One-card recall:** 2 ÷ (2 + 0) = **100%**.

The calculation assumes that a category omitted from the manual reference is absent. Both extra labels are therefore counted as false positives for this pilot, but the labels were created by one person and need independent review. This is not a controlled API experiment or evidence of general accuracy. Centering should be measured with geometry, not a vision-language model.

## Reproducible API experiment

A standard-library Python script is now available at `run_experiment.py`. It calls Gemini 3.8 Flash on each image, records the model's three qualitative defect decisions, token usage, and latency, then produces per-category TP/FP/FN, precision, and recall.

Ten photos and five-category reference labels are available in `cases.csv` and `reference_defects.csv`. The Gemini API run is in progress; add measured results below after predictions and metrics have been generated. Do not report the one-card manual pilot as the multi-case API result.

## How to interpret the next result

Report the number of cases and reference positives alongside each metric. The 10–20-case evaluation is a pilot for finding obvious failure modes, not a statistically conclusive performance guarantee. Treat self-reported model confidence as uncalibrated. Report disagreements and image-quality problems rather than silently excluding difficult cases.
