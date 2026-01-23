from __future__ import annotations

import asyncio
import gzip
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# -----------------------
# Data Model
# -----------------------
@dataclass
class Balance:
    balance_type: Optional[str] = None
    balance_code: Optional[str] = None
    amount: Optional[str] = None
    raw: Optional[str] = None


@dataclass
class ServiceCharge:
    service_class: Optional[str] = None
    service_code: Optional[str] = None
    quantity_basis: Optional[str] = None
    charge_amount: Optional[str] = None
    rate: Optional[str] = None
    units: Optional[str] = None
    description: Optional[str] = None
    raw: Optional[str] = None


@dataclass
class Account:
    account_id: Optional[str] = None
    account_desc: Optional[str] = None
    currency: Optional[str] = None
    ent: Optional[List[str]] = None
    parties: List[Dict[str, Any]] = field(default_factory=list)
    balances: List[Balance] = field(default_factory=list)
    service_charges: List[ServiceCharge] = field(default_factory=list)


@dataclass
class Transaction822:
    control_number: Optional[str] = None
    bgn: Optional[List[str]] = None
    dtm: List[List[str]] = field(default_factory=list)
    accounts: List[Account] = field(default_factory=list)


@dataclass
class Interchange:
    isa: Optional[List[str]] = None
    gs: Optional[List[str]] = None
    transactions_822: List[Transaction822] = field(default_factory=list)


@dataclass
class EDI822Document:
    interchanges: List[Interchange] = field(default_factory=list)


# -----------------------
# Separator detection (your robust version)
# -----------------------
def detect_separators_from_isa(text: str, isa_pos: int) -> Tuple[str, str, str]:
    if isa_pos < 0 or isa_pos + 4 > len(text):
        raise ValueError("Invalid ISA position for separator detection")

    element_sep = text[isa_pos + 3]

    # Find 16th occurrence of element_sep after 'ISA'
    count = 0
    i = isa_pos
    last_sep_pos = -1
    while count < 16:
        j = text.find(element_sep, i + 1)
        if j == -1:
            raise ValueError("Could not find 16 element separators inside ISA")
        last_sep_pos = j
        i = j
        count += 1

    if last_sep_pos + 2 >= len(text):
        raise ValueError("ISA is truncated; cannot read component separator and terminator")

    component_sep = text[last_sep_pos + 1]
    seg_term = text[last_sep_pos + 2]
    return element_sep, component_sep, seg_term


def split_interchanges(raw_text: str) -> List[str]:
    text = raw_text
    starts: List[int] = []
    pos = 0
    while True:
        i = text.find("ISA", pos)
        if i == -1:
            break
        starts.append(i)
        pos = i + 3

    interchanges: List[str] = []
    for idx, isa_pos in enumerate(starts):
        _, _, seg_term = detect_separators_from_isa(text, isa_pos)

        iea_pos = text.find("IEA", isa_pos)
        if iea_pos == -1:
            end = starts[idx + 1] if idx + 1 < len(starts) else len(text)
            interchanges.append(text[isa_pos:end].strip())
            continue

        iea_end = text.find(seg_term, iea_pos)
        if iea_end == -1:
            end = starts[idx + 1] if idx + 1 < len(starts) else len(text)
            interchanges.append(text[isa_pos:end].strip())
            continue

        interchanges.append(text[isa_pos:iea_end + 1].strip())

    return interchanges


def _normalize_isa_newlines(interchange: str, seg_term: str) -> str:
    i = interchange.find("ISA")
    if i == -1:
        return interchange
    term = interchange.find(seg_term, i)
    if term == -1:
        return interchange
    isa = interchange[i:term + 1].replace("\r", "").replace("\n", "")
    return interchange[:i] + isa + interchange[term + 1:]


def parse_segments_from_interchange(interchange: str) -> List[Dict[str, Any]]:
    isa_pos = interchange.find("ISA")
    if isa_pos == -1:
        raise ValueError("No ISA found in interchange")

    element_sep, _, seg_term = detect_separators_from_isa(interchange, isa_pos)
    interchange = _normalize_isa_newlines(interchange, seg_term)

    segments: List[Dict[str, Any]] = []
    for raw_seg in interchange.split(seg_term):
        raw_seg = raw_seg.strip()
        if not raw_seg:
            continue
        parts = raw_seg.split(element_sep)
        segments.append({"tag": parts[0].strip(), "elements": parts[1:], "raw": raw_seg})
    return segments


