# Project Notes

These are my working notes for the Invoice & Payment Analysis project: definitions, formulas, worked examples and the decisions I made. The README gives the overview; this file gives the detail behind it.

All data is fictional. Amounts are in Kenya Shillings (KES).

## 1. How the dataset was created

I chose these four things by hand for each of the 20 invoices:

- the customer
- the invoice date
- the subtotal (a simple, round figure so the arithmetic is easy to follow)
- how much the customer has paid so far

Everything else was calculated from those choices:

| Calculated column | Formula |
|---|---|
| `due_date` | `invoice_date` + 30 days |
| `vat` | `subtotal` × 16% |
| `total_amount` | `subtotal` + `vat` |
| `outstanding_balance` | `total_amount` − `amount_paid` |
| `payment_status` | Paid / Unpaid / Partially Paid (see below) |
| `days_overdue` | `analysis date` − `due_date`, never below 0 |
| `aging_category` | bucket based on `days_overdue` |

I then wrote the analysis script so that it **recalculates these columns independently** and compares them with the CSV. That way the file is checked, not just trusted.

I deliberately built a mix of situations into the data: fully paid invoices, part-payments, invoices with nothing paid, invoices at every aging stage, and one invoice due exactly on the analysis date.

## 2. Column definitions

| Column | Type | Definition |
|---|---|---|
| `invoice_number` | text | Unique reference for the invoice |
| `customer_name` | text | Fictional customer being billed |
| `invoice_date` | date | When the invoice was issued |
| `due_date` | date | Last day the customer can pay without being late |
| `subtotal` | KES | Value of goods/services before VAT |
| `vat` | KES | Value Added Tax charged, 16% of subtotal |
| `total_amount` | KES | What the customer is asked to pay: subtotal + VAT |
| `amount_paid` | KES | Total payments received to date against this invoice |
| `outstanding_balance` | KES | Still owed: total amount − amount paid |
| `payment_status` | text | Paid, Partially Paid or Unpaid |
| `days_overdue` | days | Days past the due date at 30 June 2026 |
| `aging_category` | text | Aging bucket (Paid, Current, 1-30 days, 31-60 days, 61-90 days, 90+ days) |

## 3. Rules used

**Payment status**

| Condition | Status |
|---|---|
| Outstanding balance = 0 | Paid |
| Amount paid = 0 | Unpaid |
| Anything else | Partially Paid |

**Days overdue**

- If the invoice has no balance, days overdue is 0 (it is settled).
- Otherwise days overdue = 30 June 2026 − due date.
- If the due date is still in the future, the answer would be negative, so it is set to 0.

**Aging category**

| Days overdue | Category |
|---|---|
| (balance is 0) | Paid |
| 0 | Current |
| 1 to 30 | 1-30 days |
| 31 to 60 | 31-60 days |
| 61 to 90 | 61-90 days |
| 91 or more | 90+ days |

**Overdue vs unpaid** are not the same thing. *Unpaid* means nothing has been paid. *Overdue* means the due date has passed and some balance remains. An invoice can be unpaid but not overdue (INV-2026-018, INV-2026-020), and a partly paid invoice can be overdue (INV-2026-003).

## 4. Worked examples (checked by hand)

**INV-2026-003 (Nyota Print Works): partially paid, 90+ days**

- Subtotal 80,000; VAT 80,000 × 0.16 = 12,800; total 92,800
- Paid 50,000, so outstanding = 92,800 − 50,000 = 42,800
- Invoice date 20 Jan 2026, so due date = 19 Feb 2026
- Days from 19 Feb to 30 Jun: 9 (rest of Feb) + 31 (Mar) + 30 (Apr) + 31 (May) + 30 (Jun) = 131
- 131 is more than 90, so category = 90+ days

**INV-2026-011 (Zuri Logistics Ltd): partially paid, 31-60 days**

- Subtotal 150,000; VAT 24,000; total 174,000
- Paid 100,000, so outstanding = 74,000
- Due date 10 May 2026. Days to 30 Jun: 21 (rest of May) + 30 (Jun) = 51
- 51 falls in 31-60 days

**INV-2026-017 (Zuri Logistics Ltd): unpaid, Current (edge case)**

- Subtotal 85,000; VAT 13,600; total 98,600; nothing paid, so outstanding = 98,600
- Invoice date 31 May 2026, so due date = 30 Jun 2026, which is the analysis date
- Days overdue = 0, so the invoice is Current. It is due today but not yet late.

## 5. Assumptions

- Analysis date is fixed at **30 June 2026**.
- Payment terms are **30 days** for every customer.
- VAT is **16%** on every invoice.
- `amount_paid` is the total received to date. Payment dates are not recorded.
- A due date equal to the analysis date is treated as **not yet overdue**.
- Paid invoices are excluded from the aging summary.
- "Total invoiced" and monthly figures **include VAT**.

## 6. Decisions I made and why

- **Fixed analysis date.** Using today's date would change days overdue and aging every day, so the results could not be reproduced or checked.
- **A "Paid" aging category.** Fully paid invoices have no balance, so putting them in an aging bucket would be misleading. The aging summary only uses invoices that still have a balance.
- **Plain hyphens in category names** (`1-30 days`, not `1–30 days`). Plain characters avoid encoding problems when a CSV is opened in different programs.
- **Whole-shilling figures.** Subtotals were chosen so that 16% VAT comes out as a whole number, which keeps every calculation exact and easy to verify.
- **Validation before analysis.** The script stops if any check fails.
- **Simple charts.** Plain bar charts with value labels, because the goal is to communicate the numbers clearly.

## 7. Things I would want a finance professional to review

- Whether it is right to show "invoiced" amounts including VAT, or whether the business would report revenue excluding VAT.
- Whether 30/60/90-day buckets suit the type of business.
- Whether a collection rate that includes not-yet-due invoices is the right headline measure. I added a second version that only includes invoices already due.
- How partial payments should be allocated when a customer pays several invoices at once (not covered here, since each invoice has one total paid figure).

## 8. Known limitations

See the README for the full list. The main ones are: tiny fictional dataset, no payment dates, one analysis date only, and no credit notes or bad debt provisions.
