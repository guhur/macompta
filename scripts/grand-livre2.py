from pathlib import Path
import pandas as pd
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
import tap


def generate_grand_livre(journal_path: str, grand_livre_path: str):
    # Load the journal data, but drop the first row
    df = pd.read_csv(journal_path, skiprows=1)

    # Sort the dataframe by 'N de compte' for processing
    df = df.sort_values('N de compte')

    # Create a new Excel workbook
    wb = openpyxl.Workbook()

    # Remove the default sheet created
    wb.remove(wb.active)

    # For each account in the Grand Livre
    for account, account_data in df.groupby('N de compte'):
        # Create a new sheet for the account
        ws = wb.create_sheet(title=str(account))

        # Write the account data to the sheet
        for row in dataframe_to_rows(account_data, index=False, header=True):
            ws.append(row)

        # Calculate and write the account totals and balance
        debit_total = account_data['Débit'].sum()
        credit_total = account_data['Crédit'].sum()
        balance = debit_total - credit_total
        ws.append(['', 'Total du compte', '', '', '', '', debit_total, credit_total])
        ws.append(['', 'Solde du compte', '', '', '', '', '', balance])

    # Save the workbook to a file
    wb.save(grand_livre_path)

class Arguments(tap.Tap):
    journal: Path # Path to the journal CSV file
    grand_livre: Path # Path to the output Grand Livre Excel file


def main():
    args = Arguments().parse_args()

    generate_grand_livre(args.journal, args.grand_livre)

if __name__ == "__main__":
    main()