# -----------------------
# 822 extraction
# -----------------------
def _parse_ser(elements: List[str], raw: str) -> ServiceCharge:
    sc = ServiceCharge(raw=raw)
    sc.service_class = elements[0] if len(elements) > 0 else None
    sc.service_code = elements[1] if len(elements) > 1 else None
    sc.quantity_basis = elements[2] if len(elements) > 2 else None
    sc.charge_amount = elements[3] if len(elements) > 3 else None
    sc.rate = elements[4] if len(elements) > 4 else None
    sc.units = elements[5] if len(elements) > 5 else None
    sc.description = elements[6] if len(elements) > 6 else None
    return sc


def _parse_bln(elements: List[str], raw: str) -> Balance:
    b = Balance(raw=raw)
    b.balance_type = elements[0] if len(elements) > 0 else None
    b.balance_code = elements[1] if len(elements) > 1 else None
    b.amount = elements[-1] if len(elements) > 0 else None
    return b


def extract_822(segments: List[Dict[str, Any]]) -> Interchange:
    ic = Interchange()
    current_tx: Optional[Transaction822] = None
    current_account: Optional[Account] = None

    for seg in segments:
        tag = seg["tag"]
        el = seg["elements"]

        if tag == "ISA":
            ic.isa = el
        elif tag == "GS":
            ic.gs = el
        elif tag == "ST":
            if len(el) > 0 and el[0] == "822":
                current_tx = Transaction822(control_number=(el[1] if len(el) > 1 else None))
                ic.transactions_822.append(current_tx)
                current_account = None
            else:
                current_tx = None
                current_account = None

        elif current_tx is not None:
            if tag == "BGN":
                current_tx.bgn = el
            elif tag == "DTM":
                current_tx.dtm.append(el)
            elif tag == "ENT":
                current_account = Account(ent=el)
                current_tx.accounts.append(current_account)
            elif tag == "N1":
                party = {
                    "entity_id_code": el[0] if len(el) > 0 else None,
                    "name": el[1] if len(el) > 1 else None,
                    "id_code_qual": el[2] if len(el) > 2 else None,
                    "id_code": el[3] if len(el) > 3 else None,
                    "raw": seg["raw"],
                }
                if current_account is not None:
                    current_account.parties.append(party)
            elif tag == "ACT":
                if current_account is None:
                    current_account = Account()
                    current_tx.accounts.append(current_account)
                current_account.account_id = el[0] if len(el) > 0 else current_account.account_id
                current_account.account_desc = el[1] if len(el) > 1 else current_account.account_desc
            elif tag == "CUR":
                if current_account is None:
                    current_account = Account()
                    current_tx.accounts.append(current_account)
                current_account.currency = el[1] if len(el) > 1 else current_account.currency
            elif tag == "BLN":
                if current_account is None:
                    current_account = Account()
                    current_tx.accounts.append(current_account)
                current_account.balances.append(_parse_bln(el, seg["raw"]))
            elif tag == "SER":
                if current_account is None:
                    current_account = Account()
                    current_tx.accounts.append(current_account)
                current_account.service_charges.append(_parse_ser(el, seg["raw"]))

    return ic


# -----------------------
# FileReader (no FastAPI)
# -----------------------
class FileReader:
    @staticmethod
    async def read_edi822(file_path: str, encoding: str = "utf-8") -> EDI822Document:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")

        if file_path.endswith(".gz"):
            with gzip.open(path, "rt", encoding=encoding, newline="") as f:
                raw_text = f.read()
        else:
            with open(path, "r", encoding=encoding, newline="") as f:
                raw_text = f.read()

        doc = EDI822Document()
        for interchange_text in split_interchanges(raw_text):
            segments = parse_segments_from_interchange(interchange_text)
            doc.interchanges.append(extract_822(segments))

        return doc


async def main():
    tmp_path = Path("C:\\Users\\FRR56\\PyCharmMiscProject\\data\\JPMC.822")

    doc = await FileReader.read_edi822(str(tmp_path))

    # Print summary
    print(f"Interchanges: {len(doc.interchanges)}")
    for i, ic in enumerate(doc.interchanges, start=1):
        print(f"\nInterchange {i}: TX count = {len(ic.transactions_822)}")
        for tx in ic.transactions_822:
            print(f"  ST02(control): {tx.control_number}, accounts: {len(tx.accounts)}")
            for a in tx.accounts:
                print(f"    ACT: {a.account_id} | {a.account_desc} | CUR: {a.currency}")
                print(f"      balances: {len(a.balances)}  service_charges: {len(a.service_charges)}")

    # If you want JSON-like output:
    # import json
    # print(json.dumps(asdict(doc), indent=2))

if __name__ == "__main__":
    asyncio.run(main())

