import streamlit as st
import pandas as pd
import re
import io
import json
from google.cloud import vision
from google.oauth2 import service_account
from pdf2image import convert_from_bytes

# إعداد الصفحة
st.set_page_config(page_title="Google AI OCR Studio", layout="wide")

# محرك قراءة جوجل
def get_vision_client():
    if "GCP_JSON" in st.secrets:
        info = json.loads(st.secrets["GCP_JSON"])
        creds = service_account.Credentials.from_service_account_info(info)
        return vision.ImageAnnotatorClient(credentials=creds)
    return None

def extract_data(image_bytes, client):
    image = vision.Image(content=image_bytes)
    # استخدام document_text_detection أفضل للـ Scanned PDF
    response = client.document_text_detection(image=image)
    full_text = response.full_text_annotation.text
    
    # محرك البحث الذكي عن البيانات (Regex)
    # طورنا البحث عشان يصطاد أي كلمة قريبة من الاسم
    name = re.search(r"(?:Name|Customer|الاسم|السيد|مريض)\s*[:\-]?\s*([a-zA-Z\s\u0621-\u064A]{3,30})", full_text)
    date = re.search(r"(\d{1,4}[-/]\d{1,2}[-/]\d{2,4})", full_text)
    
    return {
        "Name": name.group(1).strip() if name else "Not Found",
        "Date": date.group(1).strip() if date else "Not Found",
        "RawText": full_text
    }

st.title("💎 Google AI Document Intelligence")
client = get_vision_client()

if client:
    uploaded_file = st.file_uploader("Upload Scanned Document", type=["pdf", "jpg", "png"])
    
    if uploaded_file:
        with st.spinner('Google AI is analyzing your document...'):
            if uploaded_file.type == "application/pdf":
                images = convert_from_bytes(uploaded_file.read())
            else:
                from PIL import Image
                images = [Image.open(uploaded_file)]

            final_data = []
            for i, img in enumerate(images):
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                
                res = extract_data(img_byte_arr.getvalue(), client)
                res["Page"] = i + 1
                final_data.append(res)

            df = pd.DataFrame(final_data)
            
            # عرض الجدول
            st.subheader("📊 Extracted Results")
            # تنظيف البيانات قبل العرض (إخفاء النص الخام الطويل)
            display_df = df[["Page", "Name", "Date"]]
            edited_df = st.data_editor(display_df, width="stretch")
            
            # التحميل للاكسيل
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                edited_df.to_excel(writer, index=False)
            
            st.download_button("📥 Download Excel Report", output.getvalue(), "Google_Report.xlsx")
            
            # عرض النص الخام للمراجعة
            with st.expander("🔍 Show Raw Text Analysis"):
                for row in final_data:
                    st.text(f"--- Page {row['Page']} ---")
                    st.write(row['RawText'])
else:
    st.error("❌ Google API Key is missing in Secrets!")
