import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import pandas as pd
import re
import io
from PIL import Image, ImageOps

# 1. Page Configuration & Professional Theme
st.set_page_config(page_title="AI Data Parser Pro", layout="wide", page_icon="🤖")

st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #fff; border-radius: 5px; padding: 10px; }
    div[data-testid="stExpander"] { background-color: white !important; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    h1 { color: #2c3e50; font-family: 'Helvetica Neue', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# 2. Advanced Extraction Engine
def smart_parser(text):
    # Dictionary of regex patterns
    patterns = {
        "Name": [r"Name\s*[:\-]\s*([a-zA-Z\s\u0621-\u064A]+)", r"Patient\s*[:\-]\s*([a-zA-Z\s\u0621-\u064A]+)", r"Client\s*[:\-]\s*([a-zA-Z\s\u0621-\u064A]+)"],
        "Date": [r"(\d{1,4}[-/]\d{1,2}[-/]\d{2,4})", r"Date\s*[:\-]\s*([\d\w\s,-]+)"],
        "Amount": [r"(?:Total|Amount|Sum|Balance)\s*[:\-]?\s*(?:\$|£|€)?\s*([\d,]+\.?\d*)"]
    }
    
    results = {}
    for key, regex_list in patterns.items():
        found = "Not Found"
        for p in regex_list:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                found = match.group(1).strip()
                break
        results[key] = found
    return results

# 3. Sidebar UI
st.sidebar.title("⚙️ Engine Settings")
ocr_lang = st.sidebar.selectbox("OCR Language", ["English + Arabic", "English Only", "Arabic Only"])
lang_code = "eng+ara" if "Arabic" in ocr_lang else "eng"
st.sidebar.divider()
st.sidebar.success("OCR Engine: Tesseract 5.0 Ready")

# 4. Main Interface
st.title("🤖 AI Document Parser Pro")
st.caption("Advanced OCR system for Scanned PDFs and Images")

uploaded_file = st.file_uploader("Drop your file here (PDF, JPG, PNG)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    with st.spinner('🧬 Processing with AI OCR...'):
        # Step 1: File Conversion
        if uploaded_file.type == "application/pdf":
            images = convert_from_bytes(uploaded_file.read())
        else:
            images = [Image.open(uploaded_file)]
        
        extracted_data = []
        
        # Step 2: Tabs for Organization
        tab_table, tab_preview, tab_raw = st.tabs(["📊 Structured Results", "🔍 Visual Preview", "📜 Raw OCR Text"])
        
        for i, img in enumerate(images):
            # Preprocessing (Grayscale + Denoise)
            img_gray = ImageOps.grayscale(img)
            img_clean = ImageOps.autocontrast(img_gray)
            
            # Step 3: OCR Execution
            raw_text = pytesseract.image_to_string(img_clean, lang=lang_code)
            
            # Step 4: Smart Parsing
            parsed = smart_parser(raw_text)
            parsed["ID"] = i + 1
            extracted_data.append(parsed)
            
            with tab_preview:
                st.image(img_clean, caption=f"Page {i+1}", use_container_width=True)
            
            with tab_raw:
                with st.expander(f"Raw Text - Page {i+1}"):
                    st.text(raw_text)

        # Step 5: Data Management
        df = pd.DataFrame(extracted_data)
        # Reorder columns
        df = df[["ID", "Name", "Date", "Amount"]]
        
        with tab_table:
            st.subheader("Final Data Extraction")
            st.warning("Double-click any cell to manually correct errors.")
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            
            # Export to Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                edited_df.to_excel(writer, index=False, sheet_name='Data')
            
            st.divider()
            st.download_button(
                label="📥 Export to Excel (.xlsx)",
                data=output.getvalue(),
                file_name="Processed_Documents.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

else:
    st.info("👋 Welcome! Please upload a scanned document to start extracting data.")
