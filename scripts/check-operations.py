import pandas as pd
import tap

def check_debit_credit_totals(df: pd.DataFrame):
    total_debit = df['Débit'].sum()
    total_credit = df['Crédit'].sum()

    if total_debit != total_credit:
        print(f"Warning: Total Debit ({total_debit}) does not equal Total Credit ({total_credit}).")

def check_account_balances(df: pd.DataFrame):
    for account, account_data in df.groupby('N de compte'):
        balance = account_data['Débit'].sum() - account_data['Crédit'].sum()

        # Check if the balance is negative
        # But leave a tolerance of 0.01 for rounding errors
        if balance < -0.01:
            print(f"Warning: Account {account} has a negative balance ({balance}).")

def check_unused_journals(df: pd.DataFrame):
    if df['Journal'].isna().any():
        print("Warning: There are transactions with no journal specified.")

def check_account_numbers(df: pd.DataFrame):
    if not df['N de compte'].astype(str).str.match(r'\d{6}').all():
        print("Warning: There are accounts with invalid account numbers.")

def check_for_duplicates(df: pd.DataFrame):
    if df.duplicated(subset=['Journal', 'Numéro', 'Date', 'Identifiant', 'Libellé', 'Débit', 'Crédit']).any():
        print("Warning: There are duplicate transactions.")

def perform_checks(journal_path: str):
    # Load the journal data
    df = pd.read_csv(journal_path, skiprows=1)

    # Perform the checks
    check_debit_credit_totals(df)
    check_account_balances(df)
    check_unused_journals(df)
    check_account_numbers(df)
    check_for_duplicates(df)


class Arguments(tap.Tap):
    journal: str # Path to the journal CSV file

def main():
    args = Arguments().parse_args()

    perform_checks(args.journal)

if __name__ == "__main__":
    main()
