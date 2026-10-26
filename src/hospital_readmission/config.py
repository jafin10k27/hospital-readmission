"""Configuration loading and validation."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def find_project_root() -> Path:
    """Detects project root directory by searching upward for pyproject.toml."""
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists() or (parent / "config" / "settings.yaml").exists():
            return parent
    return Path.cwd()


@dataclass
class AppConfig:
    """Application configuration container."""

    raw_data_path: Path
    ids_mapping_path: Path
    processed_data_path: Path
    database_path: Path
    reports_dir: Path
    logs_dir: Path
    random_seed: int = 42
    settings: dict[str, Any] = field(default_factory=dict)
    schema: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(
        cls,
        settings_path: str | Path | None = None,
        schema_path: str | Path | None = None,
    ) -> "AppConfig":
        """Loads configuration from YAML files and environment variables.

        Args:
            settings_path: Custom path to settings.yaml.
            schema_path: Custom path to schema.yaml.

        Returns:
            Populated AppConfig instance.
        """
        root = find_project_root()

        if settings_path is None:
            settings_path = root / "config" / "settings.yaml"
        else:
            settings_path = Path(settings_path)

        if schema_path is None:
            schema_path = root / "config" / "schema.yaml"
        else:
            schema_path = Path(schema_path)

        settings: dict[str, Any] = {}
        if settings_path.exists():
            with open(settings_path, encoding="utf-8") as f:
                settings = yaml.safe_load(f) or {}

        schema: dict[str, Any] = {}
        if schema_path.exists():
            with open(schema_path, encoding="utf-8") as f:
                schema = yaml.safe_load(f) or {}

        # Resolve paths relative to root or environment variables
        paths = settings.get("paths", {})
        raw_default = os.getenv("RAW_DATA_PATH", paths.get("raw_data_default", "data/raw/diabetic_data.csv"))
        ids_default = os.getenv("IDS_MAPPING_PATH", paths.get("ids_mapping_default", "data/raw/IDS_mapping.csv"))
        proc_default = os.getenv("PROCESSED_DATA_PATH", paths.get("processed_data", "data/processed/cleaned_encounters.csv"))
        db_default = os.getenv("DATABASE_PATH", paths.get("database", "data/processed/hospital_readmission.db"))
        rep_default = os.getenv("REPORTS_DIR", paths.get("reports_dir", "reports/generated"))
        log_default = os.getenv("LOGS_DIR", paths.get("logs_dir", "logs"))

        def resolve(p: str) -> Path:
            path_obj = Path(p)
            return path_obj if path_obj.is_absolute() else (root / path_obj)

        seed = int(os.getenv("RANDOM_SEED", settings.get("app", {}).get("random_seed", 42)))

        return cls(
            raw_data_path=resolve(raw_default),
            ids_mapping_path=resolve(ids_default),
            processed_data_path=resolve(proc_default),
            database_path=resolve(db_default),
            reports_dir=resolve(rep_default),
            logs_dir=resolve(log_default),
            random_seed=seed,
            settings=settings,
            schema=schema,
        )

    def get_cleaning_config(self) -> dict[str, Any]:
        """Returns data cleaning configuration."""
        return self.settings.get("cleaning", {})

    def get_outcome_config(self) -> dict[str, Any]:
        """Returns outcome mapping configuration."""
        return self.settings.get("outcome", {})

    def get_database_config(self) -> dict[str, Any]:
        """Returns database configuration."""
        return self.settings.get("database", {})

    def get_schema(self, dataset_name: str | None = None) -> dict[str, Any]:
        """Returns schema for a specific dataset or the default dataset."""
        if dataset_name is None:
            dataset_name = self.schema.get("default_dataset", "uci_diabetes")
        return self.schema.get("schemas", {}).get(dataset_name, {})
