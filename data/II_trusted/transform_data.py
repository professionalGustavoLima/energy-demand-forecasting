import pandas as pd


class ONSTrustedData:
    """Transform ONS raw data into trusted data."""

    COLUMN_MAPPING = {
        "dat_referencia": "ref_date",
        "din_referenciautc": "ref_datetime",
        "N": "north_scheduled_load_mwmed",
        "NE": "northeast_scheduled_load_mwmed",
        "S": "south_scheduled_load_mwmed",
        "SECO": "southeast_centralwest_scheduled_load_mwmed",
    }

    def __init__(
        self,
        input_path: str,
        output_path: str,
    ) -> None:
        """
        Initialize the trusted data transformation.

        Parameters
        ----------
        input_path : str
            Path to the raw data.
        output_path : str
            Path where the trusted data will be saved.
        """
        self.input_path = input_path
        self.output_path = output_path

    def _load_raw_data(self) -> pd.DataFrame:
        """Load raw data from a Parquet file."""
        return pd.read_parquet(self.input_path)

    def _transform_to_wide(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform the data from long format to wide format."""
        df_wide = df.pivot(
            index=["dat_referencia", "din_referenciautc"],
            columns="cod_areacarga",
            values="val_cargaglobalprogramada",
        ).reset_index()

        df_wide.columns.name = None

        return df_wide

    def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename columns according to the trusted data schema."""
        return df.rename(columns=self.COLUMN_MAPPING)

    def transform(self) -> pd.DataFrame:
        """Load and transform raw data into trusted data."""
        df = self._load_raw_data()
        df = self._transform_to_wide(df)
        df = self._rename_columns(df)

        return df

    def save(self, df: pd.DataFrame) -> None:
        """Save trusted data as a Parquet file."""
        df.to_parquet(self.output_path)

    def run(self) -> pd.DataFrame:
        """Execute the trusted data transformation and save the result."""
        df_trusted = self.transform()
        self.save(df_trusted)

        return df_trusted


def main() -> None:
    """Run the ONS trusted data transformation."""

    transformer = ONSTrustedData(
        input_path="energy-demand-forecasting/data/I_raw/raw_data.parquet",
        output_path="energy-demand-forecasting/data/II_trusted/trusted_data.parquet",
    )

    df_trusted = transformer.run()

    print(df_trusted)


if __name__ == "__main__":
    main()