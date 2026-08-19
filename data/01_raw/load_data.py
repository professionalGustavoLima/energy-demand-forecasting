import time

import pandas as pd
import requests


class ONSDataLoader:
    """Load and save raw energy demand data from the ONS API."""

    BASE_URL = "https://apicarga.ons.org.br/prd/cargaprogramada"

    def __init__(
        self,
        load_codes: list[str],
        start_date: str,
        end_date: str,
        output_path: str,
        interval_months: int = 6,
        max_retries: int = 3,
        timeout: int = 60,
        retry_delay: int = 5,
    ) -> None:
        """
        Initialize the ONS data loader.

        Parameters
        ----------
        load_codes : list[str]
            Load area codes to retrieve.
        start_date : str
            Start date in YYYY-MM-DD format.
        end_date : str
            End date in YYYY-MM-DD format.
        output_path : str
            Path where the raw data will be saved.
        interval_months : int, default=6
            Number of months per API request.
        max_retries : int, default=3
            Maximum number of attempts for each request.
        timeout : int, default=60
            Request timeout in seconds.
        retry_delay : int, default=5
            Delay between retries in seconds.
        """
        self.load_codes = load_codes
        self.start_date = pd.Timestamp(start_date)
        self.end_date = pd.Timestamp(end_date)
        self.output_path = output_path
        self.interval_months = interval_months
        self.max_retries = max_retries
        self.timeout = timeout
        self.retry_delay = retry_delay

    def _generate_periods(self) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
        """Generate date intervals for the API requests."""
        periods = []

        current_date = self.start_date

        while current_date <= self.end_date:
            period_end = (
                current_date
                + pd.DateOffset(months=self.interval_months)
                - pd.Timedelta(days=1)
            )

            period_end = min(period_end, self.end_date)

            periods.append((current_date, period_end))

            current_date = period_end + pd.Timedelta(days=1)

        return periods

    def _build_url(
        self,
        load_code: str,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
    ) -> str:
        """Build the API URL for a specific load area and period."""
        return (
            f"{self.BASE_URL}"
            f"?dat_inicio={start_date:%Y-%m-%d}"
            f"&dat_fim={end_date:%Y-%m-%d}"
            f"&cod_areacarga={load_code}"
        )

    def _fetch_data(
        self,
        load_code: str,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
    ) -> pd.DataFrame:
        """Fetch data from the ONS API with retry support."""
        url = self._build_url(
            load_code=load_code,
            start_date=start_date,
            end_date=end_date,
        )

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(
                    url,
                    timeout=self.timeout,
                )

                response.raise_for_status()

                return pd.DataFrame(response.json())

            except (requests.RequestException, ValueError) as error:
                print(
                    f"Request failed "
                    f"(attempt {attempt}/{self.max_retries}) "
                    f"for {load_code} "
                    f"[{start_date:%Y-%m-%d} → {end_date:%Y-%m-%d}]: "
                    f"{error}"
                )

                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        raise RuntimeError(
            f"Failed to retrieve data for {load_code} "
            f"[{start_date:%Y-%m-%d} → {end_date:%Y-%m-%d}] "
            f"after {self.max_retries} attempts."
        )

    def load(self) -> pd.DataFrame:
        """Load and combine data for all areas and periods."""
        periods = self._generate_periods()
        dataframes = []

        total_requests = len(self.load_codes) * len(periods)
        request_number = 0

        for start_date, end_date in periods:
            for load_code in self.load_codes:
                request_number += 1

                print(
                    f"[{request_number}/{total_requests}] "
                    f"Loading {load_code} "
                    f"({start_date:%Y-%m-%d} → {end_date:%Y-%m-%d})"
                )

                df = self._fetch_data(
                    load_code=load_code,
                    start_date=start_date,
                    end_date=end_date,
                )

                dataframes.append(df)

        return pd.concat(dataframes, ignore_index=True)

    def save(self, df: pd.DataFrame) -> None:
        """Save the raw data as a Parquet file."""
        df.to_parquet(self.output_path)

    def run(self) -> pd.DataFrame:
        """Load and save the raw data."""
        df_raw = self.load()

        self.save(df_raw)

        return df_raw


def main() -> None:
    """Run the ONS raw data extraction."""

    loader = ONSDataLoader(
        load_codes=["SECO", "N", "NE", "S"],
        start_date="2020-01-01",
        end_date="2026-06-30",
        output_path="energy-demand-forecasting/data/01_raw/raw_data.parquet",
        interval_months=6,
        max_retries=3,
        timeout=60,
        retry_delay=5,
    )

    df_raw = loader.run()

    print(df_raw)


if __name__ == "__main__":
    main()