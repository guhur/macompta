"""
Ce script génère un fichier CSV contenant le livre journal en double-colonne.
Il prend en entrée :
    - le(s) fichier(s) CSV des notes de frais
    - le(s) fichier(s) CSV de la banque
    - le(s) fichier(s) CSV des ventes
    - le fichier des comptes
    - le(s) fichier(s) des immobilisations

Le script fonctionne avec les étapes suivantes :
    1. Charger les données des fichiers CSV
    2. Ecrire les opérations d'ouverture des comptes
    3. Affecter le résultat
    4. Ecrire les opérations de ventes, de banque et de notes de frais
    5. Ecrire les opérations d'immobilisations
    6. Ecrire les opérations de clôture des comptes
    7. Ecrire les opérations de résultat
    8. Ecrire les opérations de bilan

Les opérations sont écrites dans un fichier CSV avec les colonnes suivantes :
    - date
    - compte
    - libellé
    - débit
    - crédit
"""
import typing as t
from math import isclose
import logging
import tap
import time
from pathlib import Path
import csv

# Log to stdout
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Record(t.TypedDict):
    date: str
    compte: str
    libellé: str
    débit: float
    crédit: float


class Operation(t.TypedDict):
    date: str
    compte: str
    libellé: str
    ht: float
    tva: float
    ttc: float


class Account(t.TypedDict):
    compte: str
    intitulé: str
    solde: float


class Immobilisation(t.TypedDict):
    compte: str
    intitulé: str
    montant: float
    durée: float
    date: str
    amortissement: t.NotRequired[dict[int, float]]


class Arguments(tap.Tap):
    notes_de_frais: list[Path]
    banque: list[Path]
    compte: Path
    immobilisations: list[Path]
    resultat: Path
    annee: int


