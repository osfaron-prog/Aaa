import streamlit as st
import pandas as pd
import re
import io
import json
import pytesseract
import pdfplumber
from google.cloud import vision
from google.oauth2 import service_account
from pdf2image import convert_from_bytes
from PIL import Image, ImageOps

# 1. إعدادات الصفحة بتصميم احترافي
st.set_page_config(page_title="Ultra AI Document Studio", layout="wide", page_icon="🧬")

st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .status-active { color: #28a745; font-weight: bold; }
    .status-fallback { color: #fd7e14; font-weight: bold; }
    div[data-testid="stExpander"] { background-color: white !important; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. وظيفة الربط مع جوجل (المستوى الأول)
def get_google_client():
    try:
        if "GCP_JSON" in st.secrets:
            info = json.loads(st.secrets["GCP_JSON"].strip(), strict=False)
            creds = service_account.Credentials.from_service_account_info(info)
            return vision.ImageAnnotatorClient(credentials=creds)
    except:
        return None
    return None

# 3. محرك الـ NLP المتقدم لاستخراج البيانات
def advanced_nlp_extractor(text):
    results = {}
    # استخراج الأسماء بنمط NLP (بحث عن أنماط السيد/الدكتور أو كلمات كابيتال)
    name_patterns = [
        r"(?:Name|Customer|الاسم|السيد|مريض)\s*[:\-]?\s*([a-zA-Z\s\u0621-\u064A]{3,35})",
        r"(?<=Name\s)([A-Z][a-z]+\s[A-Z][a-z]+)",
        r"([\u0621-\u064A]{3,}\s[\u0621-\u064A]{3,}\s[\u0621-\u064A]{3,})"
    ]
    # استخراج التواريخ
    date_pattern = r"(\d{1,4}[-/]\d{1,2}[-/]\d{2,4})"
    # استخراج المبالغ (Currency Extraction)
    money_pattern = r"(?:Total|Amount|المبلغ|Price|EGP|\$)\s*[:\-]?\s*([\d,]+\.?\d*)"

    for key, patterns in [("Name", name_patterns), ("Date", [date_pattern]), ("Amount", [money_pattern])]:
        results[key] = "Not Found"
        for p in (patterns if isinstance(patterns, list) else [patterns]):
            match = re.search(p, text, re.IGNORECASE | re.MULTILINE)
            if match:
                results[key] = match.group(1).strip()
                break
    return results

# 4. وظيفة الـ Fallback (Tesseract)
def fallback_ocr(image):
    # تحسين الصورة قبل المعالجة المحلية
    gray = ImageOps.grayscale(image)
    clean = ImageOps.autocontrast(gray)
    return pytesseract.image_to_string(clean, lang='eng+ara')

# 5. الواجهة الرئيسية
st.title("🧬 Ultra AI Document Intelligence")
st.write("Hybrid Processing: Google Vision AI + Tesseract Local Fallback")

# فحص حالة المحركات
client = get_google_client()
if client:
    st.markdown("API Status: <span class='status-active'>Google Cloud AI (Enabled)</span>", unsafe_allow_html=True)
else:
    st.markdown("API Status: <span class='status-fallback'>Tesseract Local (Fallback Mode)</span>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Document (PDF, Images)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    final_data = []
    
    with st.spinner('Analyzing Layers...'):
        # محاولة استخراج النص مباشرة لو PDF نصي (مكتبة pdfplumber)
        is_scanned = True
        if uploaded_file.type == "application/pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                text_content = ""
                for page in pdf.pages:
                    text_content += page.extract_text() or ""
                if len(text_content.strip()) > 10:
                    is_scanned = False
                    st.toast("Digital PDF detected! Fast processing active.")
                    data = advanced_nlp_extractor(text_content)
                    data["ID"] = 1
                    data["Method"] = "Digital Stream"
                    data["Raw"] = text_content
                    final_data.append(data)

        # لو ممسوح سكان أو صورة، نستخدم الـ OCR
        if is_scanned:
            if uploaded_file.type == "application/pdf":
                images = convert_from_bytes(uploaded_file.read())
            else:
                images = [Image.open(uploaded_file)]

            for i, img in enumerate(images):
                raw_text = ""
                method = ""
                
                # محاولة جوجل أولاً
                if client:
                    try:
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format='PNG')
                        vision_image = vision.Image(content=img_byte_arr.getvalue())
                        response = client.document_text_detection(image=vision_image)
                        raw_text = response.full_text_annotation.text
                        method = "Google AI"
                    except:
                        raw_text = fallback_ocr(img)
                        method = "Tesseract (Fallback)"
                else:
                    raw_text = fallback_ocr(img)
                    method = "Tesseract (Local)"

                data = advanced_nlp_extractor(raw_text)
                data["ID"] = i + 1
                data["Method"] = method
                data["Raw"] = raw_text
                final_data.append(data)

    # عرض النتائج
    df = pd.DataFrame(final_data)
    tab1, tab2 = st.tabs(["📊 Intelligence Report", "📝 Raw Data"])
    
    with tab1:
        # عرض الجدول بدون تحذيرات
        edited_df = st.data_editor(df[["ID", "Name", "Date", "Amount", "Method"]], width=1200)
        
        # تصدير للإكسيل
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            edited_df.to_excel(writer, index=False)
        st.download_button("📥 Download Exported Intelligence", output.getvalue(), "Report.xlsx")

    with tab2:
        for item in final_data:
            st.text_area(f"Page {item['ID']} Text", item['Raw'], height=150)
