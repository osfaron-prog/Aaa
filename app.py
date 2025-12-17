import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import pandas as pd
import re
import io
from PIL import Image, ImageOps

# 1. Page Configuration
st.set_page_config(page_title="AI Document Intelligence", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    h1, h2, h3, p { color: #1e1e1e !important; }
    .status-box { padding: 10px; border-radius: 5px; background-color: #e3f2fd; border: 1px solid #2196f3; }
    </style>
    """, unsafe_allow_html=True)

# 2. Advanced Intelligent Parser
def sophisticated_parser(text, custom_keyword=None):
    results = {}
    
    # تحسين البحث عن الأسماء: يبحث عن أنماط الأسماء الإنجليزية والعربية المعقدة
    name_patterns = [
        r"(?:Name|Customer|Patient|Client|الاسم|السيد|المريض)\s*[:\-]\s*([a-zA-Z\s\u0621-\u064A]{3,30})",
        r"([A-Z][a-z]+\s[A-Z][a-z]+(?:\s[A-Z][a-z]+)?)", # الأسماء الإنجليزية التي تبدأ بحروف كبيرة
        r"([\u0621-\u064A]{3,}\s[\u0621-\u064A]{3,}(?:\s[\u0621-\u064A]{3,})?)" # الأسماء العربية الثلاثية
    ]
    
    # تحسين البحث عن التواريخ
    date_patterns = [
        r"(\d{1,4}[-/]\d{1,2}[-/]\d{2,4})",
        r"(\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{2,4})"
    ]

    # وظيفة معقدة: البحث عن كلمات مخصصة يحددها المستخدم
    if custom_keyword:
        custom_pattern = rf"{custom_keyword}\s*[:\-]?\s*([a-zA-Z0-9\s\u0621-\u064A]+)"
        custom_match = re.search(custom_pattern, text, re.IGNORECASE)
        results[custom_keyword] = custom_match.group(1).strip() if custom_match else "Not Found"

    # تنفيذ البحث
    results['Extracted Name'] = "Not Found"
    for p in name_patterns:
        match = re.search(p, text, re.IGNORECASE | re.MULTILINE)
        if match:
            results['Extracted Name'] = match.group(1).strip()
            break

    results['Detected Date'] = "Not Found"
    for p in date_patterns:
        match = re.search(p, text, re.IGNORECASE)
        if match:
            results['Detected Date'] = match.group(1).strip()
            break
            
    # استخراج كافة الأرقام المالية الموجودة في الصفحة (وظيفية معقدة)
    amounts = re.findall(r"(?:\$|£|€|EGP)?\s?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)", text)
    results['Potential Amounts'] = ", ".join(amounts[:3]) if amounts else "No digits found"

    return results

# 3. Sidebar for Advanced Controls
st.sidebar.header("🛠️ Extraction Tuning")
ocr_mode = st.sidebar.radio("OCR Precision", ["Standard", "High-Contrast (Better for Scans)"])
target_word = st.sidebar.text_input("Target Specific Label (e.g., 'ID', 'Invoice')", "")
st.sidebar.divider()
st.sidebar.info("Tip: If 'Not Found' persists, try typing the exact label found in the Raw Text tab.")

# 4. Main App UI
st.title("🚀 AI Document Intelligence Pro")
st.write("Professional-grade data extraction from unstructured scanned documents.")

uploaded_file = st.file_uploader("Upload Document", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    with st.spinner('⚙️ Analyzing Document Layers...'):
        if uploaded_file.type == "application/pdf":
            images = convert_from_bytes(uploaded_file.read())
        else:
            images = [Image.open(uploaded_file)]
        
        final_data = []
        tabs = st.tabs(["📊 Structured Intelligence", "📑 Raw Text Analysis"])
        
        for i, img in enumerate(images):
            # Preprocessing
            img_gray = ImageOps.grayscale(img)
            if ocr_mode == "High-Contrast (Better for Scans)":
                img_gray = ImageOps.autocontrast(img_gray)
            
            # OCR
            raw_text = pytesseract.image_to_string(img_gray, lang='eng+ara')
            
            # Smart Parsing
            analysis = sophisticated_parser(raw_text, target_word if target_word else None)
            analysis["Page"] = i + 1
            final_data.append(analysis)
            
            with tabs[1]:
                st.subheader(f"Page {i+1} Content")
                st.text_area(f"Raw Text Output:", raw_text, height=250, key=f"text_{i}")

        # Data Display
        df = pd.DataFrame(final_data)
        
        with tabs[0]:
            st.success("Analysis Complete!")
            # حل مشكلة التحذير في اللوجز وتوسيع الجدول
            edited_df = st.data_editor(df, num_rows="dynamic", width=1200) # تم استبدال use_container_width
            
            # Export to Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                edited_df.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Export Intelligent Report (Excel)",
                data=output.getvalue(),
                file_name="AI_Extracted_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.info("Upload a scanned file to begin AI processing.")
