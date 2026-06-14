import streamlit as st
import sqlite3
import os
import datetime
import time
import base64
import re
import html
import hmac
import json
from io import BytesIO
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from PIL import Image

try:
    from streamlit_cropper import st_cropper
except ImportError:
    st_cropper = None

# --- 1. TASARIM VE CSS ---
st.set_page_config(page_title="Doç. Dr. Ömer Osman PALA | Klinik", layout="wide", page_icon="👨‍⚕️")

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR") or (BASE_DIR / "uploads"))
DB_PATH = Path(os.getenv("DB_PATH") or (BASE_DIR / "randevu_sistemi.db"))
TOKEN_PATH = BASE_DIR / "token.json"
CREDENTIALS_PATH = BASE_DIR / "credentials.json"
CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar']

UPLOAD_DIR.mkdir(exist_ok=True)

st.markdown("""
    <style>
    :root { color-scheme: light; }
    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background: #ffffff !important;
        color: #1f2937 !important;
        font-family: "Inter", "Segoe UI", sans-serif;
    }
    [data-testid="stHeader"] {
        background: rgba(255,255,255,0.92) !important;
        border-bottom: 1px solid #edf2f7;
    }
    #MainMenu,
    footer,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    [data-testid="stDeployButton"],
    [data-testid="manage-app-button"],
    [class*="viewerBadge"],
    [class*="ViewerBadge"],
    [class*="stAppDeployButton"],
    [class*="viewerBadge_container"],
    [class*="stStatusWidget"],
    div:has(> a[href*="streamlit.io"]),
    iframe[src*="streamlit.io"],
    iframe[title*="Streamlit"],
    a[href*="streamlit.io/cloud"],
    a[href*="streamlit.io"],
    div[style*="position: fixed"][style*="bottom"][style*="right"] {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }
    .block-container {
        max-width: 1160px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    section[data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #e5edf0;
        box-shadow: 8px 0 24px rgba(15,23,42,0.04);
    }
    section[data-testid="stSidebar"] * { color: #1f2937 !important; }
    section[data-testid="stSidebar"] h2 {
        color: #0b7a75 !important;
        font-weight: 800;
    }
    h1, h2, h3, h4, h5, h6, p, label, span, div {
        letter-spacing: 0 !important;
    }
    h1, h2, h3, h4 { color: #102a43 !important; }
    p, label, .stMarkdown, .stText { color: #4b5563 !important; }

    .stButton>button, .stDownloadButton>button {
        width: 100%;
        min-height: 42px;
        border-radius: 8px;
        background-color: #0b7a75;
        color: #ffffff !important;
        border: 1px solid #0b7a75;
        font-weight: 700;
        padding: 10px 14px;
        transition: transform 160ms ease, box-shadow 160ms ease, background-color 160ms ease;
        box-shadow: 0 7px 18px rgba(11,122,117,0.14);
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #095f5b;
        border-color: #095f5b;
        transform: translateY(-1px);
        box-shadow: 0 10px 24px rgba(11,122,117,0.20);
    }
    .stButton>button:focus { box-shadow: 0 0 0 3px rgba(11,122,117,0.18); }
    .stButton>button *, .stDownloadButton>button * {
        color: #ffffff !important;
    }

    .stTextInput input, .stTextArea textarea, .stNumberInput input,
    .stDateInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #111827 !important;
        border: 1.8px solid #0b7a75 !important;
        border-radius: 8px !important;
        box-shadow: 0 0 0 3px rgba(11,122,117,0.08) !important;
    }
    div[data-baseweb="input"],
    div[data-baseweb="textarea"],
    div[data-baseweb="select"] > div,
    div[data-baseweb="base-input"] {
        border-color: #0b7a75 !important;
        border-radius: 8px !important;
        box-shadow: 0 0 0 3px rgba(11,122,117,0.08) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus,
    .stDateInput input:focus {
        border-color: #0b7a75 !important;
        box-shadow: 0 0 0 4px rgba(11,122,117,0.16) !important;
    }

    .splash-screen {
        position: fixed;
        inset: 0;
        z-index: 99999;
        background: linear-gradient(180deg, #ffffff 0%, #f7fbfa 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        padding: 28px;
        text-align: center;
        animation: splashFade 260ms ease 850ms forwards;
    }
    .splash-mark {
        width: 92px;
        height: 92px;
        border-radius: 24px;
        border: 1px solid #c9e7e2;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #0b7a75;
        font-weight: 900;
        font-size: 1.45rem;
        background: #f3fbf9;
        box-shadow: 0 18px 42px rgba(11,122,117,0.12);
        animation: splashPulse 1100ms ease-in-out infinite;
    }
    .splash-mark img {
        max-width: 72px;
        max-height: 72px;
        width: auto;
        height: auto;
        object-fit: contain;
    }
    .splash-title {
        color: #102a43 !important;
        font-size: 1.45rem;
        font-weight: 800;
        margin-top: 22px;
        margin-bottom: 8px;
    }
    .splash-subtitle {
        color: #64748b !important;
        font-size: 1rem;
        line-height: 1.5;
        margin: 0;
        max-width: 360px;
    }
    .splash-line {
        width: min(280px, 72vw);
        height: 5px;
        background: #e6eef2;
        border-radius: 999px;
        overflow: hidden;
        margin-top: 24px;
    }
    .splash-line::after {
        content: "";
        display: block;
        width: 42%;
        height: 100%;
        background: linear-gradient(90deg, #0b7a75, #f6c453);
        border-radius: 999px;
        animation: splashLoad 1100ms ease-in-out infinite;
    }
    .splash-steps {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 8px;
        margin-top: 18px;
        max-width: 460px;
    }
    .splash-step {
        color: #516173 !important;
        background: #ffffff;
        border: 1px solid #e2ecef;
        border-radius: 999px;
        padding: 7px 11px;
        font-size: 0.84rem;
        font-weight: 700;
    }
    .splash-note {
        color: #8a97a6 !important;
        font-size: 0.82rem;
        margin-top: 18px;
    }
    @keyframes splashPulse {
        0%, 100% { transform: scale(1); box-shadow: 0 0 0 rgba(11,122,117,0); }
        50% { transform: scale(1.04); box-shadow: 0 12px 28px rgba(11,122,117,0.14); }
    }
    @keyframes splashLoad {
        0% { transform: translateX(-110%); }
        100% { transform: translateX(230%); }
    }
    @keyframes splashFade {
        to { opacity: 0; visibility: hidden; }
    }

    .profile-card {
        padding: 20px;
        border-radius: 8px;
        background-color: #ffffff;
        box-shadow: 0 8px 24px rgba(15,23,42,0.05);
        text-align: center;
        border: 1px solid #e4edf0;
    }
    .profile-card h4 { margin-bottom: 12px; color: #102a43 !important; }
    .profile-card hr { border: none; border-top: 1px solid #e6eef2; margin: 14px 0; }
    .profile-img-container { display: flex; justify-content: center; margin-bottom: 18px; }
    .profile-img-container img {
        border-radius: 50%;
        width: 132px;
        height: 132px;
        object-fit: cover;
        border: 4px solid #ffffff;
        box-shadow: 0 10px 24px rgba(15,23,42,0.14);
    }

    .custom-banner {
        width: 100%;
        height: clamp(160px, 24vw, 245px);
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 22px;
        border: 1px solid #e4edf0;
        box-shadow: 0 14px 35px rgba(15,23,42,0.07);
    }
    .custom-banner img { width: 100%; height: 100%; object-fit: cover; }

    .clinic-heading {
        padding: 4px 0 22px;
        margin: 0 0 22px;
        border-bottom: 1px solid #e6eef2;
    }
    .clinic-eyebrow {
        color: #0b7a75 !important;
        font-size: 0.82rem;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .clinic-title {
        color: #102a43 !important;
        font-size: clamp(2rem, 5vw, 3.25rem);
        line-height: 1.05;
        font-weight: 850;
        margin: 0 0 12px;
    }
    .clinic-copy {
        color: #52616f !important;
        font-size: 1.05rem;
        line-height: 1.55;
        max-width: 760px;
        margin: 0;
    }
    .hero-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 18px;
    }
    .hero-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #f7fafc;
        border: 1px solid #dde8ed;
        color: #334155 !important;
        border-radius: 999px;
        padding: 8px 12px;
        font-weight: 700;
        font-size: 0.9rem;
    }

    .footer-container {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 8px;
        margin-top: 42px;
        border: 1px solid #e4edf0;
        box-shadow: 0 12px 30px rgba(15,23,42,0.05);
    }
    .footer-btn {
        background-color: #f7fafc;
        color: #0b7a75 !important;
        padding: 8px 14px;
        border-radius: 8px;
        text-decoration: none;
        margin-right: 8px;
        margin-bottom: 8px;
        font-weight: 700;
        display: inline-block;
        border: 1px solid #dde8ed;
    }
    .admin-card {
        background: white;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e4edf0;
        margin-bottom: 20px;
        box-shadow: 0 10px 24px rgba(15,23,42,0.05);
    }

    .working-hours-card {
        background-color: #ffffff;
        padding: 22px;
        border-radius: 8px;
        border: 1px dashed #b8c8d2;
        text-align: center;
        margin-top: 15px;
        margin-bottom: 25px;
    }
    .service-badge {
        display: inline-block;
        background-color: #eef8f6;
        color: #0b7a75 !important;
        padding: 8px 14px;
        border-radius: 999px;
        margin: 6px;
        font-size: 0.9em;
        font-weight: 700;
        border: 1px solid #c9e7e2;
        transition: 0.2s;
    }
    .service-badge:hover { background-color: #0b7a75; color: #ffffff !important; }

    .stat-box {
        background-color: #f7fafc;
        padding: 18px;
        border-radius: 8px;
        border: 1px solid #e4edf0;
        text-align: center;
    }
    .announcement-box {
        background-color: #fff8e6;
        color: #7c4a03 !important;
        padding: 14px 18px;
        border-radius: 8px;
        border-left: 5px solid #f6c453;
        margin-bottom: 22px;
        font-weight: 700;
        display: flex;
        align-items: center;
    }

    .summary-card {
        background-color: #ffffff;
        padding: 28px;
        border-radius: 8px;
        border: 1px solid #e4edf0;
        box-shadow: 0 14px 32px rgba(15,23,42,0.07);
        margin-bottom: 20px;
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    }
    .summary-title {
        font-size: 1.35em;
        color: #102a43 !important;
        font-weight: 800;
        margin-bottom: 24px;
        padding-bottom: 14px;
        border-bottom: 1px solid #e4edf0;
    }
    .summary-row {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 14px;
        font-size: 1.02em;
        color: #64748b !important;
    }
    .summary-row strong { color: #102a43 !important; font-weight: 800; text-align: right; }
    .summary-total {
        text-align: right;
        font-size: 1.35em;
        font-weight: 850;
        color: #0b7a75 !important;
        margin-top: 22px;
        padding-top: 18px;
        border-top: 1px solid #e4edf0;
    }

    .btn-red>button { background: #ef6f61 !important; border-color: #ef6f61 !important; color: white !important; }
    .btn-red>button:hover { background: #d85e52 !important; border-color: #d85e52 !important; }
    .col-header { text-align: center; padding: 10px; border-radius: 8px; margin-bottom: 15px; font-weight: bold; color: white !important; }

    @media (max-width: 760px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 1.2rem; }
        .clinic-title { font-size: 2.05rem; }
        .clinic-copy { font-size: 0.98rem; }
        .summary-card, .footer-container { padding: 20px; }
        .summary-row { flex-direction: column; gap: 4px; }
        .summary-row strong { text-align: left; }
        .profile-img-container img { width: 112px; height: 112px; }
    }

    /* Final clinical design overrides */
    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background: #ffffff !important;
    }
    .block-container {
        max-width: 1080px;
        padding-top: 1.25rem;
    }
    [data-testid="stHeader"] {
        background: #ffffff !important;
        border-bottom: 1px solid #eef2f4;
    }
    section[data-testid="stSidebar"] {
        background: #fbfcfd !important;
        border-right: 1px solid #e7edf1;
        box-shadow: none;
    }
    .sidebar-brand {
        padding: 12px 10px 16px;
        text-align: center;
        border-bottom: 1px solid #e7edf1;
        margin-bottom: 18px;
    }
    .sidebar-logo img {
        max-width: 170px;
        max-height: 88px;
        width: auto;
        height: auto;
        object-fit: contain;
        display: block;
        margin: 0 auto;
    }
    .top-mobile-logo {
        display: none;
    }
    .profile-card {
        box-shadow: none;
        border: 1px solid #e2e8ee;
        border-radius: 8px;
        text-align: left;
        padding: 18px;
    }
    .profile-card h4 {
        text-align: center;
        font-size: 1rem;
        line-height: 1.35;
    }
    .profile-card p {
        margin: 9px 0;
        color: #516173 !important;
        line-height: 1.45;
    }
    .profile-img-container img {
        width: 116px;
        height: 116px;
        box-shadow: 0 10px 24px rgba(18,48,74,0.12);
    }
    .custom-banner {
        height: clamp(190px, 31vw, 320px);
        border-radius: 8px;
        border: 1px solid #e2e8ee;
        box-shadow: none;
        margin-bottom: 22px;
        background: #f6f8fa;
    }
    .custom-banner img {
        object-fit: cover;
        object-position: center;
    }
    .booking-intro {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 22px;
        padding: 26px 0 22px;
        margin-bottom: 8px;
        border-bottom: 1px solid #e7edf1;
    }
    .booking-kicker {
        color: #0b7a75 !important;
        font-size: 0.78rem;
        font-weight: 850;
        text-transform: uppercase;
        margin-bottom: 7px;
    }
    .booking-title {
        color: #12304a !important;
        font-size: clamp(2rem, 4vw, 2.85rem);
        line-height: 1.08;
        font-weight: 850;
        margin: 0 0 10px;
    }
    .booking-copy {
        color: #516173 !important;
        font-size: 1rem;
        line-height: 1.55;
        max-width: 640px;
        margin: 0;
    }
    .booking-meta {
        min-width: 240px;
        border-left: 3px solid #0b7a75;
        padding-left: 16px;
        color: #516173 !important;
        font-size: 0.92rem;
        line-height: 1.65;
    }
    .booking-meta strong {
        color: #12304a !important;
    }
    .field-heading, .slot-heading {
        color: #12304a !important;
        font-weight: 800;
        margin: 22px 0 10px;
        font-size: 1.05rem;
    }
    .slot-heading {
        display: flex;
        justify-content: space-between;
        gap: 14px;
        align-items: baseline;
        border-top: 1px solid #eef2f4;
        padding-top: 18px;
    }
    .slot-heading small {
        color: #718096 !important;
        font-weight: 600;
    }
    .selected-time {
        margin: 24px 0 14px;
        padding: 14px 16px;
        border-left: 3px solid #0b7a75;
        background: #f7fbfa;
        color: #12304a !important;
        font-weight: 800;
        border-radius: 0 8px 8px 0;
    }
    .stButton>button {
        border-radius: 8px;
        box-shadow: none;
        background-color: #0b7a75;
        border-color: #0b7a75;
    }
    .stButton>button:hover {
        box-shadow: none;
        transform: none;
        background-color: #075f5b;
    }
    .stDateInput, .stTextInput, .stTextArea, .stSelectbox {
        margin-bottom: 0.45rem;
    }
    .announcement-box {
        background: #fff9ed;
        border-left: 4px solid #d89a21;
        color: #6b4a0b !important;
        box-shadow: none;
        width: 100%;
        min-height: 0;
        height: auto;
        padding: 14px 18px;
        margin: 8px 0 24px;
        border-radius: 0 8px 8px 0;
        line-height: 1.55;
        font-size: 0.98rem;
        font-weight: 750;
        display: block;
        align-items: initial;
        white-space: normal;
        overflow: visible;
        overflow-wrap: anywhere;
        word-break: normal;
    }
    .working-hours-card {
        border-color: #d6e0e6;
        background: #fbfcfd;
        border-radius: 8px;
    }
    .footer-container {
        box-shadow: none;
        background: #fbfcfd;
        border-color: #e2e8ee;
    }
    @media (max-width: 760px) {
        .top-mobile-logo {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 8px 0 14px;
        }
        .top-mobile-logo img {
            max-width: 168px;
            max-height: 72px;
            width: auto;
            height: auto;
            object-fit: contain;
        }
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-bottom: 4.5rem;
        }
        .announcement-box {
            padding: 13px 14px;
            margin-top: 10px;
            margin-bottom: 20px;
            font-size: 0.94rem;
            line-height: 1.6;
        }
        .booking-intro {
            display: block;
            padding-top: 18px;
        }
        .booking-meta {
            margin-top: 16px;
            min-width: 0;
        }
        .custom-banner {
            height: 190px;
        }
        .slot-heading {
            display: block;
        }
        .slot-heading small {
            display: block;
            margin-top: 4px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- YARDIMCI FONKSİYONLAR ---
def db_baglan():
    return sqlite3.connect(DB_PATH, timeout=10)

def local_path(path_degeri):
    if not path_degeri:
        return None
    path = Path(str(path_degeri))
    if not path.is_absolute() and path.parts and path.parts[0] == "uploads":
        return UPLOAD_DIR / Path(*path.parts[1:])
    return path if path.is_absolute() else BASE_DIR / path

def guvenli_metin(deger):
    return html.escape(str(deger or ""))

def temiz_url_degeri(deger):
    deger = str(deger or "").strip()
    if deger.startswith(("https://", "http://")):
        return deger
    return ""

def guvenli_url(deger):
    return html.escape(temiz_url_degeri(deger), quote=True)

def guvenli_tel_href(deger):
    return re.sub(r"[^0-9+]", "", str(deger or ""))

def upload_db_yolu(dosya_adi):
    return str(Path("uploads") / dosya_adi).replace("\\", "/")

def secret_degeri_getir(anahtar):
    try:
        deger = st.secrets.get(anahtar)
    except Exception:
        deger = None
    return deger or os.getenv(anahtar)

def admin_sifresi_getir():
    try:
        if DB_PATH.exists():
            conn = sqlite3.connect(DB_PATH, timeout=3)
            cursor = conn.cursor()
            cursor.execute("SELECT admin_password FROM hoca_profil WHERE id = 1")
            kayit = cursor.fetchone()
            conn.close()
            if kayit and kayit[0]:
                return kayit[0]
    except Exception:
        pass
    return secret_degeri_getir("ADMIN_PASSWORD")

def admin_sifresi_guncelle(yeni_sifre):
    conn = db_baglan()
    cursor = conn.cursor()
    cursor.execute("UPDATE hoca_profil SET admin_password=? WHERE id=1", (yeni_sifre,))
    conn.commit()
    conn.close()

def sifreleri_guvenli_karsilastir(girilen, beklenen):
    girilen = str(girilen or "")
    beklenen = str(beklenen or "")
    try:
        return hmac.compare_digest(girilen.encode("utf-8"), beklenen.encode("utf-8"))
    except Exception:
        return girilen == beklenen

def format_tarih(tarih_str):
    try: return datetime.datetime.strptime(tarih_str, "%Y-%m-%d").strftime("%d.%m.%Y")
    except: return tarih_str

@st.cache_data(show_spinner=False)
def image_data_uri_cached(path_str, mtime, max_width):
    path = Path(path_str)
    try:
        img = Image.open(path)
        img.thumbnail((max_width, max_width), Image.LANCZOS)
        output = BytesIO()
        if img.mode in ("RGBA", "LA"):
            img.save(output, format="PNG", optimize=True)
            mime = "image/png"
        else:
            img = img.convert("RGB")
            img.save(output, format="JPEG", quality=82, optimize=True)
            mime = "image/jpeg"
        return f"data:{mime};base64,{base64.b64encode(output.getvalue()).decode()}"
    except Exception:
        try:
            mime = "image/jpeg" if path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
            return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"
        except Exception:
            return ""

def get_base64_image(image_path):
    try:
        with open(local_path(image_path), "rb") as f: return base64.b64encode(f.read()).decode()
    except: return ""

def get_image_data_uri(image_path, max_width=1200):
    path = local_path(image_path)
    if not path or not path.exists():
        return ""
    try:
        return image_data_uri_cached(str(path), path.stat().st_mtime, max_width)
    except Exception:
        mime = "image/jpeg" if path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
        return f"data:{mime};base64,{get_base64_image(image_path)}"

def ilk_var_olan_yol(*paths):
    for path in paths:
        if path and local_path(path).exists():
            return path
    return None

def json_degeri_oku(deger, aciklama):
    try:
        return json.loads(str(deger))
    except json.JSONDecodeError as e:
        raise ValueError(f"{aciklama} JSON formatinda okunamadi: {e}") from e

def google_credentials_info_getir():
    secret_json = secret_degeri_getir("GOOGLE_CREDENTIALS_JSON")
    if secret_json:
        return json_degeri_oku(secret_json, "GOOGLE_CREDENTIALS_JSON")
    if CREDENTIALS_PATH.exists():
        return json_degeri_oku(CREDENTIALS_PATH.read_text(encoding="utf-8"), "credentials.json")
    raise FileNotFoundError("Google Takvim credentials bulunamadi. Canli yayin icin GOOGLE_CREDENTIALS_JSON secret'i ya da yerelde credentials.json gerekir.")

def google_token_info_getir():
    secret_json = secret_degeri_getir("GOOGLE_TOKEN_JSON")
    if secret_json:
        return json_degeri_oku(secret_json, "GOOGLE_TOKEN_JSON")
    if TOKEN_PATH.exists():
        return json_degeri_oku(TOKEN_PATH.read_text(encoding="utf-8"), "token.json")
    return None

def google_token_secret_var_mi():
    return bool(secret_degeri_getir("GOOGLE_TOKEN_JSON"))

def google_token_kaydet(creds):
    try:
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    except Exception:
        pass

def google_takvim_hazir_mi():
    try:
        return bool(google_token_info_getir()) and (bool(secret_degeri_getir("GOOGLE_CREDENTIALS_JSON")) or CREDENTIALS_PATH.exists())
    except Exception:
        return False

def get_tum_saatler():
    saatler = []
    for h in range(9, 17):
        saatler.append(f"{h:02d}:00")
        saatler.append(f"{h:02d}:30")
    return saatler

def saat_musait_mi(cursor, tarih_str, saat_str, sure=45):
    cursor.execute("SELECT 1 FROM mesai WHERE tarih=? AND saat=? AND durum=1", (tarih_str, saat_str))
    if cursor.fetchone() is None:
        return False

    try:
        yeni_baslangic = datetime.datetime.strptime(saat_str, "%H:%M")
        yeni_bitis = yeni_baslangic + datetime.timedelta(minutes=int(sure or 45))
    except ValueError:
        return False

    cursor.execute("""
        SELECT r.saat, h.sure
        FROM randevular r
        LEFT JOIN hizmetler h ON r.hizmet = h.ad
        WHERE r.tarih = ? AND r.durum IN ('Beklemede', 'Onaylandı')
    """, (tarih_str,))

    for r_saat, r_sure in cursor.fetchall():
        mevcut_baslangic = datetime.datetime.strptime(r_saat, "%H:%M")
        mevcut_bitis = mevcut_baslangic + datetime.timedelta(minutes=int(r_sure or 45))
        if yeni_baslangic < mevcut_bitis and yeni_bitis > mevcut_baslangic:
            return False
    return True

def randevu_kaydet(veri):
    try:
        sure = int(veri.get("hizmet_sure") or 45)
    except (TypeError, ValueError):
        sure = 45

    conn = db_baglan()
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE")
        if not saat_musait_mi(cursor, veri["tarih"], veri["saat"], sure):
            conn.rollback()
            return False, "Seçilen saat az önce doldu veya mesaiye kapatıldı. Lütfen başka bir saat seçin."

        cursor.execute(
            "INSERT INTO randevular (isim, telefon, hizmet, sikayet, tarih, saat) VALUES (?,?,?,?,?,?)",
            (veri["isim"], veri["tel"], veri["hizmet_adi"], veri["sikayet"], veri["tarih"], veri["saat"])
        )
        conn.commit()
        return True, None
    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Randevu kaydedilemedi: {e}"
    finally:
        conn.close()

# --- 2. GOOGLE TAKVİM ---
def get_calendar_service():
    creds = None
    credentials_info = google_credentials_info_getir()
    token_info = google_token_info_getir()
    if token_info:
        creds = Credentials.from_authorized_user_info(token_info, CALENDAR_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token: 
            try:
                creds.refresh(Request())
            except Exception:
                TOKEN_PATH.unlink(missing_ok=True)
                if secret_degeri_getir("GOOGLE_CREDENTIALS_JSON") and not CREDENTIALS_PATH.exists():
                    raise RuntimeError("Takvim tokeni yenilenemedi. Canli yayin icin GOOGLE_TOKEN_JSON secret'ini yeniden olusturmak gerekir.")
                flow = InstalledAppFlow.from_client_config(credentials_info, CALENDAR_SCOPES)
                creds = flow.run_local_server(port=0)
        else:
            if secret_degeri_getir("GOOGLE_CREDENTIALS_JSON") and not CREDENTIALS_PATH.exists():
                raise RuntimeError("Canli yayin icin GOOGLE_TOKEN_JSON secret'i gerekir. Yerelde bir kez Google izni alinip token canli ortama eklenmeli.")
            flow = InstalledAppFlow.from_client_config(credentials_info, CALENDAR_SCOPES)
            creds = flow.run_local_server(port=0)
        google_token_kaydet(creds)
    return build('calendar', 'v3', credentials=creds)

def takvime_ekle(isim, hizmet, tarih_str, saat_str, telefon, sure=45):
    try:
        service = get_calendar_service()
        start = f"{tarih_str}T{saat_str}:00"
        end = (datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S") + datetime.timedelta(minutes=int(sure))).isoformat()
        event = {'summary': f'{hizmet}: {isim}', 'description': f'Tel: {telefon}', 'start': {'dateTime': start, 'timeZone': 'Europe/Istanbul'}, 'end': {'dateTime': end, 'timeZone': 'Europe/Istanbul'}}
        return service.events().insert(calendarId='primary', body=event).execute().get('id')
    except Exception as e:
        return f"HATA: {str(e)}"

def takvimden_sil(ev_id):
    try: get_calendar_service().events().delete(calendarId='primary', eventId=ev_id).execute()
    except: pass

def takvim_oturumunu_sifirla():
    try:
        if TOKEN_PATH.exists():
            TOKEN_PATH.unlink()
            return True
    except Exception:
        pass
    return False

def takvim_hesabi_oku():
    try:
        if not google_token_info_getir():
            return {
                "ok": False,
                "error": "Takvim tokeni bulunamadı. Hesap henüz bağlanmamış.",
            }
        service = get_calendar_service()
        primary = service.calendarList().get(calendarId="primary").execute()
        return {
            "ok": True,
            "summary": primary.get("summary", ""),
            "id": primary.get("id", "primary"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

# --- 3. VERİTABANI ---
def kolon_yoksa_ekle(cursor, tablo, kolon, tanim):
    kolonlar = [row[1] for row in cursor.execute(f"PRAGMA table_info({tablo})").fetchall()]
    if kolon not in kolonlar:
        cursor.execute(f"ALTER TABLE {tablo} ADD COLUMN {kolon} {tanim}")

def veritabanı_kur():
    conn = db_baglan()
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS hoca_profil 
                   (id INTEGER PRIMARY KEY, unvan TEXT, ucret INTEGER, iban TEXT, ofis TEXT, tel TEXT, email TEXT, 
                    profile_img TEXT, banner_img TEXT, logo_img TEXT, yasal_metin TEXT, harita_url TEXT, manuel_durum TEXT DEFAULT 'Açık', canli_duyuru TEXT DEFAULT '', admin_password TEXT)""")
    cursor.execute("CREATE TABLE IF NOT EXISTS mesai (tarih TEXT, saat TEXT, durum INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS hizmetler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, fiyat INTEGER, sure INTEGER DEFAULT 45, aciklama TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS randevular (id INTEGER PRIMARY KEY AUTOINCREMENT, isim TEXT, telefon TEXT, hizmet TEXT, sikayet TEXT, tarih TEXT, saat TEXT, durum TEXT DEFAULT 'Beklemede', event_id TEXT)")
    kolon_yoksa_ekle(cursor, "hoca_profil", "logo_img", "TEXT")
    kolon_yoksa_ekle(cursor, "hoca_profil", "admin_password", "TEXT")
    
    if cursor.execute("SELECT COUNT(*) FROM hoca_profil").fetchone()[0] == 0:
        cursor.execute("INSERT INTO hoca_profil (id, unvan, manuel_durum, ofis, tel, email) VALUES (1, 'Doç. Dr. Ömer Osman PALA', 'Açık', 'Morfoloji Binası', '0374...', 'fzt.omerpala@gmail.com')")
    conn.commit()
    conn.close()

