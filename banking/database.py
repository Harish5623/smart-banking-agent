
import sqlite3
from pathlib import Path


# Keep the database location independent of the terminal's working folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "banking.db"


def get_connection():
    """Open a SQLite connection with safe defaults."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def init_db():
    """Create database tables and seed a demo customer."""

    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                account_number TEXT NOT NULL,
                account_type TEXT NOT NULL,
                balance REAL NOT NULL CHECK (balance >= 0)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS loan_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id TEXT UNIQUE,
                customer_id TEXT NOT NULL,
                loan_amount REAL NOT NULL CHECK (loan_amount > 0),
                tenure_years INTEGER NOT NULL CHECK (tenure_years > 0),
                monthly_emi REAL NOT NULL CHECK (monthly_emi > 0),
                annual_interest_rate REAL NOT NULL,
                eligibility_ratio REAL NOT NULL,
                status TEXT NOT NULL
                    CHECK (status IN ('SUBMITTED')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id)
                    REFERENCES customers(customer_id)
            )
        """)

        # Seed only if this demo customer doesn't already exist.
        conn.execute("""
            INSERT OR IGNORE INTO customers (
                customer_id, name, account_number,
                account_type, balance
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            "CUST001",
            "Demo Customer",
            "XXXXXX1234",
            "Savings",
            75000.00,
        ))


def get_customer(customer_id: str) -> dict | None:
    """Fetch one customer's mock account details."""

    with get_connection() as conn:
        row = conn.execute("""
            SELECT customer_id, name, account_number,
                   account_type, balance
            FROM customers
            WHERE customer_id = ?
        """, (customer_id,)).fetchone()

    return dict(row) if row else None


def save_loan_application(
    customer_id: str,
    loan_amount: float,
    tenure_years: int,
    monthly_emi: float,
    annual_interest_rate: float,
    eligibility_ratio: float,
) -> dict:
    """Persist an eligible, explicitly confirmed application."""

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO loan_applications (
                customer_id,
                loan_amount,
                tenure_years,
                monthly_emi,
                annual_interest_rate,
                eligibility_ratio,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, 'SUBMITTED')
        """, (
            customer_id,
            loan_amount,
            tenure_years,
            monthly_emi,
            annual_interest_rate,
            eligibility_ratio,
        ))

        row_id = cursor.lastrowid
        application_id = f"MOCK-LOAN-{row_id:06d}"

        conn.execute("""
            UPDATE loan_applications
            SET application_id = ?
            WHERE id = ?
        """, (application_id, row_id))

    return {
        "application_id": application_id,
        "customer_id": customer_id,
        "loan_amount": round(loan_amount, 2),
        "tenure_years": tenure_years,
        "monthly_emi": round(monthly_emi, 2),
        "status": "SUBMITTED",
    }


def get_loan_applications(customer_id: str) -> list[dict]:
    """Retrieve saved applications for a customer."""

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT application_id, customer_id, loan_amount,
                   tenure_years, monthly_emi,
                   annual_interest_rate, eligibility_ratio,
                   status, created_at
            FROM loan_applications
            WHERE customer_id = ?
            ORDER BY id DESC
        """, (customer_id,)).fetchall()

    return [dict(row) for row in rows]


if __name__ == "__main__":
    init_db()
    print("Database initialized:", DB_PATH)
    print("Demo customer:", get_customer("CUST001"))
