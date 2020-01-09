# Pipeline to prepare the data for Tableau

./transformed/population.csv:
	python clean_populations.py

./downloads/townest.xlsx:
	curl http://www.dlt.ri.gov/lmi/excel/townest.xlsx > ./downloads/townest.xlsx

./downloads/overdose_index.html:
	curl https://health.ri.gov/data/drugoverdoses/ > ./downloads/overdose_index.html

.PHONY: clean veryclean download
download: ./downloads/townest.xlsx ./downloads/overdose_index.html
	./get_pdfs.sh

clean:
	find ./transformed -mindepth 1 | grep -v 'README' | xargs rm -r
veryclean: clean
	find ./downloads -mindepth 1 | grep -v 'README' | xargs rm -r