def aktif_saatleri_getir(secilen_tarih_obj):
    tarih_str = str(secilen_tarih_obj)
    conn = db_baglan(); cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT saat FROM mesai WHERE tarih = ? AND durum = 1", (tarih_str,))
    acik_saatler = [row[0] for row in cursor.fetchall()]
    cursor.execute("""
        SELECT r.saat, h.sure 
        FROM randevular r
        LEFT JOIN hizmetler h ON r.hizmet = h.ad
        WHERE r.tarih = ? AND r.durum IN ('Beklemede', 'Onaylandı')
    """, (tarih_str,))
    dolu_randevular = cursor.fetchall()
    conn.close()
    
    engelli_saatler = set()
    for r_saat, r_sure in dolu_randevular:
        if not r_sure: r_sure = 45
        start_dt = datetime.datetime.strptime(r_saat, "%H:%M")
        end_dt = start_dt + datetime.timedelta(minutes=int(r_sure))
        for s in acik_saatler:
            slot_dt = datetime.datetime.strptime(s, "%H:%M")
            if start_dt <= slot_dt < end_dt:
                engelli_saatler.add(s)
                
    return sorted(list(set(acik_saatler) - engelli_saatler))

veritabanı_kur()

# --- 4. VERİ ÇEKME ---
conn = db_baglan(); cursor = conn.cursor()
cursor.execute("SELECT unvan, ucret, iban, ofis, tel, email, profile_img, banner_img, logo_img, yasal_metin, harita_url, canli_duyuru FROM hoca_profil WHERE id = 1")
p_unvan, p_ucret, p_iban, p_ofis, p_tel, p_email, p_img, p_banner, p_logo, p_yasal, p_harita, p_duyuru = cursor.fetchone()
conn.close()

