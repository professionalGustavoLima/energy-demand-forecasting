import logging
import time
from pathlib import Path

import pandas as pd

from data.I_raw.load_data import ONSDataLoader
from data.II_trusted.transform_data import ONSTrustedData
from data.III_refined.refine_data import ONSRefinedData


# ---------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]


# ---------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    ),
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


class EnergyDemandPipeline:
    """Orchestrate the ONS energy demand data pipeline."""

    def __init__(self) -> None:
        """Initialize the energy demand pipeline."""

        self.raw_path = (
            PROJECT_ROOT
            / "data"
            / "I_raw"
            / "raw_data.parquet"
        )

        self.trusted_path = (
            PROJECT_ROOT
            / "data"
            / "II_trusted"
            / "trusted_data.parquet"
        )

        self.refined_path = (
            PROJECT_ROOT
            / "data"
            / "III_refined"
            / "refined_data.parquet"
        )

    def _log_dataframe_info(
        self,
        df: pd.DataFrame,
        stage: str,
    ) -> None:
        """Log relevant information about a DataFrame."""

        logger.info("=" * 70)
        logger.info("DATASET SUMMARY | %s", stage)
        logger.info("=" * 70)

        logger.info(
            "Shape: %s rows x %s columns",
            f"{df.shape[0]:,}",
            df.shape[1],
        )

        logger.info("Schema:")

        for column, dtype in df.dtypes.items():
            logger.info(
                "  %-50s %s",
                column,
                dtype,
            )

        total_missing = df.isna().sum().sum()

        logger.info(
            "Total missing values: %s",
            f"{total_missing:,}",
        )

        missing_by_column = df.isna().sum()
        missing_by_column = (
            missing_by_column[
                missing_by_column > 0
            ]
            .sort_values(ascending=False)
        )

        if missing_by_column.empty:
            logger.info("Missing values by column: none")
        else:
            logger.info("Missing values by column:")

            for column, count in missing_by_column.items():
                logger.info(
                    "  %-50s %s",
                    column,
                    f"{count:,}",
                )

        logger.info("Descriptive statistics:")

        logger.info(
            "\n%s",
            df.describe().to_string(),
        )

        logger.info("=" * 70)

    def _run_stage(
        self,
        stage_name: str,
        transformer,
    ) -> pd.DataFrame:
        """Execute one pipeline stage and log its execution."""

        logger.info("")
        logger.info("#" * 70)
        logger.info("STARTING STAGE: %s", stage_name)
        logger.info("#" * 70)

        start_time = time.perf_counter()

        try:
            df = transformer.run()

            elapsed_time = time.perf_counter() - start_time

            self._log_dataframe_info(
                df=df,
                stage=stage_name,
            )

            logger.info(
                "Stage '%s' completed successfully.",
                stage_name,
            )

            logger.info(
                "Execution time: %.2f seconds",
                elapsed_time,
            )

            logger.info(
                "Output: %s",
                transformer.output_path,
            )

            return df

        except Exception:
            elapsed_time = time.perf_counter() - start_time

            logger.exception(
                "Stage '%s' failed after %.2f seconds.",
                stage_name,
                elapsed_time,
            )

            raise

    def run(self) -> None:
        """Execute the complete data pipeline."""

        pipeline_start = time.perf_counter()

        logger.info("")
        logger.info("=" * 70)
        logger.info("ENERGY DEMAND FORECASTING DATA PIPELINE")
        logger.info("=" * 70)

        # -------------------------------------------------------------
        # 01 - Raw
        # -------------------------------------------------------------

        raw_transformer = ONSDataLoader(
            load_codes=["SECO", "N", "NE", "S"],
            start_date="2020-01-01",
            end_date="2026-06-30",
            output_path=str(self.raw_path),
            interval_months=6,
            max_retries=3,
            timeout=60,
            retry_delay=5,
        )

        self._run_stage(
            stage_name="01_RAW",
            transformer=raw_transformer,
        )

        # -------------------------------------------------------------
        # 02 - Trusted
        # -------------------------------------------------------------

        trusted_transformer = ONSTrustedData(
            input_path=str(self.raw_path),
            output_path=str(self.trusted_path),
        )

        self._run_stage(
            stage_name="02_TRUSTED",
            transformer=trusted_transformer,
        )

        # -------------------------------------------------------------
        # 03 - Refined
        # -------------------------------------------------------------

        refined_transformer = ONSRefinedData(
            input_path=str(self.trusted_path),
            output_path=str(self.refined_path),
        )

        self._run_stage(
            stage_name="03_REFINED",
            transformer=refined_transformer,
        )

        # -------------------------------------------------------------
        # Pipeline completed
        # -------------------------------------------------------------

        total_time = time.perf_counter() - pipeline_start

        logger.info("")
        logger.info("=" * 70)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)

        logger.info(
            "Total execution time: %.2f seconds",
            total_time,
        )

        logger.info(
            "Final dataset: %s",
            self.refined_path,
        )


def main() -> None:
    """Run the complete data pipeline."""

    pipeline = EnergyDemandPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()