import pandas as pd
import tap

def calculate_account_balance(file_path: str, output_path: str):
    # Load all sheets from the Excel file into a dictionary of DataFrames
    all_sheets = pd.read_excel(file_path, sheet_name=None)

    # Initialize an empty DataFrame to hold the balance for all accounts
    all_balance_decomposed = pd.DataFrame()

    # Iterate over all sheets in the dictionary
    for sheet_name, df in all_sheets.items():
        # Drop rows where 'N de compte' is NaN
        ledger_cleaned = df.dropna(subset=['N de compte'])

        # Calculate the balance for each account
        balance = ledger_cleaned.groupby('N de compte')[['Débit', 'Crédit']].sum()

        # Decompose the balance into Debit/Credit
        solde = (balance['Débit'] - balance['Crédit'])
        # round off solde
        solde = solde.round(2)
        balance['Solde Débit'] = solde.where(solde > 0, 0)
        balance['Solde Crédit'] = solde.where(solde < 0, 0)

        balance.reset_index(inplace=True)

        # Append the balance of the current sheet to the all_balance DataFrame
        all_balance_decomposed = all_balance_decomposed._append(balance)

    # Save the all_balance DataFrame to an Excel file
    all_balance_decomposed.to_excel(output_path, index=False)


class Arguments(tap.Tap):
    grand_livre: str # Path to the Excel file containing the account data
    output: str # Path to save the output Excel file with account balance

if __name__ == "__main__":
    args = Arguments().parse_args()

    calculate_account_balance(args.grand_livre, args.output)
