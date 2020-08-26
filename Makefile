# Pipeline to prepare the data for Tableau

pdfs = $(wildcard ./downloads/*.pdf)

analysis: ./transformed/incident_rates.csv

./transformed/incident_rates.csv: ./transformed/populations.csv ./transformed/incidents.csv compute_incident_rates.py
	python compute_incident_rates.py

./transformed/populations.csv: ./downloads/townest.xlsx clean_populations.py
	python clean_populations.py

./transformed/incidents.csv: $(pdfs) clean_incidents.py
	python clean_incidents.py $^

.PHONY: clean_analysis clean_downloads download download_populations download_pdfs
download: download_populations download_pdfs

download_populations:
	curl http://www.dlt.ri.gov/lmi/excel/townest.xlsx > ./downloads/townest.xlsx

download_pdfs: get_pdfs.sh
	curl https://health.ri.gov/data/drugoverdoses/ > ./downloads/overdose_index.html
	./get_pdfs.sh

clean_analysis:
	find ./transformed -mindepth 1 | grep -v 'README' | xargs rm -r
clean_downloads: clean_analysis
	find ./downloads -mindepth 1 | grep -v 'README' | xargs rm -r
