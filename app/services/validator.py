import logging
from typing import List
from app.schemas.invoices import InvoiceExtractedData, ValidationIssue, Financials, ErrorType, InvoiceItem
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


def _validate_ice(ice: str | None, entity_type: str = "Seller") -> List[ValidationIssue]:
    issues = []
    
    if not ice:
        issues.append(ValidationIssue(
            field=f"{entity_type} ICE", 
            error_type=ErrorType.MISSING_DATA, 
            message=f"{entity_type} ICE is missing."
        ))
        return issues  

    clean_ice = ice.replace(" ", "").replace("-", "").strip()


    if not clean_ice.isdigit():
        issues.append(ValidationIssue(
            field=f"{entity_type} ICE", 
            error_type=ErrorType.CRITICAL_COMPLIANCE, 
            message=f"ICE must contain only digits. Found: '{ice}'"
        ))

        return issues 

    if len(clean_ice) != 15:
        issues.append(ValidationIssue(
            field=f"{entity_type} ICE", 
            error_type=ErrorType.CRITICAL_COMPLIANCE, 
            message=f"ICE must be exactly 15 digits. Found {len(clean_ice)} digits: '{clean_ice}'"
        ))

    return issues



def _validate_line_item_math(items: List[InvoiceItem] | None) -> List[ValidationIssue]:
    """
    Row-Level Audit: Checks if Qty * Price == Line Total for each item.
    """
    issues = []

    if not items:
        return issues

    for index, item in enumerate(items):
        calculated_total = item.quantity * item.unit_price
        diff = abs(calculated_total - item.total_line)
        
        if diff > 0.10:
            issues.append(ValidationIssue(
                field=f"Item #{index + 1} ({item.description})",
                error_type=ErrorType.MATH_MISMATCH,
                message=(
                    f"Line item math error: {item.quantity} x {item.unit_price} "
                    f"= {calculated_total:.2f}, but extracted value is {item.total_line}"
                )
            ))
    return issues
        

def _validate_math_integrity(data: InvoiceExtractedData) -> List[ValidationIssue]:
    issues = []

    issues += _validate_line_item_math(data.items)

    financials = data.financials

    calculated_total_ht = sum(item.total_line for item in data.items)

    if abs(calculated_total_ht - financials.total_ht) > 1.00:
        issues.append(ValidationIssue(
            field="Total HT",
            error_type=ErrorType.MATH_MISMATCH,
            message=(
                f"Sum of line items ({calculated_total_ht:.2f}) does not match "
                f"declared Total HT ({financials.total_ht})."
            )
        ))

    expected_ttc = financials.total_ht + financials.total_tva

    if abs(expected_ttc - financials.total_ttc) > 0.50:
        issues.append(ValidationIssue(
            field="Total TTC",
            error_type=ErrorType.MATH_MISMATCH,
            message=(
                f"Math error in totals: HT ({financials.total_ht}) + "
                f"TVA ({financials.total_tva}) = {expected_ttc:.2f}, "
                f"but invoice says {financials.total_ttc}"
            )
        ))
    
    return issues



def _validate_tax_consistency(financials: Financials) -> List[ValidationIssue]:
    issues = []
    
    if financials.total_ht == 0:
        return issues
    
    implied_rate = financials.total_tva / financials.total_ht
    valid_rates = [0.20, 0.14, 0.10, 0.07, 0.00]
    is_valid_rate = any(abs(implied_rate - rate) for rate in valid_rates)

    if not is_valid_rate:
        found_pct = implied_rate * 100

        issues.append(ValidationIssue(
            field="TVA Rate",
            error_type=ErrorType.SUSPICIOUS_VALUE,
            message=(
                f"The implied tax rate is {found_pct:.1f}%, which is not a standard "
                "Moroccan VAT rate (20%, 14%, 10%, 7%). Check amounts."
            )
        ))

    return issues
    

def _validate_required_metadata(data: InvoiceExtractedData) -> List[ValidationIssue]:
    issues = []
    meta = data.meta

    if not meta.invoice_number:
        issues.append(ValidationIssue(
            field="Invoice Number", 
            error_type=ErrorType.MISSING_DATA, 
            message="Invoice Number is missing."
        ))

    if not meta.date:
        issues.append(ValidationIssue(
            field="Invoice Date", 
            error_type=ErrorType.MISSING_DATA, 
            message="Invoice Date is missing."
        ))

    if not data.seller.name:
        issues.append(ValidationIssue(
            field="Seller Name", 
            error_type=ErrorType.MISSING_DATA, 
            message="Seller Name is missing."
        ))


    if not data.seller.if_:
        issues.append(ValidationIssue(
            field="Seller Tax ID (IF)", 
            error_type=ErrorType.CRITICAL_COMPLIANCE, 
            message="Seller Identifiant Fiscal (IF) is missing. This invoice cannot be used for tax deduction."
        ))

    if not data.client.name:
         issues.append(ValidationIssue(
            field="Client Name", 
            error_type=ErrorType.MISSING_DATA, 
            message="Client Name is missing. We cannot verify who was billed."
        ))

    return issues


def _validate_date_logic(date_str: str | None) -> List[ValidationIssue]:
    issues = []
    
    if not date_str:
        return issues 

    try:
        clean_date_str = date_str.replace("-", "/").replace(".", "/")
        invoice_date = datetime.strptime(clean_date_str, "%d/%m/%Y")
        
        today = datetime.now()


        if invoice_date > (today + timedelta(days=1)):
            issues.append(ValidationIssue(
                field="Date",
                error_type=ErrorType.SUSPICIOUS_VALUE,
                message=f"Date is in the future ({date_str}). Impossible."
            ))

        one_year_ago = today - timedelta(days=365)
        if invoice_date < one_year_ago:
            issues.append(ValidationIssue(
                field="Date",
                error_type=ErrorType.SUSPICIOUS_VALUE,
                message=f"Invoice is over 1 year old ({date_str}). Verify validity."
            ))

    except ValueError:

        issues.append(ValidationIssue(
            field="Date",
            error_type=ErrorType.DATA_QUALITY,
            message=f"Date format not recognized: '{date_str}'. Expected DD/MM/YYYY."
        ))

    return issues

def validate_invoice(data: InvoiceExtractedData) -> List[ValidationIssue]:
    issues = []

    logger.info(f"Validating Invoice: {data.meta.invoice_number}")
    
    try:
        issues += _validate_ice(data.seller.ice, entity_type="Seller")
        issues += _validate_ice(data.client.ice, entity_type="Client")
        issues += _validate_math_integrity(data)
        issues += _validate_tax_consistency(data.financials)
        issues += _validate_required_metadata(data)
        issues += _validate_date_logic(data.meta.date)

    except Exception as e:
        logger.error(f"Validation crashed: {e}", exc_info=True)
        issues.append(ValidationIssue(
            field="System Validator",
            error_type=ErrorType.CRITICAL_COMPLIANCE,
            message=f"Validation logic crashed: {str(e)}"
        ))

    return issues