import streamlit as st

# Configurazione pagina
st.set_page_config(page_title="Rugni Debt Manager PRO", layout="wide")

# --- CSS GOOGLE STYLE (PULIZIA E CONTRASTO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
    .block-container { padding-top: 2rem !important; }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; color: #1a73e8 !important; }
    html, body, [data-testid="stAppViewContainer"] { background-color: #f8f9fa !important; color: #000000 !important; }
    h1 { color: #1a73e8 !important; font-weight: 800 !important; }
    h2, h3 { color: #000000 !important; font-weight: 700 !important; border-bottom: 2px solid #1a73e8; padding-bottom: 5px; margin-top: 20px !important; }
    p, label, span, .stMarkdown p, .stWidgetLabel p { color: #000000 !important; font-weight: 600 !important; }
    div[data-testid="stMetric"], .stAlert, div.stNumberInput, div.stSelectbox, div.stSlider, div[data-baseweb="tab-list"] {
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

st.markdown('<div class="mobile-hint">📱 MENU IMPOSTAZIONI: Clicca l\'icona &equiv; o la freccia &gt; in alto a sinistra</div>', unsafe_allow_html=True)
st.title("🛡️ Rugni Debt Management")

# --- SIDEBAR ---
st.sidebar.markdown("### ⚙️ Configurazione")
is_legale = st.sidebar.toggle("⚖️ FASE LEGALE (Hybrid)")

asset_input = st.sidebar.text_input("Nome Asset", value="UNI").upper()
port_choice = st.sidebar.selectbox("Selezione Portafoglio", ["Automatico", "P1", "P2", "P3", "P2DM"])

is_precetto = False
if is_legale:
    is_precetto = st.sidebar.checkbox("🚩 Fase di Precetto")

num_pratiche = st.sidebar.number_input("N. Pratiche", min_value=1, value=1)
scelta_patr = st.sidebar.selectbox("Stato Patrimoniale", ["Negativa", "Negativa Stabile", "No Info", "Positiva < 1k", "Positiva 1k-2k", "Positiva > 2k", "Pensionato"])
is_decaduto = st.sidebar.checkbox("Già Decaduto")
pdr_attivo = st.sidebar.checkbox("PdR Attivo")

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
st.subheader(f"📋 Inserimento Debiti ({portfolio}) {' - HYBRID' if is_legale else ''}")
lista_debiti_orig = []
cols_in = st.columns(num_pratiche)
for i in range(num_pratiche):
    with cols_in[i]:
        v = st.number_input(f"Pratica {i+1} (€)", min_value=0.0, value=2500.0, key=f"d_{i}")
        lista_debiti_orig.append({"id": i+1, "valore": v})
debito_tot_orig = sum(d['valore'] for d in lista_debiti_orig)

# --- LOGICA SCONTI E RATE MINIME ---
sc_os, sc_sh, sc_hf, sc_pdr = 0, 0, 0, 0
max_mesi_sh = 500

if not is_legale:
    # --- TABELLE COMMERCIALI ---
    rate_map = {"Negativa": (150, 70), "No Info": (180, 100), "Positiva < 1k": (180, 100), "Positiva 1k-2k": (200, 130), "Positiva > 2k": (250, 180), "Pensionato": (150, 70)}
    if portfolio == "P1":
        sc_sh, sc_hf, sc_pdr = 25, 20, (10 if not is_decaduto else 0)
        sc_os = 70 if debito_tot_orig < 10000 else 60
    elif portfolio == "P2":
        sc_sh, sc_hf, sc_pdr = 30, 25, 10
        if "Positiva" in scelta_patr: sc_os = 40 if debito_tot_orig > 10000 else 20
        else: sc_os = 60 if debito_tot_orig > 10000 else 40
else:
    # --- TABELLE LEGALI (HYBRID) ---
    # Definiamo le rate minime precise per fase legale
    rate_map = {
        "Negativa": (100, 40), 
        "Negativa Stabile": (70, 25), 
        "No Info": (100, 40), # Allineato a Negativa se non specificato
        "Positiva < 1k": (100, 40), 
        "Positiva 1k-2k": (150, 50), 
        "Positiva > 2k": (200, 60), 
        "Pensionato": (100, 40)
    }
    
    # Vincoli temporali Short Arr
    if debito_tot_orig <= 5000: max_mesi_sh = 6
    elif debito_tot_orig <= 10000: max_mesi_sh = 12
    else: max_mesi_sh = 24

    if portfolio == "P2":
        if is_precetto:
            sc_os, sc_sh, sc_hf, sc_pdr = 20, 0, 0, 0
        else:
            if scelta_patr == "Negativa": sc_os, sc_sh, sc_hf, sc_pdr = 30, 20, 15, 10
            elif scelta_patr == "Negativa Stabile": sc_os, sc_sh, sc_hf, sc_pdr = 50, 30, 25, 10
            elif "Positiva" in scelta_patr: sc_os, sc_sh, sc_hf, sc_pdr = 10, 5, 5, 0
    else: # PORTAFOGLIO 1
        if is_precetto:
            sc_os, sc_sh, sc_hf, sc_pdr = 10, 0, 0, 0
        else:
            if scelta_patr == "Negativa": sc_os, sc_sh, sc_hf, sc_pdr = 20, 15, 10, 5
            elif scelta_patr == "Negativa Stabile": sc_os, sc_sh, sc_hf, sc_pdr = 40, 25, 20, 10
            elif "Positiva" in scelta_patr: sc_os, sc_sh, sc_hf, sc_pdr = 10, 5, 5, 0

# Calcolo Minima
r_sing, r_mult = rate_map.get(scelta_patr, (180, 100))
minima_totale = float(r_sing if num_pratiche == 1 else (r_mult * num_pratiche))

# --- DASHBOARD ---
st.subheader("📊 Parametri di Riferimento")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("One Shot Max", f"{sc_os}%")
m2.metric("Short Arr Max", f"{sc_sh}%")
m3.metric("High First Max", f"{sc_hf}%")
m4.metric("PdR Max", f"{sc_pdr}%")
m5.metric("Rata Minima", f"{minima_totale}€")

# --- CONFIGURAZIONE ACCORDO ---
st.subheader("🤝 Configurazione Accordo")
c1, c2 = st.columns(2)
with c1:
    tipo_accordo = st.selectbox("Strategia", ["One Shot", "Short Arrangement", "High First", "Piano di Rientro"])
with c2:
    t_max = {"One Shot": sc_os, "Short Arrangement": sc_sh, "High First": sc_hf, "Piano di Rientro": sc_pdr}[tipo_accordo]
    sconto_f = st.number_input(f"Sconto scelto (Riferimento: {t_max}%)", 0, 100, int(t_max))

if sconto_f > t_max: st.warning("⚠️ HAI CONTROLLATO CHE IN DMP PUOI FARE QUESTO SCONTO?")
if is_legale and is_precetto and tipo_accordo != "One Shot":
    st.error("🚩 ATTENZIONE: In fase di Precetto è autorizzato solo lo sconto One Shot.")

debito_scontato = debito_tot_orig * (1 - sconto_f/100)
st.info(f"💰 **Debito netto da rientrare: {debito_scontato:,.2f} €**")

# --- TABS ---
tab1, tab2 = st.tabs(["🔄 Piano Standard", "⚡ Tool: Velocità Variabile"])

with tab1:
    if tipo_accordo == "One Shot":
        st.success(f"✅ One Shot: {debito_scontato:,.2f} €")
    else:
        rata_scelta = st.number_input("Rata Mensile Concordata (€)", min_value=0.0, value=minima_totale, step=1.0)
        if rata_scelta < minima_totale: st.error("⚠️ HAI AUTORIZZAZIONE DA RM PER FARE RATA MINIMA INFERIORE?")
        
        acconto_hf = 0.0
        if tipo_accordo == "High First":
            p_acc = 10 if debito_tot_orig > 10000 else (15 if debito_tot_orig >= 5000 else 20)
            acc_min = debito_tot_orig * (p_acc / 100)
            st.warning(f"⚠️ Acconto minimo richiesto ({p_acc}%): {acc_min:,.2f} €")
            acconto_hf = st.number_input("Importo Acconto", min_value=float(acc_min), value=float(acc_min), key="acc_final")

        if rata_scelta > 0:
            # Calcolo Cascata
            deb_res_list = [{"id": d['id'], "res": d['valore']*(1-sconto_f/100) - (d['valore']/debito_tot_orig)*acconto_hf} for d in lista_debiti_orig]
            deb_ordinati = sorted(deb_res_list, key=lambda x: x['res'])
            temp_res, piani_f, mesi_t = [d['res'] for d in deb_ordinati], {d['id']: [] for d in deb_ordinati}, 0
            
            while sum(temp_res) > 0.01 and mesi_t < 500:
                attive = [v for v in temp_res if v > 0.01]
                if not attive: break
                r_p = rata_scelta / len(attive)
                m_fase = min(attive) / r_p
                for i in range(len(temp_res)):
                    if temp_res[i] > 0.01:
                        piani_f[deb_ordinati[i]['id']].append({"r": round(m_fase, 1), "v": round(r_p, 2)})
                        temp_res[i] -= (r_p * m_fase)
                mesi_t += m_fase

            durata_tot = round(mesi_t) + (1 if acconto_hf > 0 else 0)
            st.success(f"📌 Chiusura in {durata_tot} mesi")
            
            # Blocchi legali
            if is_legale and tipo_accordo == "Short Arrangement" and durata_tot > max_mesi_sh:
                st.error(f"❌ LIMITE MASSIMO SUPERATO: Per questo debito lo Short Arrangement Hybrid può durare max {max_mesi_sh} mesi.")
            if durata_tot > 160:
                st.error("❌ LIMITE MASSIMO AZIENDALE SUPERATO (160 rate).")

            col_res = st.columns(num_pratiche)
            for i, d_inf in enumerate(deb_ordinati):
                with col_res[i]:
                    st.markdown(f"**PRATICA {d_inf['id']}**")
                    if acconto_hf > 0:
                        st.write(f"🚩 **1** rata da **{(lista_debiti_orig[d_inf['id']-1]['valore']/debito_tot_orig)*acconto_hf:.2f}€**")
                    for step in piani_f[d_inf['id']]:
                        if step['r'] > 0: st.write(f"🔹 **{step['r']}** rate da **{step['v']}€**")

with tab2:
    st.markdown("### 🛠️ Simulatore a Velocità Variabile")
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        n1, i1 = st.number_input("Step 1: N. Rate", 0, value=0), st.number_input("Step 1: Importo (€)", 0.0, value=0.0)
    with col_v2:
        n2, i2 = st.number_input("Step 2: N. Rate", 0, value=0), st.number_input("Step 2: Importo (€)", 0.0, value=0.0)
    with col_v3:
        i_f = st.number_input("Step Finale: Importo Rata (€)", 0.0, value=float(minima_totale/num_pratiche if num_pratiche > 0 else 100))
    pagato_m = (n1 * i1) + (n2 * i2)
    res_v = debito_scontato - pagato_m
    if i_f > 0:
        rate_f = max(0.0, res_v / i_f)
        st.info(f"📉 Residuo: {max(0.0, res_v):,.2f} €")
        if res_v > 0:
            st.warning(f"👉 Mancano ancora **{int(rate_f) + 1} rate** da **{i_f} €**")
