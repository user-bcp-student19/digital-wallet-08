def feature_brief(feature: dict) -> str:
    criteria = "\n".join(f"- {item}" for item in feature.get("acceptance_criteria", []))
    return (
        f"\nFeature: {feature.get('title', '')}\n"
        f"Descripción: {feature.get('description', '')}\n"
        f"Criterios de aceptación:\n{criteria}"
    )
