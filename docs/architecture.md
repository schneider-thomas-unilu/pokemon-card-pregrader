# First Architecture Sketch — Pokémon Card PreGrader

## User flow

1. The user uploads a photo of a Pokémon card.
2. The app checks whether the image is clear enough to analyze.
3. A backend sends the image and inspection instructions to a hosted vision AI model.
4. The model identifies possible visible defects: centering, corner wear, edge wear, and surface scratches.
5. The backend organizes the findings into a structured report, including evidence, confidence, and limitations.
6. The app shows the report and explains that it is a preliminary estimate, not an official professional grade.
7. The user can optionally enter the card's estimated resale value and professional grading costs to help decide whether grading is worthwhile.

## Main components

- **Frontend:** Photo upload and results display.
- **Image quality checks:** Warn about blur, glare, poor lighting, or incomplete views.
- **Backend:** Coordinates the analysis and validates the model response.
- **Vision AI adapter:** Sends requests to the selected model provider. Keeping this component separate makes it easier to change providers.
- **Results module:** Displays potential defects, supporting observations, confidence, and uncertainty.
- **Value calculator:** Compares estimated resale value with grading and other relevant costs.
- **Data storage:** Stores only the information needed for the service, with user consent and appropriate privacy protections.

## Initial design decision

Start with a hosted vision AI model because it avoids training a custom model before enough labeled card images are available. Test its performance on more cards before relying on it for product decisions.

## Important limitations

The system may miss subtle defects, confuse reflections with scratches, or produce inconsistent results across different photos. It must not present its output as an official grade or guarantee a card's resale value. Any confidence score returned by the AI is an estimate and may not correspond to a verified probability that a defect is present.
