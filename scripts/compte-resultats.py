import typing as t
import os
from pathlib import Path
import pandas as pd
import tempfile
import tap


class CompteResultats(t.TypedDict):
    revenues: pd.DataFrame
    expenses: pd.DataFrame
    net_income: float


def display_amount(x: float) -> str:
    return f"{x:.2f} €"


def display_libelle(x: str) -> str:
    return (
        x.replace("&", "\\&")
        .replace("%", "\\%")
        .replace("_", "\\_")
        .replace("#", "\\#")
    )


def prepare_financial_statements(filename: Path) -> CompteResultats:
    # Load the data
    data = pd.read_csv(filename)

    # Rename the columns
    data.columns = data.iloc[0]

    # Drop the first row
    data = data[1:]

    # Convert 'N de compte' to string type to handle it properly
    data["N de compte"] = data["N de compte"].astype(str)

    # Define the sales and purchases
    sales: pd.DataFrame = data[data["N de compte"].str.startswith("7")]
    purchases: pd.DataFrame = data[data["N de compte"].str.startswith("6")]

    # Remove the '€' symbol and thousands separator, and convert to numeric
    sales["Débit"] = (
        sales["Débit"].replace({"€": "", ",": ""}, regex=True).astype(float)
    )
    sales["Crédit"] = (
        sales["Crédit"].replace({"€": "", ",": ""}, regex=True).astype(float)
    )
    purchases["Débit"] = (
        purchases["Débit"]
        .replace({"€": "", ",": ""}, regex=True)
        .astype(float)
    )
    purchases["Crédit"] = (
        purchases["Crédit"]
        .replace({"€": "", ",": ""}, regex=True)
        .astype(float)
    )

    # Calculate total sales and purchases
    total_sales = sales["Crédit"].sum() - sales["Débit"].sum()
    total_purchases = purchases["Débit"].sum() - purchases["Crédit"].sum()

    # Prepare the result
    result: CompteResultats = {
        "revenues": sales,
        "expenses": purchases,
        "net_income": float(total_sales - total_purchases),
    }

    return result


def export_to_latex(compte_resultats: CompteResultats, output: Path):
    # Write header and preambule
    with open(output, "w") as f:
        f.write("\\documentclass{article}\n")
        f.write("\\usepackage[utf8]{inputenc}\n")
        f.write("\\usepackage{booktabs}\n")
        f.write("\\usepackage{longtable}\n")
        f.write("\\usepackage{geometry}\n")
        f.write(
            "\\geometry{a4paper, total={170mm,257mm}, left=20mm, top=20mm}\n"
        )
        f.write("\\title{Compte de Résultats}\n")
        f.write("\\date{\\today}\n")
        f.write("\\begin{document}\n")

    # Write the revenues
    with open(output, "a") as f:
        f.write("\\section{Revenues}\n")
        f.write("\\begin{tabular}{l|c|c|c|c}\n")
        f.write("\\hline\n")
        f.write("Compte & Libellé & Crédit & Débit & Solde \\\\\n")
        f.write("\\hline\n")
        for index, row in compte_resultats["revenues"].iterrows():
            solde = display_amount(row["Crédit"] - row["Débit"])
            debit_str = display_amount(float(row["Débit"]))
            credit_str = display_amount(float(row["Crédit"]))
            libelle = display_libelle(str(row["Libellé"]))
            f.write(
                f"{row['N de compte']} & {libelle} & {credit_str} "
                f"& {debit_str} & {solde} \\\\\n"
            )
        f.write("\\hline\n")
        f.write("\\end{tabular}\n")

    # Write the expenses
    with open(output, "a") as f:
        f.write("\\section{Dépenses}\n")
        f.write("\\begin{tabular}{l|c|c|c|c}\n")
        f.write("\\hline\n")
        f.write("Compte & Libellé & Crédit & Débit & Solde \\\\\n")
        f.write("\\hline\n")
        for index, row in compte_resultats["expenses"].iterrows():
            solde = display_amount(row["Débit"] - row["Crédit"])
            debit_str = display_amount(float(row["Débit"]))
            credit_str = display_amount(float(row["Crédit"]))
            libelle = display_libelle(str(row["Libellé"]))
            f.write(
                f"{row['N de compte']} & {libelle} & {credit_str}"
                f"& {debit_str} & {solde} \\\\\n"
            )
        f.write("\\hline\n")
        f.write("\\end{tabular}\n")

    # Write the total and net income
    with open(output, "a") as f:
        total = display_amount(
            compte_resultats["revenues"]["Crédit"].sum()
            - compte_resultats["expenses"]["Débit"].sum()
        )
        net_income = display_amount(compte_resultats["net_income"])
        f.write("\\section{Total et Résultat Net}\n")
        f.write("\\begin{tabular}{l|c}\n")
        f.write("\\hline\n")
        f.write(f"Total & {total} \\\\\n")
        f.write("\\hline\n")
        f.write(f"Résultat Net & {net_income} \\\\\n")
        f.write("\\hline\n")
        f.write("\\end{tabular}\n")

    # Write the footer
    with open(output, "a") as f:
        f.write("\\end{document}\n")


class Arguments(tap.Tap):
    journal: Path
    output: Path


if __name__ == "__main__":
    args = Arguments().parse_args()

    compte_resultats = prepare_financial_statements(args.journal)

    if args.output.suffix == ".tex":
        export_to_latex(compte_resultats, args.output)

    elif args.output.suffix == ".pdf":
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(str(tmpdir))
            tmp_tex = tmp / "compte-resultats.tex"
            tmp_pdf = tmp / "compte-resultats.pdf"
            export_to_latex(compte_resultats, tmp_tex)
            os.system(f"pdflatex -output-directory {tmp} {tmp_tex} -quiet")
            tmp_pdf.rename(args.output)

    else:
        raise ValueError("Invalid output format")
