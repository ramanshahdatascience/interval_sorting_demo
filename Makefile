# Pipeline to prepare the data for Tableau

pdfs = $(wildcard ./downloads/*.pdf)

all: ./transformed/incident_rates.csv

./transformed/incident_rates.csv: ./transformed/populations.csv ./transformed/incidents.csv
	python compute_incident_rates.py

./transformed/populations.csv: ./downloads/townest.xlsx
	python clean_populations.py

./transformed/incidents.csv: $(pdfs)
	python clean_incidents.py $^

.PHONY: clean veryclean download download_populations download_pdfs
download: download_populations download_pdfs

download_populations:
	curl http://www.dlt.ri.gov/lmi/excel/townest.xlsx > ./downloads/townest.xlsx

download_pdfs:
	curl https://health.ri.gov/data/drugoverdoses/ > ./downloads/overdose_index.html
	./get_pdfs.sh

clean:
	find ./transformed -mindepth 1 | grep -v 'README' | xargs rm -r
veryclean: clean
	find ./downloads -mindepth 1 | grep -v 'README' | xargs rm -r
