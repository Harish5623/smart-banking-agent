
from banking.database import (
    init_db,
    get_customer,
    save_loan_application,
    get_loan_applications,
)


def main():
    init_db()

    print("\n--- CUSTOMER LOOKUP ---")
    customer = get_customer("CUST001")
    print(customer)
    assert customer is not None

    print("\n--- UNKNOWN CUSTOMER ---")
    assert get_customer("UNKNOWN") is None
    print("Unknown customer correctly handled.")

    print("\n--- SAVE MOCK APPLICATION ---")
    application = save_loan_application(
        customer_id="CUST001",
        loan_amount=500000,
        tenure_years=3,
        monthly_emi=16607.14,
        annual_interest_rate=12.0,
        eligibility_ratio=0.3601,
    )
    print(application)
    assert application["status"] == "SUBMITTED"

    print("\n--- RETRIEVE APPLICATION HISTORY ---")
    history = get_loan_applications("CUST001")
    print(history)
    assert any(
        item["application_id"] == application["application_id"]
        for item in history
    )

    print("\nAll database tests passed!")


if __name__ == "__main__":
    main()
