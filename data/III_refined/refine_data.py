import numpy as np
import pandas as pd


class ONSRefinedData:
    """Transform ONS trusted data into refined data."""

    LOAD_COLUMNS = [
        "north_scheduled_load_mwmed",
        "northeast_scheduled_load_mwmed",
        "south_scheduled_load_mwmed",
        "southeast_centralwest_scheduled_load_mwmed",
    ]

    def __init__(
        self,
        input_path: str,
        output_path: str,
    ) -> None:
        """
        Initialize the refined data transformation.

        Parameters
        ----------
        input_path : str
            Path to the trusted data.
        output_path : str
            Path where the refined data will be saved.
        """
        self.input_path = input_path
        self.output_path = output_path

    def _load_trusted_data(self) -> pd.DataFrame:
        """Load trusted data from a Parquet file."""
        return pd.read_parquet(self.input_path)

    def _remove_excessive_missing_values(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Remove rows with fewer than three valid load measurements."""
        return (
            df.dropna(
                subset=self.LOAD_COLUMNS,
                thresh=3,
            )
            .reset_index(drop=True)
        )

    def _align_analysis_period(
        self,
        df: pd.DataFrame,
        df_valid: pd.DataFrame,
    ) -> pd.DataFrame:
        """Align the data with the valid analysis period."""
        start_datetime = df_valid["ref_datetime"].iloc[0]

        return (
            df[df["ref_datetime"] >= start_datetime]
            .reset_index(drop=True)
        )

    def _standardize_datetime(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Standardize datetime to São Paulo local time."""
        df = df.copy()

        df["ref_datetime"] = (
            pd.to_datetime(df["ref_datetime"], utc=True)
            .dt.tz_convert("America/Sao_Paulo")
            .dt.tz_localize(None)
        )

        df["ref_date"] = df["ref_datetime"].dt.date

        return df

    def _remove_outliers_iqr(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Replace IQR-based outliers with missing values."""
        df = df.copy()

        for column in self.LOAD_COLUMNS:
            q1 = df[column].quantile(0.25)
            q3 = df[column].quantile(0.75)

            iqr = q3 - q1

            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            outlier_mask = (
                (df[column] < lower_bound)
                | (df[column] > upper_bound)
            )

            df.loc[outlier_mask, column] = np.nan

        return df

    def _interpolate_missing_values(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Fill missing load measurements using time-based interpolation."""
        df = df.copy()

        df = df.set_index("ref_datetime")

        df[self.LOAD_COLUMNS] = df[self.LOAD_COLUMNS].interpolate(
            method="time",
            limit=48,
            limit_direction="both",
        )

        return df.reset_index()

    def _select_columns(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Select columns according to the refined data schema."""
        return df[
            ["ref_date", "ref_datetime"] + self.LOAD_COLUMNS
        ]

    def transform(self) -> pd.DataFrame:
        """Load and transform trusted data into refined data."""
        df = self._load_trusted_data()

        df_valid = self._remove_excessive_missing_values(df)

        df = self._align_analysis_period(
            df,
            df_valid,
        )

        df = self._standardize_datetime(df)
        df = self._remove_outliers_iqr(df)
        df = self._interpolate_missing_values(df)
        df = self._select_columns(df)

        return df

    def save(self, df: pd.DataFrame) -> None:
        """Save refined data as a Parquet file."""
        df.to_parquet(
            self.output_path,
            index=False,
        )

    def run(self) -> pd.DataFrame:
        """Execute the refined data transformation and save the result."""
        df_refined = self.transform()
        self.save(df_refined)

        return df_refined


def main() -> None:
    """Run the ONS refined data transformation."""

    transformer = ONSRefinedData(
        input_path=("energy-demand-forecasting/data/II_trusted/trusted_data.parquet"),
        output_path=("energy-demand-forecasting/data/III_refined/refined_data.parquet"),
    )

    df_refined = transformer.run()

    print(df_refined)


if __name__ == "__main__":
    main()