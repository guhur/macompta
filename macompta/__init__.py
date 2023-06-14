import typing as t
from math import isclose
import logging
import time
import csv
from pathlib import Path
from .utils import convert_date


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


def is_immo_corporelle(immobilisation: Immobilisation) -> bool:
    """
    Retourne True si l'immobilisation est corporelle
    """
    if immobilisation["compte"].startswith("21"):
        return True
    return False


def update_immobilisations(
    immobilisations: list[Immobilisation], records: list[Record]
):
    """
    Mise à jour des immobilisations selon les opérations
    """
    updated_immobilisations: dict[str, Immobilisation] = {}

    for immobilisation in immobilisations:
        updated_immobilisations[immobilisation["compte"]] = immobilisation

    for record in records:
        compte = record["compte"]
        if compte in updated_immobilisations:
            updated_immobilisations[compte]["montant"] += record["débit"]
            updated_immobilisations[compte]["montant"] -= record["crédit"]

    return list(updated_immobilisations.values())


def filter_records_by_account(records: list[Record], account: str) -> list[Record]:
    """
    Retourne les opérations du compte
    """
    return [r for r in records if r["compte"] == account]
