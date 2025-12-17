import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import pandas as pd
import re
import io
from PIL import Image, ImageOps

# 1. تهيئة الصفحة بتصميم Dashboard
st.set_page_config(page_title="AI Data Studio", layout="wide", page_icon="💎")

# 2. CSS مخصص لتحويل الواجهة إلى Dashboard احترافي
st.markdown("""
    <style>
    /* تحسين الخلفية العامة */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    /* تصميم الكروت (Cards) */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 20px;
    }
    /* تنسيق النصوص */
    h1, h2, h3 {
        color: #2c3e50 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* إخفاء القوائم غير الضرورية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 3. وظيفة الاستخراج الذكية (Logic)
def extract_logic(text):
    patterns = {
        "Name": r"(?:Name|Customer|Patient|الاسم|السيد)\s*[:\-]\s*([a-zA-Z\s\u0621-\u064A]{3,30})",
        "Date": r"(\d{1,4}[-/]\d{1,2}[-/]\d{2,4})",
        "Amount": r"(?:Total|Amount|المبلغ|إجمالي)\s*[:\-]?\s*([\d,]+\.?\d*)"
    }
    extracted = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        extracted[key] = match.group(1).strip() if match else "Not Found"
    return extracted

# 4. Header Section
st.title("💎 AI Data Extraction Studio")
st.markdown("### Turn Scanned Documents into Structured Business Intelligence")

# 5. Dashboard Metrics (ملخص سريع)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<div class="metric-card"><h4>Files Uploaded</h4><h2 style="color:#007bff">1</h2></div>', unsafe_allow_html=True)

# 6. Main Sidebar
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/281/281760.png", width=100)
st.sidebar.header("Control Panel")
enhance_image = st.sidebar.checkbox("AI Image Enhancement", value=True)
ocr_speed = st.sidebar.select_slider("OCR Precision", options=["Fast", "Balanced", "High Accuracy"])

# 7. File Upload Section
uploaded_files = st.file_uploader("Upload Scanned PDFs or Images", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True)

if uploaded_files:
    all_rows = []
    
    for uploaded_file in uploaded_files:
        with st.spinner(f'Analyzing {uploaded_file.name}...'):
            # معالجة الملف
            if uploaded_file.type == "application/pdf":
                images = convert_from_bytes(uploaded_file.read())
            else:
                images = [Image.open(uploaded_file)]
            
            # معالجة كل صفحة
            for i, img in enumerate(images):
                # تحسين الصورة AI
                if enhance_image:
                    img = ImageOps.grayscale(img)
                    img = ImageOps.autocontrast(img)
                
                # استخراج النص
                raw_text = pytesseract.image_to_string(img, lang='eng+ara')
                data = extract_logic(raw_text)
                data["File Name"] = uploaded_file.name
                data["Page"] = i + 1
                all_rows.append(data)

    # تحويل للجدول
    df = pd.DataFrame(all_rows)
    
    # تنسيق عرض الـ Dashboard
    main_tab, preview_tab = st.tabs(["📊 Data Explorer", "🖼️ Document Preview"])
    
    with main_tab:
        st.markdown("#### 📝 Verified Extractions")
        # الجدول الجديد العريض
        edited_df = st.data_editor(
            df, 
            width=1400, # استبدال use_container_width
            num_rows="dynamic",
            column_config={
                "Amount": st.column_config.NumberColumn("Total Amount", format="$%f"),
                "Page": st.column_config.NumberColumn("Page No", help="Page index from the file")
            }
        )
        
        # Export Actions
        st.markdown("---")
        c1, c2 = st.columns([1, 4])
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            edited_df.to_excel(writer, index=False)
        
        c1.download_button("📥 Export to Excel", data=output.getvalue(), file_name="Studio_Export.xlsx", mime="application/vnd.ms-excel")

    with preview_tab:
        st.info("Visual preview of processed documents")
        # عرض مصغر للصور
        for file in uploaded_files:
            st.write(f"Preview: {file.name}")
            # عرض أول صفحة فقط للمعاينة لتوفير المساحة
            st.image(images[0], width=400)

else:
    # شاشة ترحيب في حالة عدم وجود ملفات
    st.markdown("""
    <div style="text-align: center; padding: 100px;">
        <img src="https://cdn-icons-png.flaticon.com/512/4080/4080032.png" width="150">
        <h3>Ready to process your documents?</h3>
        <p>Drop your files above to start the AI analysis.</p>
    </div>
    """, unsafe_allow_html=True)
