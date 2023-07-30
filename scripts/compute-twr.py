import pandas as pd
from pydantic import BaseModel
import numpy as np
import numpy_financial as npf
import tap
from macompta.twr import compute_twr


def load_data(filepath):
    """
    Load data from a CSV file.
    CSV file must have the following columns:
    - N Compte: account number
    - Date: full date
    - Type: type of transaction (apport, retrait, other)
    - Débit: debit value
    - Crédit: credit value
    """

    df = pd.read_csv(filepath)
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")
    return df


def select_account(df: pd.DataFrame, account: int) -> pd.DataFrame:
    return df[df["N Compte"] % 100 == account]


def compute_values(df: pd.DataFrame):
    """
    df is a DataFrame with the following columns:
    - N Compte: account number
    - Date: full date
    - Débit: debit value
    - Crédit: credit value
    """
    accounts: list[int] = sorted(list(df["N Compte"].unique()))
    output: dict[tuple[str, int], pd.DataFrame] = {}

    for account in accounts:
        df_account = select_account(df, account)
        df_account["Solde"] = df_account["Débit"].fillna(0.0)
        df_account["Solde"] -= df_account["Crédit"].fillna(0.0)
        df_account = df_account.set_index("Date")
        df_account = df_account.sort_index()

        twr_series = compute_twr(
            df_account["Solde"].to_numpy(),
            df_account.index.to_numpy(),
            df_account["Type"].to_numpy(),
            frequency="yearly",
        )
        # Convert index to string
        years = twr_series.index.strftime("%Y")
        twr_series.index = years

        # Compute the investments which are the cumulative sum of the solde for each period but only for operations of apport/retrait
        df_account["Solde_investment"] = np.where(
            df_account["Type"].isin(["apport", "retrait"]),
            df_account["Solde"],
            0,
        )
        inv_series = (
            df_account["Solde_investment"]
            .cumsum()
            .resample("Y")
            .last()
            .fillna(method="ffill")
        )
        inv_series.index = years
        output[("capital", account)] = inv_series

        # Compute the net values which are the cumulative solde (the last one of each period
        nv_series = (
            df_account["Solde"]
            .cumsum()
            .resample("Y")
            .last()
            .fillna(method="ffill")
        )
        nv_series.index = years
        output[("nv", account)] = nv_series

        output[("twr", account)] = twr_series

    # Convert output into a DataFrame with a hierarchical index
    export = pd.DataFrame(output)
    export.columns = pd.MultiIndex.from_product(
        [accounts, ["capital", "value", "roi"]]
    )

    return export


class Arguments(tap.Tap):
    input: str
    output: str


def main():
    args = Arguments().parse_args()

    # Load data
    df = load_data(args.input)

    # Compute values
    twr = compute_values(df)

    # Export to Excel
    # Make sure that the dates are sorted and in the right format
    # Keep only 2 decimals
    twr = twr.transpose()
    twr.to_excel(args.output, float_format="%.2f")


if __name__ == "__main__":
    main()
