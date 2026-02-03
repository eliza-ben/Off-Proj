from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import xml.etree.ElementTree as ET


TWIST_NS = "http://www.twiststandards.org/3.1/ElectronicBilling"
NS = {"t": TWIST_NS}


def _txt(el: Optional[ET.Element], path: str, default: Optional[str] = None) -> Optional[str]:
    """Safe findtext for namespaced XML."""
    if el is None:
        return default
    node = el.find(path, NS)
    if node is None or node.text is None:
        return default
    v = node.text.strip()
    return v if v else default


@dataclass
class AccountTag:
    bban: Optional[str] = None
    iban: Optional[str] = None
    account_name: Optional[str] = None
    statement_start_date: Optional[str] = None
    statement_end_date: Optional[str] = None
    statement_production_date: Optional[str] = None
    debit_account: Optional[str] = None
    delayed_debit_date: Optional[str] = None
    compensation_method: Optional[str] = None
    account_currency: Optional[str] = None


@dataclass
class Service:
    service_code: Optional[str] = None
    service_description: Optional[str] = None
    service_type: Optional[str] = None
    volume: Optional[str] = None

    unit_price_amount: Optional[str] = None
    unit_price_currency: Optional[str] = None

    settlement_amount: Optional[str] = None
    settlement_currency: Optional[str] = None

    tax_designation: Optional[str] = None
    # NOTE: no taxIdentificationGroup fields on purpose


@dataclass
class AccountServiceRow:
    account: AccountTag
    service: Service

def parse_twist_flat_service_rows(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Returns a LIST of dicts (one per <service>) with:
      bban, statement_start_date, statement_end_date, statement_production_date,
      account_currency, service_code, service_description, service_type, tax_designation
    """
    root = ET.parse(Path(path)).getroot()
    rows: List[Dict[str, Any]] = []

    for est in root.findall("t:electronicStatement", NS):
        for stmt in est.findall("t:statement", NS):
            acc_el = stmt.find("t:account", NS)

            account_id = _txt(acc_el, "t:bban")
            from_dt = _txt(acc_el, "t:statementStartDate")
            to_dt = _txt(acc_el, "t:statementEndDate")
            invoice_dt = _txt(acc_el, "t:statementProductionDate")
            currency = _txt(acc_el, "t:accountBalanceCurrencyCode")

            for svc_el in stmt.findall("t:service", NS):
                service_type = _txt(svc_el, "t:serviceType")
                if(service_type is not None):
                    rows.append(
                        {
                            "account_id": account_id,
                            "from_dt": from_dt,
                            "to_dt": to_dt,
                            "invoice_dt": invoice_dt,
                            "currency": currency,
                            "service_code": _txt(svc_el, "t:bankServiceID"),
                            "service_description": _txt(svc_el, "t:serviceDescription"),
                            "charge_amount": _txt(svc_el, "t:originalChargePrice/t:amount"),
                            "volume": _txt(svc_el, "t:volume"),
                            "units": _txt(svc_el, "t:unitPrice/t:amount"),
                            "service_type": _txt(svc_el, "t:serviceType"),
                            "tax_designation": _txt(svc_el, "t:taxDesignation"),
                        }
                    )

    return rows

# def parse_twist_account_services_file(path: Union[str, Path]) -> List[Dict[str, Any]]:
#     """
#     Parse TWIST XML from a FILE PATH.
#     Returns a list where each item = {account:{...}, service:{...}}
#     Works even if <taxIdentificationGroup> is missing.
#     """
#     root = ET.parse(Path(path)).getroot()
#     out: List[AccountServiceRow] = []
#
#     for est in root.findall("t:electronicStatement", NS):
#         for stmt in est.findall("t:statement", NS):
#             acc_el = stmt.find("t:account", NS)
#
#             account = AccountTag(
#                 bban=_txt(acc_el, "t:bban"),
#                 iban=_txt(acc_el, "t:iban"),
#                 account_name=_txt(acc_el, "t:accountName"),
#                 statement_start_date=_txt(acc_el, "t:statementStartDate"),
#                 statement_end_date=_txt(acc_el, "t:statementEndDate"),
#                 statement_production_date=_txt(acc_el, "t:statementProductionDate"),
#                 debit_account=_txt(acc_el, "t:debitAccount"),
#                 delayed_debit_date=_txt(acc_el, "t:delayedDebitDate"),
#                 compensation_method=_txt(acc_el, "t:compensationMethod"),
#                 account_currency=_txt(acc_el, "t:accountBalanceCurrencyCode"),
#             )
#
#             for svc_el in stmt.findall("t:service", NS):
#                 service = Service(
#                     service_code=_txt(svc_el, "t:bankServiceID"),
#                     service_description=_txt(svc_el, "t:serviceDescription"),
#                     service_type=_txt(svc_el, "t:serviceType"),
#                     volume=_txt(svc_el, "t:volume"),
#                     unit_price_amount=_txt(svc_el, "t:unitPrice/t:amount"),
#                     unit_price_currency=_txt(svc_el, "t:unitPrice/t:currency"),
#                     settlement_amount=_txt(svc_el, "t:totalChargeSettlementAmount/t:amount"),
#                     settlement_currency=_txt(svc_el, "t:totalChargeSettlementAmount/t:currency"),
#                     tax_designation=_txt(svc_el, "t:taxDesignation"),
#                 )
#                 out.append(AccountServiceRow(account=account, service=service))
#
#     return [asdict(r) for r in out]


# -----------------------
# Example
# -----------------------
if __name__ == "__main__":
    rows = parse_twist_flat_service_rows(r"C:\Users\FRR56\PyCharmMiscProject\data\Sample_Parser.xml")
    print("rows:", len(rows))
    print(rows)  # {'account': {...}, 'service': {...}}
