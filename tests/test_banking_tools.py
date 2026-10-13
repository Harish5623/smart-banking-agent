
from banking.tools import (
    calculate_emi,
    check_loan_eligibility,
    get_account_details,
    submit_loan_application,
)


def main():
    print("\n--- 1. EMI CALCULATION ---")
    loan = calculate_emi(500000, 3)
    print(loan)

    assert "monthly_emi" in loan
    assert round(loan["monthly_emi"]) == 16607

    print("\n--- 2. ELIGIBILITY CHECK ---")
    eligibility = check_loan_eligibility(
        monthly_salary=60000,
        existing_emi=5000,
        proposed_emi=loan["monthly_emi"],
    )
    print(eligibility)

    assert eligibility["eligible"] is True

    print("\n--- 3. ACCOUNT LOOKUP ---")
    account = get_account_details("CUST001")
    print(account)

    assert account["customer_id"] == "CUST001"
    assert get_account_details("UNKNOWN")["error"]

    print("\n--- 4. CONFIRMATION GATE ---")
    blocked = submit_loan_application(
        "CUST001", 500000, 3, loan["monthly_emi"]
    )
    print(blocked)

    assert blocked["status"] == "NOT_SUBMITTED"

    print("\n--- 5. MOCK SUBMISSION TEST ---")
    # This is a test fixture, not a real customer confirmation.
    submitted = submit_loan_application(
        "CUST001",
        500000,
        3,
        loan["monthly_emi"],
        customer_confirmed=True,
    )
    print(submitted)

    assert submitted["status"] == "SUBMITTED"

    print("\nAll banking tool tests passed!")


if __name__ == "__main__":
    main()
