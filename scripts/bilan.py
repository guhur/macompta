"""
Calcule la synthèse d'un bilan comptable sous la forme d'un tableau de l'actif puis d'un tableau du passif.

Exemple de fichier de sortie:
,ACTIF,,,,,,Exercice N,,Exercice N-1
,,,,,,Brut,Amortissements et provisions,Net,Net
,ACTIF IMMOBILISE,,,,,,,,
,Immobilisations incorporelles,,,,,€0.00,€0.00,€0.00,€0.00
,Immobilisations corporelles:,,,,,,,,
,211,Terrains,,,,"€18,285.00",€0.00,"€18,285.00","€18,285.00"
,213,Constructions,,,,"€110,694.00","€18,568.03","€92,125.97","€95,815.77"
,Immobilisations financières,,,,,€0.00,€0.00,€0.00,€0.00
,,,,Total I,,"€128,979.00","€18,568.03","€110,410.97","€114,100.77"
,ACTIF CIRCULANT,,,,,,,,
,Stocks et en-cours :,,,,,,,,
,,Matières premières et autres approvisionnements,,,,€0.00,€0.00,€0.00,€0.00
,,En cours de production,,,,€0.00,€0.00,€0.00,€0.00
,,Produits intermédiaires et finis,,,,€0.00,€0.00,€0.00,€0.00
,,Marchandises,,,,€0.00,€0.00,€0.00,€0.00
,Avances et acomptes versés sur commandes,,,,,€0.00,€0.00,€0.00,€0.00
,Créances :,,,,,,,,
,,Créances clients et comptes rattachés,,,,€0.00,€0.00,€0.00,€0.00
,,Autres,,,,€0.00,€0.00,€0.00,€0.00
,,"Capital souscrit - appelé, non versé",,,,€0.00,€0.00,€0.00,€0.00
,Valeurs mobilières de placement :,,,,,,,,
,,Actions propres,,,,€0.00,€0.00,€0.00,€0.00
,,Autres titres,,,,€0.00,€0.00,€0.00,€0.00
,Instruments de trésorerie,,,,,€0.00,€0.00,€0.00,€0.00
,Disponibilités,,,,,€0.00,€0.00,€0.00,€0.00
,Charges constatées d'avance,,,,,€0.00,€0.00,€0.00,€0.00
,,,,Total II,,€0.00,€0.00,€0.00,€0.00
,Charges à répartir sur plusieurs exercices (III),,,,,€0.00,€0.00,€0.00,€0.00
,Primes de remboursement des emprunts (IV),,,,,€0.00,,€0.00,€0.00
,Ecarts de conversion Actif (V),,,,,€0.00,,€0.00,€0.00
,,,TOTAL GENERAL,,,"€128,979.00","€18,568.03","€110,410.97","€114,100.77"
,,,,,,,,,
,PASSIF,,,,Exercice N,Exercice N-1,,,
,,,,,Net,Net,,,
,CAPITAUX PROPRES,,,,,,,,
,108,Compte d'exploitant,,,#REF!,"€12,131.93",,,
,,Ecart de réévaluation,,,,,,,
,,Réserve légale,,,€0.00,€0.00,,,
,,Réserves réglementées,,,€0.00,€0.00,,,
,,Autres,,,,,,,
,,Report à nouveau,,,€0.00,€0.00,,,
,,Résultat de l'exercice,,,"€1,474.90","€1,224.40",,,
,,Provisions réglementées,,,€0.00,€0.00,,,
,,,Total I,,#REF!,"€13,356.33",,,
,PROVISIONS POUR RISQUES ET CHARGES,,,,€0.00,€0.00,,,
,,,Total II,,€0.00,€0.00,,,
,DETTES,,,,,,,,
,164,Emprunts et dettes assimilées,,,"€95,204.53","€100,744.44",,,
,,Avances et acomptes reçues sur commandes en cours,,,€0.00,€0.00,,,
,,Dettes Fournisseurs et Comptes rattachés,,,€0.00,€0.00,,,
,,Autres dettes,,,€0.00,€0.00,,,
,Produits constatés d'avance,,,,€0.00,€0.00,,,
,,,Total III,,"€95,204.53","€100,744.44",,,
,Ecarts de conversion passif (IV),,,,€0.00,€0.00,,,
,,,TOTAL GENERAL,,#REF!,"€114,100.77",,,
"""
from pathlib import Path
import tap
from macompta import (
    Account,
    load_accounts,
    load_journals,
    update_accounts,
    filter_records_by_account,
    Record,
)


