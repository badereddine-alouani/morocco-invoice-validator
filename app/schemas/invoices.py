from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

# --- 1. Sub-Models (The Building Blocks) ---

class InvoiceMeta(BaseModel):
    invoice_number: Optional[str] = Field(None, description="The unique invoice identifier, e.g., FAC-2025-001")
    date: Optional[str] = Field(None, description="The invoice date, usually in DD/MM/YYYY format")

class EntityInfo(BaseModel):
    name: Optional[str] = Field(None, description="Company name")
    address: Optional[str] = Field(None, description="Company address")
    ice: Optional[str] = Field(None, description="Identifiant Commun de l'Entreprise (15 digits)")
    tax_id: Optional[str] = Field(None, description="Identifiant Fiscal (IF)")
    rc: Optional[str] = Field(None, description="Registre de Commerce (RC)")

class InvoiceItem(BaseModel):
    description: str = Field(..., description="Description of the product or service")
    quantity: float = Field(..., description="Quantity of items")
    unit_price: float = Field(..., description="Price per unit (HT)")
    total_line: float = Field(..., description="Total price for this line (qty * unit_price)")

class Financials(BaseModel):
    total_ht: float = Field(..., description="Total amount excluding tax")
    total_tva: float = Field(..., description="Total tax amount")
    total_ttc: float = Field(..., description="Total amount including tax (Total to pay)")

# --- 2. The Main Input Model (What the AI extracts) ---

class InvoiceExtractedData(BaseModel):
    """
    The structured data extracted from the PDF invoice.
    """
    meta: InvoiceMeta
    seller: EntityInfo = Field(..., description="Information about the company ISSUING the invoice")
    client: EntityInfo = Field(..., description="Information about the company PAYING the invoice")
    items: List[InvoiceItem] = Field(..., description="List of line items/services sold")
    financials: Financials

# --- 3. The Output Model (What we send to the Frontend) ---

class ErrorType(str, Enum):
    # 🔴 BLOCKING (The Invoice is Invalid)
    CRITICAL_COMPLIANCE = "CRITICAL_COMPLIANCE"  # Legal failures (Missing ICE)
    MATH_MISMATCH = "MATH_MISMATCH"              # Calculation failures (HT + TVA != TTC)
    MISSING_DATA = "MISSING_DATA"                # OCR failures (No Date, No Total)
    
    # 🟡 WARNINGS (The Invoice is Valid, but suspicious)
    SUSPICIOUS_VALUE = "SUSPICIOUS_VALUE"        # Weird Tax Rate (e.g., 18%), Future Date
    DATA_QUALITY = "DATA_QUALITY"                # Typos, low confidence reads

class ValidationIssue(BaseModel):
    field: str
    error_type: ErrorType
    message: str

class ValidationResult(BaseModel):
    is_valid: bool
    filename: str
    issues: List[ValidationIssue]
    # We include the extracted data so the user can see what was scanned
    extracted_data: InvoiceExtractedData