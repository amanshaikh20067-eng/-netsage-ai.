from typing import List, Dict, Any

class InputValidator:
    """Validates user input fields before processing."""

    @staticmethod
    def validate(symptom: str, topology_notes: str, show_output: str) -> Dict[str, Any]:
        errors: List[str] = []
        if not symptom or not symptom.strip():
            errors.append("Symptom is required.")
        if not topology_notes or not topology_notes.strip():
            errors.append("Topology notes are required.")
        if not show_output or not show_output.strip():
            errors.append("Show-command output is required.")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }