import streamlit as st
import pandas as pd
import re
import io
import json
from google.cloud import vision
from google.oauth2 import service_account
from pdf2image import convert_from_bytes

# 1. إعدادات الصفحة والتصميم
st.set_page_config(page_title="Google AI OCR Pro", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    h1, h2, h3 { color: #1e1e1e !important; }
    .stDataFrame { background-color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. وظيفة الربط مع جوجل (باستخدام Secrets)
def get_vision_client():
    try:
        if "GCP_JSON" in st.secrets:
            # تنظيف النص لضمان عدم وجود أخطاء JSON
            json_text = st.secrets["GCP_JSON"].strip()
            info = json.loads(json_text)
            creds = service_account.Credentials.from_service_account_info(info)
            return vision.ImageAnnotatorClient(credentials=creds)
    except Exception as e:
        st.error(f"Error in Google Credentials: {e}")
    return None

# 3. وظيفة استخراج البيانات الذكية
def extract_data(image_bytes, client):
    image = vision.Image(content=image_bytes)
    # استخدام تقنية التعرف على المستندات (أفضل للسكان)
    response = client.document_text_detection(image=image)
    full_text = response.full_text_annotation.text
    
    # محرك البحث عن الأنماط (Regex) - قابل للتطوير
    # يبحث عن الاسم بعد كلمات مفتاحية أو كنمط اسم
    name_match = re.search(r"(?:Name|الاسم|السيد|مريض|Customer)\s*[:\-]?\s*([a-zA-Z\s\u0621-\u064A]{3,35})", full_text)
    # يبحث عن أي تاريخ
    date_match = re.search(r"(\d{1,4}[-/]\d{1,2}[-/]\d{2,4})", full_text)
    
    return {
        "Name": name_match.group(1).strip() if name_match else "Not Detected",
        "Date": date_match.group(1).strip() if date_match else "Not Detected",
        "RawText": full_text
    }

# 4. الواجهة الرئيسية
st.title("🚀 Google AI Document Intelligence")
st.subheader("Transform Scanned PDFs into Clean Excel Data")

client = get_vision_client()

if client:
    uploaded_file = st.file_uploader("Upload File (PDF, JPG, PNG)", type=["pdf", "jpg", "png", "jpeg"])
    
    if uploaded_file:
        with st.spinner('AI is reading document layers...'):
            # تحويل الملف لصور (سواء كان PDF أو صورة عادية)
            if uploaded_file.type == "application/pdf":
                images = convert_from_bytes(uploaded_file.read())
            else:
                from PIL import Image
                images = [Image.open(uploaded_file)]

            final_data = []
            
            # معالجة كل صفحة
            for i, img in enumerate(images):
                # تحويل الصورة لـ Bytes لجوجل
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                
                # استخراج البيانات
                result = extract_data(img_byte_arr.getvalue(), client)
                result["Page"] = i + 1
                final_data.append(result)

            # تحويل النتائج لجدول Pandas
            df = pd.DataFrame(final_data)
            
            # تنظيم التبويبات
            tab_res, tab_raw = st.tabs(["📊 Extracted Results", "🔍 Raw AI Text"])
            
            with tab_res:
                st.write("Review and edit your data before downloading:")
                # عرض الجدول مع حل مشكلة container_width القديمة
                edited_df = st.data_editor(df[["Page", "Name", "Date"]], width=1200, num_rows="dynamic")
                
                # إنشاء ملف الإكسيل
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    edited_df.to_excel(writer, index=False)
                
                st.divider()
                st.download_button(
                    label="📥 Download Excel Report",
                    data=output.getvalue(),
                    file_name="AI_Extraction_Report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with tab_raw:
                for row in final_data:
                    st.markdown(f"**Page {row['Page']} Text Output:**")
                    st.code(row['RawText'])
else:
    st.warning("⚠️ API Key Missing: Please add 'GCP_JSON' to your Streamlit Secrets.")

st.sidebar.markdown("---")
st.sidebar.info("Powered by Google Cloud Vision AI")
