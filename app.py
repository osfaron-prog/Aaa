import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import pandas as pd
import re
import io
from PIL import Image, ImageOps

# 1. إعدادات الصفحة والألوان (حل مشكلة بياض النص)
st.set_page_config(page_title="PDF Data Pro", layout="wide", page_icon="📊")

st.markdown("""
    <style>
    /* تأمين ظهور النصوص بالألوان الصحيحة */
    .main { background-color: #ffffff; }
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #262730 !important;
    }
    .stButton>button {
        background-color: #007bff;
        color: white !important;
        font-weight: bold;
    }
    /* تحسين شكل الجدول */
    .stDataFrame { border: 1px solid #e6e9ef; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. دوال مساعدة لاستخراج البيانات بذكاء (Regex)
def extract_info(text):
    # أنماط بحث مطورة للأسماء العربية والإنجليزية
    name_match = re.search(r"(?:الاسم|مريض|عميل|Name|Customer|Patient)\s*[:\-]\s*([\u0621-\u064A\s\w]+)", text)
    # أنماط بحث عن التواريخ بمختلف الأشكال
    date_match = re.search(r"(\d{1,4}[-/]\d{1,2}[-/]\d{2,4})", text)
    # أنماط بحث عن المبالغ المالية
    amount_match = re.search(r"(?:المبلغ|إجمالي|Total|Amount|Price)\s*[:\-]\s*([\d,.]+)", text)
    
    return {
        "الاسم": name_match.group(1).strip() if name_match else "غير موجود",
        "التاريخ": date_match.group(1).strip() if date_match else "غير موجود",
        "المبلغ": amount_match.group(1).strip() if amount_match else "0.00"
    }

# 3. واجهة المستخدم
st.title("📄 مستخرج البيانات المطور (النسخة النهائية)")
st.write("ارفع ملف الـ PDF (المسحوب سكان) وسنقوم بتحويله لجدول بيانات.")

uploaded_file = st.file_uploader("اختر ملف PDF من هاتفك", type="pdf")

if uploaded_file:
    # تحويل PDF لصور
    with st.spinner('جاري معالجة الملف بتقنية OCR...'):
        pdf_bytes = uploaded_file.read()
        images = convert_from_bytes(pdf_bytes)
        
        all_data = []
        
        # إنشاء تبويبات لعرض النتائج
        tab1, tab2 = st.tabs(["📊 البيانات المستخرجة", "🖼️ معاينة الصفحات"])
        
        for i, img in enumerate(images):
            # تحسين الصورة للقراءة
            img_gray = ImageOps.grayscale(img)
            img_processed = ImageOps.autocontrast(img_gray)
            
            # استخراج النص (يدعم العربية والانجليزية)
            raw_text = pytesseract.image_to_string(img_processed, lang='ara+eng')
            
            # استخراج البيانات المحددة
            extracted = extract_info(raw_text)
            extracted["الصفحة"] = i + 1
            all_data.append(extracted)
            
            with tab2:
                st.image(img_processed, caption=f"صفحة رقم {i+1}", width=400)
                st.text_area(f"النص المستخرج (صفحة {i+1})", raw_text, height=100)

        # تحويل النتائج لجدول
        df = pd.DataFrame(all_data)
        
        with tab1:
            st.subheader("📝 راجع البيانات وعدلها إذا لزم الأمر")
            # جدول تفاعلي يسمح بالتعديل اليدوي قبل التحميل
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            
            # تجهيز ملف الاكسيل
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                edited_df.to_excel(writer, index=False, sheet_name='Sheet1')
            
            st.divider()
            st.download_button(
                label="📥 تحميل ملف Excel الجاهز",
                data=buffer.getvalue(),
                file_name="Extracted_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

else:
    st.warning("⚠️ في انتظار رفع ملف PDF للبدء...")

# تعليمات جانبية
st.sidebar.header("عن الأداة")
st.sidebar.info("هذه الأداة تستخدم محرك Tesseract OCR للتعرف على الحروف العربية والانجليزية من الصور والملفات الممسوحة ضوئياً.")