simdi = datetime.datetime.now()
bugun_tarih = simdi.strftime("%Y-%m-%d")
p_unvan_html = guvenli_metin(p_unvan)
p_ofis_html = guvenli_metin(p_ofis)
p_tel_html = guvenli_metin(p_tel)
p_email_html = guvenli_metin(p_email)
p_tel_href = guvenli_tel_href(p_tel)
p_email_href = html.escape(str(p_email or ""), quote=True)
p_yasal_html = guvenli_metin(p_yasal)
gorunen_p_img = ilk_var_olan_yol(p_img, "uploads/profile_1363.jpg", "uploads/profile_Gemini_Generated_Image_c7k0akc7k0akc7k0.png")
gorunen_banner = ilk_var_olan_yol(p_banner, "uploads/banner_1363 (1).jpg", "uploads/banner_Gemini_Generated_Image_c7k0akc7k0akc7k0.png")
gorunen_logo = ilk_var_olan_yol(p_logo)
SAYFA_RANDEVU = "📅 Randevu Al"
SAYFA_ADMIN = "Yönetim"
SAYFA_SECENEKLERI = [SAYFA_RANDEVU, SAYFA_ADMIN]

# --- 5. SIDEBAR ---
with st.sidebar:
    if gorunen_logo:
        st.markdown(f'<div class="sidebar-brand sidebar-logo"><img src="{get_image_data_uri(gorunen_logo, max_width=520)}"></div>', unsafe_allow_html=True)
    if gorunen_p_img:
        st.markdown(f'<div class="profile-img-container"><img src="{get_image_data_uri(gorunen_p_img, max_width=360)}"></div>', unsafe_allow_html=True)

    st.markdown(f"""<div class="profile-card"><h4>{p_unvan_html}</h4><hr><div style="text-align:left; font-size:0.9em; color:#4a5568;"><p>📍 {p_ofis_html}</p><p>📞 {p_tel_html}</p><p>✉️ {p_email_html}</p></div></div>""", unsafe_allow_html=True)

