"""
Ce script génère un fichier CSV contenant le grand livre de l'année.
Il prend en entrée :
    - le fichier des comptes
    - le livre journal

Le script fonctionne avec les étapes suivantes :
    1. Charger les comptes
    2. Charger les opérations
    3. Afficher les opérations par compte et par classe

"""
import logging
from pathlib import Path
import tap
from macompta import (
    load_accounts,
    update_accounts,
    filter_records_by_account,
    load_journals,
    filter_accounts_by_class,
)
from macompta.utils import two_decimals

# Log to stdout
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Arguments(tap.Tap):
    compte: Path
    journals: list[Path]
    output: Path
    annee: int


def main():
    args = Arguments().parse_args()

    # Load the records
    records = load_journals(args.journals)
    logger.info(f"Chargement des opérations : {len(records)}")

    accounts = load_accounts([args.compte])
    # add accounts in the journals
    accounts = update_accounts(accounts, records)
    accounts = sorted(accounts, key=lambda x: x["compte"])
    logger.info(f"Chargement des comptes : {len(accounts)}")

    # Export header
    with open(args.output, "w") as f:
        f.write("Grand livre\n")
        f.write(f"1.1.{args.annee} - 31.12.{args.annee}\n")
        f.write("\n")
        f.write("Compte\tLibellé\tDébit\tCrédit\tSolde\n")

    # Export the operations filtered by accounts
    # do it class by class (a class is when the first digit is the same)
    with open(args.output, "a") as f:
        for classe in range(1, 9):
            # Filter the accounts
            accounts_classe = filter_accounts_by_class(accounts, classe)
            accounts_classe = sorted(accounts_classe, key=lambda x: x["compte"])

            # Export header
            f.write(f"Classe {classe}\n")
            f.write("\n")
            logger.info(f"Classe {classe} : {len(accounts_classe)} comptes")
            debit = 0.0
            credit = 0.0

            for account in accounts_classe:
                records_classe = filter_records_by_account(records, account["compte"])

                account_credit = sum([r["crédit"] for r in records_classe])
                account_debit = sum([r["débit"] for r in records_classe])
                solde = account_debit - account_credit

                f.write(
                    f"{account['compte']}\t{account['intitulé']}\t{two_decimals(account_debit)}\t{two_decimals(account_credit)}\t{solde}\n"
                )

                # Write the records for this account
                for record in records_classe:
                    f.write(
                        f"\t{record['libellé']}\t{two_decimals(record['débit'])}\t{two_decimals(record['crédit'])}\t\n"
                    )

                debit += account_debit
                credit += account_credit

                # Write the empty line
                f.write("\n")

            # Write the total for this class
            solde = debit - credit
            f.write(
                f"\t\t{two_decimals(debit)}\t{two_decimals(credit)}\t{two_decimals(solde)}\n"
            )

            # Write the empty line
            f.write("\n")


if __name__ == "__main__":
    main()
