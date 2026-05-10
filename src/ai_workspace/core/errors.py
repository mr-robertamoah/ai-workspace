"""Custom error hierarchy for ai-workspace."""


class WorkspaceError(Exception):
    """Base for all workspace errors."""


class WorkspaceNotFoundError(WorkspaceError):
    """No .ai/ or workspace.yaml in current directory."""


class WorkspaceValidationError(WorkspaceError):
    """YAML schema validation failed."""


class SecurityError(WorkspaceError):
    """Security check failed."""


class SkillError(WorkspaceError):
    """Skill operation failed."""


class IndexError(WorkspaceError):
    """Index read or write failed."""