class Arguments(tap.Tap):
    """
    Arguments de la ligne de commande.
    """

    journals: list[Path]
    comptes: list[Path]
    annee: int
    output: Path


def main():
    """
    Point d'entrée du programme.
    """
    args = Arguments().parse_args()
    print(args)

    # Lire les journaux
    journals = load_journals(args.journals)

    # et les comptes
    compte = load_accounts(args.comptes)
    compte = update_accounts(compte, journals)

    ecrire_header(args.output, args.annee)
    ecrire_actif(journals, args.output)
    ecrire_passif(compte, args.output)


def ecrire_header(output: Path, annee: int):
    """
    Ecrit l'en-tête du bilan.
    """
    with open(output, "w") as fid:
        fid.write(",,,,,,,,,\n")
        fid.write(",Bilan comptable,,,,,,,,\n")
        fid.write(f"1.1.{annee} - 31.12.{annee}\n")
        fid.write(",,,,,,,,,\n")


def ecrire_actif(records: list[Record], output: Path):
    """
    Ecrit l'actif du bilan.
    """
    with open(output, "a") as fid:
        fid.write(",,Exercice N,,Exercice N-1\n")
        fid.write("ACTIF,,,,\n")
        fid.write("ACTIF IMMOBILISE,,,,\n")

    ecrire_actif_immobilise(records, output)


def ecrire_actif_immobilise(records: list[Record], output: Path):
    with open(output, "a") as fid:
        fid.write("ACTIF IMMOBILISE,,,,\n")

    # Calcul les totaux des immobilisations incorporelles (comptes 20x)
    # - exercice N: brut, amortissements & provisions, net
    # - exercice N-1: net
    # Puis affiche les lignes correspondantes
    immo_incorporelles = filter_records_by_account(records, "20")
    amort_incorporelles = filter_records_by_account(records, "280")
    prov_incorporelles = filter_records_by_account(records, "281")
    brut_n = sum(
        [record["débit"] - record["crédit"] for record in immo_incorporelles]
    )
    amort_n = sum(
        [record["débit"] - record["crédit"] for record in amort_incorporelles]
    )
    prov_n = sum(
        [record["débit"] - record["crédit"] for record in prov_incorporelles]
    )
    net_n = brut_n - amort_n - prov_n

    with open(output, "a") as fid:
        fid.write(
            f"Immobilisations incorporelles,{brut_n},{amort_n+prov_n},{net_n}\n"
        )
    # fid.write(",,,,,\n")
    # fid.write("Frais d'établissement,,,,,,,,,\n")
    # fid.write(",,,,,,,,,\n")
    # fid.write("Frais de recherche et de développement,,,,,,,,,\n")
    # fid.write(",,,,,,,,,\n")
    # fid.write(
    #     "Concessions, brevets, licences, marques, droits et valeurs similaires,,,,,,,,,\n"
    # )
    # fid.write(",,,,,,,,,\n")
    # fid.write("Fonds commercial,,,,,,,,,\n")
    # fid.write(",,,,,,,,,\n")
    # fid.write("Autres immobilisations incorporelles,,,,,,,,,\n")
    # fid.write(",,,,,,,,,\n")
    # fid.write("Immobilisations corporelles,,,,,,,,,\n")
    # fid.write(",,,,,,,,,\n")
    # fid.write("Terrains,,,,,,,,,\n")
    # fid.write(",,,,,,,,,\n")
    # fid.write("Constructions,,,,,,,,,\n")
    # fid.write(",,,,,,,,,\n")
    # fid.write("Immobilisations financières,,,,,,,,,\n")
    # fid.write(",,,,,,,,,\n")
