"""
Ce script permet de créer un fichier csv contenant les immobilisations
Exemple de fichier de sortie:

Tableau des immobilisations					
1.1.2021 - 31.12.2021					
					
Postes de bilan		Valeur brute au début de l'exercice	Augmentations	Diminutions	Valeur brute à la fin de l'exercice
Immobilisations corporelles		€3,951.51	€0.00	€3,951.51	€0.00
215501	Scanner laser	€372.53	€0.00	€372.53	€0.00
215502	2D Lidar Sensor	€2,064.00	€0.00	€2,064.00	€0.00
215503	Turtleboat3	€461.64	€0.00	€461.64	€0.00
218301	PLG Boitier	€496.67	€0.00	€496.67	€0.00
218302	PC Config	€556.67	€0.00	€556.67	€0.00
					
Immobilisations incorporelles		€21,568.20	0	0	€21,568.20
205001	Logiciel	€19,000.00	0	0	€19,000.00
205002	Brevet	€2,568.20	0	0	€2,568.20
"""
import logging
from pathlib import Path
import tap
from macompta import (
    Immobilisation,
    Record,
    load_accounts,
    load_csv,
    load_immobilisations,
    update_immobilisations,
    is_immo_corporelle,
    filter_records_by_account,
)
from macompta.utils import convert_date

# Log to stdout
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Arguments(tap.Tap):
    compte: Path
    immobilisations: list[Path]
    livre_journal: Path
    annee: int


def main(args: Arguments) -> None:
    """
    Crée le fichier des immobilisations
    """
    logger.info("Création du fichier des immobilisations")
    logger.info(f"Année: {args.annee}")
    logger.info(f"Compte: {args.compte}")
    logger.info(f"Immobilisation: {','.join([str(i) for i in args.immobilisations])}")

    # Load the accounts
    accounts = load_accounts([args.compte])
    logger.info(f"Comptes chargés: {len(accounts)}")

    # Load the immobilisations
    immobilisations = load_immobilisations(args.immobilisations)
    logger.info(f"Immobilisations chargées: {len(immobilisations)}")

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
    output = Path(f"immobilisations_{args.annee}.csv")
    logger.info(f"Création du fichier {output}")

    # Write the header
    with open(output, "w") as f:
        f.write("Tableau des immobilisations\n")
        f.write(f"1.1.{args.annee} - 31.12.{args.annee}\n")
        f.write("\n")
        f.write(
            "Postes de bilan\tValeur brute au début de l'exercice\tAugmentations\tDiminutions\tValeur brute à la fin de l'exercice\n"
        )

    # Ecriture des immobilisations corporelles
    with open(output, "a") as f:
        f.write("Immobilisations corporelles\t\t\t\t\n")
    immo_corporelles = [i for i in immobilisations if is_immo_corporelle(i)]
    ecrire_immobilisations(output, immo_corporelles, records)

    # Ecriture des immobilisations incorporelles
    with open(output, "a") as f:
        f.write("Immobilisations incorporelles\t\t\t\t\n")
    immo_incorporelles = [i for i in immobilisations if not is_immo_corporelle(i)]
    ecrire_immobilisations(output, immo_incorporelles, records)


def ecrire_immobilisations(
    output: Path, immobilisations: list[Immobilisation], records: list[Record]
) -> None:
    """
    Ecrit les immobilisations corporelles dans le fichier de sortie
    """
    with open(output, "a") as f:
        # Write the immobilisations
        for immo in immobilisations:
            debut = immo["montant"]
            aug = sum(
                [
                    op["débit"]
                    for op in filter_records_by_account(records, immo["compte"])
                ]
            )
            dim = sum(
                [
                    op["crédit"]
                    for op in filter_records_by_account(records, immo["compte"])
                ]
            )
            fin = debut + aug - dim

            compte = immo["compte"]
            intitule = immo["intitulé"]

            f.write(f"{compte}\t{intitule}\t{debut}\t{aug}\t{dim}\t{fin}\n")


if __name__ == "__main__":
    main(Arguments().parse_args())
