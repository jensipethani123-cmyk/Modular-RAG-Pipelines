import csv
import html
import json
import os
import re
from datetime import datetime
from io import BytesIO, StringIO
import streamlit as st
from groq import Groq
from pypdf import PdfReader

st.set_page_config(
    page_title="KinetixRAG",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "doc_chunks" not in st.session_state:
    st.session_state.doc_chunks = []
if "loaded_file_name" not in st.session_state:
    st.session_state.loaded_file_name = ""
if "loaded_file_size_kb" not in st.session_state:
    st.session_state.loaded_file_size_kb = 0
if "loaded_file_ext" not in st.session_state:
    st.session_state.loaded_file_ext = "PDF"
if "active_file_count" not in st.session_state:
    st.session_state.active_file_count = 0
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "active_nav" not in st.session_state:
    st.session_state.active_nav = "Dashboard"
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "auto"
if "top_k_chunks" not in st.session_state:
    st.session_state.top_k_chunks = 4
if "pending_question" not in st.session_state:
    st.session_state.pending_question = ""
if "upload_success_banner" not in st.session_state:
    st.session_state.upload_success_banner = False

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        html, body, .stApp {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background:
                radial-gradient(circle at 64% 12%, rgba(99, 102, 241, 0.34), transparent 34%),
                radial-gradient(circle at 86% 24%, rgba(56, 189, 248, 0.16), transparent 36%),
                radial-gradient(circle at 18% 82%, rgba(79, 70, 229, 0.20), transparent 40%),
                radial-gradient(1.2px 1.2px at 12% 18%, rgba(255,255,255,0.85), transparent),
                radial-gradient(1px 1px at 31% 11%, rgba(147,197,253,0.75), transparent),
                radial-gradient(1.3px 1.3px at 54% 28%, rgba(255,255,255,0.85), transparent),
                radial-gradient(1px 1px at 78% 14%, rgba(196,181,253,0.8), transparent),
                radial-gradient(1.2px 1.2px at 93% 42%, rgba(255,255,255,0.75), transparent),
                radial-gradient(1px 1px at 43% 76%, rgba(125,211,252,0.6), transparent),
                linear-gradient(135deg, #020512 0%, #050a22 50%, #030617 100%);
            color: #f8fafc;
        }

        header[data-testid="stHeader"] {
            background: transparent !important;
        }

        .block-container {
            padding-top: 0.75rem;
            padding-bottom: 1.0rem;
            max-width: 1440px;
        }

        /* Sidebar Cosmic Theme */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #030718 0%, #060c26 55%, #04081b 100%) !important;
            border-right: 1px solid rgba(56, 189, 248, 0.28) !important;
            min-width: 215px !important;
            max-width: 235px !important;
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.0rem;
            padding-left: 0.85rem;
            padding-right: 0.85rem;
        }

        .k-side-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 2px 4px 14px 4px;
        }

        .k-side-title {
            font-size: 19px;
            font-weight: 800;
            color: #ffffff;
            line-height: 1.1;
            letter-spacing: -0.02em;
        }

        .k-side-sub {
            font-size: 10.5px;
            font-weight: 500;
            color: #94a3b8;
            margin-top: 2px;
        }

        section[data-testid="stSidebar"] .stButton {
            margin-bottom: 5px !important;
        }

        section[data-testid="stSidebar"] .stButton > button {
            width: 100% !important;
            justify-content: flex-start !important;
            text-align: left !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            padding: 8px 13px !important;
            border-radius: 10px !important;
        }

        section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
            background: transparent !important;
            border: 1px solid transparent !important;
            box-shadow: none !important;
            color: #cbd5e1 !important;
        }

        section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
            background: rgba(59, 130, 246, 0.14) !important;
            color: #ffffff !important;
        }

        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: linear-gradient(90deg, rgba(37, 99, 235, 0.92) 0%, rgba(79, 70, 229, 0.85) 100%) !important;
            color: #ffffff !important;
            border: 1px solid rgba(96, 165, 250, 0.65) !important;
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.42) !important;
        }

        .k-side-bot-card {
            margin-top: 14px;
            background: linear-gradient(165deg, rgba(13, 24, 62, 0.88), rgba(6, 12, 34, 0.95));
            border: 1px solid rgba(99, 102, 241, 0.35);
            border-radius: 15px;
            padding: 12px 10px;
            text-align: center;
            box-shadow: 0 8px 24px rgba(1, 4, 18, 0.75);
        }

        .k-side-tagline {
            font-size: 12px;
            font-weight: 700;
            color: #f1f5f9;
            line-height: 1.32;
            margin-top: 5px;
        }

        /* Hero Section */
        .rag-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(23, 35, 76, 0.85);
            border: 1px solid rgba(96, 165, 250, 0.55);
            color: #93c5fd;
            font-size: 10.5px;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 999px;
            margin-bottom: 6px;
            box-shadow: 0 0 14px rgba(59, 130, 246, 0.28);
        }

        .hero-title {
            margin: 0;
            font-size: 38px;
            font-weight: 800;
            letter-spacing: -0.03em;
            color: #ffffff;
            line-height: 1.06;
            text-shadow: 0 0 28px rgba(99, 102, 241, 0.35);
        }

        .hero-sub {
            margin: 6px 0 0 0;
            font-size: 13px;
            color: #cbd5e1;
            font-weight: 400;
            line-height: 1.42;
        }

        /* Top Stat Cards */
        .neon-stat-card {
            background: linear-gradient(165deg, rgba(16, 27, 68, 0.90) 0%, rgba(7, 13, 35, 0.96) 100%);
            border: 1.5px solid rgba(96, 165, 250, 0.58);
            border-radius: 15px;
            padding: 12px 6px;
            text-align: center;
            box-shadow:
                0 0 22px rgba(56, 189, 248, 0.20),
                inset 0 0 12px rgba(99, 102, 241, 0.14);
        }

        .neon-stat-num {
            font-size: 24px;
            font-weight: 800;
            color: #ffffff;
            line-height: 1.15;
            margin-top: 3px;
        }

        .neon-stat-lbl {
            font-size: 11px;
            font-weight: 600;
            color: #94a3b8;
            margin-top: 2px;
        }

        /* Main Neon Panels (Document Control & Ask & Explore) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: linear-gradient(165deg, rgba(10, 19, 50, 0.92) 0%, rgba(5, 10, 28, 0.96) 100%) !important;
            border: 1.5px solid rgba(56, 189, 248, 0.65) !important;
            border-radius: 18px !important;
            padding: 12px 15px !important;
            box-shadow:
                0 0 26px rgba(37, 99, 235, 0.25),
                0 0 10px rgba(56, 189, 248, 0.16),
                inset 0 0 16px rgba(59, 130, 246, 0.10) !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] > div,
        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        .panel-title {
            font-size: 15.5px;
            font-weight: 700;
            color: #ffffff;
            line-height: 1.2;
        }

        .panel-sub {
            font-size: 11px;
            color: #94a3b8;
            margin-top: 2px;
        }

        .drop-box-top {
            background: rgba(8, 16, 44, 0.80);
            border: 1.5px dashed rgba(96, 165, 250, 0.48);
            border-bottom: none;
            border-radius: 14px 14px 0 0;
            padding: 12px 10px 4px 10px;
            text-align: center;
            margin-top: 8px;
        }

        .drop-title {
            font-size: 13.5px;
            font-weight: 700;
            color: #f8fafc;
            margin-top: 5px;
        }

        .drop-or {
            font-size: 11px;
            color: #94a3b8;
            margin-top: 2px;
        }

        /* File Uploader Styled Like image_ef5a29.jpg */
        div[data-testid="stFileUploader"] section {
            background: rgba(8, 16, 44, 0.80) !important;
            border: 1.5px dashed rgba(96, 165, 250, 0.48) !important;
            border-top: none !important;
            border-radius: 0 0 14px 14px !important;
            padding: 4px 12px 12px 12px !important;
        }

        div[data-testid="stFileUploader"] section > div:first-child {
            display: none !important;
        }

        div[data-testid="stFileUploader"] section span,
        div[data-testid="stFileUploader"] section small {
            color: #94a3b8 !important;
        }

        div[data-testid="stFileUploader"] button,
        div[data-testid="stFileUploader"] button * {
            background: transparent !important;
            color: #ffffff !important;
        }

        div[data-testid="stFileUploader"] button {
            background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 55%, #2563eb 100%) !important;
            color: #ffffff !important;
            border: 1px solid rgba(167, 139, 250, 0.55) !important;
            border-radius: 10px !important;
            padding: 8px 24px !important;
            font-size: 12.5px !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 20px rgba(109, 40, 217, 0.48) !important;
        }

        div[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"],
        div[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] > div {
            background-color: rgba(15, 26, 64, 0.92) !important;
            color: #e2e8f0 !important;
            border: 1px solid rgba(96, 165, 250, 0.35) !important;
            border-radius: 9px !important;
        }

        .uploaded-file-card {
            background: rgba(12, 22, 56, 0.88);
            border: 1px solid rgba(96, 165, 250, 0.34);
            border-radius: 11px;
            padding: 9px 11px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 5px;
        }

        .uploaded-file-name {
            font-size: 12.5px;
            font-weight: 700;
            color: #f8fafc;
        }

        .uploaded-file-meta {
            font-size: 10.5px;
            color: #94a3b8;
        }

        .upload-ok-banner {
            background: linear-gradient(90deg, rgba(16, 185, 129, 0.25), rgba(5, 150, 105, 0.16));
            border: 1px solid rgba(52, 211, 153, 0.58);
            color: #a7f3d0;
            border-radius: 10px;
            padding: 8px 12px;
            font-size: 12px;
            font-weight: 600;
            margin-top: 7px;
        }

        /* Ask & Explore Chips & Chat */
        .try-label {
            font-size: 11.5px;
            font-weight: 700;
            color: #e2e8f0;
            margin-bottom: 5px;
        }

        .user-bubble-row {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 10px;
            margin: 8px 0 4px 0;
        }

        .user-bubble {
            background: linear-gradient(90deg, #4f46e5 0%, #6d28d9 100%);
            border: 1px solid rgba(167, 139, 250, 0.48);
            color: #ffffff;
            border-radius: 11px;
            padding: 8px 15px;
            font-size: 12.5px;
            font-weight: 600;
            box-shadow: 0 4px 16px rgba(79, 70, 229, 0.35);
        }

        .user-meta-time {
            text-align: right;
            font-size: 10px;
            color: #94a3b8;
            margin-right: 42px;
            margin-bottom: 6px;
        }

        .bot-panel-box {
            background: linear-gradient(155deg, rgba(20, 32, 74, 0.90) 0%, rgba(11, 18, 46, 0.94) 100%);
            border: 1px solid rgba(129, 140, 248, 0.36);
            border-radius: 15px;
            padding: 12px 15px;
            box-shadow: 0 8px 24px rgba(1, 4, 18, 0.50);
        }

        .bot-title-blue {
            font-size: 12.5px;
            font-weight: 700;
            color: #60a5fa;
            margin-bottom: 3px;
        }

        .bot-ready-head {
            font-size: 13px;
            font-weight: 700;
            color: #ffffff;
        }

        .bot-ready-desc {
            font-size: 12px;
            color: #cbd5e1;
            margin-top: 2px;
            line-height: 1.42;
        }

        .bot-ts {
            text-align: right;
            font-size: 10px;
            color: #94a3b8;
            margin-top: 5px;
        }

        /* Chat Input */
        div[data-testid="stChatInput"],
        div[data-testid="stChatInput"] > div,
        div[data-testid="stChatInput"] > div > div,
        div[data-testid="stChatInput"] textarea {
            background-color: rgba(10, 18, 46, 0.94) !important;
            color: #f8fafc !important;
            caret-color: #60a5fa !important;
        }

        div[data-testid="stChatInput"] {
            border: 1.5px solid rgba(96, 165, 250, 0.58) !important;
            border-radius: 13px !important;
            box-shadow: 0 0 18px rgba(59, 130, 246, 0.20) !important;
        }

        div[data-testid="stChatInput"] textarea::placeholder {
            color: #94a3b8 !important;
        }

        div[data-testid="stChatInput"] button {
            background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 9px !important;
        }

        /* Main Buttons & Chips */
        div[data-testid="stMainBlockContainer"] .stButton > button {
            border-radius: 9px !important;
            font-weight: 600 !important;
            font-size: 11px !important;
            white-space: nowrap !important;
        }

        div[data-testid="stMainBlockContainer"] .stButton > button:not([kind="primary"]) {
            background: rgba(18, 29, 66, 0.88) !important;
            color: #e2e8f0 !important;
            border: 1px solid rgba(96, 165, 250, 0.36) !important;
        }

        div[data-testid="stMainBlockContainer"] .stButton > button:not([kind="primary"]):hover {
            background: rgba(37, 99, 235, 0.38) !important;
            border-color: rgba(147, 197, 253, 0.68) !important;
            color: #ffffff !important;
        }

        div[data-testid="stMainBlockContainer"] .stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #2563eb 0%, #4f46e5 100%) !important;
            color: #ffffff !important;
            border: 1px solid rgba(129, 140, 248, 0.58) !important;
            box-shadow: 0 4px 18px rgba(37, 99, 235, 0.38) !important;
        }

        .k-bottom-bar {
            margin-top: 10px;
            padding-top: 6px;
            border-top: 1px solid rgba(96, 165, 250, 0.16);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
            color: #94a3b8;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_groq_key() -> str:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if key:
        return key
    try:
        return str(st.secrets.get("GROQ_API_KEY", "")).strip()
    except Exception:
        return ""


def get_model_candidates(client: Groq) -> list[str]:
    preferred = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "gemma2-9b-it",
        "qwen/qwen3-32b",
    ]
    selected = st.session_state.selected_model
    ordered = []
    if selected and selected != "auto":
        ordered.append(selected)

    try:
        models_page = client.models.list()
        available_ids = [
            m.id
            for m in getattr(models_page, "data", [])
            if getattr(m, "id", None)
            and not any(skip in m.id.lower() for skip in ("whisper", "guard", "embed", "tts", "playai"))
        ]
        for p in preferred:
            if p in available_ids and p not in ordered:
                ordered.append(p)
        for m_id in available_ids:
            if m_id not in ordered:
                ordered.append(m_id)
    except Exception:
        for p in preferred:
            if p not in ordered:
                ordered.append(p)

    return ordered or preferred


def chat_with_groq(messages: list[dict], api_key: str, temperature: float = 0.2) -> str:
    client = Groq(api_key=api_key)
    candidates = get_model_candidates(client)
    errors = []

    for model_name in candidates:
        try:
            resp = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
            )
            content = (resp.choices[0].message.content or "").strip()
            if content:
                st.session_state.last_used_model = model_name
                return content
        except Exception as err:
            errors.append(f"{model_name}: {err}")

    raise RuntimeError(" | ".join(errors[-2:]) if errors else "No available Groq model responded.")


