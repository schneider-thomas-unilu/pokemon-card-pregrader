# Candidate AI Approaches

## Approach A: Hosted Vision AI API

A pretrained multimodal AI model receives a card image and a structured prompt asking it to identify visible defects and provide a preliminary condition estimate. This approach requires little initial model development.

## Approach B: Custom Computer-Vision Model

A specialized image model is trained or fine-tuned to detect specific defects, such as damaged corners, edge wear, surface scratches, and centering issues. This approach requires a suitable labeled dataset and additional development.

## Comparison

| Criterion | A: Hosted Vision AI API | B: Custom Computer-Vision Model |
|---|---|---|
| Output quality | Can describe several defect types without task-specific training; consistency and accuracy must be tested. | Can detect targeted defects reliably if trained on representative, well-labeled images. |
| Cost per unit of work | Per-request image and token charges; little initial infrastructure required. | Training, data preparation, and hosting can be expensive initially; inference can be inexpensive at scale. |
| Latency | Network and model processing usually take seconds; measure actual latency. | Can be fast after deployment; depends on hardware and model size. |
| Data needed | Card images and a carefully designed prompt; no custom training set required to start. | Many labeled card images covering different defects, card conditions, lighting, and angles. |
| Failure modes | Missed subtle defects, inconsistent assessments, glare, and false confidence. | Overfitting, incorrect labels, missed defects, and poor performance on unfamiliar cards. |
| Vendor lock-in | Moderate to high if the implementation relies on provider-specific features. | Potentially lower if model weights and code are portable; cloud infrastructure may still create lock-in. |

## Preliminary Decision

The provisional choice for the MVP is a hosted vision AI API because it allows us to prototype the application without first building a large labeled training dataset.

The completed one-card pilot used ChatGPT's vision interface manually; it did not test a hosted model API programmatically. Therefore, the pilot does not establish that the API approach is more accurate or cost-effective than a custom computer-vision model.

The decision will be reviewed after testing more cards and evaluating output quality, measured latency, estimated operating costs, and implementation feasibility.

## Switching Criteria

We will reconsider the hosted API if it repeatedly misses visible defects, exceeds our cost or latency limits, or performs worse than a feasible custom model. We will keep the model integration modular to make switching providers or approaches easier.

## Evidence Status

This comparison contains initial technical expectations, not measured experimental results. Performance claims must be validated through testing before a final approach is selected.