def load_csv(csv_file: Path):
    """
    Charge un fichier CSV
    """
    with open(csv_file, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Clean up keys
            row = {k.strip(): v for k, v in row.items()}
            yield row


def load_immobilisations(immobilisations: list[Path]) -> list[Immobilisation]:
    """
    Charge les immobilisations depuis les fichiers CSV
    """
    rows = []
    for immobilisation in immobilisations:
        for row in load_csv(immobilisation):
            # Discard columns not used
            immo: Immobilisation = {
                "compte": str(row["compte"]),
                "intitulé": str(row["intitulé"]),
                "montant": float(row["montant"]),
                "durée": float(row["durée"]),
                "date": str(row["date"]),
            }
            immo["amortissement"] = build_amortissement(immo)
            rows.append(immo)

    return rows


def build_amortissement(immobilisation: Immobilisation) -> dict[int, float]:
    """
    Construit le tableau d'amortissement d'une immobilisation.
    Retourn un dictionnaire avec les années en clé et les dotations en valeur.
    """
    amortissement = {}
    montant = immobilisation["montant"]
    durée = int(immobilisation["durée"])
    taux = 1 / durée
    annuité = montant * taux

    # Pour l'année 1, on amortit au pro rata temporis
    date = time.strptime(immobilisation["date"], "%d/%m/%Y")
    year = date.tm_year
    days_in_year = time.strptime(f"{year}-12-31", "%Y-%m-%d").tm_yday
    days = date.tm_yday
    amortissement[year] = annuité * (days / days_in_year)

    while montant > 0:
        dot = min(annuité, montant)
        montant -= dot
        year += 1
        amortissement[year] = dot

    return amortissement


def load_accounts(accounts: list[Path]) -> list[Account]:
    """
    Charge les comptes depuis les fichiers CSV
    """
    rows: list[Account] = []
    for file in accounts:
        for account in load_csv(file):
            rows.append(
                {
                    "compte": str(account["compte"]),
                    "intitulé": str(account["intitulé"]),
                    "solde": float(account["solde"]),
                }
            )
    return rows


def main():
    args = Arguments().parse_args()

    accounts = load_accounts([args.compte])
    logger.info(f"Chargement des comptes : {len(accounts)}")

    records = ouverture_comptes(accounts, args.annee)
    records += affecter_resultat(accounts, args.annee)
    records += ecrire_notes_de_frais(args.notes_de_frais)
    records += ecrire_banque(args.banque)

    records += ecrire_immobilisations(args.immobilisations, args.annee)

    updated_accounts = update_accounts(accounts, records)
    records += ecrire_cloture_comptes(updated_accounts, args.annee)

    # Export
    with open(args.resultat, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    # Vérification: le solde de tous les comptes (sauf 8) doit être nul
    updated2 = update_accounts(updated_accounts, records)
    for account in updated2:
        if (
            int(account["compte"][0]) < 6
            and account["compte"] not in {"120", "129"}
            and account["solde"] != 0.0
        ):
            logger.warning(f"Compte {account['compte']} non soldé : {account['solde']}")

    # Vérification: le solde du compte 8 doit être égal au résultat
    compte8 = next((a for a in updated2 if a["compte"] == "8"), None)
    resultat = [a for a in updated2 if a["compte"].startswith("12")][-1]
    if compte8 is None:
        logger.warning("Compte 8 non trouvé")
    elif compte8["solde"] != resultat["solde"]:
        logger.warning(
            f"Solde du compte 8 ({compte8['solde']}) différent du résultat ({resultat['solde']})"
        )

    # Vérification: les débits et crédits sont tous positifs:
    for record in records:
        if record["débit"] < 0:
            logger.warning(f"Le débit de {record['débit']} est négatif")
        if record["crédit"] < 0:
            logger.warning(f"Le crédit de {record['crédit']} est négatif")

    # Vérification: les débits et crédits doivent être égaux
    debits = sum(r["débit"] for r in records)
    credits = sum(r["crédit"] for r in records)
    if not isclose(debits, credits):
        logger.warning(f"Les débits ({debits}) et crédits ({credits}) sont différents")


def update_accounts(accounts: list[Account], records: list[Record]) -> list[Account]:
    """
    Met à jour les comptes avec les opérations
    """
    updated_accounts: dict[str, Account] = {}

    for account in accounts:
        updated_accounts[account["compte"]] = {
            "compte": account["compte"],
            "intitulé": account["intitulé"],
            "solde": 0.0,
        }

    for record in records:
        compte = record["compte"]
        if compte not in updated_accounts:
            logger.warning(f"Compte {compte} non trouvé")
            updated_accounts[compte] = {
                "compte": compte,
                "intitulé": f"Compte {compte}",
                "solde": 0.0,
            }
        updated_accounts[compte]["solde"] += record["débit"] - record["crédit"]

    return list(updated_accounts.values())


def ecrire_immobilisations(immo_files, year: int):
    """
    Ecrire les opérations d'immobilisations
    """
    records: list[Record] = []

    immos = load_immobilisations(immo_files)

    for immo in immos:
        if "amortissement" not in immo:
            immo["amortissement"] = build_amortissement(immo)

        # Dotation aux amortissements (on insert un 8 en 2ème position)
        compte_amortissement = f"28{immo['compte'][2:]}"
        records.append(
            {
                "compte": compte_amortissement,
                "date": f"31/12/{year}",
                "libellé": f"Dot. amort.: {immo['intitulé']}",
                "débit": 0.0,
                "crédit": immo["amortissement"][year],
            }
        )
        records.append(
            {
                "compte": "681",
                "date": f"31/12/{year}",
                "libellé": f"Dot. amort.: {immo['intitulé']}",
                "débit": immo["amortissement"][year],
                "crédit": 0.0,
            }
        )

        # Si l'immobilisation est entièrement amortie, on la sort du bilan
        year_debut = time.strptime(immo["date"], "%d/%m/%Y").tm_year
        if year == year_debut + int(immo["durée"]):
            records.append(
                {
                    "date": immo["date"],
                    "compte": compte_amortissement,
                    "libellé": immo["intitulé"],
                    "débit": immo["montant"],
                    "crédit": 0.0,
                }
            )
            records.append(
                {
                    "date": immo["date"],
                    "compte": immo["compte"],
                    "libellé": immo["intitulé"],
                    "débit": 0.0,
                    "crédit": immo["montant"],
                }
            )

    return records


def ecrire_cloture_comptes(accounts: list[Account], year: int):
    """
    Ecrire les opérations de clôture des comptes
    """
    records: list[Record] = []
    resultat = 0.0

    accounts = sorted(accounts, key=lambda a: a["compte"])

    for account in accounts:
        # Skip if solde = 0
        if account["solde"] == 0.0:
            continue

        if account["compte"].startswith("6"):
            resultat -= abs(account["solde"])
            records.append(
                {
                    "date": f"31/12/{year}",
                    "compte": account["compte"],
                    "libellé": f"Fermeture: {account['intitulé']}",
                    "débit": 0.0,
                    "crédit": abs(account["solde"]),
                }
            )

        elif account["compte"].startswith("7"):
            resultat += abs(account["solde"])
            records.append(
                {
                    "date": f"31/12/{year}",
                    "compte": account["compte"],
                    "libellé": f"Fermeture: {account['intitulé']}",
                    "débit": account["solde"],
                    "crédit": 0.0,
                }
            )

        elif account["compte"].startswith("8"):
            continue

        else:
            if account["solde"] > 0:
                debit = account["solde"]
                credit = 0.0
            else:
                debit = 0.0
                credit = abs(account["solde"])

            records.append(
                {
                    "date": f"31/12/{year}",
                    "compte": "891",
                    "libellé": f"Fermeture: {account['intitulé']}",
                    "débit": debit,
                    "crédit": credit,
                }
            )
            records.append(
                {
                    "date": f"31/12/{year}",
                    "compte": account["compte"],
                    "libellé": f"Fermeture: {account['intitulé']}",
                    "débit": credit,
                    "crédit": debit,
                }
            )

    # Ajout du résultat
    if resultat >= 0:
        records.append(
            {
                "date": f"31/12/{year}",
                "compte": "120",
                "libellé": "Résultat de l'exercice",
                "débit": resultat,
                "crédit": 0.0,
            }
        )
    else:
        records.append(
            {
                "date": f"31/12/{year}",
                "compte": "129",
                "libellé": "Résultat de l'exercice",
                "débit": abs(resultat),
                "crédit": 0.0,
            }
        )

    return records


def convert_date(date: str) -> str:
    """
    Convertit la date au format JJ/MM/AAAA
    """
    # Convert date like August 5, 2022
    if "," in date:
        return time.strftime("%d/%m/%Y", time.strptime(date, "%B %d, %Y"))
    if "-" in date:
        return time.strftime("%d/%m/%Y", time.strptime(date, "%Y-%m-%d"))
    if "/" in date:
        return date
    raise ValueError(f"Date {date} not recognized")


def load_operations(operations: list[Path]) -> list[Operation]:
    """
    Charge les opérations depuis les fichiers CSV
    """
    records = []
    for operation in operations:
        for row in load_csv(operation):
            # Discard columns not used
            op: Operation = {
                "date": convert_date(row["date"]),
                "compte": str(row["compte"]),
                "libellé": str(row["libellé"]),
                "ht": float(row["ht"]),
                "tva": float(row["tva"]),
                "ttc": float(row["ttc"]),
            }
            assert isclose(
                abs(op["ht"]) + abs(op["tva"]), abs(op["ttc"])
            ), f"Check op {op['libellé']}"
            records.append(op)

    return records


def ecrire_notes_de_frais(notes_de_frais: list[Path]) -> list[Record]:
    """
    Ecrire les opérations de notes de frais
    """
    records: list[Record] = []

    operations = load_operations(notes_de_frais)

    for op in operations:
        # Add the operation (HT -> 455, TVA -> 445, TTC -> 707)
        records.append(
            {
                "date": op["date"],
                "compte": op["compte"],
                "libellé": op["libellé"],
                "débit": op["ht"],
                "crédit": 0.0,
            }
        )
        records.append(
            {
                "date": op["date"],
                "compte": "445",
                "libellé": op["libellé"],
                "débit": op["tva"],
                "crédit": 0.0,
            }
        )
        records.append(
            {
                "date": op["date"],
                "compte": "455",
                "libellé": op["libellé"],
                "débit": 0.0,
                "crédit": op["ttc"],
            }
        )

    return records


def ecrire_banque(banques: list[Path]) -> list[Record]:
    """
    Ecrire les opérations de ventes, de banque et de notes de frais
    """
    operations = load_operations(banques)
    records: list[Record] = []

    for op in operations:
        # Seperating a sell from an expense
        if op["ttc"] >= 0:
            # Add the operation (HT -> 512, TVA -> 445, TTC -> op["compte"])
            records.append(
                {
                    "date": op["date"],
                    "compte": op["compte"],
                    "libellé": op["libellé"],
                    "débit": op["ht"],
                    "crédit": 0.0,
                }
            )
            records.append(
                {
                    "date": op["date"],
                    "compte": "445",
                    "libellé": op["libellé"],
                    "débit": op["tva"],
                    "crédit": 0.0,
                }
            )
            records.append(
                {
                    "date": op["date"],
                    "compte": "512",
                    "libellé": op["libellé"],
                    "débit": 0.0,
                    "crédit": op["ttc"],
                }
            )
        else:
            # Add the operation (HT -> 512, TVA -> 445, TTC -> op["compte"])
            records.append(
                {
                    "date": op["date"],
                    "compte": op["compte"],
                    "libellé": op["libellé"],
                    "débit": 0.0,
                    "crédit": abs(op["ht"]),
                }
            )
            records.append(
                {
                    "date": op["date"],
                    "compte": "445",
                    "libellé": op["libellé"],
                    "débit": 0.0,
                    "crédit": abs(op["tva"]),
                }
            )
            records.append(
                {
                    "date": op["date"],
                    "compte": "512",
                    "libellé": op["libellé"],
                    "débit": abs(op["ttc"]),
                    "crédit": 0.0,
                }
            )

    return records


def affecter_resultat(accounts, year: int) -> list[Record]:
    """
    Affecter le résultat de l'exercice précédent à l'ouverture de l'exercice
    """

    for account in accounts:
        # Bénéfice
        if account["compte"] == "120":
            return [
                {
                    "date": f"01/01/{year}",
                    "compte": "120",
                    "libellé": "Affection du résultat (bénéfice)",
                    "débit": 0.0,
                    "crédit": account["solde"],
                },
                {
                    "date": f"01/01/{year}",
                    "compte": "110",
                    "libellé": "Affection du résultat (bénéfice)",
                    "débit": account["solde"],
                    "crédit": 0.0,
                },
            ]

        # Perte
        elif account["compte"] == "129":
            return [
                {
                    "date": f"01/01/{year}",
                    "compte": "129",
                    "libellé": "Affection du résultat (perte)",
                    "débit": account["solde"],
                    "crédit": 0.0,
                },
                {
                    "date": f"01/01/{year}",
                    "compte": "119",
                    "libellé": "Affection du résultat (perte)",
                    "débit": 0.0,
                    "crédit": account["solde"],
                },
            ]

    raise ValueError("Impossible d'affecter le résultat")


def ouverture_comptes(accounts: list[Account], year: int) -> list[Record]:
    """
    Ecrire les opérations d'ouverture des comptes
    """
    records: list[Record] = []

    for account in accounts:
        # On débite le compte 890
        records.append(
            {
                "date": f"01/01/{year}",
                "compte": "890",
                "libellé": "Ouverture des comptes",
                "débit": account["solde"],
                "crédit": 0.0,
            }
        )

        # On crédite le compte correspondant
        records.append(
            {
                "date": f"01/01/{year}",
                "compte": account["compte"],
                "libellé": account["intitulé"],
                "débit": 0.0,
                "crédit": account["solde"],
            }
        )

    return records


if __name__ == "__main__":
    main()
