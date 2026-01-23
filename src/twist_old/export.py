from pathlib import Path
import csv

def export_csv_and_excel(doc, out_dir: str = "output"):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "twist_services.csv"
    xlsx_path = out_dir / "twist_services.xlsx"

    # --------- Flatten to rows (one row per service) ----------
    rows = []
    for es_idx, es in enumerate(doc.electronic_statements):
        for st_idx, st in enumerate(es.statements):
            acc = st.account

            account_id = ""
            iban = ""
            debit_account = ""
            stmt_start = ""
            stmt_end = ""
            bal_ccy = ""
            settle_ccy = ""
            host_ccy = ""

            if acc:
                iban = acc.iban or ""
                debit_account = acc.debit_account or ""
                account_id = debit_account or iban

                stmt_start = acc.statement_start_date or ""
                stmt_end = acc.statement_end_date or ""
                bal_ccy = acc.account_balance_currency_code or ""
                settle_ccy = acc.settlement_currency_code or ""
                host_ccy = acc.host_currency_code or ""

            for svc in st.services:
                rows.append({
                    "electronic_statement_index": es_idx,
                    "statement_index": st_idx,

                    "account_id": account_id,
                    "debit_account": debit_account,
                    "iban": iban,

                    "statement_start_date": stmt_start,
                    "statement_end_date": stmt_end,
                    "balance_currency": bal_ccy,
                    "settlement_currency": settle_ccy,
                    "host_currency": host_ccy,

                    "bankServiceID": svc.bank_service_id or "",
                    "serviceDescription": svc.service_description or "",
                    "serviceType": svc.service_type or "",
                    "volume": svc.volume or "",
                    "pricingCurrencyCode": svc.pricing_currency_code or "",

                    "unitPrice_amount": (svc.unit_price.amount if svc.unit_price else "") or "",
                    "unitPrice_currencyCode": (svc.unit_price.currency_code if svc.unit_price else "") or "",

                    "originalChargeSettlement_amount": (svc.original_charge_settlement.amount if svc.original_charge_settlement else "") or "",
                    "originalChargeSettlement_currencyCode": (svc.original_charge_settlement.currency_code if svc.original_charge_settlement else "") or "",
                })

    # --------- Write CSV ----------
    headers = [
        "electronic_statement_index", "statement_index",
        "account_id", "debit_account", "iban",
        "statement_start_date", "statement_end_date",
        "balance_currency", "settlement_currency", "host_currency",
        "bankServiceID", "serviceDescription", "serviceType", "volume", "pricingCurrencyCode",
        "unitPrice_amount", "unitPrice_currencyCode",
        "originalChargeSettlement_amount", "originalChargeSettlement_currencyCode",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        w.writerows(rows)

    # --------- Write Excel ----------
    # Requires: pip install pandas openpyxl
    import pandas as pd
    df = pd.DataFrame(rows, columns=headers)
    df.to_excel(xlsx_path, index=False)

    print(f"CSV  : {csv_path.resolve()}")
    print(f"Excel: {xlsx_path.resolve()}")
