
import json

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_ollama import ChatOllama

from banking.tools import (
    calculate_emi,
    check_loan_eligibility,
    get_account_details,
)


@tool
def calculate_loan_emi(
    loan_amount: float,
    tenure_years: int,
    annual_interest_rate: float = 12.0,
) -> str:
    """Calculate the monthly EMI, total interest and repayment
    for a proposed loan. Amounts are in Indian rupees."""

    result = calculate_emi(
        loan_amount=loan_amount,
        tenure_years=tenure_years,
        annual_interest_rate=annual_interest_rate,
    )
    return json.dumps(result)


@tool
def assess_loan_eligibility(
    monthly_salary: float,
    existing_emi: float,
    proposed_loan_amount: float,
    tenure_years: int,
    annual_interest_rate: float = 12.0,
) -> str:
    """Assess loan eligibility using the illustrative 40 percent
    EMI-to-income rule. Calculate the proposed EMI first."""

    emi_result = calculate_emi(
        loan_amount=proposed_loan_amount,
        tenure_years=tenure_years,
        annual_interest_rate=annual_interest_rate,
    )

    if "error" in emi_result:
        return json.dumps({"error": emi_result["error"]})

    result = check_loan_eligibility(
        monthly_salary=monthly_salary,
        existing_emi=existing_emi,
        proposed_emi=emi_result["monthly_emi"],
    )

    return json.dumps({
        "emi_calculation": emi_result,
        "eligibility_assessment": result,
        "policy_note": (
            "Illustrative demo policy only; not a real bank approval."
        ),
    })


@tool
def retrieve_account_details(customer_id: str) -> str:
    """Retrieve mock account details using a supplied customer ID.
    Do not guess or invent a customer ID."""

    result = get_account_details(customer_id)
    return json.dumps(result)


SYSTEM_PROMPT = """
You are a helpful Smart Banking Support Agent for a simulated bank.

Rules:
1. Use the banking tools for calculations, eligibility assessments,
   and account lookups. Never invent tool results.
2. Ask for missing information when necessary.
3. A customer ID is required for account lookup. Never guess one.
4. The demo interest rate is 12 percent per year unless another
   rate is explicitly supplied.
5. Eligibility uses an illustrative 40 percent EMI-to-income limit.
   This is not an actual bank lending policy or final loan approval.
6. Report rupee amounts clearly and summarize the tool results.
7. Never claim that an application has been submitted when it has not.
8. You cannot submit loan applications. Explain that submission
   requires the customer to review the details and explicitly confirm
   through the banking interface.
9. Do not ask customers to share passwords, PINs, or OTPs.
10. The proposed loan EMI is separate from the customer's existing EMI.
11. Total monthly debt commitments equal proposed EMI plus existing EMI.
12. Never describe the existing EMI as part of the proposed loan EMI.
13. Eligibility passing the demo rule is not final bank approval.
"""

model = ChatOllama(
    model="llama3.2:3b",
    temperature=0,
)

agent = create_agent(
    model=model,
    tools=[
        calculate_loan_emi,
        assess_loan_eligibility,
        retrieve_account_details,
    ],
    system_prompt=SYSTEM_PROMPT,
)


def ask_banking_agent(message: str) -> str:
    """Send a customer message to the single banking agent."""

    result = agent.invoke({
        "messages": [
            {"role": "user", "content": message}
        ]
    })

    # The final assistant message contains the consolidated response.
    for item in reversed(result["messages"]):
        if getattr(item, "type", None) == "ai":
            if not getattr(item, "tool_calls", None):
                return item.content

    return "I couldn't generate a final response. Please try again."


if __name__ == "__main__":
    print("Smart Banking Agent is ready.")
    print("Type 'exit' to stop.\n")

    while True:
        user_message = input("Customer: ").strip()

        if user_message.lower() in {"exit", "quit"}:
            break

        if not user_message:
            continue

        try:
            response = ask_banking_agent(user_message)
            print("\nBanking Agent:", response, "\n")
        except Exception as exc:
            print("\nAgent error:", exc, "\n")
