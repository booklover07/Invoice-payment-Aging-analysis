"""
Invoice & Payment Analysis
--------------------------
A small learning project using FICTIONAL invoice data (amounts in KES).

What this script does:
    1. Loads the invoice data from invoice_data.csv
    2. Checks that the numbers are internally consistent (validation)
    3. Calculates headline figures (invoiced, collected, outstanding, collection rate)
    4. Summarises invoices by payment status and by days overdue
    5. Builds an accounts-receivable aging summary
    6. Summarises outstanding balances by customer
    7. Summarises invoicing by month
    8. Saves three simple charts as PNG files

Run it with:   python invoice_analysis.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# ---------------------------------------------------------------------------
# 1. SETTINGS
# ---------------------------------------------------------------------------

# Folder where this script lives, so the files are found no matter where I run it from
BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "invoice_data.csv"

# A FIXED date is used instead of today's date so the results never change.
ANALYSIS_DATE = pd.Timestamp("2026-06-30")

VAT_RATE = 0.16          # Kenya standard VAT rate, used for the dataset
PAYMENT_TERMS_DAYS = 30  # every invoice is "due 30 days after invoice date"

# The order I want the aging buckets to appear in (tables and chart)
AGING_ORDER = ["Current", "1-30 days", "31-60 days", "61-90 days", "90+ days"]


def kes(amount):
    """Format a number as KES with thousands separators, e.g. KES 1,234,567"""
    return f"KES {amount:,.0f}"


def print_heading(text):
    """Print a section heading so the output is easy to read."""
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


# ---------------------------------------------------------------------------
# 2. LOAD THE DATA
# ---------------------------------------------------------------------------

# parse_dates tells pandas to treat these two columns as dates, not plain text.
df = pd.read_csv(DATA_FILE, parse_dates=["invoice_date", "due_date"])

print_heading("DATA LOADED")
print(f"Invoices loaded : {len(df)}")
print(f"Analysis date   : {ANALYSIS_DATE.date()}")


# ---------------------------------------------------------------------------
# 3. VALIDATION - are the numbers consistent?
# ---------------------------------------------------------------------------
# I recalculate the key columns myself and compare them with what is in the CSV.
# Each check gives True (every row passes) or False (at least one row fails).

# (a) Days overdue: only invoices that still have a balance can be overdue.
#     If the due date is in the future the result is negative, so I clip it to 0.
days_past_due = (ANALYSIS_DATE - df["due_date"]).dt.days
recalc_days_overdue = np.where(df["outstanding_balance"] > 0,
                               days_past_due.clip(lower=0),
                               0)


# (b) Aging category: a simple function that looks at one invoice at a time.
def get_aging_category(balance, days_overdue):
    if balance == 0:
        return "Paid"            # nothing owed, so aging does not apply
    if days_overdue == 0:
        return "Current"         # owed, but not late yet
    if days_overdue <= 30:
        return "1-30 days"
    if days_overdue <= 60:
        return "31-60 days"
    if days_overdue <= 90:
        return "61-90 days"
    return "90+ days"


recalc_aging = [get_aging_category(b, d)
                for b, d in zip(df["outstanding_balance"], recalc_days_overdue)]

# (c) Payment status: Paid / Unpaid / Partially Paid.
#     np.select checks the conditions in order and uses the first one that is true.
recalc_status = np.select(
    [df["outstanding_balance"] == 0, df["amount_paid"] == 0],
    ["Paid", "Unpaid"],
    default="Partially Paid",
)

checks = {
    "Subtotal + VAT = Total invoice amount":
        (df["subtotal"] + df["vat"] == df["total_amount"]).all(),
    "VAT = 16% of subtotal":
        np.isclose(df["subtotal"] * VAT_RATE, df["vat"]).all(),
    "Total invoice amount - Amount paid = Outstanding balance":
        (df["total_amount"] - df["amount_paid"] == df["outstanding_balance"]).all(),
    "No invoice has been paid more than its total":
        (df["amount_paid"] <= df["total_amount"]).all(),
    "Due date = invoice date + 30 days":
        ((df["due_date"] - df["invoice_date"]).dt.days == PAYMENT_TERMS_DAYS).all(),
    "Invoice numbers are unique":
        df["invoice_number"].is_unique,
    "Payment status matches the amounts":
        (df["payment_status"] == recalc_status).all(),
    "Days overdue matches my recalculation":
        (df["days_overdue"] == recalc_days_overdue).all(),
    "Aging category matches my recalculation":
        (df["aging_category"] == recalc_aging).all(),
}

print_heading("VALIDATION CHECKS")
for name, passed in checks.items():
    print(f"[{'PASS' if passed else 'FAIL'}] {name}")

if not all(checks.values()):
    raise SystemExit("\nValidation failed - fix the data before trusting any results.")
print("\nAll checks passed.")


# ---------------------------------------------------------------------------
# 4. HEADLINE FIGURES
# ---------------------------------------------------------------------------
total_invoiced = df["total_amount"].sum()
total_collected = df["amount_paid"].sum()
total_outstanding = df["outstanding_balance"].sum()

# Collection rate = money received as a percentage of money invoiced
collection_rate = total_collected / total_invoiced * 100

print_heading("HEADLINE FIGURES (VAT-inclusive)")
print(f"Total amount invoiced    : {kes(total_invoiced)}")
print(f"Total amount collected   : {kes(total_collected)}")
print(f"Total outstanding balance: {kes(total_outstanding)}")
print(f"Collection rate          : {collection_rate:.1f}%")

# A second, fairer view: only count invoices whose due date has already arrived.
# Customers are not expected to have paid invoices that are not due yet.
due_so_far = df[df["due_date"] <= ANALYSIS_DATE]
collection_rate_due = due_so_far["amount_paid"].sum() / due_so_far["total_amount"].sum() * 100
print(f"Collection rate (only invoices already due): {collection_rate_due:.1f}% "
      f"({len(due_so_far)} of {len(df)} invoices)")

# Cross-check: what was invoiced should equal what was collected plus what is still owed
assert total_invoiced == total_collected + total_outstanding


# ---------------------------------------------------------------------------
# 5. PAYMENT STATUS AND DAYS OVERDUE
# ---------------------------------------------------------------------------
status_summary = df.groupby("payment_status").agg(
    invoices=("invoice_number", "count"),
    total_invoiced=("total_amount", "sum"),
    collected=("amount_paid", "sum"),
    outstanding=("outstanding_balance", "sum"),
)

print_heading("INVOICES BY PAYMENT STATUS")
print(status_summary.to_string())

# Overdue = still has a balance AND the due date has passed (days_overdue > 0)
overdue = df[df["days_overdue"] > 0].sort_values("days_overdue", ascending=False)

print_heading("OVERDUE INVOICES (past due date, balance still owing)")
print(overdue[["invoice_number", "customer_name", "due_date", "payment_status",
               "outstanding_balance", "days_overdue"]].to_string(index=False))
print(f"\nNumber of overdue invoices : {len(overdue)}")
print(f"Overdue balance            : {kes(overdue['outstanding_balance'].sum())}"
      f" ({overdue['outstanding_balance'].sum() / total_outstanding * 100:.1f}% of outstanding)")
print(f"Average days overdue       : {overdue['days_overdue'].mean():.0f}")
print(f"Longest overdue            : {overdue['days_overdue'].max()} days")

# Invoices that are unpaid but NOT yet late - they are not a problem yet
unpaid_not_due = df[(df["payment_status"] == "Unpaid") & (df["days_overdue"] == 0)]
print(f"Unpaid but not yet overdue : {len(unpaid_not_due)} invoices, "
      f"{kes(unpaid_not_due['outstanding_balance'].sum())}")


# ---------------------------------------------------------------------------
# 6. ACCOUNTS-RECEIVABLE AGING
# ---------------------------------------------------------------------------
# Only invoices with a balance belong in the aging report (paid ones are excluded).
open_invoices = df[df["outstanding_balance"] > 0]

aging = open_invoices.groupby("aging_category").agg(
    invoices=("invoice_number", "count"),
    outstanding=("outstanding_balance", "sum"),
)
# reindex puts the buckets in the right order and adds a 0 row if a bucket is empty
aging = aging.reindex(AGING_ORDER, fill_value=0)
aging["share_of_outstanding_%"] = (aging["outstanding"] / total_outstanding * 100).round(1)

print_heading("ACCOUNTS-RECEIVABLE AGING (open invoices only)")
print(aging.to_string())
print(f"\nTotal: {aging['invoices'].sum()} invoices, {kes(aging['outstanding'].sum())}")


# ---------------------------------------------------------------------------
# 7. OUTSTANDING BALANCE BY CUSTOMER
# ---------------------------------------------------------------------------
by_customer = df.groupby("customer_name").agg(
    invoices=("invoice_number", "count"),
    total_invoiced=("total_amount", "sum"),
    collected=("amount_paid", "sum"),
    outstanding=("outstanding_balance", "sum"),
    oldest_days_overdue=("days_overdue", "max"),
)
by_customer["share_of_outstanding_%"] = (by_customer["outstanding"] / total_outstanding * 100).round(1)
by_customer = by_customer.sort_values("outstanding", ascending=False)

print_heading("OUTSTANDING BALANCE BY CUSTOMER")
print(by_customer.to_string())


# ---------------------------------------------------------------------------
# 8. MONTHLY INVOICED AMOUNTS
# ---------------------------------------------------------------------------
# Turn each invoice date into a month (e.g. 2026-03) so invoices can be grouped by month
df["invoice_month"] = df["invoice_date"].dt.to_period("M")

monthly = df.groupby("invoice_month").agg(
    invoices=("invoice_number", "count"),
    subtotal=("subtotal", "sum"),
    vat=("vat", "sum"),
    total_invoiced=("total_amount", "sum"),
)

print_heading("MONTHLY INVOICED AMOUNTS")
print(monthly.to_string())
print(f"\nAverage per month: {kes(monthly['total_invoiced'].mean())}")


# ---------------------------------------------------------------------------
# 9. CHARTS
# ---------------------------------------------------------------------------
# Shared helper: shows y-axis numbers as 100,000 instead of 100000 (or 1e5)
thousands = FuncFormatter(lambda value, _: f"{value:,.0f}")
BAR_COLOUR = "#2F5D8C"


def add_value_labels(ax, bars, horizontal=False):
    """Write each bar's value next to the bar."""
    for bar in bars:
        if horizontal:
            value = bar.get_width()
            ax.text(value, bar.get_y() + bar.get_height() / 2,
                    f" {value:,.0f}", va="center", ha="left", fontsize=9)
        else:
            value = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, value,
                    f"{value:,.0f}", ha="center", va="bottom", fontsize=9)


