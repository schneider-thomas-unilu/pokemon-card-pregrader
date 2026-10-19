# Pokémon Card PreGrader — Experiment

## Objective
Evaluate whether a vision AI model can identify visible Pokémon card defects from photographs.

## Research question
Can a vision AI model consistently identify visible centering issues, corner wear, edge wear, and surface damage in Pokémon card images?

## Dataset
We plan to use 10 or more Pokémon card photographs representing different card conditions and image qualities.

No experiment results are claimed until the model has been run on the images.

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
Preparation in progress. Images, model outputs, and measured results still need to be recorded.

## Limitations
- Photographs may hide defects because of glare, lighting, or camera angles.
- Manual reference labels may be imperfect.
- Visible defect detection does not establish an official professional grade.
