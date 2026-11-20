"""Shared validation functions for questionnaire inputs."""
def require_non_negative(**values):
    invalid = [name for name, value in values.items() if value < 0]
    if invalid:
        raise ValueError("Values must be non-negative: " + ", ".join(invalid))
