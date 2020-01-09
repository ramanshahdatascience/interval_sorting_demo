#! /bin/bash

grep 'Overdose.pdf' downloads/overdose_index.html \
	| sort -u \
	| sed -e 's|.*datareports/||' -e 's|pdf.*|pdf|' \
	| while read filename
do
	curl https://health.ri.gov/publications/datareports/${filename} \
		> downloads/${filename}
done