if gorunen_logo:
    st.markdown(f'<div class="top-mobile-logo"><img src="{get_image_data_uri(gorunen_logo, max_width=520)}"></div>', unsafe_allow_html=True)

sayfa = st.radio("İşlem Seçiniz", SAYFA_SECENEKLERI, horizontal=True)

if 'randevu_adimi' not in st.session_state:
    st.session_state.randevu_adimi = 1
if 'gecici_randevu_verisi' not in st.session_state:
    st.session_state.gecici_randevu_verisi = {}

# --- 6. RANDEVU AL (HASTA EKRANI) ---
if sayfa == SAYFA_RANDEVU:
    # --- KARŞILAMA ANİMASYONU ---
    if 'splash_gosterildi' not in st.session_state:
        st.session_state.splash_gosterildi = True
        splash_logo_src = get_image_data_uri(gorunen_logo, max_width=240) if gorunen_logo else ""
        splash_mark_html = f'<img src="{splash_logo_src}" alt="Klinik logosu">' if splash_logo_src else "Klinik"
        splash = st.empty()
        with splash.container():
            st.markdown(f"""
            <div class="splash-screen">
                <div class="splash-mark">{splash_mark_html}</div>
                <div class="splash-title">Randevu sistemi hazırlanıyor</div>
                <p class="splash-subtitle">Uygun günler ve saatler kontrol ediliyor.</p>
                <div class="splash-steps">
                    <span class="splash-step">Takvim hazırlanıyor</span>
                    <span class="splash-step">Saatler kontrol ediliyor</span>
                    <span class="splash-step">Form açılıyor</span>
                </div>
                <div class="splash-line"></div>
                <div class="splash-note">Lütfen kısa bir an bekleyin</div>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.35)
        splash.empty()

    if gorunen_banner:
        st.markdown(f'<div class="custom-banner"><img src="{get_image_data_uri(gorunen_banner, max_width=1400)}"></div>', unsafe_allow_html=True)
    
    if p_duyuru and p_duyuru.strip() != "":
        st.markdown(f'<div class="announcement-box">📢 Klinik Duyurusu: {guvenli_metin(p_duyuru)}</div>', unsafe_allow_html=True)
        
    st.markdown(f"""
    <section class="booking-intro">
        <div>
            <div class="booking-kicker">Online Randevu</div>
            <h1 class="booking-title">Randevu Oluştur</h1>
            <p class="booking-copy">{p_unvan_html} için uygun tarih ve saati seçerek randevu talebinizi iletebilirsiniz.</p>
        </div>
        <div class="booking-meta">
            <div><strong>Çalışma aralığı:</strong> 09:00 - 16:30</div>
            <div><strong>Planlama:</strong> 3 gün - 1 ay sonrası</div>
            <div><strong>Konum:</strong> {p_ofis_html}</div>
        </div>
    </section>
    """, unsafe_allow_html=True)
    en_erken = datetime.date.today() + datetime.timedelta(days=3)
    en_gec = datetime.date.today() + datetime.timedelta(days=30)
    st.markdown('<div class="field-heading">Randevu tarihi</div>', unsafe_allow_html=True)
    tarih_hasta = st.date_input("Randevu Tarihi", min_value=en_erken, max_value=en_gec, format="DD/MM/YYYY")
    
    musaitler = aktif_saatleri_getir(tarih_hasta)
    if not musaitler: 
        st.info("Bu tarih için uygun randevu bulunmamaktadır. Lütfen takvimden ileri bir tarih seçiniz.")
        st.markdown("""
        <div class="working-hours-card">
            <h4 style="color: #2d3748; margin-bottom: 10px;">🕒 Genel Çalışma Saatlerimiz</h4>
            <p style="color: #64748b; margin: 0;">Pazartesi - Cuma: <b>09:00 - 16:30</b></p>
            <p style="color: #94a3b8; font-size: 0.85em; margin-top: 8px;">Randevular en erken 3 gün, en geç 1 ay sonrası için alınabilmektedir.</p>
        </div>
        """, unsafe_allow_html=True)

        conn = db_baglan(); cursor = conn.cursor()
        cursor.execute("SELECT ad, sure FROM hizmetler")
        hizmetler_liste = cursor.fetchall()
        conn.close()

        if hizmetler_liste:
            st.markdown("<h4 style='color: #2d3748; margin-top: 35px; margin-bottom: 15px; text-align: center;'>💼 Kliniğimizde Verilen Hizmetler</h4>", unsafe_allow_html=True)
            badges_html = '<div style="text-align: center; margin-bottom: 30px;">'
            for h in hizmetler_liste:
                badges_html += f'<span class="service-badge">{guvenli_metin(h[0])} ({guvenli_metin(h[1])} dk)</span>'
            badges_html += '</div>'
            st.markdown(badges_html, unsafe_allow_html=True)

    else:
        st.markdown(f'<div class="slot-heading"><span>Uygun saatler</span><small>{format_tarih(str(tarih_hasta))}</small></div>', unsafe_allow_html=True)
        cols = st.columns(4)
        for i, s in enumerate(musaitler):
            if cols[i%4].button(s, key=f"btn_h_{tarih_hasta}_{s}"): 
                st.session_state.secilen_saat = s
                st.session_state.randevu_adimi = 1 
        
        if 'secilen_saat' in st.session_state and st.session_state.secilen_saat:
            if st.session_state.randevu_adimi == 1:
                st.markdown(f'<div class="selected-time">Seçilen zaman: {format_tarih(str(tarih_hasta))} - {st.session_state.secilen_saat}</div>', unsafe_allow_html=True)
                with st.form("randevu_form"):
                    isim = st.text_input("Ad Soyad")
                    tel = st.text_input("Telefon")
                    conn = db_baglan(); cursor = conn.cursor()
                    cursor.execute("SELECT ad, fiyat, sure FROM hizmetler")
                    hz_list = [f"{h[0]} ({h[2]} dk) ({h[1]} ₺)" for h in cursor.fetchall()]
                    conn.close()
                    hizmet = st.selectbox("Hizmet", hz_list if hz_list else ["Genel Muayene (45 dk) (0 ₺)"])
                    sikayet = st.text_area("Not / Şikayet")
                    
                    if st.form_submit_button("Devam Et"):
                        if not isim or not tel:
                            st.warning("Lütfen Ad Soyad ve Telefon kısımlarını doldurun.")
                        else:
                            h_parca = hizmet.split(" (")
                            h_adi = h_parca[0]
                            h_sure = h_parca[1].replace(" dk)", "") if len(h_parca) > 1 else "45"
                            h_fiyat = h_parca[2].replace(" ₺)", "") if len(h_parca) > 2 else "0"
                            
                            st.session_state.gecici_randevu_verisi = {
                                "isim": isim, "tel": tel, "hizmet_adi": h_adi, "hizmet_fiyat": h_fiyat, "hizmet_sure": h_sure,
                                "sikayet": sikayet, "tarih": str(tarih_hasta), "saat": st.session_state.secilen_saat
                            }
                            st.session_state.randevu_adimi = 2
                            st.rerun()

            elif st.session_state.randevu_adimi == 2:
                veri = st.session_state.gecici_randevu_verisi
                gosterim_tarihi = format_tarih(veri['tarih'])
                
                st.markdown(f"""
                <div class="summary-card">
                    <div class="summary-title">Bireysel Fizyoterapi Danışmanlığı</div>
                    <div class="summary-row"><span>Tarih:</span> <strong>{guvenli_metin(gosterim_tarihi)} {guvenli_metin(veri['saat'])}</strong></div>
                    <div class="summary-row"><span>Öğretim Üyesi:</span> <strong>{p_unvan_html}</strong></div>
                    <div class="summary-row"><span>Hizmet:</span> <strong>{guvenli_metin(veri['hizmet_adi'])}</strong></div>
                    <div class="summary-total">Ücret: {guvenli_metin(veri['hizmet_fiyat'])},00 TL</div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.form("onay_form", border=False):
                    onay_1 = st.checkbox(f"Randevunuza gidemeyecekseniz, en geç randevu gününden bir önceki gün {p_tel} numarası üzerinden iptal edebilirsiniz. *")
                    onay_2 = st.checkbox("Öğretim üyesinden alınan her bir seans için ücretin döner sermaye hesabına yatırılması gerekmektedir. *")
                    
                    c_geri, c_onay = st.columns([1, 2])
                    geri_basildi = c_geri.form_submit_button("Geri Dön")
                    
                    st.markdown('<div class="btn-red">', unsafe_allow_html=True)
                    onay_basildi = c_onay.form_submit_button("Randevuyu Onayla ✔", use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    if geri_basildi:
                        st.session_state.randevu_adimi = 1
                        st.rerun()
                        
                    if onay_basildi:
                        if onay_1 and onay_2:
                            kayit_basarili, hata_mesaji = randevu_kaydet(veri)
                            if kayit_basarili:
                                st.session_state.secilen_saat = None
                                st.session_state.randevu_adimi = 1
                                st.session_state.gecici_randevu_verisi = {}
                                
                                st.success(f"✅ Randevu talebiniz başarıyla alınmıştır! ({gosterim_tarihi})")
                                time.sleep(0.1)
                                st.rerun()
                            else:
                                st.error(hata_mesaji)
                        else:
                            st.error("Lütfen randevuyu tamamlamak için koşulları onaylayınız.")

    harita_src = guvenli_url(p_harita)
    if harita_src:
        harita_html = f'<iframe src="{harita_src}" width="100%" height="250" style="border:0; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>'
    else:
        harita_html = '<div style="background:#f1f5f9; padding:20px; border-radius:15px; text-align:center; color:#64748b;">📍 Harita konumu henüz eklenmedi.</div>'

    st.markdown(f"""<div class="footer-container"><h4>{p_unvan_html}</h4><a href="tel:{p_tel_href}" class="footer-btn">📞 Ara</a><a href="mailto:{p_email_href}" class="footer-btn">✉️ E-Posta</a><br><br><h4>Yasal</h4><details><summary>KVKK ve Çerezler</summary><p>{p_yasal_html}</p></details><br><h4>Konum</h4>{harita_html}</div>""", unsafe_allow_html=True)

# --- 7. HOCA PANELİ ---
elif sayfa == SAYFA_ADMIN:
    st.title("Hoca Kontrol Merkezi")
    admin_sifresi = str(admin_sifresi_getir() or "")
    if not admin_sifresi:
        st.warning("Yönetim paneli şifresi ayarlanmamış. .streamlit/secrets.toml dosyasına ADMIN_PASSWORD ekleyin.")
    else:
        if "admin_giris_onayli" not in st.session_state:
            st.session_state.admin_giris_onayli = False

        if not st.session_state.admin_giris_onayli:
            with st.form("admin_login_form"):
                girilen_sifre = st.text_input("Şifre", type="password")
                giris_basildi = st.form_submit_button("Giriş Yap", use_container_width=True)
            if giris_basildi:
                if sifreleri_guvenli_karsilastir(girilen_sifre, admin_sifresi):
                    st.session_state.admin_giris_onayli = True
                    st.rerun()
                else:
                    st.error("Şifre hatalı.")
            st.stop()

        t1, t2, t3, t4 = st.tabs(["📊 Özet & Planlama", "📩 Randevular", "💼 Hizmetler Düzenleme", "📝 Profil"])
        
        with t1:
            st.markdown('<div class="admin-card">', unsafe_allow_html=True)
            st.subheader("📌 Günün Vaka Analizi")
            conn = db_baglan(); cursor = conn.cursor()
            cursor.execute("SELECT hizmet FROM randevular WHERE tarih=? AND durum='Onaylandı'", (bugun_tarih,))
            bugunku_vakalar = cursor.fetchall()
            
            if not bugunku_vakalar:
                st.info("Bugün için onaylanmış randevunuz bulunmuyor.")
            else:
                vaka_sayilari = {}
                for v in bugunku_vakalar:
                    hz = v[0]
                    vaka_sayilari[hz] = vaka_sayilari.get(hz, 0) + 1
                vaka_metni = " • ".join([f"**{adet}** adet {guvenli_metin(isim)}" for isim, adet in vaka_sayilari.items()])
                st.markdown(f'<div class="stat-box" style="text-align:left; background-color:#e6f2f1; border-color:#bce0df;"><p style="color:#0b7a75; font-size:1.1em; margin-bottom:10px;">Bugün kliniğinizde beklenen hastalar:</p><h4>{vaka_metni}</h4></div>', unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 25px 0;'>", unsafe_allow_html=True)
            st.subheader("📢 Canlı Duyuru Panosu")
            yeni_duyuru = st.text_input("Hasta ekranının tepesinde görünecek anlık duyuru metni:", value=p_duyuru)
            if st.button("Duyuruyu Güncelle"):
                cursor.execute("UPDATE hoca_profil SET canli_duyuru=? WHERE id=1", (yeni_duyuru,))
                conn.commit()
                st.success("✅ Klinik duyurusu başarıyla güncellendi!")
                time.sleep(0.1)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            conn.close()
            
            st.subheader("🕒 Mesai Planla (Buçuklu Saatler Dahil)")
            sec_tar = st.date_input("Tarih Seç", value=datetime.date.today(), format="DD/MM/YYYY")
            saatler = get_tum_saatler()
            
            conn = db_baglan(); cursor = conn.cursor()
            cursor.execute("SELECT saat FROM mesai WHERE tarih=? AND durum=1", (str(sec_tar),)); kayitli = [r[0] for r in cursor.fetchall()]
            
            cols = st.columns(4); yeni_m = {}
            for i, s in enumerate(saatler): 
                yeni_m[s] = cols[i%4].checkbox(s, value=(s in kayitli), key=f"ms_{s}")
            
            if st.button("Mesaiyi Kaydet"):
                cursor.execute("DELETE FROM mesai WHERE tarih=?", (str(sec_tar),))
                for s, d in yeni_m.items(): 
                    cursor.execute("INSERT INTO mesai (tarih, saat, durum) VALUES (?,?,?)", (str(sec_tar), s, 1 if d else 0))
                conn.commit(); conn.close()
                st.success(f"✅ {format_tarih(str(sec_tar))} tarihi için mesai saatleri kaydedildi!")
                time.sleep(0.1)
                st.rerun()

        with t2:
            conn = db_baglan(); cursor = conn.cursor()
            # ID DESC ile en son alınan randevu en üstte olacak şekilde sıraladık
            cursor.execute("SELECT id, isim, telefon, hizmet, tarih, saat, durum, event_id FROM randevular ORDER BY id DESC")
            tum_randevular = cursor.fetchall()
            
            bekleyenler = [r for r in tum_randevular if r[6] == 'Beklemede']
            onaylananlar = [r for r in tum_randevular if r[6] == 'Onaylandı']
            iptaller = [r for r in tum_randevular if r[6] == 'İptal Edildi']

            col_bekleyen, col_onaylanan, col_iptal = st.columns(3)
            
            def kart_olustur(r_data, col, btn_tur):
                tid, tisim, ttel, thz, ttar, tsaat, tdur, evid = r_data
                ikon = "🟠" if tdur == "Beklemede" else "🟢" if tdur == "Onaylandı" else "🔴"
                
                with col:
                    with st.expander(f"{ikon} {tisim} ({tsaat})"):
                        st.markdown(f"**Tarih:** {format_tarih(ttar)}")
                        st.markdown(f"**📞 Tel:** {ttel}")
                        st.markdown(f"**💼 Hizmet:** {thz}")
                        
                        if btn_tur == "bekleyen":
                            c1, c2 = st.columns(2)
                            if c1.button("Onayla", key=f"on_{tid}"):
                                cursor.execute("SELECT sure FROM hizmetler WHERE ad=?", (thz,))
                                h_sure_row = cursor.fetchone()
                                h_sure = h_sure_row[0] if h_sure_row else 45
                                ev_id = takvime_ekle(tisim, thz, ttar, tsaat, ttel, h_sure) if google_takvim_hazir_mi() else None
                                if ev_id and str(ev_id).startswith("HATA"):
                                    cursor.execute("UPDATE randevular SET durum='Onaylandı', event_id=NULL WHERE id=?", (tid,))
                                    conn.commit()
                                    st.warning(f"Randevu onaylandı, ancak Google Takvim'e eklenemedi: {ev_id}")
                                else:
                                    cursor.execute("UPDATE randevular SET durum='Onaylandı', event_id=? WHERE id=?", (ev_id, tid))
                                    conn.commit()
                                    st.success("✅ Onaylandı!")
                                time.sleep(0.1); st.rerun()
                                
                            if c2.button("İptal", key=f"ip_{tid}"):
                                cursor.execute("UPDATE randevular SET durum='İptal Edildi' WHERE id=?", (tid,))
                                conn.commit()
                                st.warning("❌ İptal Edildi."); time.sleep(0.1); st.rerun()
                                
                        elif btn_tur == "onaylanan":
                            if st.button("İptal Et", key=f"ip_onay_{tid}"):
                                if evid and not str(evid).startswith("HATA"): takvimden_sil(evid)
                                cursor.execute("UPDATE randevular SET durum='İptal Edildi' WHERE id=?", (tid,))
                                conn.commit()
                                st.warning("❌ İptal Edildi."); time.sleep(0.1); st.rerun()
                                
                        elif btn_tur == "iptal":
                            if st.button("🗑️ Tamamen Sil", key=f"sil_{tid}"):
                                cursor.execute("DELETE FROM randevular WHERE id=?", (tid,))
                                conn.commit()
                                st.error("🗑️ Kayıt silindi."); time.sleep(0.1); st.rerun()

            with col_bekleyen:
                st.markdown('<div class="col-header" style="background-color:#f59e0b;">🟠 BEKLEYENLER</div>', unsafe_allow_html=True)
                if not bekleyenler: st.info("Bekleyen randevu yok.")
                for r in bekleyenler: kart_olustur(r, col_bekleyen, "bekleyen")

            with col_onaylanan:
                st.markdown('<div class="col-header" style="background-color:#10b981;">🟢 ONAYLANANLAR</div>', unsafe_allow_html=True)
                if not onaylananlar: st.info("Onaylı randevu yok.")
                for r in onaylananlar: kart_olustur(r, col_onaylanan, "onaylanan")

            with col_iptal:
                st.markdown('<div class="col-header" style="background-color:#ef4444;">🔴 İPTAL EDİLENLER</div>', unsafe_allow_html=True)
                if not iptaller: st.info("İptal randevu yok.")
                for r in iptaller: kart_olustur(r, col_iptal, "iptal")
                
            conn.close()

        with t3:
            st.subheader("💼 Yeni Hizmet Ekle")
            conn = db_baglan(); cursor = conn.cursor()
            with st.form("hz_ekle", clear_on_submit=True):
                nad = st.text_input("Hizmet Adı (Örn: Manuel Terapi)")
                nsure = st.number_input("Hizmet Süresi (Dakika)", min_value=10, max_value=120, value=45)
                nfiyat = st.number_input("Fiyat (₺)", min_value=0, value=1000)
                if st.form_submit_button("Hizmeti Sisteme Ekle"): 
                    cursor.execute("INSERT INTO hizmetler (ad, fiyat, sure) VALUES (?,?,?)", (nad, nfiyat, nsure))
                    conn.commit()
                    st.success(f"✅ '{nad}' hizmeti {nsure} dk süre ve {nfiyat} ₺ fiyatla eklendi!")
                    time.sleep(0.1)
                    st.rerun()
            
            st.markdown("<hr>", unsafe_allow_html=True)
            st.subheader("✏️ Mevcut Hizmetleri Düzenle")
            cursor.execute("SELECT id, ad, fiyat, sure FROM hizmetler")
            hizmetler_verisi = cursor.fetchall()
            
            for hid, had, hfiyat, hsure in hizmetler_verisi:
                with st.expander(f"⚙️ {had} ({hsure} dk) — {hfiyat} ₺"):
                    with st.form(f"hz_duzenle_{hid}"):
                        u_ad = st.text_input("Hizmet Adı", value=had)
                        u_sure = st.number_input("Süre (Dakika)", min_value=10, max_value=120, value=int(hsure) if hsure else 45)
                        u_fiyat = st.number_input("Fiyat (₺)", min_value=0, value=int(hfiyat))
                        
                        c1, c2 = st.columns(2)
                        if c1.form_submit_button("Değişiklikleri Kaydet"):
                            cursor.execute("UPDATE hizmetler SET ad=?, fiyat=?, sure=? WHERE id=?", (u_ad, u_fiyat, u_sure, hid))
                            conn.commit()
                            st.success(f"✅ {u_ad} güncellendi!")
                            time.sleep(0.1)
                            st.rerun()
                        if c2.form_submit_button("🗑️ Hizmeti Tamamen Sil", type="primary"):
                            cursor.execute("DELETE FROM hizmetler WHERE id=?", (hid,))
                            conn.commit()
                            st.error(f"🗑️ {had} hizmeti sistemden silindi.")
                            time.sleep(0.1)
                            st.rerun()
            conn.close()

        with t4:
            st.subheader("Profil ve Görseller")
            with st.container():
                st.markdown('<div class="admin-card">', unsafe_allow_html=True)
                st.markdown("**Google Takvim Yönetimi**")
                c1, c2 = st.columns(2)
                if c1.button("Takvim oturumunu sıfırla"):
                    silinenler = takvim_oturumunu_sifirla()
                    if silinenler:
                        st.success("Takvim tokeni silindi. Yeni Gmail ile yeniden bağlanabilirsiniz.")
                    elif google_token_secret_var_mi():
                        st.warning("Canlı yayında token Secrets alanında duruyor. Yeni Gmail için GOOGLE_TOKEN_JSON secret'ini güncelleyin.")
                    else:
                        st.info("Silinecek token bulunamadı.")
                if c2.button("Bağlı hesabı kontrol et"):
                    durum = takvim_hesabi_oku()
                    if durum["ok"]:
                        st.success(f"Bağlı hesap: {durum['summary']} ({durum['id']})")
                    else:
                        st.error(f"Takvim bağlantısı yok ya da yetki hatası var: {durum['error']}")
                st.caption("Yeni Gmail'e geçmek için önce tokeni sıfırlayıp sonra takvimi yeniden yetkilendirin.")
                st.markdown("</div>", unsafe_allow_html=True)

            with st.container():
                st.markdown('<div class="admin-card">', unsafe_allow_html=True)
                st.markdown("**Yönetim Şifresi**")
                with st.form("admin_sifre_form"):
                    yeni_sifre = st.text_input("Yeni şifre", type="password")
                    yeni_sifre_tekrar = st.text_input("Yeni şifre tekrar", type="password")
                    sifre_kaydet = st.form_submit_button("Şifreyi Güncelle", use_container_width=True)
                if sifre_kaydet:
                    if len(yeni_sifre.strip()) < 6:
                        st.error("Yeni şifre en az 6 karakter olmalı.")
                    elif yeni_sifre != yeni_sifre_tekrar:
                        st.error("Şifreler eşleşmiyor.")
                    else:
                        admin_sifresi_guncelle(yeni_sifre.strip())
                        st.session_state.admin_giris_onayli = False
                        st.success("Şifre güncellendi. Yeni şifreyle tekrar giriş yapabilirsiniz.")
                        time.sleep(0.1)
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            with st.container():
                up_logo = st.file_uploader("Klinik Logosu", type=["jpg","jpeg","png"])
                up_p = st.file_uploader("Profil Resmi", type=["jpg","png"])
                if up_p:
                    img = Image.open(up_p)
                    if st_cropper:
                        cropped = st_cropper(img, aspect_ratio=(1,1))
                    else:
                        cropped = img
                    st.session_state.new_p = cropped
                up_b = st.file_uploader("Banner Resmi", type=["jpg","png"])
            
            with st.form("prof_form"):
                u_unvan = st.text_input("Unvan ve İsim", p_unvan); u_ofis = st.text_input("Ofis", p_ofis)
                u_tel = st.text_input("Tel", p_tel); u_mail = st.text_input("E-posta", p_email)
                u_yas = st.text_area("Yasal Metin", p_yasal); u_har = st.text_input("Harita URL (Sadece link veya HTML kodun tamamı)", p_harita)
                
                if st.form_submit_button("Bilgileri Güncelle"):
                    pi, bi, li = p_img, p_banner, p_logo
                    if u_har and "<iframe" in u_har:
                        match = re.search(r'src="([^"]+)"', u_har)
                        if match: u_har = match.group(1)
                    u_har = temiz_url_degeri(u_har)

                    if up_logo:
                        li = upload_db_yolu(f"logo_{int(time.time())}.png")
                        with open(local_path(li),"wb") as f: f.write(up_logo.getbuffer())
                    if 'new_p' in st.session_state:
                        pi = upload_db_yolu(f"p_{int(time.time())}.png")
                        st.session_state.new_p.save(local_path(pi))
                    if up_b:
                        bi = upload_db_yolu(f"b_{int(time.time())}.png")
                        with open(local_path(bi),"wb") as f: f.write(up_b.getbuffer())
                    
                    conn = db_baglan(); cursor = conn.cursor()
                    cursor.execute("UPDATE hoca_profil SET unvan=?, ofis=?, tel=?, email=?, profile_img=?, banner_img=?, logo_img=?, yasal_metin=?, harita_url=? WHERE id=1", (u_unvan, u_ofis, u_tel, u_mail, pi, bi, li, u_yas, u_har))
                    conn.commit(); conn.close()
                    st.success("✅ Tüm profil bilgileri ve görseller başarıyla güncellendi!")
                    time.sleep(0.1)
                    st.rerun()
