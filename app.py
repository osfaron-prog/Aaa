import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import pandas as pd
import re
import io
from PIL import Image, ImageOps

# 1. Page Config
st.set_page_config(page_title="AI Data Parser Pro", layout="wide")

# حل مشكلة الألوان والتحذيرات
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h1, h2, h3, p, span, label, div { color: #1f1f1f !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. محرك استخراج البيانات المطور (عشان يحل مشكلة NotFound)
def smart_parser(text):
    # مصفوفة أنماط بحث أوسع بكتير
    patterns = {
        "Name": [
            r"(?:Name|Customer|Patient|Client|الاسم|السيد|المريض)\s*[:\-]\s*([a-zA-Z\s\u0621-\u064A]+)",
            r"Name\s+([a-zA-Z\s]+)",
            r"([\u0621-\u064A]+\s+[\u0621-\u064A]+\s+[\u0621-\u064A]+)" # محاولة صيد اسم ثلاثي عربي
        ],
        "Date": [
            r"(\d{1,4}[-/]\d{1,2}[-/]\d{2,4})",
            r"(?:Date|التاريخ)\s*[:\-]\s*([\d\w\s,-]+)"
        ],
        "Amount": [
            r"(?:Total|Amount|Sum|Balance|المبلغ|إجمالي)\s*[:\-]?\s*(?:\$|£|€)?\s*([\d,]+\.?\d*)"
        ]
    }
    
    results = {}
    for key, regex_list in patterns.items():
        found = "Not Found"
        for p in regex_list:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                if len(val) > 1: # التأكد إنه مش حرف عشوائي
                    found = val
                    break
        results[key] = found
    return results

# 3. Sidebar UI
st.sidebar.title("⚙️ OCR Settings")
ocr_lang = st.sidebar.selectbox("Language", ["eng+ara", "eng", "ara"])

# 4. Main UI
st.title("📄 Professional PDF Extractor")
uploaded_file = st.file_uploader("Upload Scanned PDF or Image", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    with st.spinner('🧬 Processing... Please wait'):
        if uploaded_file.type == "application/pdf":
            images = convert_from_bytes(uploaded_file.read())
        else:
            images = [Image.open(uploaded_file)]
        
        extracted_data = []
        tab1, tab2 = st.tabs(["📊 Results Table", "📜 Raw OCR Text"])
        
        for i, img in enumerate(images):
            # تحسين الصورة (مهم جداً للـ Scanned PDF)
            img_gray = ImageOps.grayscale(img)
            img_clean = ImageOps.autocontrast(img_gray)
            
            # قراءة النص
            raw_text = pytesseract.image_to_string(img_clean, lang=ocr_lang)
            
            # استخراج البيانات
            parsed = smart_parser(raw_text)
            parsed["ID"] = i + 1
            extracted_data.append(parsed)
            
            with tab2:
                st.text_area(f"Raw Text - Page {i+1}", raw_text, height=200)

        df = pd.DataFrame(extracted_data)
        
        with tab1:
            st.subheader("Extracted Data")
            # تم استبدال use_container_width بـ width='stretch' لحل مشكلة الـ Logs
            edited_df = st.data_editor(df, num_rows="dynamic", width="stretch")
            
            # Export Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                edited_df.to_excel(writer, index=False)
            
            st.download_button(label="📥 Download Excel", data=output.getvalue(), file_name="extracted_data.xlsx")
else:
    st.info("Please upload a file to start.")
