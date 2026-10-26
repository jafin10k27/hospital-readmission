"""Pipeline Orchestrator Module.

Coordinates end-to-end data processing workflow:
Ingestion -> Validation -> Cleaning -> Outcome Definition -> Database Storage -> Analytics.
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from hospital_readmission.cleaning import CleaningPipeline
from hospital_readmission.config import AppConfig
from hospital_readmission.database import DatabaseManager
from hospital_readmission.ingestion import DatasetLoader, IngestionMetadata, load_id_mappings
from hospital_readmission.logging_config import setup_logger
from hospital_readmission.outcomes import OutcomeSummary, define_readmission_outcome
from hospital_readmission.quality_analysis import QualityAnalyzer, QualitySummary
from hospital_readmission.schema_validation import DataValidator, ValidationReport

logger = setup_logger(__name__)


@dataclass
class PipelineState:
    """Encapsulates the complete state of the analytics pipeline."""

    raw_df: pd.DataFrame
    cleaned_df: pd.DataFrame
    ingestion_metadata: IngestionMetadata
    validation_report: ValidationReport
    cleaning_log_df: pd.DataFrame
    outcome_summary: OutcomeSummary
    quality_summary: QualitySummary
    database_manager: DatabaseManager
    id_mappings: dict[str, dict[int, str]]
    config: AppConfig


class HealthcarePipeline:
    """Executes the hospital readmission analytics pipeline."""

    def __init__(self, config: AppConfig | None = None):
        self.config = config or AppConfig.load()
        self.loader = DatasetLoader()
        self.db = DatabaseManager(self.config.database_path)

    def run(
        self,
        file_path: str | Path | None = None,
        nrows: int | None = None,
        patient_dedup_strategy: str | None = None,
    ) -> PipelineState:
        """Executes the full pipeline from raw data to SQL and analytics."""
        target_path = Path(file_path) if file_path else self.config.raw_data_path

        logger.info("Executing HealthcarePipeline on %s (nrows=%s)...", target_path, nrows)

        # 1. Ingestion
        raw_df, ingestion_meta = self.loader.load_csv(target_path, nrows=nrows)

        # 2. Load ID Mappings
        id_mappings = load_id_mappings(self.config.ids_mapping_path)

        # 3. Schema & Quality Validation
        schema = self.config.get_schema()
        validator = DataValidator(schema=schema)
        val_report = validator.validate(raw_df)

        # 4. Cleaning
        cleaning_cfg = self.config.get_cleaning_config().copy()
        if patient_dedup_strategy:
            cleaning_cfg["patient_deduplication"] = patient_dedup_strategy

        cleaner = CleaningPipeline(
            config=cleaning_cfg,
            schema=schema,
            id_mappings=id_mappings,
        )
        cleaned_df, cleaning_entries = cleaner.clean(raw_df)
        cleaning_log_df = cleaner.get_log_dataframe()

        # 5. Readmission Outcome Definition
        outcome_cfg = self.config.get_outcome_config()
        cleaned_df, outcome_summary = define_readmission_outcome(
            cleaned_df,
            outcome_col=outcome_cfg.get("raw_column", "readmitted"),
            target_col=outcome_cfg.get("target_column", "readmitted_30d"),
            positive_values=outcome_cfg.get("positive_values", ["<30"]),
            negative_values=outcome_cfg.get("negative_values", [">30", "NO"]),
        )

        # 6. Quality Profile
        quality_analyzer = QualityAnalyzer()
        qual_summary = quality_analyzer.get_summary(cleaned_df)

        # 7. Database Persistence
        self.db.init_schema()
        self.db.store_encounters(cleaned_df, table_name="encounters")
        self.db.store_log(cleaning_log_df, table_name="cleaning_log")
        self.db.store_log(val_report.to_dataframe(), table_name="validation_log")

        logger.info("Pipeline execution completed successfully.")

        return PipelineState(
            raw_df=raw_df,
            cleaned_df=cleaned_df,
            ingestion_metadata=ingestion_meta,
            validation_report=val_report,
            cleaning_log_df=cleaning_log_df,
            outcome_summary=outcome_summary,
            quality_summary=qual_summary,
            database_manager=self.db,
            id_mappings=id_mappings,
            config=self.config,
        )
