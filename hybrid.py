


import streamlit as st

# Configurazione pagina
st.set_page_config(page_title="Rugni Debt Manager PRO", layout="wide")

# --- CSS GOOGLE STYLE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
    .block-container { padding-top: 2rem !important; }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; color: #1a73e8 !important; }
    html, body, [data-testid="stAppViewContainer"] { background-color: #f8f9fa !important; color: #000000 !important; }
    h1 { color: #1a73e8 !important; font-weight: 800 !important; }
    h2, h3 { color: #000000 !important; font-weight: 700 !important; border-bottom: 2px solid #1a73e8; padding-bottom: 5px; margin-top: 20px !important; }
    p, label, span, .stMarkdown p, .stWidgetLabel p { color: #000000 !important; font-weight: 600 !important; }
    div[data-testid="stMetric"], .stAlert, div.stNumberInput, div.stSelectbox, div.stSlider {
        background-color: #ffffff !important;
        border: 1px solid #dadce0 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 2px rgba(60,64,67,0.3) !important;
        margin-bottom: 15px !important;
    }
    .mobile-hint { background-color: #1a73e8 !important; color: #ffffff !important; padding: 12px; border-radius: 8px; text-align: center; font-weight: 700; margin-bottom: 20px; }
    [data-testid="stMetricValue"] { color: #1a73e8 !important; font-weight: 800 !important; font-size: 35px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Rugni Debt Management")

# --- SIDEBAR ---
st.sidebar.markdown("### ⚙️ Configurazione")
is_legale = st.sidebar.toggle("⚖️ FASE LEGALE (Hybrid)")

asset_input = st.sidebar.text_input("Nome Asset", value="UNI").upper()
port_choice = st.sidebar.selectbox("Selezione Portafoglio", ["Automatico", "P1", "P2", "P3", "P2DM"])

# --- RECUPERO SEZIONE CLASSIC/BEHAVIORAL (Solo per Amicable) ---
tipo_negoziazione = "N/A"
if not is_legale:
    tipo_negoziazione = st.sidebar.radio("Tipo Negoziazione", ["Classic", "Behavioral"])

is_precetto = False
if is_legale:
    is_precetto = st.sidebar.checkbox("🚩 Fase di Precetto")

num_pratiche = st.sidebar.number_input("N. Pratiche", min_value=1, value=1)
scelta_patr = st.sidebar.selectbox("Stato Patrimoniale", ["Negativa", "Negativa Stabile", "No Info", "Positiva < 1k", "Positiva 1k-2k", "Positiva > 2k", "Pensionato"])
is_decaduto = st.sidebar.checkbox("Già Decaduto")

# --- DATABASE ASSET ---
p2_amicable = ["AGSUN/2", "AGS/2", "AGSF/2", "FLO/2", "AFLO/2", "UNIF/1", "UNIF/2", "UNIG", "UCQ/2", "UCQ/3", "DBF/1", "DBF/3", "CMFC/1", "CCRII"]
p2_legale = ["UNI", "IUB", "IFIS", "LOC", "MPS", "EDS", "SRG", "CMP", "CMS", "INT", "FIN"]

if port_choice == "Automatico":
    if is_legale:
        portfolio = "P2" if asset_input in p2_legale else "P1"
    else:
        portfolio = "P2" if asset_input in p2_amicable else "P1"
else:
    portfolio = port_choice

# --- INPUT DEBITI ---
st.subheader(f"📋 Debiti {portfolio} - {'HYBRID' if is_legale else 'AMICABLE'}")
lista_debiti_orig = []
cols_in = st.columns(num_pratiche)
for i in range(num_pratiche):
    with cols_in[i]:
        v = st.number_input(f"Pratica {i+1} (€)", min_value=0.0, value=2500.0, key=f"d_{i}")
        lista_debiti_orig.append({"id": i+1, "valore": v})
debito_tot_orig = sum(d['valore'] for d in lista_debiti_orig)

# --- LOGICA SCONTI ---
sc_os, sc_sh, sc_hf, sc_pdr = 0, 0, 0, 0
max_mesi_sh = 500

if not is_legale:
    # --- TABELLE AMICABLE (Ripristinate) ---
    rate_map = {"Negativa": (150, 70), "No Info": (180, 100), "Pensionato": (150, 70), "Positiva < 1k": (180, 100), "Positiva 1k-2k": (200, 130), "Positiva > 2k": (250, 180)}
    
    if portfolio == "P1":
        sc_sh, sc_hf, sc_pdr = 25, 20, (10 if not is_decaduto else 0)
        sc_os = 70 if debito_tot_orig < 10000 else 60
    elif portfolio == "P2":
        # Qui usiamo la scelta Classic/Behavioral
        sc_sh, sc_hf, sc_pdr = (35, 30, 15) if tipo_negoziazione == "Behavioral" else (30, 25, 10)
        if "Positiva" in scelta_patr:
            sc_os = 40 if debito_tot_orig > 10000 else 20
        else:
            sc_os = 60 if debito_tot_orig > 10000 else 40
else:
    # --- TABELLE HYBRID (Legali) ---
    rate_map = {"Negativa": (100, 40), "Negativa Stabile": (70, 25), "No Info": (100, 40), "Positiva < 1k": (100, 40), "Positiva 1k-2k": (150, 50), "Positiva > 2k": (200, 60), "Pensionato": (100, 40)}
    if debito_tot_orig <= 5000: max_mesi_sh = 6
    elif debito_tot_orig <= 10000: max_mesi_sh = 12
    else: max_mesi_sh = 24

    if portfolio == "P2":
        if is_precetto: sc_os, sc_sh, sc_hf, sc_pdr = 20, 0, 0, 0
        else:
            if scelta_patr == "Negativa": sc_os, sc_sh, sc_hf, sc_pdr = 30, 20, 15, 10
            elif scelta_patr == "Negativa Stabile": sc_os, sc_sh, sc_hf, sc_pdr = 50, 30, 25, 10
            elif "Positiva" in scelta_patr: sc_os, sc_sh, sc_hf, sc_pdr = 10, 5, 5, 0
    else: # P1 Legale
        if is_precetto: sc_os, sc_sh, sc_hf, sc_pdr = 10, 0, 0, 0
        else:
            if scelta_patr == "Negativa": sc_os, sc_sh, sc_hf, sc_pdr = 20, 15, 10, 5
            elif scelta_patr == "Negativa Stabile": sc_os, sc_sh, sc_hf, sc_pdr = 40, 25, 20, 10
            elif "Positiva" in scelta_patr: sc_os, sc_sh, sc_hf, sc_pdr = 10, 5, 5, 0

# Calcolo Minima
r_sing, r_mult = rate_map.get(scelta_patr, (180, 100))
minima_totale = float(r_sing if num_pratiche == 1 else (r_mult * num_pratiche))

# Dashboard
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("One Shot Max", f"{sc_os}%")
m2.metric("Short Arr Max", f"{sc_sh}%")
m3.metric("High First Max", f"{sc_hf}%")
m4.metric("PdR Max", f"{sc_pdr}%")
m5.metric("Rata Minima", f"{minima_totale}€")

# Accordi e Calcolatore (il resto del codice rimane uguale...)
# [OMISSIS per brevità, ma includi tutto il calcolo a cascata che avevamo già]
