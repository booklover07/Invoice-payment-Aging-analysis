# Invoice & Payment Analysis

A small personal learning project where I use Python to analyse a set of **fictional** invoices and answer basic accounts-receivable questions: how much was invoiced, how much has been paid, who still owes money, and how late those payments are.

> **All data in this project is made up.** The customers, invoices and amounts are fictional and do not come from any real company, employer or client. Any resemblance to real businesses is a coincidence.

## Why I built this

I studied Economics and Finance and have worked with financial records, payment documentation and record keeping in accounts and administration roles. I am now learning data analytics with Python. I wanted a project that connects the two: taking something I understand from finance (invoices, VAT, payments, overdue balances) and practising how to analyse it with code.

This is a beginner project. It is meant to show that I understand the basic ideas and can turn them into working, checkable calculations, not that I have built a production system.

## What is in this repository

```
invoice-payment-analysis/
├── README.md                 <- this file
├── invoice_data.csv          <- the fictional dataset (20 invoices)
├── invoice_analysis.py       <- the Python analysis script
├── aging_analysis.png        <- chart: outstanding balance by aging category
├── monthly_invoicing.png     <- chart: invoiced amount per month
├── customer_outstanding.png  <- chart: outstanding balance by customer
└── PROJECT_NOTES.md          <- column definitions, formulas and assumptions
```

## The dataset

`invoice_data.csv` has 20 invoices issued between January and June 2026, to 7 fictional customers. All amounts are in Kenya Shillings (KES).

| Column | Meaning |
|---|---|
| `invoice_number` | Unique invoice reference, e.g. INV-2026-001 |
| `customer_name` | Fictional customer |
| `invoice_date` | Date the invoice was issued |
| `due_date` | Invoice date + 30 days |
| `subtotal` | Amount before VAT |
| `vat` | VAT at 16% of the subtotal |
| `total_amount` | Subtotal + VAT |
| `amount_paid` | Total received so far against the invoice |
| `outstanding_balance` | Total amount − amount paid |
| `payment_status` | Paid, Partially Paid or Unpaid |
| `days_overdue` | Days past the due date, as at the analysis date |
| `aging_category` | Which aging bucket the invoice falls in |

I kept the amounts simple so that any row can be checked by hand. For example, invoice INV-2026-003 is 80,000 + 12,800 VAT = 92,800. The customer paid 50,000, so 42,800 is still owed.

## What I analysed

Using a fixed **analysis date of 30 June 2026** (so the results are the same every time the script runs), I looked at:

1. Total amount invoiced
2. Total amount collected
3. Total outstanding balance
4. Collection rate
5. Paid, partially paid and unpaid invoices
6. Overdue invoices and days overdue
7. Accounts-receivable aging
8. Outstanding balance by customer
9. Monthly invoiced amounts

Before any analysis runs, the script checks the data for internal consistency (see "Validation" below).

## How outstanding balances are calculated

```
Total invoice amount = Subtotal + VAT
Outstanding balance  = Total invoice amount − Amount paid
```

- If the outstanding balance is 0, the invoice is **Paid**.
- If nothing has been paid, it is **Unpaid**.
- If something has been paid but a balance remains, it is **Partially Paid**.

## How aging works

Aging groups unpaid balances by how long they are past their **due date**. It answers the question: "Of the money we are waiting for, how much is late, and how late?"

```
Days overdue = Analysis date − Due date        (never below 0)
```

| Category | Rule |
|---|---|
| Paid | Nothing owed, so aging does not apply |
| Current | Balance owed, but not past the due date (0 days overdue) |
| 1-30 days | 1 to 30 days past due |
| 31-60 days | 31 to 60 days past due |
| 61-90 days | 61 to 90 days past due |
| 90+ days | More than 90 days past due |

Only invoices that still have a balance are included in the aging summary. An invoice due exactly on the analysis date (INV-2026-017) counts as Current, because it is not yet late.

## Validation

The script recalculates key columns and compares them with the CSV. All 9 checks pass:

- Subtotal + VAT = Total invoice amount
- VAT = 16% of subtotal
- Total invoice amount − Amount paid = Outstanding balance
- No invoice has been paid more than its total
- Due date = invoice date + 30 days
- Invoice numbers are unique
- Payment status matches the amounts
- Days overdue matches my own recalculation
- Aging category matches my own recalculation

If any check fails, the script stops instead of producing results from bad data. I tested this by deliberately changing one balance by KES 100 in a copy of the file, and the script correctly stopped.