# Chart 1: outstanding balance by aging category
fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(aging.index, aging["outstanding"], color=BAR_COLOUR)
add_value_labels(ax, bars)
ax.set_title("Outstanding Balance by Aging Category\nAs at 30 June 2026 (fictional data)")
ax.set_xlabel("Aging category (days past due date)")
ax.set_ylabel("Outstanding balance (KES)")
ax.yaxis.set_major_formatter(thousands)
ax.set_ylim(0, aging["outstanding"].max() * 1.15)   # a little room for the labels
plt.tight_layout()
plt.savefig(BASE_DIR / "aging_analysis.png", dpi=150)
plt.close()

# Chart 2: monthly invoiced amount
fig, ax = plt.subplots(figsize=(8, 5))
month_labels = monthly.index.strftime("%b %Y")
bars = ax.bar(month_labels, monthly["total_invoiced"], color=BAR_COLOUR)
add_value_labels(ax, bars)
ax.set_title("Monthly Invoiced Amount (VAT-inclusive)\nJan - Jun 2026 (fictional data)")
ax.set_xlabel("Invoice month")
ax.set_ylabel("Total invoiced (KES)")
ax.yaxis.set_major_formatter(thousands)
ax.set_ylim(0, monthly["total_invoiced"].max() * 1.15)
plt.tight_layout()
plt.savefig(BASE_DIR / "monthly_invoicing.png", dpi=150)
plt.close()

# Chart 3 (optional): outstanding balance by customer, customers that owe money only
owing = by_customer[by_customer["outstanding"] > 0].sort_values("outstanding")  # smallest first
fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.barh(owing.index, owing["outstanding"], color=BAR_COLOUR)
add_value_labels(ax, bars, horizontal=True)
ax.set_title("Outstanding Balance by Customer\nAs at 30 June 2026 (fictional data)")
ax.set_xlabel("Outstanding balance (KES)")
ax.xaxis.set_major_formatter(thousands)
ax.set_xlim(0, owing["outstanding"].max() * 1.18)
plt.tight_layout()
plt.savefig(BASE_DIR / "customer_outstanding.png", dpi=150)
plt.close()

print_heading("DONE")
print("Charts saved: aging_analysis.png, monthly_invoicing.png, customer_outstanding.png")
