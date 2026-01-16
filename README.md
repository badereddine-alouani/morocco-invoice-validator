### 🚧 Project Roadmap & Status

This project is currently under active development. The goal is to build a production-ready compliance engine for the 2026 Moroccan Electronic Invoicing mandate.

**Current Phase:** `Phase 1: Core Logic & Data Pipeline`

- [x] **Architecture Design:** Define system flow (FastAPI -> LangChain -> Validation).
- [x] **Synthetic Data Generation:** Script to generate realistic Moroccan PDF invoices (Valid & Fraudulent).
- [ ] **OCR & Extraction:** Implement LangChain pipeline to parse unstructured PDFs into JSON.
- [ ] **Validation Logic:**
    - [ ] Implement ICE verification (15-digit check).
    - [ ] Implement mathematical audit (HT + TVA = TTC).
- [ ] **API Development:** Build FastAPI endpoints (`POST /validate`).
- [ ] **Containerization:** Write `Dockerfile` and `docker-compose.yml`.
- [ ] **Demo UI:** Build a simple Streamlit dashboard for visual testing.
