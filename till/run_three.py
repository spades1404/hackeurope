"""Run the end-to-end reconciliation workflow for the first 3 transactions.

Prints intermediate results from the search query builder and matching engine.
"""

import csv
import logging
import sys
from datetime import date
from pathlib import Path

# Verbose logging so agent internals are visible
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
)

# Monkey-patch search_query_builder and matching_engine BEFORE importing agent
import search_query_builder as sqb
import matching_engine as me

_orig_build_search_query = sqb.build_search_query
_orig_score_match = me.score_match


def _patched_build_search_query(**kwargs):
    result = _orig_build_search_query(**kwargs)
    print("\n" + "─" * 60)
    print("  SEARCH QUERY BUILDER OUTPUT")
    print(f"  Query    : {result['query']}")
    print(f"  Reasoning: {result.get('reasoning', 'N/A')}")
    print("─" * 60)
    return result


def _patched_score_match(transaction, invoice):
    proposal = _orig_score_match(transaction, invoice)
    print("\n" + "─" * 60)
    print("  MATCHING ENGINE — EXTRACTED INVOICE")
    print(f"  invoice_number   : {invoice.invoice_number}")
    print(f"  invoice_date     : {invoice.invoice_date}")
    print(f"  due_date         : {invoice.due_date}")
    print(f"  vendor_name      : {invoice.vendor_name}")
    print(f"  vendor_iban      : {invoice.vendor_iban}")
    print(f"  vendor_address   : {invoice.vendor_address}")
    print(f"  vendor_tax_id    : {invoice.vendor_tax_id}")
    print(f"  buyer_name       : {invoice.buyer_name}")
    print(f"  net_amount       : {invoice.net_amount}")
    print(f"  vat_rate         : {invoice.vat_rate}")
    print(f"  vat_amount       : {invoice.vat_amount}")
    print(f"  gross_amount     : {invoice.gross_amount}")
    print(f"  payment_ref      : {invoice.payment_reference}")
    if invoice.line_items:
        print(f"  line_items       : {invoice.line_items}")
    print()
    print(f"  TRANSACTION")
    print(f"  id               : {transaction.id}")
    print(f"  counterparty     : {transaction.counterparty_name}")
    print(f"  amount           : {transaction.amount}  {transaction.currency}")
    print(f"  date             : {transaction.date}")
    print(f"  iban             : {transaction.counterparty_iban}")
    print(f"  reference        : {transaction.reference}")
    print()
    print(f"  RESULT: confidence={proposal.confidence_score:.3f}  →  {proposal.status.value.upper()}")
    print(f"  amount={proposal.amount_match} | vendor={proposal.vendor_match} | "
          f"date={proposal.date_match} | iban={proposal.iban_match} | ref={proposal.reference_match}")
    for r in proposal.match_reasons:
        print(f"    ✓ {r}")
    print("─" * 60)
    return proposal


sqb.build_search_query = _patched_build_search_query
me.score_match = _patched_score_match

# Now import the agent (it will pick up the patched functions)
from reconciliation_agent import reconcile_transaction
from schemas import Transaction


def load_first_n_transactions(csv_path: Path, n: int) -> list[Transaction]:
    transactions = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        sample = f.read(2048); f.seek(0)
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
        reader = csv.DictReader(f, delimiter=delimiter)
        for i, row in enumerate(reader):
            if i >= n:
                break
            # Amount: debit = outgoing (negative), credit = incoming (positive)
            debit = row["Debit"].strip()
            credit = row["Credit"].strip()
            if debit:
                amount = -float(debit)
            elif credit:
                amount = float(credit)
            else:
                amount = 0.0

            txn = Transaction(
                id=row["Transaction ID"].strip(),
                date=date.fromisoformat(row["Transaction Date (Local)"].strip()),
                amount=amount,
                currency=row["Currency"].strip(),
                counterparty_name=row["Counterparty Name"].strip(),
                counterparty_iban=row["Counterparty IBAN"].strip() or None,
                reference=row["Reference"].strip() or None,
            )
            transactions.append(txn)
    return transactions


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else None
    csv_file = sys.argv[2] if len(sys.argv) > 2 else "500_transactions.csv"
    csv_path = Path(__file__).parent / "test_data" / csv_file
    transactions = load_first_n_transactions(csv_path, n or 10_000)

    total = len(transactions)
    print(f"\n{'═' * 60}")
    print(f"  Loaded {total} transactions from {csv_path.name}")
    print(f"{'═' * 60}\n")

    results = []
    counters = {"matched": 0, "needs_review": 0, "no_match": 0, "error": 0}

    for i, txn in enumerate(transactions, 1):
        print(f"\n{'─' * 60}")
        print(f"  [{i}/{total}] {txn.id} | {txn.counterparty_name} | {txn.amount:+.2f} {txn.currency}")
        print(f"{'─' * 60}")

        result = reconcile_transaction(txn)
        results.append(result)
        counters[result.status] = counters.get(result.status, 0) + 1

        conf = f"{result.match_proposal.confidence_score:.3f}" if result.match_proposal else "N/A"
        print(f"  → {result.status.upper():<12} confidence={conf}  emails={result.emails_found}")
        if result.error:
            print(f"  ! Error: {result.error}")

        # Progress summary every 10 transactions
        if i % 10 == 0:
            pct = i / total * 100
            print(f"\n  ── PROGRESS {i}/{total} ({pct:.0f}%) ──")
            print(f"     Matched:      {counters['matched']}")
            print(f"     Needs review: {counters['needs_review']}")
            print(f"     No match:     {counters['no_match']}")
            print(f"     Errors:       {counters['error']}")
            match_rate = (counters['matched'] + counters['needs_review']) / i * 100
            print(f"     Match rate:   {match_rate:.1f}%")

    # Final summary
    matched_results = [r for r in results if r.status == "matched"]
    avg_conf = (
        sum(r.match_proposal.confidence_score for r in matched_results) / len(matched_results)
        if matched_results else 0
    )
    match_rate = (counters["matched"] + counters["needs_review"]) / total * 100

    print(f"\n{'═' * 60}")
    print(f"  FINAL SUMMARY — {total} transactions")
    print(f"{'═' * 60}")
    print(f"  Matched:          {counters['matched']:>4}  ({counters['matched']/total*100:.1f}%)")
    print(f"  Needs review:     {counters['needs_review']:>4}  ({counters['needs_review']/total*100:.1f}%)")
    print(f"  No match:         {counters['no_match']:>4}  ({counters['no_match']/total*100:.1f}%)")
    print(f"  Errors:           {counters['error']:>4}  ({counters['error']/total*100:.1f}%)")
    print(f"  ──────────────────────────────")
    print(f"  Overall match rate: {match_rate:.1f}%")
    print(f"  Avg confidence (matched): {avg_conf:.3f}")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    main()