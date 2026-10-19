# Pokémon Card PreGrader — Digital Transformation Project

## Problem and target users

Pokémon card resellers need to decide whether a card is worth submitting for professional grading. Evaluating visible defects takes time, and grading fees can make a submission unprofitable. The proposed app helps resellers and collectors inspect card photos and make a more informed preliminary decision.

## Proposed solution and value proposition

The user uploads a card photo. A vision AI model identifies possible centering issues, corner wear, edge wear, and surface scratches, then provides observations, confidence, and image-quality warnings. An optional calculator compares estimated resale value with grading and other costs. The app provides preliminary guidance, not an official grade or a guarantee of value.

## Approaches considered

**Hosted vision AI API:** Faster to prototype and does not require a custom labeled training dataset, but may have recurring usage costs and inconsistent results.

**Custom computer-vision model:** Offers more control over training and evaluation, but requires a larger labeled dataset and additional development work.

The initial preference is a hosted model for the MVP. The experiment so far is only a one-card pilot using ChatGPT's vision interface, so it does not establish which approach performs best.

## Experiment and evidence

The initial pilot used one Pokémon card photo. Two defects were manually recorded as reference labels, and the vision response identified both, giving a preliminary defect recall of 2/2 (100%). This result is highly limited: the reference labels were created by one person, the sample contains only one card, and the experiment did not test a direct model API. It is not evidence of general accuracy or official-grade prediction.

## Initial architecture

Photo upload → image-quality checks → backend → hosted vision model adapter → structured defect report → optional grading-value calculator. The adapter keeps the model provider replaceable.

## Cost and next steps

The initial cost estimate uses assumed input/output token counts and must be checked against current provider pricing. Next steps are to test more varied card photos, improve independently reviewed reference labels, measure actual API cost and latency, and build a minimal upload-and-results prototype.

## Key limitations

Glare and blur can hide defects; model results may be inconsistent; and image-based estimates cannot guarantee a professional grade or resale value. Reconsider the approach if evaluation on at least 30 varied cards shows inadequate reliability, cost or latency exceeds the target budget, or an alternative performs better under a controlled comparison.
