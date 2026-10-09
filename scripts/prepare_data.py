"""Prepare USAspending contract transaction data for the Power BI model.

Reads every Contracts_PrimeTransactions*.csv in Data/Raw (USAspending splits large
downloads into _1, _2, ...), keeps only the columns the semantic model uses, and writes
one slim CSV to Data/Processed. Power BI's staging query reads that file, so refreshes
parse a much smaller file instead of the full 297-column extract.

Usage (from the project root):
    python scripts/prepare_data.py

Standard library only - no packages to install.
"""
import csv
import glob
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, 'Data', 'Raw')
OUT_DIR = os.path.join(ROOT, 'Data', 'Processed')
OUT_FILE = os.path.join(OUT_DIR, 'contract_transactions.csv')

# Must match SelectedColumns in stg_ContractTransactions (expressions.tmdl).
# Not exported: award-level running totals (never summed), funding agency (future dimension),
# action_date_fiscal_year (DimDate derives it) and usaspending_permalink (rebuilt from the award key).
COLUMNS = [
    'contract_transaction_unique_key', 'contract_award_unique_key', 'award_id_piid',
    'modification_number', 'parent_award_id_piid',
    'federal_action_obligation',
    'action_date',
    'period_of_performance_start_date', 'period_of_performance_current_end_date',
    'awarding_agency_code', 'awarding_agency_name',
    'awarding_sub_agency_code', 'awarding_sub_agency_name',
    'awarding_office_code', 'awarding_office_name',
    'recipient_uei', 'recipient_name', 'recipient_parent_uei', 'recipient_parent_name',
    'recipient_city_name', 'recipient_state_code',
    'primary_place_of_performance_state_code', 'primary_place_of_performance_state_name',
    'primary_place_of_performance_country_code', 'primary_place_of_performance_country_name',
    'naics_code', 'naics_description',
    'product_or_service_code', 'product_or_service_code_description',
    'award_type_code', 'award_type',
    'type_of_contract_pricing_code', 'type_of_contract_pricing',
    'extent_competed_code', 'extent_competed',
    'type_of_set_aside_code', 'type_of_set_aside',
    'contracting_officers_determination_of_business_size_code',
    'contracting_officers_determination_of_business_size',
    'number_of_offers_received',
    'action_type_code', 'action_type',
    'transaction_description', 'last_modified_date',
]


def main():
    files = sorted(glob.glob(os.path.join(RAW_DIR, 'Contracts_PrimeTransactions*.csv')))
    if not files:
        sys.exit(f'No Contracts_PrimeTransactions*.csv files found in {RAW_DIR}')

    os.makedirs(OUT_DIR, exist_ok=True)
    tmp_file = OUT_FILE + '.tmp'
    start = time.time()
    rows = 0
    keys = set()

    with open(tmp_file, 'w', encoding='utf-8', newline='') as out:
        writer = csv.writer(out)
        writer.writerow(COLUMNS)
        for path in files:
            with open(path, encoding='utf-8-sig', newline='') as f:
                reader = csv.reader(f)
                header = next(reader)
                missing = [c for c in COLUMNS if c not in header]
                if missing:
                    sys.exit(f'{os.path.basename(path)} is missing columns: {missing}')
                idx = [header.index(c) for c in COLUMNS]
                key_idx = header.index('contract_transaction_unique_key')
                file_rows = 0
                for row in reader:
                    # Split downloads can overlap at file boundaries; keep the first occurrence
                    if row[key_idx] in keys:
                        continue
                    keys.add(row[key_idx])
                    writer.writerow([row[i] for i in idx])
                    file_rows += 1
            rows += file_rows
            print(f'{os.path.basename(path)}: {file_rows:,} rows')

    os.replace(tmp_file, OUT_FILE)
    size_mb = os.path.getsize(OUT_FILE) / 1048576
    print(f'Wrote {OUT_FILE}: {rows:,} rows, {len(COLUMNS)} columns, {size_mb:,.1f} MB '
          f'in {time.time() - start:,.0f}s')


if __name__ == '__main__':
    main()
