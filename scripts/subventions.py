"""
WARNING: this file is not finished!
Ce script permet de créer un fichier csv contenant les subventions
Exemple de fichier de sortie:


Tableaux des subventions,,,,,,
1.1.2021 - 31.12.2021,,,,,,
,,,,,,
Postes de bilan,,Valeur brute au début de l'exercice,Débit,Crédit,Valeur brute à la fin de l'exercice,
Immobilisations corporelles,,"€3,776.06",€175.45,"€3,454.84",€496.67,
2815501,Scanner laser,€372.53,€0.00,€372.53,€0.00,

Immobilisations incorporelles,,"€7,568.91","€4,328.41",€0.00,"€11,897.32",
2805001,Logiciel,"€7,200.00","€4,200.00",€0.00,"€11,400.00",
2805002,Brevet,€368.91,€128.41,€0.00,€497.32,

Etalement de la subvention,,,,,,

,,Durée,,5,,
,,Achat,,"€19,000.00",,
,,Mode,,linéaire,,
,,Etalement annuel,,"€3,800.00",,

[...]
"""
import logging
from pathlib import Path
import tap
from macompta import (
    Immobilisation,
    Record,
    load_accounts,
    load_csv,
    filter_records_by_account,
)
from macompta.utils import convert_date

# Log to stdout
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Arguments(tap.Tap):
    compte: Path
    livre_journal: Path
    annee: int
    output: Path


def main(args: Arguments) -> None:
    """
    Crée le fichier des subventions
    """
    logger.info("Création du fichier des subventions")
    logger.info(f"Année: {args.annee}")
    logger.info(f"Compte: {args.compte}")

    # Load the accounts
    accounts = load_accounts([args.compte])
    logger.info(f"Comptes chargés: {len(accounts)}")

    # Load the records
    records: list[Record] = []
    for row in load_csv(args.livre_journal):
        records.append(
            {
                "date": convert_date(row["date"]),
                "compte": str(row["compte"]),
                "libellé": str(row["libellé"]),
                "débit": float(row["débit"]),
                "crédit": float(row["crédit"]),
            }
        )

    # Create the output file
    logger.info(f"Création du fichier {args.output}")

    # Détection des subventions
    logger.info("Détection des subventions")
    subventions = []
    for record in records:
        if record["compte"].startswith("13"):
            subventions.append(record["compte"])

    # Ecriture du tableau des subventions
    ecrire_amortissements(args.output, subventions, records, args.annee)


def ecrire_amortissements(
    output: Path, subventions: list[str], records: list[Record], annee: int
) -> None:
    """
    Ecrit le tableau des subventions dans le fichier de sortie
    """
    with open(output, "w") as f:
        f.write("Tableau des subventions\n")
        f.write(f"1.1.{annee} - 31.12.{annee}\n")
        f.write("\n")
        f.write(
            "Postes de bilan\tValeur brute au début de l'exercice\tAugmentations\tDiminutions\tValeur brute à la fin de l'exercice\n"
        )

    with open(output, "a") as f:
        # Write the immobilisations
        for sub in subventions:
            debut = immo["montant"]
            compte_amortissement = f"28{immo['compte'][2:]}"
            aug = sum(
                [
                    op["débit"]
                    for op in filter_records_by_account(
                        records, compte_amortissement
                    )
                ]
            )
            dim = sum(
                [
                    op["crédit"]
                    for op in filter_records_by_account(
                        records, compte_amortissement
                    )
                ]
            )
            fin = debut + aug - dim

            compte = immo["compte"]
            intitule = immo["intitulé"]

            f.write(f"{compte}\t{intitule}\t{debut}\t{aug}\t{dim}\t{fin}\n")


if __name__ == "__main__":
    main(Arguments().parse_args())
