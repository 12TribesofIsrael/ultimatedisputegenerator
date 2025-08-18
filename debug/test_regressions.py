#!/usr/bin/env python3
"""Regression checks to prevent reintroducing known bugs.

Run: python test_regressions.py
Exits with non-zero code on failure.
"""

from extract_account_details import (
    merge_accounts_by_key,
    create_deletion_dispute_letter,
    get_bureau_addresses,
)


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def test_discover_alias_and_masking() -> None:
    # Two aliases should merge into one tradeline
    accounts = [
        {
            "creditor": "DISCOVER",
            "account_number": "601101XXXXXX",
            "balance": "$4,946",
            "status": "Charge off",
            "negative_items": ["Charge off"],
        },
        {
            "creditor": "DISCOVER CARD",
            "account_number": "601101XXXXXX",
            "balance": "$4,946",
            "status": "Charge off",
            "negative_items": ["Charge off"],
        },
    ]

    merged = merge_accounts_by_key(accounts)
    assert_true(len(merged) == 1, f"Expected DISCOVER aliases to merge; got {len(merged)} entries")

    # Letter must preserve report-masked account number verbatim
    bureau = get_bureau_addresses()["Equifax"]
    letter = create_deletion_dispute_letter(merged, "Test User", bureau, round_number=1, consumer_address_lines=["123 Main St", "City, ST 00000"])  # type: ignore
    assert_true("601101XXXXXX" in letter, "Masked account number not preserved in letter for DISCOVER")


def test_full_number_is_masked_to_last4() -> None:
    accounts = [
        {
            "creditor": "AMERICAN EXPRESS",
            "account_number": "3499929444639913",
            "balance": "$100",
            "status": "Charge off",
            "negative_items": ["Charge off"],
        }
    ]
    bureau = get_bureau_addresses()["Experian"]
    letter = create_deletion_dispute_letter(accounts, "Test User", bureau, round_number=1, consumer_address_lines=["123 Main St"])  # type: ignore
    assert_true("XXXX-XXXX-XXXX-9913" in letter, "Full numbers must be masked to last4 in letters")


if __name__ == "__main__":
    test_discover_alias_and_masking()
    test_full_number_is_masked_to_last4()
    print("OK: regressions guarded")