def split_into_chunks(text: str, source_label: str, chunk_size: int = 900, overlap: int = 150) -> list[dict]:
    cleaned = re.sub(r"\s+", " ", (text or "")).strip()
    if not cleaned:
        return []

    chunks = []
    start = 0
    while start < len(cleaned):
        end = start + chunk_size
        piece = cleaned[start:end].strip()
        if piece:
            chunks.append({"source": source_label, "text": piece})
        start += max(1, chunk_size - overlap)
    return chunks


def extract_document_chunks(uploaded_file) -> list[dict]:
    file_name = uploaded_file.name.lower()
    raw_bytes = uploaded_file.getvalue()

    if file_name.endswith(".pdf"):
        reader = PdfReader(BytesIO(raw_bytes))
        all_chunks = []
        for page_idx, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            all_chunks.extend(split_into_chunks(page_text, f"Page {page_idx}"))
        return all_chunks

    decoded_text = raw_bytes.decode("utf-8", errors="replace")

    if file_name.endswith(".csv"):
        reader = csv.DictReader(StringIO(decoded_text))
        row_chunks = []
        for idx, row in enumerate(reader, start=1):
            row_str = " | ".join([f"{k}: {v}" for k, v in row.items() if k is not None])
            row_chunks.extend(split_into_chunks(row_str, f"Row {idx}", chunk_size=700, overlap=80))
        return row_chunks if row_chunks else split_into_chunks(decoded_text, "CSV Data")

    if file_name.endswith(".json"):
        try:
            parsed = json.loads(decoded_text)
            pretty_json = json.dumps(parsed, indent=2, ensure_ascii=False)
        except Exception:
            pretty_json = decoded_text
        return split_into_chunks(pretty_json, "JSON Data")

    return split_into_chunks(decoded_text, "Text Section")


