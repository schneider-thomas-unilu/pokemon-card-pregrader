# Pokémon Card PreGrader — Experiment

## Objective

Evaluate whether a vision AI model can identify visible Pokémon card defects from photographs.

## Research question

Can a vision AI model consistently identify visible centering issues, corner wear, edge wear, and surface damage in Pokémon card images?

## Dataset

The initial pilot used one Pokémon card photograph and two manually recorded reference defect labels.

The planned extended evaluation will use 10 or more Pokémon card photographs representing different card conditions and image qualities.

No conclusions about general model accuracy will be drawn from the single-card pilot.

## Procedure

1. Assign each image a unique ID.
2. Inspect the image manually and record clearly visible defects.
3. Submit the same image to the selected vision model using a standardized prompt.
4. Save the model's complete output.
5. Compare the model's detected defects with the reference checklist.
6. Document the findings and limitations.

## Evaluation metric

Defect recall = correctly detected reference defects / total reference defects × 100.

A defect counts as correctly detected when the model identifies the same defect category in the same image.

If the reference checklist contains no defects, recall cannot be calculated for that image.

## Experiment status

A preliminary one-card pilot has been completed. The AI assessment identified both of the two manually recorded reference defects, giving a preliminary defect recall of 100% (2/2).

This result is based on only one image and is not evidence of general model accuracy. The extended evaluation remains to be completed.

## Limitations

- Photographs may hide defects because of glare, lighting, or camera angles.
- Manual reference labels may be imperfect.
- The initial AI assessment was performed through ChatGPT's vision interface rather than a controlled API benchmark.
- A small dataset cannot establish reliable performance across different cards and conditions.
- Visible defect detection does not establish an official professional grade.
