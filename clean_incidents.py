#! /usr/bin/env python


import csv
import fitz
from sys import argv

COLS_IN_TABLE = 11

with open('./transformed/incidents.csv', 'w', newline='') as csvfile:
    fieldnames = ['municipality', 'incidents']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for pdf_file in argv[1:]:
        report = fitz.open(pdf_file)
        # Table 9: Accidental Drug Overdose Deaths by Location and Year, 2009 -
        # 2018 is found on the 14th page of the report (labeled 13 because the
        # cover page is not paginated).
        page = report.loadPage(13)
        lines = page.getText("text").split('\n')

        # In the below, we find Table 9 and use the fact that PyMuPDF parses these data
        # tables as a rectangular list of cells, left to right, then top to bottom, to
        # find the 2018 total incidents in the given muncipality.
        # print('\n'.join(s for s in text.split() if 'Table' in s))
        table_start = next((i for (i, s) in enumerate(lines) if 'Table 9' in s), None)

        result = {'municipality': lines[table_start + 1].strip()}
        # Check that the table conforms to our expectation (want this to fail loudly if
        # the number of columns changes in re-use of this data pipeline)
        assert 'Resident Count' in lines[table_start + 1 + COLS_IN_TABLE]
        assert 'Incident Count' in lines[table_start + 1 + 2 * COLS_IN_TABLE]
        result['incidents'] = lines[table_start + 1 + 3 * COLS_IN_TABLE - 1].strip()

        writer.writerow(result)
