import streamlit as st
import requests
import base64
import json
from fpdf import FPDF

# Set page configuration
st.set_page_config(page_title="PO to Tax Invoice Generator", layout="centered")

st.title("🧾 Tax Invoice Generator")
st.write("Upload a Purchase Order (PDF or Image) to automatically extract details and generate the formatted bill.")

# 1. Manual Inputs
st.subheader("1. Bill Details")
col1, col2 = st.columns(2)
with col1:
    bill_no = st.text_input("Bill No.", value="1721")
with col2:
    bill_date = st.text_input("Date (DD-MM-YYYY)", value="27-06-2026")

# 2. File Uploader 
st.subheader("2. Upload Purchase Order")
uploaded_file = st.file_uploader("Upload PO document", type=["pdf", "jpg", "jpeg", "png"])

if uploaded_file is not None:
    is_pdf = uploaded_file.name.lower().endswith(".pdf")
    if is_pdf:
        st.success(f"📄 PDF Document Uploaded: {uploaded_file.name}")
    else:
        st.image(uploaded_file, caption="Uploaded Purchase Order", use_container_width=True)
    
    if st.button("🚀 Process PO & Generate PDF Bill"):
        with st.spinner("Bypassing SDK to read Purchase Order natively..."):
            try:
                # Get the AQ. API key from Streamlit secrets safely
                api_key = st.secrets["GEMINI_API_KEY"]
                
                # Instruction prompt
                ai_prompt = """
                Analyze this Purchase Order and extract the information. 
                Return STRICTLY a JSON object without markdown or codeblocks with this exact structure:
                {
                  "buyer_name_address": "Full Buyer Name, Delivery Address, GST No if present",
                  "po_no": "PO Number or reference",
                  "po_date": "PO Date",
                  "items": [
                    {
                      "sr_no": "1",
                      "particular": "Item description",
                      "item_code": "Item code if available, else empty",
                      "hsn_code": "HSN code if available, else empty",
                      "qty": "1.00",
                      "unit": "EA",
                      "rate": "100.00",
                      "amount": "100.00"
                    }
                  ],
                  "amount_in_words": "TOTAL AMOUNT IN WORDS"
                }
                """
                
                # Encode file to base64 to send directly
                mime_type = "application/pdf" if is_pdf else "image/jpeg"
                file_b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
                
                # --- NATIVE API CALL (Bypassing the buggy SDK) ---
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                headers = {'Content-Type': 'application/json'}
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": ai_prompt},
                            {"inline_data": {
                                "mime_type": mime_type,
                                "data": file_b64
                            }}
                        ]
                    }]
                }
                
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status() 
                
                # Clean JSON response
                response_data = response.json()
                raw_json = response_data['candidates'][0]['content']['parts'][0]['text']
                raw_json = raw_json.replace("```json", "").replace("```", "").strip()
                data = json.loads(raw_json)
                
                # --- PDF GENERATION (No changes to your father's layout) ---
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(0, 5, "TAX INVOICE", align="C", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", "B", 14)
                pdf.cell(0, 7, "KAUSHAL ENGINEERING WORKS", align="C", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", "", 9)
                pdf.cell(0, 5, "K-198, MIDC WALUJ, CHH. SAMBHAJINAGAR-431136", align="C", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(3)
                
                y_start = pdf.get_y()
                pdf.rect(10, y_start, 100, 32)
                pdf.set_xy(12, y_start + 2)
                pdf.set_font("helvetica", "B", 8)
                pdf.cell(96, 4, "BUYER / DELIVERY ADDRESS:", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", "", 8)
                pdf.set_x(12)
                pdf.multi_cell(96, 4, str(data.get("buyer_name_address", "N/A")))
                
                pdf.rect(110, y_start, 90, 32)
                pdf.set_xy(112, y_start + 2)
                pdf.cell(40, 5, f"Bill No.: {bill_no}")
                pdf.cell(45, 5, f"Date: {bill_date}", new_x="LMARGIN", new_y="NEXT")
                
                pdf.set_x(112)
                pdf.cell(40, 5, f"P.O. Date: {data.get('po_date', 'N/A')}")
                pdf.cell(45, 5, f"P.O. No.: {data.get('po_no', 'N/A')}", new_x="LMARGIN", new_y="NEXT")
                
                pdf.set_y(y_start + 35)
                
                pdf.set_font("helvetica", "B", 8)
                pdf.cell(10, 8, "Sr.", border=1, align="C")
                pdf.cell(65, 8, "Particular", border=1, align="C")
                pdf.cell(20, 8, "Item Code", border=1, align="C")
                pdf.cell(20, 8, "HSN", border=1, align="C")
                pdf.cell(15, 8, "Qty.", border=1, align="C")
                pdf.cell(15, 8, "Unit", border=1, align="C")
                pdf.cell(20, 8, "Rate", border=1, align="C")
                pdf.cell(25, 8, "Amount", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
                
                pdf.set_font("helvetica", "", 8)
                subtotal = 0.0
                sr = 1
                for item in data.get("items", []):
                    amt_str = str(item.get("amount", "0")).replace(",", "").strip()
                    try:
                        amt_val = float(amt_str)
                    except ValueError:
                        amt_val = 0.0
                    subtotal += amt_val
                    
                    pdf.cell(10, 7, str(sr), border=1, align="C")
                    pdf.cell(65, 7, str(item.get("particular", ""))[:35], border=1)
                    pdf.cell(20, 7, str(item.get("item_code", "")), border=1, align="C")
                    pdf.cell(20, 7, str(item.get("hsn_code", "")), border=1, align="C")
                    pdf.cell(15, 7, str(item.get("qty", "")), border=1, align="C")
                    pdf.cell(15, 7, str(item.get("unit", "")), border=1, align="C")
                    pdf.cell(20, 7, str(item.get("rate", "")), border=1, align="R")
                    pdf.cell(25, 7, f"{amt_val:.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
                    sr += 1
                
                cgst = subtotal * 0.09
                sgst = subtotal * 0.09
                grand_total = round(subtotal + cgst + sgst)
                
                pdf.set_font("helvetica", "B", 8)
                pdf.cell(145, 6, "Sub Total", border=1, align="R")
                pdf.cell(45, 6, f"{subtotal:.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
                
                pdf.cell(145, 6, "CGST 9%", border=1, align="R")
                pdf.cell(45, 6, f"{cgst:.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
                
                pdf.cell(145, 6, "SGST 9%", border=1, align="R")
                pdf.cell(45, 6, f"{sgst:.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
                
                pdf.cell(145, 6, "Total", border=1, align="R")
                pdf.cell(45, 6, f"{grand_total:.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
                
                pdf.ln(3)
                words = data.get("amount_in_words", "")
                pdf.cell(0, 5, f"RS. IN WORD: {words}", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(5)
                pdf.cell(0, 5, "For, KAUSHAL ENGINEERING WORKS", align="R", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(8)
                pdf.cell(0, 5, "Authorise Signatory", align="R", new_x="LMARGIN", new_y="NEXT")
                
                pdf_file_name = f"Bill_{bill_no}.pdf"
                pdf.output(pdf_file_name)
                
                st.success("✅ Bill generated successfully!")
                with open(pdf_file_name, "rb") as f:
                    st.download_button(
                        label="⬇️ Download PDF Invoice",
                        data=f,
                        file_name=pdf_file_name,
                        mime="application/pdf"
                    )
            except Exception as e:
                st.error(f"Error processing document: {e}")
