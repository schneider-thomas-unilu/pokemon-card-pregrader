# Pokémon Card PreGrader — Experiment Instructions

## Purpose

This experiment explores whether a vision-capable AI can identify visible defects in Pokémon card photographs.

## Files

- `pokemon_card_pregrader_experiment.ipynb` — Google Colab notebook containing the experiment code.
- `experiment-plan.md` — plan for the experiment and its evaluation.
- `reference_defects.csv` — manually recorded reference defects.
- `predictions.csv` — defects reported by the AI assessment.
- `experiment_report.md` — experiment method, result, and limitations.
- `EXPERIMENT_README.md` — additional experiment setup and reproduction notes.

## How to reproduce the pilot

1. Open `pokemon_card_pregrader_experiment.ipynb` in Google Colab.
2. Run the notebook cells in order.
3. Upload a suitable card photograph when prompted.
4. Review the manually recorded reference labels and the recorded AI assessment.
5. Run the comparison cell to calculate preliminary defect recall.

The notebook uses Python and pandas for dataset handling. The original AI assessment was performed manually through ChatGPT's vision interface; the notebook does not call a model API to generate predictions automatically.

## Initial result

The pilot used one Pokémon card photograph and two reference defect labels. The AI assessment reported both reference defects, giving a preliminary recall of 100% (2/2).

This result is based on a single card and is not evidence of general model accuracy.

## Limitations

- Only one card was tested.
- Reference labels were based on one person's visual inspection.
- The AI assessment came from a chat interface rather than a controlled API benchmark.
- Image angle, lighting, and reflections may affect defect detection.
- No official professional grade was established.

## Next steps

Test additional cards, independently verify reference labels, and compare approaches using the same images and evaluation criteria.
