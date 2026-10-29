# Pokémon Card PreGrader — Project Summary

## Problem and target user

Pokémon card resellers must decide whether an ungraded card is worth buying or submitting for professional grading. Fees, shipping, time, and uncertain condition can turn a poor decision into a loss. The proposed tool is for resellers and collectors who want a transparent preliminary inspection and a grading-versus-raw-sale calculation.

## Customer discovery and alternatives

No reseller interviews have been completed yet. Customer needs, willingness to pay, and decision thresholds remain hypotheses; three interviews are planned by 6 November 2026.

Alternatives include manual inspection, direct professional grading, and existing card-scanning tools. The proposed differentiator is a marked-up photo, explicit uncertainty, geometry-based centering, and a profit comparison ending in a practical send/sell recommendation. This differentiator still needs validation with users.

## Candidate approaches and current decision

The team compared a hosted vision API with a custom computer-vision model. For the MVP, the provisional choice is Gemini 3.8 Flash for qualitative surface/corner/edge observations, visible card bends or creases, and other visible issues such as stains or print defects, while code measures centering from image geometry. “Other visible issue” excludes ordinary card design and the named categories. A single front photo cannot rule out hidden bending. A provider adapter limits lock-in. A larger labeled set and user interviews may change this choice.

## Experiment status and evidence

The existing manual ChatGPT-interface pilot used one card and two reference defects. The recorded response identified both, but it also reported centering and edge wear absent from the reference. Counting those unlisted categories as negatives gives 2 true positives and 2 false positives: 50% precision and 100% recall on one card. Reference labels were made by one person, so this is not reliable accuracy evidence.

A separate script now calls Gemini directly, records token usage and latency, and calculates per-defect TP/FP/FN for five categories, including card bending and other visible issues. Ten photos and five-category reference labels are present. The experiment has not yet completed because Gemini returned a transient HTTP 503; retry the API run and record the results before presenting an outcome.

## First architecture

Photo upload → photo-quality gate → code-based centering measurement plus hosted qualitative defect detection → marked-up result with confidence and grade range → raw-versus-grading profit calculation → "send for grading" or "sell raw." Poor photos receive retake guidance. The grade estimate is explicitly not official.

## First cost estimate

As checked 29 October 2026, Gemini 3.8 Flash standard paid rates are $0.75 per million input tokens and $3.75 per million output tokens through 31 December 2026. Assuming 2,000 input tokens and 500 output tokens, one action is estimated at $0.003375. The experiment will record actual token use; photo tokenization and output size can differ from the planning assumptions.

## Limitations and next steps

1. Glare, blur, cropping, and viewing angle can obscure defects.
2. Current reference labels and pilot evidence are too small and subjective to establish accuracy.
3. Image analysis cannot guarantee an official grade or resale profit.

Next: interview resellers; gather 10–20 permissioned, labeled photos; run the API experiment; implement photo rejection and geometry-based centering; then test the marked-up result and profit recommendation with users. Switch approaches if measured reliability, cost, latency, privacy, or user feedback fails agreed targets.

## Proposed task ownership and dates

Assignments are proposed, not accepted or completed. See the [MVP plan](decision-and-mvp-plan.md) for named owners and target dates from 3–27 November 2026.
