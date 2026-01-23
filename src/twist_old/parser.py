from xml.etree.ElementTree import iterparse, Element
from typing import Optional, List

from src.twist_old.model import Money, Account, CurrencyTranslation, Service, TaxDetails, TaxRegion, ServiceDetail, \
    TaxCalculationList, TaxCalculation, ServiceAdjustment, TwistDocument, ElectronicStatement, Statement


# ---- helpers ----
def _t(e: Optional[Element]) -> Optional[str]:
    if e is None or e.text is None:
        return None
    s = e.text.strip()
    return s or None

def _money(parent: Optional[Element], base: str) -> Money:
    if parent is None:
        return Money(None, None)
    return Money(
        amount=_t(parent.find(f"{base}/amount")),
        currency_code=_t(parent.find(f"{base}/currencyCode")),
    )

# ---- leaf parsers (parse a whole subtree when its END tag fires) ----
def _parse_account(acc: Element) -> Account:
    return Account(
        statement_start_date=_t(acc.find("statementStartDate")),
        statement_end_date=_t(acc.find("statementEndDate")),
        statement_production_date=_t(acc.find("statementProductionDate")),
        statement_status=_t(acc.find("statementStatus")),
        account_level=_t(acc.find("accountLevel")),
        iban=_t(acc.find("iban")),
        domicile_bank_identifier=_t(acc.find("domicileBankIdentifier")),
        compensation_method=_t(acc.find("compensationMethod")),
        debit_account=_t(acc.find("debitAccount")),
        delayed_debit_date=_t(acc.find("delayedDebitDate")),
        settlement_advice=_t(acc.find("settlementAdvice")),
        account_balance_currency_code=_t(acc.find("accountBalanceCurrencyCode")),
        settlement_currency_code=_t(acc.find("settlementCurrencyCode")),
        host_currency_code=_t(acc.find("hostCurrencyCode")),
        tax_calculation_method=_t(acc.find("taxCalculationMethod")),
        tax_region_code=_t(acc.find("taxRegionCode")),
        bank_contact_name=_t(acc.find("bankContactName")),
        bank_contact_phone=_t(acc.find("bankContactPhone")),
        bank_contact_fax=_t(acc.find("bankContactFax")),
        bank_contact_email=_t(acc.find("bankContactEmail")),
    )

def _parse_currency_translation(ct: Element) -> CurrencyTranslation:
    return CurrencyTranslation(
        original_currency=_t(ct.find("originalCurrency")),
        target_currency=_t(ct.find("targetCurrency")),
        translation_value=_t(ct.find("translationValue")),
        basis=_t(ct.find("basis")),
    )

def _parse_service(s: Element) -> Service:
    return Service(
        bank_service_id=_t(s.find("bankServiceID")),
        service_description=_t(s.find("serviceDescription")),
        service_type=_t(s.find("serviceType")),
        volume=_t(s.find("volume")),
        pricing_currency_code=_t(s.find("pricingCurrencyCode")),
        unit_price=_money(s, "unitPrice"),
        price_method=_t(s.find("priceMethod")),
        payment_method=_t(s.find("paymentMethod")),
        original_charge_settlement=_money(s, "originalChargeSettlement"),
    )

