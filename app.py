import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import pandas as pd
import re
import io
from PIL import Image, ImageOps

# إعدادات واجهة الموقع
st.set_page_config(page_title="Data Extractor Pro", layout="wide", page_icon="🔍")

# CSS بسيط لتحسين المظهر
st.markdown("""
    <style>
    .stApp { background-color: #fafafa; }
    .css-154489f { background-color: #007bff; }
    </style>
    """, unsafe_allow_html=True)

st.title("📄 مستخرج البيانات الذكي من الـ PDF")
st.subheader("تحويل ملفات السكان (Scanned) إلى جداول إكسيل بدقة عالية")

uploaded_file = st.file_uploader("قم بسحب وإفلات ملف الـ PDF هنا", type="pdf")

if uploaded_file:
    # 1. تحويل الملف لصور
    with st.spinner('جاري قراءة صفحات الملف...'):
        images = convert_from_bytes(uploaded_file.read())
    
    st.success(f"تم تحميل {len(images)} صفحة بنجاح!")
    
    final_results = []

    # 2. معالجة كل صفحة
    for i, img in enumerate(images):
        with st.expander(f"تفاصيل الصفحة {i+1}", expanded=(i==0)):
            # تحسين جودة الصورة (Preprocessing)
            img_gray = ImageOps.grayscale(img)
            img_clean = ImageOps.autocontrast(img_gray)
            
            # قراءة النص (يدعم العربي والإنجليزي)
            text = pytesseract.image_to_string(img_clean, lang='ara+eng')
            
            # محرك البحث عن البيانات (Regex)
            # تقدر تعدل الكلمات دي (الاسم، التاريخ، المبلغ) حسب ملفاتك
            name = re.search(r"(?:الاسم|Name|السيد|Customer)\s*[:\-]\s*([\u0621-\u064A\s\w]+)", text)
            date = re.search(r"(\d{1,4}[-/]\d{1,2}[-/]\d{2,4})", text)
            amount = re.search(r"(?:المبلغ|Total|Amount|السعر)\s*[:\-]\s*([\d,.]+)", text)

            extracted_row = {
                "الصفحة": i + 1,
                "الاسم": name.group(1).strip() if name else "غير موجود",
                "التاريخ": date.group(1).strip() if date else "غير موجود",
                "المبلغ": amount.group(1).strip() if amount else "0.00"
            }
            final_results.append(extracted_row)
            
            # عرض المعاينة
            col1, col2 = st.columns([1, 2])
            col1.image(img_clean, caption="الصورة المعالجة")
            col2.text_area(f"النص المستخرج من صفحة {i+1}", text, height=200)

    # 3. عرض الجدول النهائي القابل للتعديل
    st.divider()
    st.header("📝 مراجعة وتعديل البيانات")
    st.info("يمكنك الضغط على أي خلية لتعديل النص يدوياً قبل التحميل")
    
    df = pd.DataFrame(final_results)
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    # 4. زر التحميل لـ Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        edited_df.to_excel(writer, index=False)
    
    st.download_button(
        label="📥 تحميل ملف Excel النهائي",
        data=output.getvalue(),
        file_name="Extracted_Data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )