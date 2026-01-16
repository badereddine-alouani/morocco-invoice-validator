import os
import random
from fpdf import FPDF
from datetime import date, timedelta

# Create output directory
os.makedirs("data/synthetic", exist_ok=True)

class PDF(FPDF):
    def header(self):
        # Logo Placeholder
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'FACTURE / INVOICE', 0, 1, 'R')
        self.set_draw_color(0, 0, 0)
        self.line(10, 25, 200, 25) # Horizontal line
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, 'Generated for Compliance AI Project - Synthetic Data', 0, 0, 'C')

def generate_invoice(filename, is_valid=True):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    # --- 1. RANDOM DATA SETUP ---
    
    # Dates
    today = date.today()
    invoice_date = today.strftime("%d/%m/%Y")
    due_date = (today + timedelta(days=30)).strftime("%d/%m/%Y")
    invoice_num = f"FAC-{random.randint(2025001, 2025999)}"

    # Seller Info
    cities = ["Casablanca", "Rabat", "Tanger", "Agadir", "Marrakech"]
    sectors = ["Tech", "Conseil", "Logistique", "Travaux", "Industrie"]
    legal_forms = ["SARL", "SARL AU", "SA"]
    comp_name = f"{random.choice(sectors)} {random.choice(['Maroc', 'Solutions', 'North', 'Atlas'])} {random.choice(legal_forms)}"
    address = f"{random.randint(1, 200)} Bd {random.choice(['Zerktouni', 'Mohammed V', 'Anfa', 'Massira'])}, {random.choice(cities)}"
    
    # Client Info
    client_name = f"Groupe {random.choice(['OCP', 'Banque', 'Holding', 'Telecom'])}"
    client_ice = str(random.randint(100000000000000, 999999999999999))

    # --- 2. HEADER & INFO BLOCKS ---
    
    # Top Left: Seller
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 5, comp_name, ln=1)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, address, ln=1)
    pdf.cell(0, 5, f"Tél: +212 5 22 {random.randint(10, 99)} {random.randint(10, 99)}", ln=1)
    pdf.ln(5)

    # Top Right: Invoice Details
    pdf.set_xy(110, 35)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(80, 8, f"N° FACTURE: {invoice_num}", 0, 1, 'R')
    pdf.set_xy(110, 43)
    pdf.set_font("Arial", size=10)
    pdf.cell(80, 5, f"Date: {invoice_date}", 0, 1, 'R')
    pdf.set_xy(110, 48)
    pdf.cell(80, 5, f"Echéance: {due_date}", 0, 1, 'R')
    pdf.ln(20)

    # Client Box
    pdf.set_fill_color(240, 240, 240)
    pdf.rect(10, pdf.get_y(), 190, 25, 'F')
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(100, 8, "  FACTURÉ À (CLIENT):", 0, 1)
    pdf.set_font("Arial", size=10)
    pdf.cell(100, 5, f"  {client_name}", 0, 1)
    pdf.cell(100, 5, f"  ICE Client: {client_ice}", 0, 1)
    pdf.ln(15)

    # --- 3. DYNAMIC ITEMS LOOP ---
    
    # Table Header
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(50, 50, 50)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(100, 10, "  Description", 1, 0, 'L', True)
    pdf.cell(30, 10, "Qté", 1, 0, 'C', True)
    pdf.cell(30, 10, "Prix Uni. HT", 1, 0, 'R', True)
    pdf.cell(30, 10, "Total HT", 1, 1, 'R', True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=10)

    # Item Generation
    services = [
        "Développement Web (Backend)", "Consulting IT (Jours/Homme)", 
        "Maintenance Serveur", "Audit de Sécurité", "Licence Logiciel",
        "Installation Réseau", "Formation Personnel", "Support Technique"
    ]
    
    num_items = random.randint(1, 5) # 1 to 5 random items
    calculated_ht = 0.0

    for _ in range(num_items):
        item_name = random.choice(services)
        qty = random.randint(1, 10)
        price = round(random.uniform(500.0, 5000.0), 2)
        line_total = round(qty * price, 2)
        
        calculated_ht += line_total

        # Add Row
        pdf.cell(100, 10, f"  {item_name}", 1)
        pdf.cell(30, 10, str(qty), 1, 0, 'C')
        pdf.cell(30, 10, f"{price:.2f}", 1, 0, 'R')
        pdf.cell(30, 10, f"{line_total:.2f}", 1, 1, 'R')

    pdf.ln(5)

    # --- 4. FINANCIALS & FRAUD LOGIC ---

    # Setup standard math
    tva_amount = round(calculated_ht * 0.20, 2)
    final_ttc = calculated_ht + tva_amount

    # Setup ICE
    valid_ice = str(random.randint(100000000000000, 999999999999999)) # 15 digits
    invalid_ice = str(random.randint(1000000000000, 9999999999999))     # 13 digits

    # Apply Logic based on 'is_valid' flag
    if is_valid:
        ice = valid_ice
        display_ttc = final_ttc # Math is correct
    else:
        # 50% chance: Bad ICE
        if random.random() > 0.5:
            ice = invalid_ice
            display_ttc = final_ttc
        # 50% chance: Bad Math (ICE is fine, but Total is wrong)
        else:
            ice = valid_ice
            display_ttc = final_ttc - 500.00 # Fraud!
            
    # --- 5. TOTALS & FOOTER ---

    x_totals = 130
    pdf.set_x(x_totals)
    pdf.cell(40, 8, "Total HT:", 1)
    pdf.cell(30, 8, f"{calculated_ht:.2f} DH", 1, 1, 'R')

    pdf.set_x(x_totals)
    pdf.cell(40, 8, "TVA (20%):", 1)
    pdf.cell(30, 8, f"{tva_amount:.2f} DH", 1, 1, 'R')

    pdf.set_x(x_totals)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(40, 10, "TOTAL TTC:", 1)
    pdf.cell(30, 10, f"{display_ttc:.2f} DH", 1, 1, 'R') # Uses potentially 'fake' total
    
    pdf.ln(15)

    # Legal Footer
    pdf.set_font("Arial", size=8)
    pdf.cell(0, 5, f"Arrêté la présente facture à la somme de: {display_ttc:.2f} Dirhams TTC", ln=1)
    pdf.ln(2)
    
    legal_string = f"RC: {random.randint(10000, 99999)}  |  Patente (TP): {random.randint(10000000, 99999999)}  |  IF: {random.randint(10000000, 99999999)}"
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 5, legal_string, 0, 1, 'C')
    
    # The ICE Target
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, f"ICE: {ice}", 0, 1, 'C')

    pdf.output(f"data/synthetic/{filename}")

# --- EXECUTION ---
print("Generating 20 Mixed Invoices...")
for i in range(1, 16):
    generate_invoice(f"invoice_valid_{i}.pdf", is_valid=True)
for i in range(1, 6):
    generate_invoice(f"invoice_INVALID_{i}.pdf", is_valid=False)
print("✅ Done! Check 'data/synthetic'.")