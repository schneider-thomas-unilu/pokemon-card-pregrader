# Pokémon Card PreGrader — Initial Experiment

## Objective

Test whether a vision-capable AI can identify visible Pokémon card defects.

## Method

- One actual Pokémon card photograph was inspected.
- A standardized prompt asked about centering, corner wear, edge wear, and surface scratches.
- Two reference defects were manually recorded: surface scratches and corner wear.
- The AI's written assessment was recorded in `predictions.csv`.
- The recorded predictions were compared with the manual reference labels.

## Result

- Cards tested: 1
- Reference defect labels: 2
- Reference defects detected by AI: 2
- Preliminary defect recall: 100% (2/2)

**Calculation:** \(2 \div 2 \times 100 = 100\%\)

## Interpretation

The AI reported both defects in the manual reference labels. This gives a preliminary defect recall of 100% for this single image.

The AI also reported centering and edge wear, which have not yet been independently verified against reference labels. Therefore, the experiment does not establish whether all its observations were correct. Recall measures detection of the recorded reference defects, not the accuracy of every prediction.

This is a one-card pilot and does not establish overall model accuracy, grading reliability, or financial usefulness.

## Limitations

1. Only one card has been tested.
2. Reference labels are based on one person's visual inspection.
3. The AI response came from a chat interface, not a controlled API benchmark.
4. Photograph angle, lighting, and reflections may affect observations.
5. No official professional grade was established.

## Next steps

Test more cards, use consistent photographs, and independently verify reference labels before drawing conclusions.
