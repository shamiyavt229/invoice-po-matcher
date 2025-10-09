import re
import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

# --- This setup is for Google Gemini ---
import google.generativeai as genai
# PASTE YOUR NEW GOOGLE AI API KEY HERE
API_KEY = 'AIzaSyCga-46XDgqLQ7QZvM_bopX1sq0b69Pa-A' 
genai.configure(api_key=API_KEY)


import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image

# Make sure this path is correct for your Tesseract installation
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\ASUS\Desktop\tesseract\tesseract.exe'

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allowing all for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_text_with_ocr(file_content: bytes) -> str:
    """Extracts text from a file's bytes using OCR."""
    try:
        images = convert_from_bytes(file_content)
        full_text = ""
        for img in images:
            # --- THIS IS THE ONLY CHANGE: Added lang='eng' for better accuracy ---
            full_text += pytesseract.image_to_string(img, lang='eng') + "\n"
        return full_text
    except Exception as e:
        print(f"OCR Error: {e}")
        raise HTTPException(status_code=500, detail="OCR processing failed.")
import pdfplumber

def extract_text(file_content: bytes) -> str:
    """Extracts text from PDF using pdfplumber, fallback to OCR if needed."""
    from io import BytesIO
    
    try:
        text = ""
        with pdfplumber.open(BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        
        if text.strip():  # If text exists, return it
            return text
        else:
            # fallback to OCR
            return extract_text_with_ocr(file_content)
    except Exception as e:
        print(f"PDF extract error: {e}")
        return extract_text_with_ocr(file_content)

def parse_document_data_with_gemini(text: str) -> Dict[str, Any]:
    """
    Parses document text using Google Gemini and extracts structured info,
    including items and quantities.
    """
    model = genai.GenerativeModel("gemini-2.5-pro")

    prompt = f"""
    You are an AI that parses purchase orders or invoices.

    From the document text below, extract and return a JSON object
    with the following structure:

    {{
        "vendor_name": "...",
        "customer_name": "...",
        "po_number": "...",
        "invoice_number": "...",
        "total_amount": 0.0,
        "items": [
            {{
                "description": "...",
                "quantity": 0,
                "unit_price": 0.0,
                "total": 0.0
            }},
            ...
        ]
    }}

    - "items" should be an array of all products or line items found.
    - Quantities and prices must be numeric.
    - If something is missing, set it to "N/A" or 0.
    - Do not include any text outside JSON.
    
    Document text:
    ---
    {text}
    ---
    """

    try:
        response = model.generate_content(prompt)
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(json_text)

        # Clean numeric fields
        for item in data.get("items", []):
            if isinstance(item.get("quantity"), str):
                item["quantity"] = float(re.sub(r"[^\d.]", "", item["quantity"]) or 0)
            if isinstance(item.get("unit_price"), str):
                item["unit_price"] = float(re.sub(r"[^\d.]", "", item["unit_price"]) or 0)
            if isinstance(item.get("total"), str):
                item["total"] = float(re.sub(r"[^\d.]", "", item["total"]) or 0)

        if data.get("total_amount") and not isinstance(data["total_amount"], (int, float)):
            data["total_amount"] = float(re.sub(r"[^\d.]", "", str(data["total_amount"])) or 0)

        return data
    except Exception as e:
        print(f"AI Parsing Error: {e}")
        return {
            "vendor_name": "Error",
            "customer_name": "Error",
            "po_number": "N/A",
            "invoice_number": "N/A",
            "total_amount": 0.0,
            "items": []
        }

from rapidfuzz import fuzz, process
def normalize_desc(desc: str) -> str:
    return (desc.lower()
            .replace("model:", "")
            .replace("hs code", "")
            .replace("origin", "")
            .strip())

@app.post("/match")
async def match_documents(invoice: UploadFile = File(...), po: UploadFile = File(...)):
    invoice_text = extract_text(await invoice.read())
    po_text = extract_text(await po.read())

    invoice_data = parse_document_data_with_gemini(invoice_text)
    po_data = parse_document_data_with_gemini(po_text)

    issues = []

    # --- Vendor & Customer Matching (fuzzy) ---
    vendor_score = fuzz.token_sort_ratio(invoice_data.get("vendor_name", ""), po_data.get("vendor_name", ""))
    vendor_match = vendor_score >= 80

    customer_score = fuzz.token_sort_ratio(invoice_data.get("customer_name", ""), po_data.get("customer_name", ""))
    customer_match = customer_score >= 80

    # --- Total Amount Matching ---
    invoice_total = invoice_data.get("total_amount", 0)
    po_total = po_data.get("total_amount", 0)
    total_match = abs(invoice_total - po_total) < 0.01
    if not total_match:
        issues.append(f"Total amount mismatch: PO={po_total}, Invoice={invoice_total}")

    # --- Item Matching ---
    item_issues = []
    po_items = po_data.get("items", [])
    inv_items = invoice_data.get("items", [])

    for inv_item in inv_items:
        inv_desc = normalize_desc(inv_item["description"])
        po_descs = [normalize_desc(i["description"]) for i in po_items]

        if not po_descs:
            item_issues.append("No PO items found to match against.")
            continue

        match_result = process.extractOne(inv_desc, po_descs, scorer=fuzz.partial_ratio)
        if not match_result:
            item_issues.append(f"Could not find a match for '{inv_item['description']}' in PO.")
            continue

        best_match, score, _ = match_result
        if score < 65:
            item_issues.append(f"Item '{inv_item['description']}' not found in PO (best match score {score:.1f}).")
            continue

        # Get the actual PO item
        po_item = next((i for i in po_items if normalize_desc(i["description"]) == best_match), None)
        if not po_item:
            item_issues.append(f"Best match '{best_match}' not found in PO items list.")
            continue

        # Quantity check
        if inv_item["quantity"] != po_item["quantity"]:
            item_issues.append(
                f"Quantity mismatch for '{inv_item['description']}': PO={po_item['quantity']}, Invoice={inv_item['quantity']}."
            )

        # Price check
        if abs(inv_item["unit_price"] - po_item["unit_price"]) > 0.01:
            item_issues.append(
                f"Price mismatch for '{inv_item['description']}': PO={po_item['unit_price']}, Invoice={inv_item['unit_price']}."
            )

    # --- Missing PO Items in Invoice ---
    po_names = [normalize_desc(i["description"]) for i in po_items]
    inv_names = [normalize_desc(i["description"]) for i in inv_items]
    for po_name in po_names:
        match_result = process.extractOne(po_name, inv_names, scorer=fuzz.partial_ratio)
        if not match_result or match_result[1] < 65:
            item_issues.append(f"Item '{po_name}' missing in invoice.")

    if item_issues:
        issues.extend(item_issues)

    # --- Vendor/Customer Issues ---
    if not vendor_match:
        issues.append("Vendor name mismatch.")
    if not customer_match:
        issues.append("Customer name mismatch.")

    # --- Final Status ---
    status = "APPROVED" if not issues else "NEEDS REVIEW"

    return {
        "status": status,
        "invoice_number": invoice_data.get("invoice_number"),
        "po_number": po_data.get("po_number"),
        "vendor_match": vendor_match,
        "customer_match": customer_match,
        "total_match": total_match,
        "issues": issues
    }
