import pytest
from datetime import datetime, timedelta
from app.services.validator import validate_invoice
from app.schemas.invoices import (
    InvoiceExtractedData, 
    InvoiceMeta, 
    EntityInfo, 
    Financials, 
    InvoiceItem,
    ErrorType
)

# --- 1. The "Perfect Invoice" Generator ---
# This helper creates a valid invoice. We will break it in specific ways for each test.
def create_valid_invoice():
    today_str = datetime.now().strftime("%d/%m/%Y")

    return InvoiceExtractedData(
        meta=InvoiceMeta(
            invoice_number="FAC-2025-001",
            date=today_str
        ),
        seller=EntityInfo(
            name="Tech Solutions SARL",
            ice="123456789012345",  # 15 digits
            tax_id="12345678",
            address="Casablanca"
        ),
        client=EntityInfo(
            name="Client SA",
            ice="999999999999999"   # 15 digits
        ),
        items=[
            InvoiceItem(description="Service A", quantity=1, unit_price=1000.0, total_line=1000.0),
            InvoiceItem(description="Service B", quantity=2, unit_price=500.0, total_line=1000.0)
        ],
        financials=Financials(
            total_ht=2000.0,    # 1000 + 1000
            total_tva=400.0,    # 20% of 2000
            total_ttc=2400.0    # 2000 + 400
        )
    )

# --- 2. The Tests ---

def test_valid_invoice_passes():
    """Happy Path: A perfect invoice should have 0 issues."""
    data = create_valid_invoice()
    issues = validate_invoice(data)
    assert len(issues) == 0

def test_detects_bad_ice_length():
    """Scenario: Seller ICE is too short."""
    data = create_valid_invoice()
    data.seller.ice = "123" # Too short
    
    issues = validate_invoice(data)
    
    assert len(issues) >= 1
    assert issues[0].field == "Seller ICE"
    assert issues[0].error_type == ErrorType.CRITICAL_COMPLIANCE

def test_detects_math_error_horizontal():
    """Scenario: HT + TVA does not equal TTC."""
    data = create_valid_invoice()
    # 2000 + 400 should be 2400, but we say 2500
    data.financials.total_ttc = 2500.0
    
    issues = validate_invoice(data)
    
    # We expect a math mismatch error
    assert any(i.error_type == ErrorType.MATH_MISMATCH for i in issues)

def test_detects_math_error_vertical():
    """Scenario: Items do not sum up to Total HT."""
    data = create_valid_invoice()
    # Items sum to 2000, but we claim Total HT is 5000
    data.financials.total_ht = 5000.0
    
    issues = validate_invoice(data)
    
    assert any(i.field == "Total HT" for i in issues)

def test_detects_future_date():
    """Scenario: Invoice is from the future (Time Travel)."""
    data = create_valid_invoice()
    future_date = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
    data.meta.date = future_date
    
    issues = validate_invoice(data)
    
    assert any(i.error_type == ErrorType.SUSPICIOUS_VALUE for i in issues)
    assert "future" in issues[0].message

def test_detects_missing_metadata():
    """Scenario: Missing Invoice Number."""
    data = create_valid_invoice()
    data.meta.invoice_number = None
    
    issues = validate_invoice(data)
    
    assert any(i.error_type == ErrorType.MISSING_DATA for i in issues)