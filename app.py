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
from PIL import Image, ImageOps

# 1. إعدادات الصفحة والوضع الداكن (Quantum Dark UI)
st.set_page_config(page_title="NEURAL DOC HUB", layout="wide", page_icon="🌑")

st.markdown("""
    <style>
    /* التنسيق الداكن العميق */
    .stApp { background-color: #0b0e14; color: #e6edf3; }
    h1, h2, h3 { color: #58a6ff !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* تصميم الكروت الاحترافية */
    .ai-card {
        background: #161b22;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30363d;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    /* تحسين وضوح الحروف */
    .ocr-output {
        font-family: 'Consolas', 'Courier New', monospace;
        color: #d1d5db;
        background: #0d1117;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #58a6ff;
        line-height: 1.7;
        font-size: 16px;
    }
    
    /* أزرار مخصصة */
    .stButton>button { width: 100%; background-color: #238636; color: white !important; border: none; }
    </style>
    """, unsafe_allow_html=True)

# 2. تحميل المحركات (AI Engines)
@st.cache_resource
def load_all_engines():
    # محرك التلخيص (DistilBART)
    summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    # محرك استخراج الأسماء والجهات (Spacy)
    try:
        nlp = spacy.load("en_core_web_sm")
    except:
        import os
        os.system("python -m spacy download en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
    return summarizer, nlp

# 3. الربط مع Google Vision API
def get_vision_client():
    try:
        if "GCP_JSON" in st.secrets:
            json_info = json.loads(st.secrets["GCP_JSON"].strip(), strict=False)
            creds = service_account.Credentials.from_service_account_info(json_info)
            return vision.ImageAnnotatorClient(credentials=creds)
    except Exception as e:
        st.error(f"Credentials Error: {e}")
    return None

# 4. الواجهة والمنطق (The App Body)
summarizer, nlp = load_all_engines()
client = get_vision_client()

st.title("🌑 NEURAL DOCUMENT INTELLIGENCE HUB")
st.caption("The ultimate hybrid system for OCR, NLP Analysis, and Risk Assessment")

if client:
    with st.sidebar:
        st.header("⚙️ Control Panel")
        st.info("System: Connected to Google Cloud AI")
        st.divider()
        mode = st.radio("Processing Mode", ["High Accuracy", "Fast Scan"])
        st.write("---")
        st.success("NLP Models: Ready")

    uploaded_file = st.file_uploader("Drop your Document (PDF/Image)", type=["pdf", "jpg", "png", "jpeg"])

    if uploaded_file:
        with st.spinner('🧬 Synchronizing Neural Networks...'):
            # معالجة الملف وتحويله لنص
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

            # 5. تحليل البيانات (The AI Logic)
            # أ. استخراج الكيانات (NER)
            doc = nlp(full_text[:5000])
            entities = [{"Text": ent.text, "Category": ent.label_} for ent in doc.ents]
            
            # ب. تقييم المخاطر (Risk Check)
            risk_keywords = ["fine", "penalty", "court", "lawsuit", "urgent", "غرامة", "محكمة", "فوري"]
            risk_score = sum(15 for word in risk_keywords if word in full_text.lower())
            risk_score = min(risk_score, 100)

            # 6. لوحة التحكم (The Dashboard)
            col_left, col_right = st.columns([2, 1])

            with col_left:
                st.markdown('<div class="ai-card">', unsafe_allow_html=True)
                st.subheader("🤖 AI Executive Summary")
                if len(full_text.split()) > 40:
                    summary_text = summarizer(full_text[:1024], max_length=150, min_length=40)[0]['summary_text']
                    st.write(summary_text)
                else:
                    st.write("Insufficient data for neural summarization.")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="ai-card">', unsafe_allow_html=True)
                st.subheader("📊 Structured Intelligence (NER)")
                if entities:
                    st.dataframe(pd.DataFrame(entities).drop_duplicates(), use_container_width=True, height=250)
                else:
                    st.write("No named entities detected.")
                st.markdown('</div>', unsafe_allow_html=True)

            with col_right:
                st.markdown('<div class="ai-card">', unsafe_allow_html=True)
                st.subheader("⚖️ Compliance Score")
                st.metric("Risk Level", f"{risk_score}%", delta="- Negative" if risk_score > 40 else "+ Healthy")
                st.progress(risk_score / 100)
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="ai-card">', unsafe_allow_html=True)
                st.subheader("💬 Smart Q&A")
                q = st.text_input("Ask a question about the doc:")
                if q:
                    if "date" in q.lower() or "تاريخ" in q:
                        found_date = re.search(r"(\d{1,4}[-/]\d{1,2}[-/]\d{2,4})", full_text)
                        st.info(f"Found: {found_date.group(0)}" if found_date else "No date found.")
                    else:
                        st.write("Contextual searching...")
                st.markdown('</div>', unsafe_allow_html=True)

            # 7. قسم الحروف والوضوح (The Visible Font Section)
            st.divider()
            tab_view, tab_raw, tab_export = st.tabs(["🖼️ Document View", "📜 Decoded Stream", "📥 Export Report"])
            
            with tab_view:
                st.image(images[0], use_container_width=True)
            
            with tab_raw:
                st.markdown(f'<div class="ocr-output">{full_text}</div>', unsafe_allow_html=True)

            with tab_export:
                excel_df = pd.DataFrame(entities)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    excel_df.to_excel(writer, index=False)
                st.download_button("📥 Download Intelligence Report (Excel)", output.getvalue(), "AI_Analysis.xlsx")

else:
    st.error("GCP_JSON MISSING IN SECRETS! Please activate the AI Brain first.")
