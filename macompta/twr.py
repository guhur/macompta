import typing as t
import pandas as pd
import numpy as np
import unittest


Frequency = t.Literal["daily", "weekly", "monthly", "quarterly", "yearly"]


def compute_twr(
    solde: np.ndarray,
    date: np.ndarray,
    type: np.ndarray,
    frequency: Frequency = "yearly",
) -> pd.DataFrame:
    """
    Compute the Time-Weighted Rate of Return (TWR) at the end of each period.

    Parameters:
        solde (np.ndarray): A numpy array containing the solde at the end of each day.
        date (np.ndarray): A numpy array containing the date at the end of each day.
        type (np.ndarray): A numpy array containing the type of transaction at the end of each day.


    Returns:
        pd.Series: A pandas Series containing the TWR at the end of each month.
    """
    df = pd.DataFrame(
        {"date": date, "débit": solde, "crédit": 0, "type": type}
    )
    df["net_cash_flow"] = df["débit"] - df["crédit"]

    # Filter out rows with 'capital' type (only consider 'appreciation/depreciation')
    capital_df = df[df["type"].isin({"apport", "retrait"})]

    periods = {
        "daily": "D",
        "weekly": "W",
        "monthly": "M",
        "quarterly": "Q",
        "yearly": "Y",
    }
    if frequency not in periods:
        raise ValueError(f"Invalid frequency: {frequency}")
    period = periods[frequency]

    # Group by period and calculate the product of (1 + returns) for each period
    times = df["date"].dt.to_period(period)
    value_by_period = df.groupby(times)["net_cash_flow"].sum()
    investment_by_period = capital_df.groupby(times)["net_cash_flow"].sum()

    # Compute the cumulative product of returns for each month to get the TWR
    twr_by_period = value_by_period.cumsum() / investment_by_period.cumsum()

    # Fill missing values with the last known value
    twr_by_period = twr_by_period.fillna(method="ffill")

    # Compute the average TWR for each period by taking the geometric mean wrt the period length
    ref = twr_by_period.index[0]
    period_length = twr_by_period.index.to_timestamp() - ref.to_timestamp())
    # Convert period length to the unit of frequency
    period_length = period_length / pd.to_timedelta(1, unit=period)
    twr_by_period = twr_by_period ** (1.0 / period_length)

    return twr_by_period


# Unit tests for compute_twr function
class TestComputeTWR(unittest.TestCase):
    def setUp(self):
        # Sample investment data for testing
        data = {
            "date": pd.to_datetime(
                [
                    "2023-01-01",
                    "2023-01-15",
                    "2023-02-01",
                    "2023-02-15",
                    "2023-03-01",
                    "2023-03-15",
                ]
            ),
            "débit": [1000, 100, 1500, 100, 0, 200],
            "crédit": [0, 0, 0, 0, 0, 0],
            "type": [
                "apport",
                "plus-value",
                "apport",
                "plus-value",
                "apport",
                "plus-value",
            ],
        }
        self.investment_data = pd.DataFrame(data)

    def test_compute_twr(self):
        # Calculate the TWR using the function
        twr_series = compute_twr(
            self.investment_data["débit"].to_numpy()
            - self.investment_data["crédit"].to_numpy(),
            self.investment_data["date"].to_numpy(),
            self.investment_data["type"].to_numpy(),
            frequency="monthly",
        )

        # Expected TWR values (manually computed)
        expected_twr = pd.Series(
            [1.10, 1.08, 1.16],
            index=pd.to_datetime(["2023-01", "2023-02", "2023-03"]).to_period(
                "M"
            ),
        )

        # Compare the actual and expected TWR
        self.assertTrue(twr_series.equals(expected_twr))


if __name__ == "__main__":
    unittest.main()
