# Pokémon Card PreGrader

An AI-assisted prototype concept for identifying possible visible defects in Pokémon cards and helping collectors and resellers decide whether professional grading may be worthwhile.

## Problem

Assessing card condition takes time, and professional grading costs money. This project explores whether vision AI can provide useful preliminary observations about centering, corner wear, edge wear, and surface scratches.

## Project status

This is an early-stage experiment, not a production application. The initial pilot covers one card and two manually recorded reference defect labels. Both were detected, giving a preliminary recall of 100% on this single-card sample. This result is too limited to establish general accuracy.

## Repository structure

- [`docs/`](docs/README.md) — approach comparison, architecture, cost estimate, MVP plan, and submission summary.
- [`experiment/`](experiment/README.md) — experiment notebook, reference labels, recorded predictions, and report.

## Main documents

- [Submission summary](docs/submission-summary.md)
- [Approach comparison](docs/approach-comparison.md)
- [Architecture sketch](docs/architecture.md)
- [Cost estimate](docs/cost-estimate.md)
- [Decision and MVP plan](docs/decision-and-mvp-plan.md)

## Experiment

Start with the [experiment README](experiment/README.md). The notebook was developed in Google Colab. The experiment used ChatGPT's vision interface manually; it did not call a model API directly.

## Limitations

The pilot uses one card and one person's reference labels. Photo quality, glare, and viewing angle can affect observations. The app cannot guarantee a professional grade or resale
