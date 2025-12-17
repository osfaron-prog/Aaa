import streamlit as st
import pandas as pd
import io
import json
import re
import spacy
from google.cloud import vision
from google.oauth2 import service_account
from pdf2image import convert_from_bytes
from transformers import pipeline
from PIL import Image

# 1. إعدادات الصفحة والتصميم الفاخر
st.set_page_config(page_title="Ultra AI Document Studio", layout="wide", page_icon="🧬")

# CSS مخصص لتحسين الرؤية والحروف
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Cairo:wght@400;700&display=swap" rel="stylesheet">
    <style>
    html, body, [class*="st-"] {
        font-family: 'Roboto', 'Cairo', sans-serif;
        color: #1A1A1B;
    }
    .main {
        background: linear-gradient(to bottom right, #f8f9fa, #e9ecef);
    }
    .stCard {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        border: 1px solid #dee2e6;
        margin-bottom: 20px;
    }
    .highlight {
        color: #007bff;
        font-weight: bold;
    }
    /* تحسين وضوح الحروف في الجداول */
    .stDataFrame div {
        font-size: 16px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. تحميل نماذج الذكاء الاصطناعي (Caching)
@st.cache_resource
def load_heavy_models():
    # نموذج التلخيص والتحليل
    summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    nlp = spacy.load("en_core_web_sm")
    return summarizer, nlp

# 3. محرك الاستخراج والربط
def get_vision_client():
    try:
        if "GCP_JSON" in st.secrets:
            info = json.loads(st.secrets["GCP_JSON"].strip(), strict=False)
            creds = service_account.Credentials.from_service_account_info(info)
            return vision.ImageAnnotatorClient(credentials=creds)
    except Exception as e:
        st.error(f"Credentials Error: {e}")
    return None

# 4. الواجهة البرمجية
summarizer, nlp = load_heavy_models()
client = get_vision_client()

st.title("🧬 Ultra AI Document Intelligence")
st.markdown("### Advanced Neural Extraction & Chat System")

if client:
    uploaded_file = st.file_uploader("Upload Document (PDF/Image)", type=["pdf", "jpg", "png", "jpeg"])
    
    if uploaded_file:
        with st.spinner('🧬 Activating Neural Layers...'):
            # تحويل المستند
            if uploaded_file.type == "application/pdf":
                images = convert_from_bytes(uploaded_file.read())
            else:
                images = [Image.open(uploaded_file)]

            full_text = ""
            for img in images:
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                response = client.document_text_detection(image=vision.Image(content=buf.getvalue()))
                full_text += response.full_text_annotation.text + "\n"

            # عرض النتائج في Dashboard
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("🤖 AI Smart Summary")
                if len(full_text.split()) > 40:
                    summary = summarizer(full_text[:1024], max_length=150, min_length=40, do_sample=False)[0]['summary_text']
                    st.write(summary)
                else:
                    st.warning("Text too short for summarization.")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("🔍 Named Entity Recognition")
                doc = nlp(full_text[:5000])
                ents = [{"Entity": ent.text, "Type": ent.label_} for ent in doc.ents]
                if ents:
                    st.table(pd.DataFrame(ents).drop_duplicates().head(10))
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("💬 Ask the Document")
                user_question = st.text_input("What would you like to know?")
                if user_question:
                    # نظام Q&A بسيط يعتمد على الـ Regex والذكاء الاصطناعي
                    if any(word in user_question.lower() for word in ["date", "التاريخ"]):
                        found = re.search(r"(\d{1,4}[-/]\d{1,2}[-/]\d{2,4})", full_text)
                        st.success(f"I found this date: {found.group(0)}" if found else "Date not found.")
                    else:
                        st.info("I am analyzing the context... (NLP active)")
                        # هنا يمكن إضافة دالة QA كاملة
                st.markdown('</div>', unsafe_allow_html=True)

            # التصدير النهائي
            st.divider()
            with st.expander("📄 Full Extracted Text (Highly Visible)"):
                st.markdown(f"<div style='font-size:18px; line-height:1.6;'>{full_text}</div>", unsafe_allow_html=True)

else:
    st.error("GCP_JSON is missing! Project cannot start without Google AI Credentials.")
