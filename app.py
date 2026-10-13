
import streamlit as st

from banking.agent import ask_banking_agent
from banking.database import init_db, get_loan_applications
from banking.tools import (
    calculate_emi,
    check_loan_eligibility,
    get_account_details,
    submit_loan_application,
)

init_db()

st.set_page_config(
    page_title="Smart Banking Support Agent",
    page_icon="🏦",
    layout="wide",
)

st.title("🏦 Smart Banking Support Agent")
st.caption("Educational demo using simulated banking data.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pending_application" not in st.session_state:
    st.session_state.pending_application = None

if "submission_result" not in st.session_state:
    st.session_state.submission_result = None


# -------------------- AI CHAT --------------------

st.header("1. Banking Assistant")

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_message = st.chat_input("Ask a banking question")

if user_message:
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_message,
    })

    with st.chat_message("user"):
        st.markdown(user_message)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = ask_banking_agent(user_message)
            except Exception:
                response = (
                    "The assistant is temporarily unavailable. "
                    "Please check Ollama and try again."
                )

        st.markdown(response)

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": response,
    })


# -------------------- LOAN APPLICATION --------------------

st.divider()
st.header("2. Personal Loan Application")
st.info(
    "Demo policy: 12% annual interest and a maximum "
    "40% EMI-to-income ratio. This is not a real bank approval."
)

with st.form("loan_details_form"):
    customer_id = st.text_input(
        "Demo customer ID",
        value="CUST001",
    )
    loan_amount = st.number_input(
        "Loan amount (₹)",
        min_value=1000,
        max_value=5000000,
        value=500000,
        step=10000,
    )
    tenure_years = st.selectbox(
        "Tenure (years)",
        options=[1, 2, 3, 4, 5],
        index=2,
    )
    monthly_salary = st.number_input(
        "Monthly salary (₹)",
        min_value=1,
        value=60000,
        step=1000,
    )
    existing_emi = st.number_input(
        "Existing monthly EMI (₹)",
        min_value=0,
        value=5000,
        step=500,
    )

    calculate_button = st.form_submit_button(
        "Calculate and Check Eligibility"
    )

if calculate_button:
    account = get_account_details(customer_id.strip())

    if "error" in account:
        st.error("Customer not found. Use a valid demo customer ID.")
        st.session_state.pending_application = None
    else:
        emi_result = calculate_emi(
            float(loan_amount),
            int(tenure_years),
            12.0,
        )

        eligibility = check_loan_eligibility(
            float(monthly_salary),
            float(existing_emi),
            emi_result["monthly_emi"],
        )

        st.session_state.pending_application = None
        st.session_state.submission_result = None

        if "error" in eligibility:
            st.error(eligibility["error"])
        else:
            st.session_state.pending_application = {
                "customer_id": customer_id.strip(),
                "loan_amount": float(loan_amount),
                "tenure_years": int(tenure_years),
                "monthly_salary": float(monthly_salary),
                "existing_emi": float(existing_emi),
                "emi_result": emi_result,
                "eligibility": eligibility,
            }


pending = st.session_state.pending_application

if pending:
    emi = pending["emi_result"]
    eligibility = pending["eligibility"]

    st.subheader("Review Your Loan Details")

    c1, c2, c3 = st.columns(3)
    c1.metric("Proposed monthly EMI", f"₹{emi['monthly_emi']:,.2f}")
    c2.metric("Existing EMI", f"₹{pending['existing_emi']:,.2f}")
    c3.metric("Total monthly EMI", f"₹{eligibility['total_monthly_emi']:,.2f}")

    st.write(f"**Loan amount:** ₹{pending['loan_amount']:,.2f}")
    st.write(f"**Tenure:** {pending['tenure_years']} years")
    st.write("**Annual interest rate:** 12% (illustrative)")
    st.write(f"**Total interest:** ₹{emi['total_interest']:,.2f}")
    st.write(
        f"**EMI-to-income ratio:** "
        f"{eligibility['emi_to_income_ratio_percent']:.2f}%"
    )

    if eligibility["eligible"]:
        st.success(
            "Passes the illustrative eligibility rule. "
            "This is not a bank's final approval."
        )

        st.warning(
            "Review all details before confirming. "
            "Confirmation will save a mock application to SQLite."
        )

        with st.form("confirmation_form"):
            confirmed = st.checkbox(
                "I have reviewed these details and confirm "
                "submission of this simulated loan application."
            )
            submit_button = st.form_submit_button(
                "Confirm and Submit Application"
            )

        if submit_button:
            if not confirmed:
                st.error("Please confirm the application before submission.")
            else:
                # Recalculate on the server using the reviewed values.
                verified_emi = calculate_emi(
                    pending["loan_amount"],
                    pending["tenure_years"],
                    12.0,
                )
                verified_eligibility = check_loan_eligibility(
                    pending["monthly_salary"],
                    pending["existing_emi"],
                    verified_emi["monthly_emi"],
                )

                if not verified_eligibility.get("eligible", False):
                    st.error("Eligibility verification failed.")
                else:
                    result = submit_loan_application(
                        customer_id=pending["customer_id"],
                        loan_amount=pending["loan_amount"],
                        tenure_years=pending["tenure_years"],
                        monthly_emi=verified_emi["monthly_emi"],
                        customer_confirmed=True,
                        eligibility_approved=True,
                        annual_interest_rate=12.0,
                        eligibility_ratio=(
                            verified_eligibility[
                                "emi_to_income_ratio_percent"
                            ] / 100
                        ),
                    )

                    st.session_state.submission_result = result
                    st.session_state.pending_application = None
                    st.rerun()
    else:
        st.error(
            "This application does not pass the illustrative "
            "eligibility rule and cannot be submitted."
        )

result = st.session_state.submission_result

if result:
    if result.get("status") == "SUBMITTED":
        st.success("Mock loan application submitted successfully!")
        st.write(f"**Application ID:** {result['application_id']}")
        st.write(f"**Status:** {result['status']}")
    else:
        st.error(result.get("reason", "Application was not submitted."))


# -------------------- APPLICATION HISTORY --------------------

st.divider()
st.header("3. Application History")

history_customer_id = st.text_input(
    "Customer ID for history",
    value="CUST001",
    key="history_customer_id",
)

if st.button("View Saved Applications"):
    account = get_account_details(history_customer_id.strip())

    if "error" in account:
        st.error("Customer not found.")
    else:
        applications = get_loan_applications(
            history_customer_id.strip()
        )

        if applications:
            st.dataframe(applications, use_container_width=True)
        else:
            st.info("No saved applications for this customer.")
