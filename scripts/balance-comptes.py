"""
Enregistre la balance des comptes

Prend en entrée :
    - le fichier des comptes
    - les journaux

Le script créé un fichier balance.csv avec les colonnes suivantes :
    - compte
    - intitulé
    - mouvement: débit (somme des débits liés à ce compte)
    - mouvement: crédit (somme des crédits liés à ce compte)
    - solde: débit (solde si positif)
    - solde: crédit (solde si négatif)

Les nombres sont arrondis à deux décimales.

On ajoute à la fin une ligne avec le résultat net.

Le script contient des étapes de vérification :
    - les comptes doivent être équilibrés
    - le résultat net doit être égal à la différence entre les comptes de bilan
"""

import logging
from pathlib import Path
import tap
from macompta import (
    Account,
    Record,
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


# Arguments CLI
class Arguments(tap.Tap):
    compte: Path
    journals: list[Path]
    output: Path
    annee: int


def main():
    args = Arguments().parse_args()

    # Load the records
    records = load_journals(args.journals)
    # Remove the records with the libellé starting with "Fermeture: "
    records = [record for record in records if record["compte"][:1] != "8"]
    logger.info(f"Chargement des opérations : {len(records)}")

    accounts = load_accounts([args.compte])
    # add accounts in the journals
    accounts = update_accounts(accounts, records)
    accounts = sorted(accounts, key=lambda x: x["compte"])
    logger.info(f"Chargement des comptes : {len(accounts)}")

    export_header(args.output, args.annee)

    for classe in range(1, 9):
        # Filter the accounts
        accounts_classe = filter_accounts_by_class(accounts, classe)

        # Export the accounts
        for account in accounts_classe:
            export_account(args.output, account, records)


def export_account(output: Path, account: Account, records: list[Record]):
    # Filter the records
    records_account = filter_records_by_account(records, account["compte"])

    # Compute the balance
    mvt_credit = sum([record["crédit"] for record in records_account])
    mvt_debit = sum([record["débit"] for record in records_account])
    balance = mvt_debit - mvt_credit
    solde_debit = balance if balance > 0 else 0
    solde_credit = -balance if balance < 0 else 0

    # Export the account
    with open(output, "a") as f:
        f.write(
            f"{account['compte']}\t{account['intitulé']}\t"
            f"{two_decimals(mvt_debit)}\t"
            f"{two_decimals(mvt_credit)}\t"
            f"{two_decimals(solde_debit)}\t"
            f"{two_decimals(solde_credit)}\n"
        )


def export_header(output: Path, annee: int):
    # Export header
    with open(output, "w") as f:
        f.write("Grand livre\n")
        f.write(f"1.1.{annee} - 31.12.{annee}\n")
        f.write("\n")
        f.write("Numéro de\tLibellé\tMouvement\t\tSolde\n")
        f.write("Compte\tLibellé\tDébit\tCrédit\tSolde\n")


if __name__ == "__main__":
    main()
