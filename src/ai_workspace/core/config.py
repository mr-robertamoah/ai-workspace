"""Workspace YAML schema and loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from ai_workspace.core.errors import WorkspaceValidationError

yaml = YAML(typ="safe")
yaml_writer = YAML()
yaml_writer.default_flow_style = False

WorkspaceType = Literal["monorepo", "single", "multi"]
PrimaryLanguage = Literal["python", "go", "typescript", "rust", "java", "other"]
ArchitectureStyle = Literal[
    "modular-monolith", "microservices", "monolith", "serverless", "library", "other"
]
AgentName = Literal["claude", "codex", "kiro"]
DocumentationStructure = Literal["standard", "minimal", "full"]
TestingStandard = Literal["pytest", "jest", "go-test", "rspec", "other"]
FormattingStandard = Literal["black", "prettier", "gofmt", "other"]
LintingStandard = Literal["ruff", "eslint", "golangci-lint", "other"]


class StrictModel(BaseModel):
    """Base model that rejects undeclared fields."""

    model_config = ConfigDict(extra="forbid")


class WorkspaceMetadata(StrictModel):
    """Workspace identity information."""

    name: str = Field(pattern=r"^[a-z0-9-]+$", max_length=64)
    type: WorkspaceType


class RepositoryConfig(StrictModel):
    """A repository entry for monorepo or multi-repo workspaces."""

    name: str = Field(pattern=r"^[a-z0-9-]+$")
    path: str

    @field_validator("path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        path = Path(value)
        if path.is_absolute():
            raise ValueError("Repository paths must be relative to the project root.")
        return str(path)


class LanguageConfig(StrictModel):
    """Programming language choices for the workspace."""

    primary: PrimaryLanguage
    secondary: list[PrimaryLanguage] = Field(default_factory=list)


class ArchitectureConfig(StrictModel):
    """High-level architecture style."""

    style: ArchitectureStyle


class AIConfig(StrictModel):
    """AI-related workspace features."""

    enabled: bool = True
    adr: bool = True
    handoffs: bool = True
    tasks: bool = True
    agents: list[AgentName] = Field(default_factory=list)


class DocumentationConfig(StrictModel):
    """Documentation generation settings."""

    enabled: bool = True
    structure: DocumentationStructure = "standard"


class SecurityConfig(StrictModel):
    """Security automation settings."""

    enabled: bool = True
    dependency_scanning: bool = True
    bandit: bool = True


class StandardsConfig(StrictModel):
    """Tooling standards for the workspace."""

    testing: TestingStandard = "pytest"
    formatting: FormattingStandard = "black"
    linting: LintingStandard = "ruff"


class WorkspaceConfig(StrictModel):
    """Top-level workspace configuration."""

    workspace: WorkspaceMetadata
    repositories: list[RepositoryConfig] = Field(default_factory=list)
    language: LanguageConfig
    architecture: ArchitectureConfig = Field(
        default_factory=lambda: ArchitectureConfig(style="modular-monolith")
    )
    ai: AIConfig = Field(default_factory=AIConfig)
    documentation: DocumentationConfig = Field(default_factory=DocumentationConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    standards: StandardsConfig = Field(default_factory=StandardsConfig)

    @field_validator("repositories")
    @classmethod
    def validate_repositories(cls, value: list[RepositoryConfig], info) -> list[RepositoryConfig]:
        workspace = info.data.get("workspace")
        if workspace and workspace.type in {"monorepo", "multi"} and not value:
            raise ValueError(
                "repositories is required when workspace.type is 'monorepo' or 'multi'."
            )
        return value


def _format_validation_error(error: ValidationError) -> str:
    parts: list[str] = []
    for issue in error.errors():
        location = ".".join(str(item) for item in issue["loc"])
        parts.append(f"{location}: {issue['msg']}")
    return "; ".join(parts)


def load_workspace_yaml(path: Path) -> WorkspaceConfig:
    """Read and validate a workspace.yaml file."""

    try:
        data = yaml.load(path.read_text(encoding="utf-8"))
        if data is None:
            data = {}
        return WorkspaceConfig.model_validate(data)
    except FileNotFoundError as exc:
        raise WorkspaceValidationError(f"Workspace file not found: {path}") from exc
    except YAMLError as exc:
        raise WorkspaceValidationError(f"Invalid YAML in {path}: {exc}") from exc
    except ValidationError as exc:
        raise WorkspaceValidationError(_format_validation_error(exc)) from exc


def workspace_config_data(config: WorkspaceConfig) -> dict[str, Any]:
    """Return a plain-Python representation ready for YAML serialization."""

    return config.model_dump(mode="python", exclude_none=False)


def write_workspace_yaml(path: Path, config: WorkspaceConfig) -> None:
    """Write a validated workspace config to disk as YAML."""

    with path.open("w", encoding="utf-8") as handle:
        yaml_writer.dump(workspace_config_data(config), handle)
