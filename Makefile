

# Install project with poetry
install:
	poetry install


# Run scripts
journal:
	poetry run python scripts/livre-journal.py \
		--notes_de_frais data/note-de-frais.csv \
		--compte data/compte.csv \
		--banques data/banque.csv \
		--immobilisations data/immobilisations.csv \
		--resultat data/livre-journal.csv \
		--annee 2022

immobilisations:
	poetry run python scripts/immobilisations.py \
	        --immobilisations data/immobilisations.csv \
		--annee 2022 \
		--journals data/livre-journal.csv \
		--compte data/compte.csv \
		--output data/immobilisations-2022.csv

amortissements:
	poetry run python scripts/amortissements.py \
	        --immobilisations data/immobilisations.csv \
		--annee 2022 \
		--journals data/livre-journal.csv \
		--compte data/compte.csv \
		--output data/amortissements-2022.csv


grand-livre:
	poetry run python scripts/grand-livre.py \
		--annee 2022 \
		--journals data/livre-journal.csv \
		--compte data/compte.csv \
		--output data/grand-livre-2022.csv

balance-comptes:
	poetry run python scripts/balance-comptes.py \
		--annee 2022 \
		--journals data/livre-journal.csv \
		--compte data/compte.csv \
		--output data/balance-comptes-2022.csv

bilan:
	poetry run python scripts/bilan.py \
		--annee 2022 \
		--journals data/livre-journal.csv \
		--compte data/compte.csv \
		--output data/bilan-2022.csv
