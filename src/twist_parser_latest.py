from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Dict, Any
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

def parse_twist_flat_service_rows(raw_text) -> List[Dict[str, Any]]:
    """
    Returns a LIST of dicts (one per <service>) with:
      bban, statement_start_date, statement_end_date, statement_production_date,
      account_currency, service_code, service_description, service_type, tax_designation
    """
    root = ET.parse(raw_text).getroot()
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


# -----------------------
# Example
# -----------------------
if __name__ == "__main__":
    path = Path("C:\\Users\\FRR56\\PyCharmMiscProject\\data\\Sample_Parser.xml")

    file_handle = open(path, 'r', encoding="UTF-8")
    try:
        records = parse_twist_flat_service_rows(file_handle)
        print("rows:", len(records))
        print(records)
    finally:
        file_handle.close()
