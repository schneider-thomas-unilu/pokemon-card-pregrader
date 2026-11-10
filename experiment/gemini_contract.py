"""Shared Gemini prompt and structured response schema for the experiment and API."""

DEFECT_TYPES = (
    "corner_wear",
    "edge_wear",
    "surface_scratch",
    "card_bending",
    "other_visible_issue",
)

GEMINI_PROMPT = (
    "Inspect this Pokémon card photo for visible corner wear, "
    "edge wear, surface scratches, and card bending. For card_bending, "
    "report only visible creases, folds, or warping; do not infer a "
    "bend from perspective, a hand holding the card, or reflections. "
    "A single front photo cannot rule out hidden bends, so state that "
    "limitation in the evidence when relevant. Also report "
    "other_visible_issue only for visible discoloration, stains, dents, "
    "print defects, or similar issues not covered by the four named "
    "categories. Do not count ordinary card design or holographic "
    "patterns as defects. Do not assess centering; "
    "it will be measured separately with image geometry. Mark a defect "
    "present only when visible evidence supports it. Reflections alone "
    "are not proof of scratches. Return a short evidence note and a "
    "self-assessed confidence from 0 to 1 for each category. This is "
    "not an official grade."
)


def gemini_response_schema() -> dict:
    """Return the experiment's JSON schema for structured Gemini output."""
    properties = {
        defect: {
            "type": "OBJECT",
            "properties": {
                "present": {"type": "BOOLEAN"},
                "confidence": {"type": "NUMBER"},
                "evidence": {"type": "STRING"},
            },
            "required": ["present", "confidence", "evidence"],
        }
        for defect in DEFECT_TYPES
    }
    return {
        "type": "OBJECT",
        "properties": {
            "defects": {
                "type": "OBJECT",
                "properties": properties,
                "required": list(DEFECT_TYPES),
            }
        },
        "required": ["defects"],
    }
