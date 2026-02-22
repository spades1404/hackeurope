"""Test the search query builder on the first 10 rows of the transactions CSV."""

import csv
import sys
import time
from pathlib import Path

# Make sure imports resolve from the till/ directory
sys.path.insert(0, str(Path(__file__).parent))

from search_query_builder import build_search_query

CSV_PATH = Path(__file__).parent / "test_data" / "transactions.csv"


def main():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [row for _, row in zip(range(5), reader)]

    print(f"Testing search query builder on {len(rows)} transactions\n")
    print("=" * 80)

    for i, row in enumerate(rows, 1):
        date = row["Transaction Date (Local)"]
        amount = float(row["Total Amount (incl. VAT)"])
        counterparty = row["Counterparty Name"]
        iban = row["Counterparty IBAN"] or None
        currency = row["Currency"] or "EUR"

        print(f"\n[{i}] {counterparty}")
        print(f"    Date: {date}  Amount: {currency} {amount:,.2f}  IBAN: {iban}")

        result = build_search_query(
            transaction_date=date,
            amount=amount,
            currency=currency,
            counterparty_name=counterparty,
            iban=iban,
        )

        print(f"    Query:     {result['query']}")
        print(f"    Reasoning: {result['reasoning']}")

        time.sleep(6)  # stay under 10 RPM free-tier limit

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