def _parse_tax_details(td: Element) -> TaxDetails:
    regions: List[TaxRegion] = []
    for tr in td.findall("./taxRegion"):
        # serviceDetail (optional)
        sd_node = tr.find("serviceDetail")
        service_detail = None
        if sd_node is not None:
            service_detail = ServiceDetail(
                bank_service_id=_t(sd_node.find("bankServiceId")),
                service_description=_t(sd_node.find("serviceDescription")),
                original_charge=_money(sd_node, "originalCharge"),
            )

        # taxCalculation (optional)
        tc_node = tr.find("taxCalculation")
        tax_calc = None
        if tc_node is not None:
            tcl_list: List[TaxCalculationList] = []
            for item in tc_node.findall("taxCalculationList"):
                tcl_list.append(
                    TaxCalculationList(
                        tax_identification_number=_t(item.find("taxIdentificationNumber")),
                        tax_identifier_description=_t(item.find("taxIdentifierDescription")),
                        tax_identifier_rate=_t(item.find("taxIdentifierRate")),
                        tax_identifier_total_tax_amount=_money(item, "taxIdentifierTotalTaxAmount"),
                    )
                )

            tax_calc = TaxCalculation(
                host_cur_code=_t(tc_node.find("hostCurCode")),
                taxable_service_charge=_money(tc_node, "taxHostConversion/taxableServiceCharge"),
                taxable_service_charge_host=_money(tc_node, "taxHostConversion/taxableServiceChargeHost"),
                total_taxable_svc_charge_host_amount=_money(tc_node, "totalTaxableSvcChargeHostAmount"),
                tax_calculation_list=tcl_list,
                total_tax_amount=_money(tc_node, "totalTaxAmount"),
            )

        regions.append(
            TaxRegion(
                tax_region_number=_t(tr.find("taxRegionNumber")),
                tax_region_name=_t(tr.find("taxRegionName")),
                customer_tax_id=_t(tr.find("customerTaxId")),
                tax_invoice_number=_t(tr.find("taxInvoiceNumber")),
                service_detail=service_detail,
                tax_calculation=tax_calc,
                settlement_amount=_money(tr, "settlementAmount"),
                tax_due_to_region=_money(tr, "taxDueToRegion"),
            )
        )

    return TaxDetails(tax_regions=regions)

def _parse_service_adjustment(sa: Element) -> ServiceAdjustment:
    return ServiceAdjustment(
        type=_t(sa.find("Type")),
        description=_t(sa.find("description")),
        service_adjustment_amt=_money(sa, "serviceAdjustmentAmt"),
        adjustment_error_date=_t(sa.find("adjustmentErrorDate")),
        service_adjustment_id=_t(sa.find("serviceAdjustmentID")),
        new_charge=_money(sa, "newCharge"),
    )

# ---- main streaming parser ----
def parse_twist_multi(xml_path: str) -> TwistDocument:
    electronic_statements: List[ElectronicStatement] = []

    # contexts
    current_es_statements: List[Statement] = []
    in_es = False

    current_statement: Optional[Statement] = None
    in_stmt = False

    for event, elem in iterparse(xml_path, events=("start", "end")):
        tag = elem.tag

        if event == "start":
            if tag == "electronicStatement":
                in_es = True
                current_es_statements = []

            elif tag == "statement" and in_es:
                in_stmt = True
                current_statement = Statement(
                    account=None,
                    currency_translation=None,
                    services=[],
                    tax_details=None,
                    service_adjustment=None,
                )
            continue

        # --- END event ---
        if tag == "account" and in_stmt and current_statement:
            current_statement.account = _parse_account(elem)

        elif tag == "currencyTranslation" and in_stmt and current_statement:
            current_statement.currency_translation = _parse_currency_translation(elem)

        elif tag == "service" and in_stmt and current_statement:
            current_statement.services.append(_parse_service(elem))

        elif tag == "taxDetails" and in_stmt and current_statement:
            current_statement.tax_details = _parse_tax_details(elem)

        elif tag == "serviceAdjustment" and in_stmt and current_statement:
            current_statement.service_adjustment = _parse_service_adjustment(elem)

        elif tag == "statement" and in_stmt and current_statement:
            current_es_statements.append(current_statement)
            current_statement = None
            in_stmt = False

        elif tag == "electronicStatement" and in_es:
            electronic_statements.append(ElectronicStatement(statement_list=current_es_statements, statement_header=None))
            current_es_statements = []
            in_es = False

        # memory cleanup
        elem.clear()

    return TwistDocument(header=None, electronic_statement_list=electronic_statements)

