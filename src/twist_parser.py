
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
import xml.etree.ElementTree as ET

NS = {"tw": "http://www.twiststandards.org/3.1/ElectronicBilling"}

def _txt(el: Optional[ET.Element]) -> Optional[str]:
    if el is None or el.text is None:
        return None
    s = el.text.strip()
    return s if s else None

def _find_text(parent: ET.Element, path: str) -> Optional[str]:
    return _txt(parent.find(path, NS))

@dataclass
class CompensationRecord:
    # Account / statement context
    account_level: Optional[str] = None
    bban: Optional[str] = None
    iban: Optional[str] = None
    account_name: Optional[str] = None
    domicile_bank_identifier: Optional[str] = None
    statement_start_date: Optional[str] = None
    statement_end_date: Optional[str] = None
    statement_production_date: Optional[str] = None

    # Compensation fields
    compensation_identifier: Optional[str] = None
    amount: Optional[str] = None
    currency: Optional[str] = None
    currency_type: Optional[str] = None


def parse_all_compensations(path: str | Path) -> List[CompensationRecord]:
    path = Path(path)
    out: List[CompensationRecord] = []

    # stream parse
    for event, elem in ET.iterparse(path, events=("end",)):
        # each <electronicStatement> contains 1..N <statement>
        if elem.tag == f"{{{NS['tw']}}}electronicStatement":
            for st_el in elem.findall("tw:statement", NS):
                acct = st_el.find("tw:account", NS)

                # account context (same for every comp inside this statement)
                ctx = {
                    "account_level": _find_text(acct, "tw:accountLevel") if acct is not None else None,
                    "bban": _find_text(acct, "tw:bban") if acct is not None else None,
                    "iban": _find_text(acct, "tw:iban") if acct is not None else None,
                    "account_name": _find_text(acct, "tw:accountName") if acct is not None else None,
                    "domicile_bank_identifier": _find_text(acct, "tw:domicileBankIdentifier") if acct is not None else None,
                    "statement_start_date": _find_text(acct, "tw:statementStartDate") if acct is not None else None,
                    "statement_end_date": _find_text(acct, "tw:statementEndDate") if acct is not None else None,
                    "statement_production_date": _find_text(acct, "tw:statementProductionDate") if acct is not None else None,
                }

                # 0..N compensations under a statement
                for comp in st_el.findall("tw:compensation", NS):
                    comp_identifier = _find_text(comp, "tw:compensationIdentifier")

                    comp_val = comp.find("tw:compensationValue", NS)
                    amount = _find_text(comp_val, "tw:amount") if comp_val is not None else None
                    currency = _find_text(comp_val, "tw:currency") if comp_val is not None else None

                    currency_type = _find_text(comp, "tw:currencyType")

                    out.append(
                        CompensationRecord(
                            **ctx,
                            compensation_identifier=comp_identifier,
                            amount=amount,
                            currency=currency,
                            currency_type=currency_type,
                        )
                    )

            elem.clear()

    return out


# ---- Example ----
if __name__ == "__main__":
    records = parse_all_compensations(r"C:\Users\FRR56\PyCharmMiscProject\data\Sample_Parser.xml")
    print("Total compensations:", len(records))
    for r in records:
        print(r)
