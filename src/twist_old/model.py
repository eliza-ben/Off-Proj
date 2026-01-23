from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Money:
    amount: Optional[str]
    currency_code: Optional[str]


@dataclass
class Account:
    statement_start_date: Optional[str]
    statement_end_date: Optional[str]
    statement_production_date: Optional[str]
    statement_status: Optional[str]
    account_level: Optional[str]
    iban: Optional[str]
    bban: Optional[str]
    account_name: Optional[str]
    domicile_bank_qualifier: Optional[str]
    domicile_bank_identifier: Optional[str]
    compensation_method: Optional[str]
    debit_account: Optional[str]
    delayed_debit_date: Optional[str]
    settlement_advice: Optional[str]
    account_balance_currency_code: Optional[str]
    settlement_currency_code: Optional[str]
    host_currency_code: Optional[str]
    tax_calculation_method: Optional[str]
    tax_region_code: Optional[str]
    bank_contact_name: Optional[str]
    bank_contact_phone: Optional[str]
    bank_contact_fax: Optional[str]
    bank_contact_email: Optional[str]


@dataclass
class CurrencyTranslation:
    original_currency: Optional[str]
    target_currency: Optional[str]
    translation_value: Optional[str]
    basis: Optional[str]

@dataclass
class TaxIdentificationGroup:
    tax_identifier_number: Optional[str]
    tax_identifier_description: Optional[str]
    tax_identifier_rate: Optional[str]
    tax_identifier_host_amount: Money
    tax_identifier_price_amount: Money


@dataclass
class Service:
    bank_service_id: Optional[str]
    service_description: Optional[str]
    service_type: Optional[str]
    volume: Optional[str]
    pricing_currency_code: Optional[str]
    unit_price: Money
    price_method: Optional[str]
    payment_method: Optional[str]
    original_charge_settlement: Money
    tax_designation: Optional[str]
    original_charge_price: Money
    total_charge_settlement: Money
    tax_identification_group: Optional[TaxIdentificationGroup]



@dataclass
class TaxHostConversion:
    taxable_service_charge: Money
    taxable_service_charge_host: Money

@dataclass
class ServiceDetail:
    bank_service_id: Optional[str]
    service_description: Optional[str]
    original_charge: Money


@dataclass
class TaxCalculationList:
    tax_identification_number: Optional[str]
    tax_identifier_description: Optional[str]
    tax_identifier_rate: Optional[str]
    tax_identifier_total_tax_amount: Money


@dataclass
class TaxCalculation:
    host_cur_code: Optional[str]
    tax_host_conversion_list: List[TaxHostConversion]
    total_taxable_svc_charge_host_amount: Money
    tax_calculation_list: List[TaxCalculationList]
    total_tax_amount: Money


@dataclass
class TaxRegion:
    tax_region_number: Optional[str]
    tax_region_name: Optional[str]
    customer_tax_id: Optional[str]
    tax_invoice_number: Optional[str]
    service_details: List[ServiceDetail]
    tax_calculation: Optional[TaxCalculation]
    settlement_amount: Money
    tax_due_to_region: Money


@dataclass
class TaxDetails:
    tax_regions: List[TaxRegion]


@dataclass
class ServiceAdjustment:
    type: Optional[str]
    description: Optional[str]
    service_adjustment_amt: Money
    adjustment_error_date: Optional[str]
    service_adjustment_id: Optional[str]
    new_charge: Money

@dataclass
class Compensation:
    compensation_identifier: Optional[str]
    compensation_value: Money
    currency_type: Optional[str]


@dataclass
class Statement:
    account: Optional[Account]
    currency_translation: Optional[CurrencyTranslation]
    compensations: List[Compensation]
    services: List[Service]
    tax_details: Optional[TaxDetails]
    service_adjustment: Optional[ServiceAdjustment]


@dataclass
class Address:
    address_identifier: Optional[str]
    department_name: Optional[str]
    street_name: Optional[str]
    building_num: Optional[str]
    address_line: Optional[str]
    city: Optional[str]
    country: Optional[str]
    post_code: Optional[str]
    country_sub_div: Optional[str]
    floor: Optional[str]
    post_box: Optional[str]
    building_name: Optional[str]
    room: Optional[str]


@dataclass
class ContactInfo:
    individual_contact: Optional[str]
    phone: Optional[str]
    fax: Optional[str]
    email: Optional[str]
    post_Address: Optional[Address]

@dataclass
class OrgId:
    org_id_type: Optional[str]
    org_id_num: Optional[str]

@dataclass
class SendParty:
    name: Optional[str]
    legal_name: Optional[str]
    contact_info_list: List[ContactInfo]
    org_id: Optional[OrgId]


@dataclass
class StatementHeader:
    stmt_reciver: Optional[SendParty]
    stmt_sender: Optional[SendParty]

@dataclass
class ElectronicStatement:
    statement_list: List[Statement]
    statement_header: Optional[StatementHeader]

@dataclass
class TypedPartyId:
    party_id: Optional[str]
    party_id_type: Optional[str]

@dataclass
class SentBy:
    type_party_id: Optional[TypedPartyId]

@dataclass
class Header:
    message_id: Optional[str]
    in_reply_to: Optional[str]
    sent_by: Optional[SentBy]
    offset_date_time: Optional[str]



@dataclass
class TwistDocument:
    header: Optional[Header]
    electronic_statement_list: Optional[ElectronicStatement]

