class ConfigLoadError(Exception):
    """Raised when the input JSON/YAML config cannot be parsed or is missing required fields."""
    pass


class ValidationError(Exception):
    """Raised when static validation (overlap/boundary/duplicate checks) fails."""
    pass


class CodeGenError(Exception):
    """Raised when header file generation fails (e.g., bad output path, unsupported width)."""
    pass