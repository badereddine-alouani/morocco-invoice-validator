import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import ChatPromptTemplate
from app.schemas.invoices import InvoiceExtractedData




_cached_llm = None
logger = logging.getLogger(__name__)

def _get_llm(model: str):

    global _cached_llm
    if _cached_llm is None:
        logger.info(f"Initializing vLLM Client for Worker (Model: {model})")
        _cached_llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=0,
        )
    return _cached_llm




PROMPT_TEMPLATE = """
You are an expert AI accountant specializing in Moroccan Tax Law (DGI).
Your task is to extract structured invoice data from the provided raw text.

GENERAL EXTRACTION RULES
- Extract ONLY information explicitly present in the text.
- Never infer, guess, normalize, or recompute values.
- If a field is missing, unclear, or not explicitly stated, return null.
- Preserve numbers exactly as written.
- Do not omit legally required identifiers if they are present anywhere in the text.

ENTITY ROLES (CRITICAL)

SELLER (Invoice Issuer)
- The seller is the company issuing the invoice.
- It usually appears at the top of the document and may also appear in the footer.
- Extract seller:
  - name
  - address
  - ICE
  - IF (Identifiant Fiscal)
  - RC

CLIENT (Billed Entity)
- The client is the entity being billed.
- The client section is often introduced by headers such as:
  “FACTURÉ À”, “CLIENT”, “FACTURÉ AU CLIENT”.
- IMPORTANT:
  - The client name may appear on the line immediately AFTER the header.
  - If a company name appears directly under a client header, it IS the client name.

IDENTIFIER EXTRACTION RULES (VERY IMPORTANT)

ICE (Identifiant Commun de l’Entreprise)
- ICE is ALWAYS a 15-digit numeric value.
- Distinguish clearly:
  - Seller ICE → belongs to the issuer
  - Client ICE → explicitly labeled “ICE Client”
- If both are present, extract both.

IF (Identifiant Fiscal)
- IF belongs ONLY to the seller.
- IF is extracted ONLY when explicitly labeled:
  “IF”, “I.F.”, “Identifiant Fiscal”, “الرقم الضريبي”.
- IF may appear:
  - In the footer
  - After totals
  - On the same line as RC or TP
  - Separated by symbols like “|”
- Even if IF appears after totals, it MUST be extracted if present.
- Never confuse IF with ICE, RC, or TP.

RC (Registre de Commerce)
- Extract only if explicitly labeled “RC”.

INVOICE METADATA
- Extract invoice number and invoice date.
- Ignore due date unless required by the schema.

LINE ITEMS
- Extract each line item as written.
- Do not merge duplicate descriptions.
- Do not calculate missing values.

FINANCIAL TOTALS
- Extract Total HT, Total TVA, and Total TTC only if explicitly written.
- Do not recompute totals.

ROBUSTNESS TO PDF TEXT
- Assume text may be noisy, reordered, or poorly aligned.
- Footer administrative blocks are legally important and MUST be parsed.

OUTPUT
- Return ONLY the structured data matching the required schema.
- Do NOT include explanations, warnings, or validation logic.

RAW INVOICE TEXT:
{text}

"""


def extract_invoice_data(pdf_path: str) -> InvoiceExtractedData:
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    if not docs:
        raise ValueError("PDF is empty or unreadable")

    content = docs[0].page_content

    logger.debug("="*50)
    logger.debug(f"RAW PDF CONTENT START\n{content}")
    logger.debug("RAW PDF CONTENT END")
    logger.debug("="*50)
    
    llm = _get_llm("models/gemini-flash-latest")

    structured_llm = llm.with_structured_output(InvoiceExtractedData)
    
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    chain = prompt | structured_llm

    result = chain.invoke({"text": content})

    return result



