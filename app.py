import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import pandas as pd
import re
import io
from PIL import Image, ImageOps

# 1. Page Configuration
st.set_page_config(page_title="AI Data Parser Pro", layout="wide", page_icon="🤖")

# حل مشكلة التحذير بخصوص use_container_width والألوان
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    h1, h2, h3, p, span, label { color: #2c3e50 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. تحسين محرك البحث عن البيانات (Regex)
def smart_parser(text):
    # وسعنا نطاق البحث عشان نغطي كل الاحتمالات اللي بتطلع "Not Found"
    patterns = {
        "Name": [
            r"(?:Name|Customer|Patient|Client|الاسم|مريض|عميل)\s*[:\-]\s*([a-zA-Z\s\u0621-\u064A]+)",
            r"([a-zA-Z\u0621-\u064A]+\s+[a-zA-Z\u0621-\u064A]+)" # بيبحث عن أي كلمتين ورا بعض لو ملقاش كلمة "اسم"
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
                if len(val) > 2: # للتأكد إنه مش حرف عشوائي
                    found = val
                    break
        results[key] = found
    return results

# 3. Sidebar UI
st.sidebar.title("⚙️ Settings")
ocr_lang = st.sidebar.selectbox("OCR Language", ["eng+ara", "eng", "ara"])

# 4. Main Interface
st.title("🤖 AI Document Parser")
uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    with st.spinner('🧬 Extracting Text...'):
        if uploaded_file.type == "application/pdf":
            images = convert_from_bytes(uploaded_file.read())
        else:
            images = [Image.open(uploaded_file)]
        
        extracted_data = []
        tab_table, tab_raw = st.tabs(["📊 Results", "📜 Raw Text"])
        
        for i, img in enumerate(images):
            # تحسين الصورة للقراءة (مهم جداً عشان مطلعش Not Found)
            img_gray = ImageOps.grayscale(img)
            img_clean = ImageOps.autocontrast(img_gray)
            
            # قراءة النص
            raw_text = pytesseract.image_to_string(img_clean, lang=ocr_lang)
            
            # تحليل النص
            parsed = smart_parser(raw_text)
            parsed["ID"] = i + 1
            extracted_data.append(parsed)
            
            with tab_raw:
                st.text_area(f"Raw Text Page {i+1}", raw_text, height=150)

        df = pd.DataFrame(extracted_data)
        
        with tab_table:
            st.subheader("Extracted Data")
            # استبدال use_container_width بـ width='stretch' لحل مشكلة الـ Logs
            edited_df = st.data_editor(df, num_rows="dynamic", width='stretch')
            
            # Export to Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                edited_df.to_excel(writer, index=False)
            
            st.download_button(label="📥 Download Excel", data=output.getvalue(), file_name="data.xlsx")