def retrieve_relevant_chunks(question: str, chunks: list[dict], top_k: int = 4) -> list[dict]:
    words = {w.lower() for w in re.findall(r"\w{3,}", question)}
    if not words:
        return chunks[:top_k]

    scored = []
    for item in chunks:
        lower_text = item["text"].lower()
        score = sum(lower_text.count(w) for w in words)
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    best = [item for score, item in scored if score > 0][:top_k]
    return best if best else chunks[:top_k]


def ask_groq_about_doc(question: str, relevant_chunks: list[dict], api_key: str) -> str:
    context_block = "\n\n".join([f"[{c['source']}]: {c['text']}" for c in relevant_chunks])
    prompt = (
        "You are KinetixRAG Assistant, a clear and helpful AI document assistant. "
        "Answer the user's question accurately using the provided document context when available.\n"
        "Use clean bullet points for key details and mention source sections or pages when relevant.\n\n"
        f"Document Context:\n{context_block}\n\n"
        f"Question: {question}"
    )
    return chat_with_groq(
        messages=[
            {"role": "system", "content": "You are KinetixRAG Assistant. Be clear, accurate, and concise."},
            {"role": "user", "content": prompt},
        ],
        api_key=api_key,
        temperature=0.2,
    )


def run_query(question: str):
    timestamp = datetime.now().strftime("%I:%M %p")
    groq_key = get_groq_key()

    if not st.session_state.doc_chunks:
        if "what is kinetixrag" in question.lower():
            ans = (
                "KinetixRAG is an AI-powered RAG document assistant that lets you upload PDF, TXT, CSV, or JSON files, "
                "splits them into searchable chunks, and answers questions with relevant excerpts."
            )
            st.session_state.chat_history.append(
                {"question": question, "answer": ans, "sources": [], "time": timestamp}
            )
            return

        if groq_key:
            try:
                ans = chat_with_groq(
                    messages=[
                        {"role": "system", "content": "You are KinetixRAG Assistant. Keep answers concise and helpful."},
                        {"role": "user", "content": question},
                    ],
                    api_key=groq_key,
                    temperature=0.3,
                )
            except Exception as err:
                ans = f"Please upload a document in Document Control first to query your files. (Note: {err})"
        else:
            ans = "Please upload a PDF, TXT, CSV, or JSON file in Document Control on the left and process it."

        st.session_state.chat_history.append(
            {"question": question, "answer": ans, "sources": [], "time": timestamp}
        )
        return

    top_chunks = retrieve_relevant_chunks(question, st.session_state.doc_chunks, top_k=st.session_state.top_k_chunks)
    if groq_key:
        try:
            ans = ask_groq_about_doc(question, top_chunks, groq_key)
        except Exception as err:
            ans = (
                f"API error: {err}\n\nMatching excerpts:\n"
                + "\n\n".join([f"**{c['source']}:** {c['text'][:250]}" for c in top_chunks[:2]])
            )
    else:
        ans = (
            "GROQ_API_KEY is not set; showing top matching excerpts:\n\n"
            + "\n\n".join([f"**{c['source']}:** {c['text'][:250]}" for c in top_chunks[:2]])
        )

    st.session_state.chat_history.append(
        {"question": question, "answer": ans, "sources": top_chunks, "time": timestamp}
    )


