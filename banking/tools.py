
from math import isfinite
from banking.database import (
    init_db,
    get_customer,
    save_loan_application,
    get_loan_applications,
)


# Illustrative project policies, not real bank lending rules.
DEFAULT_ANNUAL_INTEREST_RATE = 12.0
MAX_EMI_TO_INCOME_RATIO = 0.40


# Temporary mock data. We will move this into SQLite in Phase 3.
MOCK_ACCOUNTS = {
    "CUST001": {
        "customer_id": "CUST001",
        "name": "Demo Customer",
        "account_number": "XXXXXX1234",
        "account_type": "Savings",
        "balance": 75000.00,
    }
}


def calculate_emi(
    loan_amount: float,
    tenure_years: int,
    annual_interest_rate: float = DEFAULT_ANNUAL_INTEREST_RATE,
) -> dict:
    """Calculate EMI, total repayment and total interest."""

    values = (loan_amount, annual_interest_rate)

    if not all(isfinite(v) for v in values):
        return {"error": "Financial inputs must be finite numbers."}

    if loan_amount <= 0 or tenure_years <= 0:
        return {"error": "Loan amount and tenure must be positive."}

    if not isinstance(tenure_years, int) or isinstance(tenure_years, bool):
        return {"error": "Tenure must be a whole number of years."}

    if tenure_years > 40:
        return {"error": "Tenure exceeds the project's 40-year limit."}

    if annual_interest_rate < 0 or annual_interest_rate > 100:
        return {"error": "Interest rate must be between 0 and 100%."}

    months = tenure_years * 12
    monthly_rate = annual_interest_rate / 1200

    if monthly_rate == 0:
        emi = loan_amount / months
    else:
        factor = (1 + monthly_rate) ** months
        emi = loan_amount * monthly_rate * factor / (factor - 1)

    total_repayment = emi * months

    return {
        "loan_amount": round(loan_amount, 2),
        "tenure_years": tenure_years,
        "tenure_months": months,
        "annual_interest_rate_percent": annual_interest_rate,
        "monthly_emi": round(emi, 2),
        "total_repayment": round(total_repayment, 2),
        "total_interest": round(total_repayment - loan_amount, 2),
    }


def check_loan_eligibility(
    monthly_salary: float,
    existing_emi: float,
    proposed_emi: float,
) -> dict:
    """Apply an illustrative EMI-to-income eligibility rule."""

    values = (monthly_salary, existing_emi, proposed_emi)

    if not all(isfinite(v) for v in values):
        return {"error": "Financial inputs must be finite numbers."}

    if monthly_salary <= 0:
        return {"error": "Monthly salary must be positive."}

    if existing_emi < 0 or proposed_emi < 0:
        return {"error": "EMI amounts cannot be negative."}

    total_emi = existing_emi + proposed_emi
    ratio = total_emi / monthly_salary
    eligible = ratio <= MAX_EMI_TO_INCOME_RATIO

    return {
        "eligible": eligible,
        "monthly_salary": round(monthly_salary, 2),
        "existing_emi": round(existing_emi, 2),
        "proposed_emi": round(proposed_emi, 2),
        "total_monthly_emi": round(total_emi, 2),
        "emi_to_income_ratio_percent": round(ratio * 100, 2),
        "maximum_allowed_ratio_percent": 40.0,
        "reason": (
            "Passes the illustrative EMI-to-income rule."
            if eligible
            else "Exceeds the illustrative EMI-to-income limit."
        ),
    }


def get_account_details(customer_id: str) -> dict:
    """Retrieve account details from SQLite."""

    init_db()
    account = get_customer(customer_id)

    if account is None:
        return {"error": "Customer not found."}

    return account



def submit_loan_application(
    customer_id: str,
    loan_amount: float,
    tenure_years: int,
    monthly_emi: float,
    customer_confirmed: bool = False,
    eligibility_approved: bool = False,
    annual_interest_rate: float = DEFAULT_ANNUAL_INTEREST_RATE,
    eligibility_ratio: float = 0.0,
) -> dict:
    """Save a mock application only after confirmation and eligibility."""

    if customer_confirmed is not True:
        return {
            "status": "NOT_SUBMITTED",
            "reason": "Explicit customer confirmation is required.",
        }

    if eligibility_approved is not True:
        return {
            "status": "NOT_SUBMITTED",
            "reason": "The eligibility check must pass first.",
        }

    if not get_account_details(customer_id).get("customer_id"):
        return {
            "status": "ERROR",
            "reason": "Customer not found.",
        }

    if (
        not all(
            isfinite(v)
            for v in (
                loan_amount,
                monthly_emi,
                annual_interest_rate,
                eligibility_ratio,
            )
        )
        or loan_amount <= 0
        or monthly_emi <= 0
        or annual_interest_rate < 0
        or eligibility_ratio < 0
        or eligibility_ratio > 0.40
        or not isinstance(tenure_years, int)
        or isinstance(tenure_years, bool)
        or tenure_years <= 0
    ):
        return {
            "status": "ERROR",
            "reason": "Invalid application or eligibility details.",
        }

    init_db()

    application = save_loan_application(
        customer_id=customer_id,
        loan_amount=loan_amount,
        tenure_years=tenure_years,
        monthly_emi=monthly_emi,
        annual_interest_rate=annual_interest_rate,
        eligibility_ratio=eligibility_ratio,
    )

    return {
        **application,
        "message": "Mock application saved successfully.",
    }

