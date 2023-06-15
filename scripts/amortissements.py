"""
Ce script permet de créer un fichier csv contenant les amortissements
Exemple de fichier de sortie:


Tableaux des amortissements,,,,,,
1.1.2021 - 31.12.2021,,,,,,
,,,,,,
Postes de bilan,,Valeur brute au début de l'exercice,Débit,Crédit,Valeur brute à la fin de l'exercice,
Immobilisations corporelles,,"€3,776.06",€175.45,"€3,454.84",€496.67,
2815501,Scanner laser,€372.53,€0.00,€372.53,€0.00,

Immobilisations incorporelles,,"€7,568.91","€4,328.41",€0.00,"€11,897.32",
2805001,Logiciel,"€7,200.00","€4,200.00",€0.00,"€11,400.00",
2805002,Brevet,€368.91,€128.41,€0.00,€497.32,

Amortissement du logiciel,,,,,,

,,Durée,,5,,
,,Achat,,"€19,000.00",,
,,Mode,,linéaire,,
,,Amortissement annuel,,"€3,800.00",,
"""
import logging
from pathlib import Path
import tap
from macompta import (
    Immobilisation,
    Record,
    load_accounts,
    load_immobilisations,
    is_immo_corporelle,
    filter_records_by_account,
    load_journals,
)
from macompta.utils import two_decimals

# Log to stdout
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Arguments(tap.Tap):
    compte: Path
    immobilisations: list[Path]
    journals: list[Path]
    annee: int
    output: Path


def main(args: Arguments) -> None:
    """
    Crée le fichier des immobilisations
    """
    logger.info("Création du fichier des immobilisations")
    logger.info(f"Année: {args.annee}")
    logger.info(f"Compte: {args.compte}")
    logger.info(
        f"Immobilisation: {','.join([str(i) for i in args.immobilisations])}"
    )

    # Load the accounts
    accounts = load_accounts([args.compte])
    logger.info(f"Comptes chargés: {len(accounts)}")

    # Load the immobilisations
    immobilisations = load_immobilisations(args.immobilisations)
    logger.info(f"Immobilisations chargées: {len(immobilisations)}")

    # Load the records
    records = load_journals(args.journals)

    # Create the output file
    logger.info(f"Création du fichier {args.output}")

    # Write the header
    with open(args.output, "w") as f:
        f.write("Tableau des amortissements\n")
        f.write(f"1.1.{args.annee} - 31.12.{args.annee}\n")
        f.write("\n")
        f.write(
            "Postes de bilan\tValeur brute au début de l'exercice\tAugmentations\tDiminutions\tValeur brute à la fin de l'exercice\n"
        )

    # Ecriture des amortissements liees aux immobilisations corporelles
    with open(args.output, "a") as f:
        f.write("Immobilisations corporelles\t\t\t\t\n")
    immo_corporelles = [i for i in immobilisations if is_immo_corporelle(i)]
    ecrire_amortissements(args.output, immo_corporelles, records)

    # Ecriture des amortissements liees aux immobilisations incorporelles
    with open(args.output, "a") as f:
        f.write("Immobilisations incorporelles\t\t\t\t\n")
    immo_incorporelles = [
        i for i in immobilisations if not is_immo_corporelle(i)
    ]
    ecrire_amortissements(args.output, immo_incorporelles, records)


def ecrire_amortissements(
    output: Path, immobilisations: list[Immobilisation], records: list[Record]
) -> None:
    """
    Ecrit les amortissements liées aux immobilisations corporelles dans le fichier de sortie
    """
    with open(output, "a") as f:
        # Write the immobilisations
        for immo in immobilisations:
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

            f.write(
                f"{compte}\t{intitule}\t{debut}\t{two_decimals(aug)}\t{two_decimals(dim)}\t{two_decimals(fin)}\n"
            )


if __name__ == "__main__":
    main(Arguments().parse_args())