## Main findings

| Measure | Result |
|---|---|
| Total invoiced (incl. VAT) | KES 1,514,960 |
| Total collected | KES 859,880 |
| Total outstanding | KES 655,080 |
| Collection rate (all invoices) | 56.8% |
| Collection rate (only invoices already due) | 64.2% |

**Payment status:** 9 invoices are fully paid, 5 are partially paid and 6 are unpaid.

**Aging of the KES 655,080 outstanding:**

| Category | Invoices | Outstanding (KES) | Share |
|---|---|---|---|
| Current | 4 | 285,080 | 43.5% |
| 1-30 days | 2 | 133,400 | 20.4% |
| 31-60 days | 2 | 120,400 | 18.4% |
| 61-90 days | 1 | 44,400 | 6.8% |
| 90+ days | 2 | 71,800 | 11.0% |

What stands out:

- **The 56.8% collection rate looks low, but it is not the full picture.** Three invoices were not yet due at 30 June. If I only count invoices that had already reached their due date, the rate is 64.2%.
- **Seven invoices are overdue**, totalling KES 370,000 (56.5% of the outstanding balance). The oldest is 131 days overdue.
- **Zuri Logistics Ltd** has the largest outstanding balance (KES 172,600). **Tumaini Stationery Mart** is second (KES 162,400) and has paid nothing at all on its three invoices, one of which is over 90 days overdue.
- **Nyota Print Works** has the oldest overdue invoice (131 days), but the amount is relatively small (KES 42,800).
- **April was the biggest invoicing month** (KES 365,400) and January the smallest (KES 185,600).

### Charts

![Outstanding balance by aging category](aging_analysis.png)

![Monthly invoiced amount](monthly_invoicing.png)

![Outstanding balance by customer](customer_outstanding.png)

## Tools used

- **Python 3**
- **pandas** for loading the CSV, grouping and summarising
- **NumPy** for a few conditional calculations (`np.where`, `np.select`, `np.isclose`)
- **Matplotlib** for the charts

To run it:

```bash
pip install pandas numpy matplotlib
python invoice_analysis.py
```

The script prints the results and re-creates the three PNG charts in the same folder.

## How this project was built

I used an AI assistant to help plan the project and draft the first version of the files. I then went through the code and each calculation line by line so that I understand how they work and can explain them. The dataset, VAT and aging logic and all figures above can be checked by hand from `invoice_data.csv`.

## What I learned

- How the parts of an invoice fit together (subtotal, VAT, total, payments, balance) and how an outstanding balance is worked out.
- Why accounts receivable is reported by **aging** and not just as one total: a KES 50,000 balance that is 5 days late and one that is 120 days late are very different risks.
- Why a fixed analysis date matters: "days overdue" changes every day, so without a fixed date the results would not be reproducible.
- Why a simple headline number like collection rate needs context. Including invoices that are not yet due makes it look worse than it really is.
- How to use pandas `groupby` to summarise data, and how to add basic validation checks so I am not trusting numbers blindly.
- How to make simple, readable charts with Matplotlib.

## Limitations

- **Tiny, made-up dataset.** 20 invoices cannot show real customer behaviour or reliable trends.
- **No payment dates.** I only know how much was paid, not when. So I cannot tell if a "Paid" invoice was paid late, and I cannot calculate the average days customers take to pay.
- **Single analysis date.** The results are a snapshot as at 30 June 2026, not a trend over time.
- **Fixed 30-day payment terms and 16% VAT on every invoice.** Real businesses can have different terms per customer, and some items may be zero-rated or VAT-exempt.
- **VAT is included in the totals.** Monthly "invoiced" figures include VAT, which is not really the business's own revenue. A finance reviewer might prefer the figures before VAT.
- **No credit notes, discounts, write-offs or bad debt provisions.**
- **Simple aging buckets** based only on days past the due date.
- **Not connected to any accounting system.** The data is a hand-built CSV.

## Possible future improvements

- Add a payment-date column and calculate the average days to pay for each customer.
- Show the monthly invoiced figures before VAT as well.
- Compare aging across several month-end dates to see whether collections are improving.
- Add a simple expected-credit-loss or provision estimate using assumed percentages for each aging bucket.
- Add credit notes and write-offs to the dataset.
- Practise with a larger, randomly generated fictional dataset.
- Export the summary tables to Excel for easier sharing.
