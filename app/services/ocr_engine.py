from langchain_ollama import ChatOllama
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import ChatPromptTemplate
from app.schemas.invoices import InvoiceExtractedData


llm = ChatOllama(
    model="mistral:7b",
)

structured_llm = llm.with_structured_output(InvoiceExtractedData)

PROMPT_TEMPLATE = """
You are an expert AI accountant specializing in Moroccan Tax Law (DGI).
Your task is to extract structured data from the following invoice text.

CRITICAL RULES:
1. **ICE (Identifiant Commun de l'Entreprise)**: Look for a 15-digit number labeled "ICE". It is usually in the footer or header.
2. **Amounts**: Extract 'Total HT', 'Total TVA', and 'Total TTC'.
3. **Missing Data**: If a field is missing, leave it as null or 0.0. Do not hallucinate numbers.

INVOICE TEXT:
{text}
"""




def extract_invoice_data(pdf_path: str) -> InvoiceExtractedData:
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    content = docs[0].page_content
    
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    chain = prompt | structured_llm

    result = chain.invoke({"text": content})

    return result