def clear_loaded_document():
    st.session_state.doc_chunks = []
    st.session_state.loaded_file_name = ""
    st.session_state.loaded_file_size_kb = 0
    st.session_state.active_file_count = 0
    st.session_state.upload_success_banner = False


with st.sidebar:
    st.markdown(
        """
        <div class="k-side-brand">
            <svg width="36" height="36" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="sideKGrad" x1="4" y1="4" x2="44" y2="44" gradientUnits="userSpaceOnUse">
                        <stop offset="0%" stop-color="#38BDF8"/>
                        <stop offset="55%" stop-color="#6366F1"/>
                        <stop offset="100%" stop-color="#9333EA"/>
                    </linearGradient>
                </defs>
                <rect x="4" y="4" width="40" height="40" rx="11" fill="url(#sideKGrad)"/>
                <path d="M16 14V34M31 14L20 24L32 34" stroke="#FFFFFF" stroke-width="4.2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <div>
                <div class="k-side-title">KinetixRAG</div>
                <div class="k-side-sub">RAG Powered AI</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav_items = [
        ("🏠", "Dashboard"),
        ("🕒", "History"),
        ("⚙️", "Settings"),
        ("ℹ️", "About"),
    ]
    for icon, label in nav_items:
        btn_type = "primary" if st.session_state.active_nav == label else "secondary"
        if st.button(f"{icon}   {label}", key=f"nav_{label}", type=btn_type, use_container_width=True):
            st.session_state.active_nav = label
            st.rerun()

    st.markdown(
        """
        <div class="k-side-bot-card">
            <svg width="56" height="50" viewBox="0 0 64 58" fill="none" xmlns="http://www.w3.org/2000/svg">
                <line x1="32" y1="4" x2="32" y2="12" stroke="#93C5FD" stroke-width="2.5" stroke-linecap="round"/>
                <circle cx="32" cy="4" r="3" fill="#38BDF8"/>
                <rect x="14" y="12" width="36" height="26" rx="11" fill="#1E2952" stroke="#60A5FA" stroke-width="2"/>
                <rect x="20" y="19" width="24" height="11" rx="5.5" fill="#090F26"/>
                <circle cx="26.5" cy="24.5" r="2.6" fill="#38BDF8"/>
                <circle cx="37.5" cy="24.5" r="2.6" fill="#38BDF8"/>
                <rect x="20" y="40" width="24" height="12" rx="6" fill="#2563EB" stroke="#93C5FD" stroke-width="1.5"/>
            </svg>
            <div class="k-side-tagline">Smarter Search.<br>Deeper Insights.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

h_left, h_mid, h_s1, h_s2, h_s3 = st.columns([2.25, 1.15, 0.72, 0.72, 0.72], gap="medium")

with h_left:
    st.markdown(
        """
        <div style="padding: 2px 0 4px 0;">
            <div class="rag-pill">✦ RAG Powered AI</div>
            <div class="hero-title">KinetixRAG</div>
            <div class="hero-sub">Upload PDFs, TXT, CSV or JSON files and ask questions<br>for instant answers with advanced RAG technology.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with h_mid:
    st.markdown(
        """
        <div style="display:flex; justify-content:center; align-items:center; padding-top:4px;">
            <svg width="166" height="92" viewBox="0 0 190 110" fill="none" xmlns="http://www.w3.org/2000/svg">
                <ellipse cx="95" cy="56" rx="78" ry="34" fill="#4F46E5" opacity="0.24"/>
                <g transform="rotate(-12 56 54)">
                    <rect x="34" y="22" width="44" height="58" rx="8" fill="#1E1B4B" stroke="#F87171" stroke-width="2"/>
                    <text x="56" y="54" fill="#FCA5A5" font-size="13" font-weight="800" text-anchor="middle">PDF</text>
                </g>
                <g transform="translate(72, 16)">
                    <rect x="0" y="0" width="46" height="62" rx="8" fill="#172554" stroke="#60A5FA" stroke-width="2"/>
                    <text x="23" y="34" fill="#BFDBFE" font-size="13" font-weight="800" text-anchor="middle">TXT</text>
                </g>
                <g transform="rotate(12 142 54)">
                    <rect x="120" y="22" width="44" height="58" rx="8" fill="#064E3B" stroke="#34D399" stroke-width="2"/>
                    <text x="142" y="54" fill="#A7F3D0" font-size="13" font-weight="800" text-anchor="middle">CSV</text>
                </g>
            </svg>
        </div>
        """,
        unsafe_allow_html=True,
    )

with h_s1:
    st.markdown(
        f"""
        <div class="neon-stat-card">
            <div style="font-size:19px;">🗂️</div>
            <div class="neon-stat-num">{st.session_state.active_file_count}</div>
            <div class="neon-stat-lbl">Active Files</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with h_s2:
    st.markdown(
        f"""
        <div class="neon-stat-card">
            <div style="font-size:19px;">💬</div>
            <div class="neon-stat-num">{len(st.session_state.chat_history)}</div>
            <div class="neon-stat-lbl">Queries</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with h_s3:
    st.markdown(
        """
        <div class="neon-stat-card">
            <div style="font-size:19px;">⭐</div>
            <div class="neon-stat-num">0</div>
            <div class="neon-stat-lbl">Credits</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

if st.session_state.active_nav == "Dashboard":
    left_col, right_col = st.columns([1.08, 1.92], gap="medium")

    with left_col:
        with st.container(border=True):
            st.markdown(
                """
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="width:34px; height:34px; border-radius:10px; background:linear-gradient(135deg,#2563eb,#4f46e5); display:flex; align-items:center; justify-content:center; font-size:16px;">☁️</div>
                    <div>
                        <div class="panel-title">Document Control</div>
                        <div class="panel-sub">Upload your files to build your knowledge base</div>
                    </div>
                </div>
                <div class="drop-box-top">
                    <svg width="40" height="30" viewBox="0 0 56 44" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M16 36H42C47.5228 36 52 31.5228 52 26C52 20.8403 48.0921 16.5931 43.0736 16.0566C41.2981 9.11942 35.0046 4 27.5 4C18.6634 4 11.5 11.1634 11.5 20C11.5 20.3492 11.5112 20.6958 11.5332 21.0394C7.28397 22.1292 4 25.9844 4 30.6C4 33.5823 6.41766 36 9.4 36H16Z" stroke="#60A5FA" stroke-width="2.6" fill="rgba(59,130,246,0.16)"/>
                        <path d="M28 29V16M28 16L22 22M28 16L34 22" stroke="#93C5FD" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <div class="drop-title">Drag &amp; Drop your files here</div>
                    <div class="drop-or">or</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            uploaded_doc = st.file_uploader(
                "Choose Files",
                type=["pdf", "txt", "csv", "json"],
                label_visibility="collapsed",
            )

            st.markdown(
                "<div style='text-align:center; font-size:10.5px; color:#94a3b8; margin-top:4px;'>Supported: PDF, TXT, CSV, JSON</div>"
                "<div style='text-align:center; font-size:10.5px; font-weight:700; color:#cbd5e1; margin:3px 0 5px 0;'>OR</div>",
                unsafe_allow_html=True,
            )

            if st.button("Process & Index Document", type="primary", use_container_width=True):
                if uploaded_doc is not None:
                    chunks = extract_document_chunks(uploaded_doc)
                    if chunks:
                        st.session_state.doc_chunks = chunks
                        st.session_state.loaded_file_name = uploaded_doc.name
                        st.session_state.loaded_file_size_kb = max(1, round(len(uploaded_doc.getvalue()) / 1024))
                        st.session_state.loaded_file_ext = uploaded_doc.name.split(".")[-1].upper()
                        st.session_state.active_file_count = 1
                        st.session_state.chat_history = []
                        st.session_state.upload_success_banner = True
                        st.rerun()
                    else:
                        st.error("Could not extract text from this file.")
                else:
                    st.warning("Please choose a file first.")

            if st.session_state.doc_chunks:
                hdr_f1, hdr_f2 = st.columns([2.2, 1])
                with hdr_f1:
                    st.markdown(
                        f"<div style='font-size:12px; font-weight:700; color:#e2e8f0; margin-top:5px;'>Uploaded Files ({st.session_state.active_file_count})</div>",
                        unsafe_allow_html=True,
                    )
                with hdr_f2:
                    if st.button("🗑️ Clear All", key="clear_uploaded_btn", use_container_width=True):
                        clear_loaded_document()
                        st.rerun()

                st.markdown(
                    f"""
                    <div class="uploaded-file-card">
                        <div style="display:flex; align-items:center; gap:9px;">
                            <div style="background:#ef4444; color:#ffffff; font-size:9.5px; font-weight:800; padding:4px 6px; border-radius:6px;">{html.escape(st.session_state.loaded_file_ext)}</div>
                            <div>
                                <div class="uploaded-file-name">{html.escape(st.session_state.loaded_file_name)}</div>
                                <div class="uploaded-file-meta">{html.escape(st.session_state.loaded_file_ext)} • {st.session_state.loaded_file_size_kb} KB • {len(st.session_state.doc_chunks)} chunks</div>
                            </div>
                        </div>
                        <div style="color:#34d399; font-weight:800; font-size:13px;">✓</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.session_state.upload_success_banner:
                    st.markdown(
                        '<div class="upload-ok-banner">✓ &nbsp;File uploaded successfully!</div>',
                        unsafe_allow_html=True,
                    )

    with right_col:
        with st.container(border=True):
            r_hdr_l, r_hdr_r = st.columns([3.5, 1])
            with r_hdr_l:
                st.markdown(
                    """
                    <div style="display:flex; align-items:center; gap:10px;">
                        <div style="width:34px; height:34px; border-radius:10px; background:linear-gradient(135deg,#6366f1,#9333ea); display:flex; align-items:center; justify-content:center; font-size:15px;">💬</div>
                        <div>
                            <div class="panel-title">Ask &amp; Explore</div>
                            <div class="panel-sub">Ask anything about your documents and get instant answers.</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with r_hdr_r:
                if st.button("🗑️ Clear Chat", key="clear_chat_top", use_container_width=True):
                    st.session_state.chat_history = []
                    st.rerun()

            st.markdown('<div class="try-label" style="margin-top:6px;">✦ Try asking:</div>', unsafe_allow_html=True)
            chips = [
                "What is KinetixRAG?",
                "Summarize the document",
                "Key points?",
                "Any contact info?",
            ]
            chip_cols = st.columns([1.3, 1.55, 0.95, 1.2], gap="small")
            for idx, chip_text in enumerate(chips):
                with chip_cols[idx]:
                    if st.button(chip_text, key=f"chip_{idx}", use_container_width=True):
                        st.session_state.pending_question = chip_text

            now_str = datetime.now().strftime("%I:%M %p")

            if not st.session_state.chat_history:
                st.markdown(
                    f"""
                    <div class="user-bubble-row">
                        <div class="user-bubble">KinetixRAG Workspace is Ready</div>
                        <div style="width:30px; height:30px; border-radius:999px; background:linear-gradient(135deg,#38bdf8,#2563eb); display:flex; align-items:center; justify-content:center; font-size:14px;">👤</div>
                    </div>
                    <div class="user-meta-time">{now_str} ✓✓</div>
                    """,
                    unsafe_allow_html=True,
                )

                bot_col_l, bot_col_r = st.columns([0.13, 0.87], gap="small")
                with bot_col_l:
                    st.markdown(
                        """
                        <div style="margin-top:4px; display:flex; justify-content:center;">
                            <svg width="34" height="34" viewBox="0 0 64 58" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <rect x="14" y="12" width="36" height="26" rx="11" fill="#1E2952" stroke="#60A5FA" stroke-width="2"/>
                                <rect x="20" y="19" width="24" height="11" rx="5.5" fill="#090F26"/>
                                <circle cx="26.5" cy="24.5" r="2.6" fill="#38BDF8"/>
                                <circle cx="37.5" cy="24.5" r="2.6" fill="#38BDF8"/>
                            </svg>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with bot_col_r:
                    st.markdown(
                        f"""
                        <div class="bot-panel-box">
                            <div class="bot-title-blue">KinetixRAG Assistant</div>
                            <div class="bot-ready-head">KinetixRAG Workspace is Ready! 🎉</div>
                            <div class="bot-ready-desc">You can now upload your documents and ask any questions. The system will search through your files and provide accurate, relevant answers.</div>
                            <div class="bot-ts">{now_str}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            for turn in st.session_state.chat_history:
                q_esc = html.escape(turn["question"])
                t_esc = html.escape(turn.get("time", now_str))
                st.markdown(
                    f"""
                    <div class="user-bubble-row">
                        <div class="user-bubble">{q_esc}</div>
                        <div style="width:30px; height:30px; border-radius:999px; background:linear-gradient(135deg,#38bdf8,#2563eb); display:flex; align-items:center; justify-content:center; font-size:14px;">👤</div>
                    </div>
                    <div class="user-meta-time">{t_esc} ✓✓</div>
                    """,
                    unsafe_allow_html=True,
                )
                with st.container(border=True):
                    st.markdown('<div class="bot-title-blue">KinetixRAG Assistant</div>', unsafe_allow_html=True)
                    st.markdown(turn["answer"])
                    st.markdown(f'<div class="bot-ts">{t_esc}</div>', unsafe_allow_html=True)
                if turn.get("sources"):
                    with st.expander("View Referenced Excerpts", expanded=False):
                        for src in turn["sources"]:
                            st.markdown(f"**{src['source']}:** {src['text'][:260]}...")

            typed_q = st.chat_input("Ask any question about the uploaded files...")
            question_to_run = st.session_state.pending_question or (typed_q.strip() if typed_q else "")
            if question_to_run:
                st.session_state.pending_question = ""
                run_query(question_to_run)
                st.rerun()

elif st.session_state.active_nav == "History":
    with st.container(border=True):
        st.markdown('<div class="panel-title">🕒 Query History</div>', unsafe_allow_html=True)
        if not st.session_state.chat_history:
            st.info("No queries asked yet in this session.")
        else:
            for i, item in enumerate(reversed(st.session_state.chat_history), start=1):
                st.markdown(f"**{i}. {item['question']}** ({item.get('time', '')})")
                st.markdown(item["answer"])
                st.divider()

elif st.session_state.active_nav == "Settings":
    with st.container(border=True):
        st.markdown('<div class="panel-title">⚙️ KinetixRAG Settings</div>', unsafe_allow_html=True)
        model_opts = ["auto", "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it", "qwen/qwen3-32b"]
        curr_idx = model_opts.index(st.session_state.selected_model) if st.session_state.selected_model in model_opts else 0
        st.session_state.selected_model = st.selectbox("Groq Model", model_opts, index=curr_idx)
        st.session_state.top_k_chunks = st.slider("Retrieved Chunks per Query", min_value=2, max_value=8, value=st.session_state.top_k_chunks)
        st.info("GROQ_API_KEY status: " + ("Configured" if get_groq_key() else "Not found in environment/secrets"))
        if st.session_state.get("last_used_model"):
            st.caption(f"Last active Groq model: {st.session_state.last_used_model}")

else:
    with st.container(border=True):
        st.markdown('<div class="panel-title">ℹ️ About KinetixRAG</div>', unsafe_allow_html=True)
        st.write("KinetixRAG parses PDF, TXT, CSV, and JSON documents and answers questions using Groq LLMs with source excerpts.")

st.markdown(
    """
    <div class="k-bottom-bar">
        <div>Built with <span style="color:#f43f5e;">♥</span> using RAG Technology</div>
        <div><span style="color:#34d399;">●</span> &nbsp;KinetixRAG v1.0.0</div>
    </div>
    """,
    unsafe_allow_html=True,
)