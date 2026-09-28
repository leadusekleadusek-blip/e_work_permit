import datetime
import json
import urllib.request
import streamlit as st
import unicodedata
from fpdf import FPDF

# ---------------------------------------------------------
# CONFIGURATION DE LA PAGE STREAMLIT
# ---------------------------------------------------------
st.set_page_config(
    page_title="P&G Amiens — e-Work Permit System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS P&G avec fond d'application très clair pour maximiser le contraste des champs
st.markdown("""
<style>
    /* Fond principal fortement éclairci pour faire ressortir les encarts de saisie */
    .stApp { background-color: #f8fafc !important; }
    .main { background-color: #f8fafc; }

    .pg-header {
        background: linear-gradient(135deg, #003366 0%, #0056b3 100%);
        color: white; padding: 22px; border-radius: 12px; margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .welcome-card {
        background: white; border: 1px solid #cbd5e1; padding: 30px; border-radius: 12px;
        text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 15px;
    }
    .stepper-bar {
        background: white; border: 1px solid #cbd5e1; padding: 12px; border-radius: 10px;
        margin-bottom: 20px; text-align: center; font-weight: bold;
    }
    .weather-card {
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
        border: 1px solid #0284c7; padding: 12px 18px; border-radius: 10px;
        margin-bottom: 20px; color: #0369a1;
    }
    .status-pending {
        background-color: #fef08a; color: #854d0e; border: 2px solid #eab308;
        padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 1.1rem;
        margin-bottom: 15px;
    }
    .status-validated {
        background-color: #dcfce7; color: #166534; border: 2px solid #22c55e;
        padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 1.1rem;
        margin-bottom: 15px;
    }
    .stButton>button { border-radius: 8px; font-weight: bold; }

    /* MISE EN VALEUR ET CONTRASTE DES ENCARTS DE SAISIE ET TEXTE LIBRE */
    div[data-baseweb="input"] {
        background-color: #e0f2fe !important;
        border: 1.5px solid #0284c7 !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #003366 !important;
        box-shadow: 0 0 0 3px rgba(0, 51, 102, 0.25) !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #e0f2fe !important;
        border: 1.5px solid #0284c7 !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# FONCTION DE RÉCUPÉRATION MÉTÉO EN DIRECT (OPEN-METEO AMIENS)
# ---------------------------------------------------------
@st.cache_data(ttl=1800)
def obtenir_meteo_amiens_live():
    """Récupère la météo réelle d'Amiens via Open-Meteo API"""
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=49.8941&longitude=2.2957&daily=temperature_2m_max,windgusts_10m_max&timezone=Europe%2FParis"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            temp_j0 = round(data['daily']['temperature_2m_max'][0])
            vent_j0 = round(data['daily']['windgusts_10m_max'][0])
            temp_j1 = round(data['daily']['temperature_2m_max'][1])
            vent_j1 = round(data['daily']['windgusts_10m_max'][1])
            return {
                "temp_j0": temp_j0, "vent_j0": vent_j0,
                "temp_j1": temp_j1, "vent_j1": vent_j1,
                "source": "Open-Meteo Live API"
            }
    except Exception:
        return {
            "temp_j0": 16, "vent_j0": 14,
            "temp_j1": 18, "vent_j1": 9,
            "source": "Mode Hors-Ligne (Secours)"
        }

# ---------------------------------------------------------
# RÉFÉRENTIELS & BASES DE DONNÉES P&G
# ---------------------------------------------------------
db_societes = ["ABYLSEN", "APAVE", "AXIMA", "ENGIE", "EULER"]

db_pdps = {
    "ABYLSEN": ["PDP-2026-042 (Bâtiment M1 - Rénovation)", "PDP-2026-089 (Bâtiment M2 - Maintenance)"],
    "APAVE": ["PDP-2026-104 (Inspection Pression Tuyauterie)", "PDP-2026-112 (Conformité Électrique TGBT)"],
    "AXIMA": ["PDP-2026-015 (HVAC Zone Production M1)"],
    "ENGIE": ["PDP-2026-067 (Chaufferie Vapeur Nord)"],
    "EULER": ["PDP-2026-090 (Génie Civil & Terrassement TP)"]
}

db_mops = {
    "PDP-2026-042 (Bâtiment M1 - Rénovation)": ["MoP-01: Peinture & Finitions M1", "MoP-02: Remplacement Cloisons"],
    "PDP-2026-089 (Bâtiment M2 - Maintenance)": ["MoP-01: Maintenance Ligne 3"],
    "PDP-2026-104 (Inspection Pression Tuyauterie)": ["MoP-01: Épreuve Hydraulique Tuyauterie"],
    "PDP-2026-112 (Conformité Électrique TGBT)": ["MoP-01: Audit Armoires TGBT"],
    "PDP-2026-015 (HVAC Zone Production M1)": ["MoP-01: Nettoyage Filtres CTA"],
    "PDP-2026-067 (Chaufferie Vapeur Nord)": ["MoP-01: Isoler Purgeur Vapeur"],
    "PDP-2026-090 (Génie Civil & Terrassement TP)": ["MoP-01: Fouille Terrassement TP"]
}

db_n2 = ["Léa DUSEK", "Matthieu MARTIN", "Alexandre LEFEBVRE", "Cindy BERNARD"]

db_zones_carto = {
    "Bâtiment M1 - Zone Production": {
        "pr": "PR-2 (Parking Ouest)", "confinement": "ZC-01 (Hall M1)", "urgence": "03.22.54.33.33 (Poste Garde M1)"
    },
    "Bâtiment M1 - Bureaux": {
        "pr": "PR-2 (Parking Ouest)", "confinement": "ZC-01 (Hall M1)", "urgence": "03.22.54.30.00 (Infirmerie M1)"
    },
    "Bâtiment M2 - Conditionnement": {
        "pr": "PR-4 (Zone Nord)", "confinement": "ZC-03 (Atrium M2)", "urgence": "03.22.54.33.34 (Poste Garde M2)"
    },
    "Zone Extérieure / Logistique": {
        "pr": "PR-1 (Entrée Principale)", "confinement": "ZC-00 (Poste Central)", "urgence": "03.22.54.33.33 (SAMU Site)"
    }
}

db_materiaux = ["Acier / Carbone", "Inox 316L / 304L", "Aluminium", "Béton / Maçonnerie / Carrelage", "PVC / Plastique", "Autre matériau"]
db_disques_blanchiment = ["Disque fibre abrasif", "Brosse métallique torsadée", "Disque à décapant synthétique (Clean & Strip)", "Disque semi-flexible"]

etapes_noms = [
    "1. Date & Entreprise", 
    "2. PDP & MoP", 
    "3. Responsable N2", 
    "4. Zone & Urgences", 
    "5. Check-list & EPIs", 
    "6. Formulaires Spécifiques", 
    "7. Synthèse & Signatures"
]

# Initialisation BDD Permis
if "permis_db" not in st.session_state:
    st.session_state.permis_db = [
        {
            "id": "PT-2026-0928-01",
            "date_travaux": datetime.date.today().strftime("%d/%m/%Y"),
            "societe": "ABYLSEN",
            "pdp": "PDP-2026-042 (Bâtiment M1 - Rénovation)",
            "mop": "MoP-01: Peinture & Finitions M1",
            "n2": "Léa DUSEK",
            "zone": "Bâtiment M1 - Bureaux",
            "emplacement": "1er étage, Bureau 104",
            "pr": "PR-2 (Parking Ouest)",
            "confinement": "ZC-01 (Hall M1)",
            "urg": "03.22.54.30.00 (Infirmerie M1)",
            "statut": "EN_ATTENTE_BATCH",
            "heure": "06:45",
            "intervenants": ["Léa DUSEK (N2)", "Matthieu MARTIN (N1)"],
            "derogations": ["Meuleuse d'angle"],
            "permis_specifiques": [],
            "tableau_risques": [
                {"activite": "Rénovation Peinture", "risque": "Inhalation solvants / Espace exigu", "prevention": "Cartouche ABEK + Gants EN 374-1/2"},
                {"activite": "Découpe supportage", "risque": "Projections étincelles / Bruit", "prevention": "Lunettes EN 166 + Bouchons d'oreilles Moulés"}
            ]
        }
    ]

# Navigation Kiosk
if "kiosk_mode" not in st.session_state:
    st.session_state.kiosk_mode = "HOME"
if "step" not in st.session_state:
    st.session_state.step = 1

# Initialisation des données de formulaire
if "form_data" not in st.session_state:
    st.session_state.form_data = {
        "date_str": datetime.date.today().strftime("%d/%m/%Y"),
        "societe": "ABYLSEN",
        "pdp": "PDP-2026-042 (Bâtiment M1 - Rénovation)",
        "mop": "MoP-01: Peinture & Finitions M1",
        "n2_nom": "Léa DUSEK",
        "lieu_pdp": "Bâtiment M1 - Bureaux",
        "lieu_precision": "1er étage, Bureau 104",
        "description": "Peinture mur nord bureau 104",
        "intervenants": ["Léa DUSEK", "Matthieu MARTIN"],
        
        # Permis Spécifiques
        "p_hauteur": False, "p_toiture": False, "p_points_chauds": False, "p_excavation": False,
        "p_grutage": False, "p_confine": False, "p_electrique": False, "p_consignation_pression": False,
        "p_consignation_mecanique": False, "p_consignation_equipement": False, "p_consignation_laser": False,
        "p_chimique": False, "p_demolition": False,

        # Champs spécifiques obligatoires
        "confine_o2": "20.9 %", "confine_co_h2s": "0 ppm (Conforme)", "confine_vigie": "Matthieu MARTIN", "confine_ventilation": True,
        "chaud_travaux": "Soudure Chalumeau / Meulage", "chaud_extincteur": "Extincteur Eau Pulvérisée 6L + CO2 sur zone", "chaud_ronde_post": "Ronde de sécurité programmée 2h après fin de chauffe",
        "loto_cadenas": "LOTO-PG-884", "loto_charge": "Léa DUSEK", "loto_fluide_elec": "Électrique & Pneumatique",
        "hauteur_ancrage": "Ligne de vie conforme EN 795 / Point d'ancrage vérifié", "hauteur_harnais": "Harnais 2 longes avec absorbeur d'énergie",
        "toiture_balisage": "Balisage zone d'exclusion au sol effectué",
        "excav_reseaux": "DICT / Plan des réseaux enterrés validé", "excav_blindage": "Blindage / Talutage mis en place (> 1.30m)",
        "grutage_capacite": "Charge de levage < 80% capacité grue", "grutage_sol": "Plaques de répartition des stabs posées",

        # STA & Outils
        "sta_prod_chimique": False, "produits_liste": "", "sta_dta": False,
        "sta_electroportatif": False, "sta_meuleuse": False,
        
        # MEULEUSE - DONNÉES SPÉCIFIQUES COMPLÈTES
        "meuleuse_diametre": "125 mm",
        "meuleuse_operateurs": ["Léa DUSEK"],
        "meuleuse_marque": "Bosch Professional",
        "meuleuse_alim": "Batterie 18V",
        "meuleuse_ref": "MEU-PG-042",
        "meuleuse_vitesse": "11 000 tr/min",
        
        # Environnement Meuleuse
        "meu_env_plain_pied": True,
        "meu_env_hauteur": False,
        "meu_env_confine": False,
        "meu_env_excavation": False,
        "meu_env_stable": True,
        "meu_env_maintien_2mains": True,
        "meu_env_piece_fixee": True,
        "meu_env_hors_ligne_tir": True,
        "meu_position_op": "Debout",

        # Types d'utilisation meuleuse
        "meuleuse_u_decoupe": False,
        "meuleuse_mat_decoupe": db_materiaux[0],
        "meuleuse_u_ebavurage": False,
        "meuleuse_mat_ebavurage": db_materiaux[0],
        "meuleuse_u_flap": False,
        "meuleuse_u_blanchiment": False,
        "meuleuse_disque_blanchiment": db_disques_blanchiment[0],

        "sta_pirl_nacelle": False, "sta_couteau_lame": False, "sta_echelle_escabeau": False,

        # Dangers & Risques
        "r_exigu": False, "r_superpose": False, "r_inconfortable": False, "r_fumee_poussiere": False,
        "r_bruit_80db": False, "r_rayonnement": False, "r_enzymes": False, "r_eq_mouvement": False,
        "r_chute_objets": False, "r_vehicule": False, "r_escalier": False, "r_liquide_sol": False,
        "r_ouverture_sol": False, "r_stockage_sol": False, "r_bords_tranchants": False,
        "r_perforation": False, "r_metaux_chaud": False, "r_metaux_froid": False,
        "r_feu_flamme": False, "r_cables_sol": False, "r_voies_circulation": False, "r_stockage_defini": True,

        # EPIS EXHAUSTIFS
        "epi_lunettes_chantier_visiere": True, "epi_lunettes_etanches": False,
        "epi_visiere_idra": False, "epi_pare_visage": False, "epi_casque_jugulaire": False,
        "epi_casque_auditif": False, "epi_gants_coupure": True, "epi_gants_manutention": False,
        "epi_gants_chimique": False, "epi_gants_electrique": False, "epi_bouchons_jetables": False,
        "epi_bouchons_moules": False, "epi_ffp1_ffp2": False, "epi_3m6000": False,
        "epi_versaflo": False, "epi_cartouche_abek": False, "epi_autre": ""
    }

# ---------------------------------------------------------
# NETTOYAGE DES TEXTES POUR POLICES FPDF (LATIN-1/ASCII)
# ---------------------------------------------------------
def sanitize_text(text):
    if not isinstance(text, str):
        text = str(text)
    text = text.replace("🔥", "[Pt Chaud]").replace("🦺", "[Confiné]").replace("🧗", "[Hauteur]").replace("⚡", "[LOTO]")
    text = text.replace("⚠️", "[!]").replace("✅", "[OK]").replace("🚜", "[Excavation]").replace("🚀", "")
    normalized = unicodedata.normalize('NFKD', text)
    cleaned = ''.join(c for c in normalized if not unicodedata.combining(c))
    return cleaned.encode('latin-1', 'ignore').decode('latin-1')

# ---------------------------------------------------------
# MOTEUR DE GÉNÉRATION PDF NATIVE (FPDF)
# ---------------------------------------------------------
def generer_pdf_bytes(permis):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_fill_color(0, 51, 102)
    pdf.rect(10, 10, 190, 22, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.text(15, 20, sanitize_text("PROCTER & GAMBLE AMIENS - e-Work Permit System"))
    pdf.set_font("Helvetica", "", 10)
    pdf.text(15, 27, sanitize_text(f"Ref: {permis['id']} | Date: {permis['date_travaux']} | Heure: {permis['heure']}"))

    pdf.set_y(38)

    if permis['statut'] == 'VALIDÉ':
        pdf.set_fill_color(220, 252, 231)
        pdf.set_draw_color(34, 197, 94)
        pdf.set_text_color(22, 101, 52)
        status_str = "PERMIS VALIDE PAR LE DONNEUR D'ORDRE"
    else:
        pdf.set_fill_color(254, 240, 138)
        pdf.set_draw_color(234, 179, 8)
        pdf.set_text_color(133, 77, 14)
        status_str = "PERMIS EN ATTENTE DE VALIDATION BATCH (07h30)"

    pdf.rect(10, 38, 190, 10, 'DF')
    pdf.set_font("Helvetica", "B", 11)
    pdf.text(15, 44.5, sanitize_text(status_str))

    pdf.set_text_color(0, 0, 0)
    pdf.set_y(54)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, sanitize_text("1. INFORMATIONS GENERALES & LOCALISATION"), 0, 1)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, sanitize_text(f"Société Intervenante: {permis['societe']} | PDP: {permis['pdp']}"), 0, 1)
    pdf.cell(0, 5, sanitize_text(f"Mode Opératoire (MoP): {permis.get('mop', 'N/A')}"), 0, 1)
    pdf.cell(0, 5, sanitize_text(f"Responsable N2: {permis['n2']} | Secteur: {permis['zone']} ({permis.get('emplacement', '')})"), 0, 1)
    pdf.cell(0, 5, sanitize_text(f"Point de Rassemblement (PR): {permis.get('pr')} | Confinement: {permis.get('confinement')}"), 0, 1)
    pdf.cell(0, 5, sanitize_text(f"Urgence Secteur: {permis.get('urg')}"), 0, 1)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, sanitize_text("2. SYNTHESE DES RISQUES ET MOYENS DE PREVENTION"), 0, 1)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(60, 6, sanitize_text("Activité Cochée"), 1, 0, 'L', True)
    pdf.cell(65, 6, sanitize_text("Risque Identifié"), 1, 0, 'L', True)
    pdf.cell(65, 6, sanitize_text("Moyens de Prévention / EPIs"), 1, 1, 'L', True)

    pdf.set_font("Helvetica", "", 8)
    risques = permis.get("tableau_risques", [])
    if not risques:
        pdf.cell(60, 6, sanitize_text("Travaux Généraux PDP"), 1, 0)
        pdf.cell(65, 6, sanitize_text("Risques standards chantier"), 1, 0)
        pdf.cell(65, 6, sanitize_text("EPIs Obligatoires P&G"), 1, 1)
    else:
        for r in risques:
            act = sanitize_text(str(r.get("activite", "")))[:32]
            ris = sanitize_text(str(r.get("risque", "")))[:36]
            prev = sanitize_text(str(r.get("prevention", "")))[:36]
            pdf.cell(60, 6, act, 1, 0)
            pdf.cell(65, 6, ris, 1, 0)
            pdf.cell(65, 6, prev, 1, 1)

    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, sanitize_text("3. PERMIS SPECIFIQUES ET DEROGATIONS"), 0, 1)
    pdf.set_font("Helvetica", "", 9)
    spe_all = permis.get('permis_specifiques', []) + permis.get('derogations', [])
    if spe_all:
        clean_spe = [sanitize_text(s) for s in spe_all]
        pdf.cell(0, 5, " - " + ", ".join(clean_spe), 0, 1)
    else:
        pdf.cell(0, 5, sanitize_text(" - Aucun permis spécifique ou dérogation requise"), 0, 1)

    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, sanitize_text("4. CO-SIGNATURES TACTILES AUDITEES"), 0, 1)
    pdf.set_font("Helvetica", "", 8)
    for sign in permis.get("intervenants", []):
        pdf.cell(0, 5, sanitize_text(f" [OK] Signature horodatée sur borne tactile : {sign}"), 1, 1)

    return bytes(pdf.output())

# ---------------------------------------------------------
# BARRE LATÉRALE
# ---------------------------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Procter_%26_Gamble_logo.svg/1024px-Procter_%26_Gamble_logo.svg.png", width=80)
st.sidebar.title("e-Work Permit P&G")
st.sidebar.caption("Site d'Amiens — Solution Unifiée")

role = st.sidebar.radio(
    "Interface à démontrer :",
    [
        "🖥️ Borne Kiosk Tactile (EE / N2)",
        "📊 DDS Board & Batch 07h30 (DO / HSE)",
        "📱 Inspection Terrain QR Code (Casque Rouge)"
    ]
)

# ==============================================================================
# INTERFACE 1 : BORNE KIOSK TACTILE (EE / N2)
# ==============================================================================
if role == "🖥️ Borne Kiosk Tactile (EE / N2)":

    st.markdown("""
    <div class="pg-header">
        <h1 style='margin:0; font-size: 2.1rem;'>PROCTER & GAMBLE — AMIENS</h1>
        <p style='margin:4px 0 0 0; opacity:0.85; font-size: 1.05rem;'>WORK PERMIT IT | BORNE TACTILE KIOSK</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.kiosk_mode == "HOME":
        st.write("### Veuillez sélectionner votre démarche :")
        st.write("")

        col_act1, col_act2 = st.columns(2)

        with col_act1:
            st.markdown("""
            <div class="welcome-card">
                <h2 style="color:#003366; margin-bottom:10px;">🚀 Permis de Travail</h2>
                <p style="color:#475569;">Émettre un nouveau Permis de Travail (STA, Check-list, EPIs normés & Signatures).</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 COMMENCER UN PERMIS DE TRAVAIL", type="primary", use_container_width=True):
                st.session_state.kiosk_mode = "PERMIS"
                st.session_state.step = 1
                st.rerun()

        with col_act2:
            st.markdown("""
            <div class="welcome-card">
                <h2 style="color:#003366; margin-bottom:10px;">📝 Émargement PDP</h2>
                <p style="color:#475569;">Émarger et signer un Plan de Prévention enregistré pour votre entreprise.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📝 SIGNER UN PLAN DE PRÉVENTION (PDP)", use_container_width=True):
                st.session_state.kiosk_mode = "PDP"
                st.rerun()

    elif st.session_state.kiosk_mode == "PDP":
        if st.button("⬅️ Retour à l'accueil"):
            st.session_state.kiosk_mode = "HOME"
            st.rerun()

        st.subheader("📝 Émargement d'un Plan de Prévention (PDP)")
        st.divider()

        soc_pdp = st.selectbox("1. Sélectionnez votre Entreprise Extérieure (EE) :", db_societes)
        pdps_disponibles = db_pdps.get(soc_pdp, ["Aucun PDP trouvé"])
        pdp_sel = st.selectbox(f"2. Plans de Prévention enregistrés pour {soc_pdp} :", pdps_disponibles)

        st.divider()

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            nom_pdp = st.text_input("Nom & Prénom de l'intervenant :")
            statut_pdp = st.selectbox("Statut sur le chantier :", ["N1 (Compagnon)", "N2 (Responsable)"])

        with col_p2:
            if "N2" in statut_pdp:
                tel_pdp = st.text_input("N° Téléphone Portable du Responsable N2 :", placeholder="06 XX XX XX XX")
            else:
                tel_pdp = "Non requis (N1)"

            st.write("✍️ **Signature Tactile de l'Émargement :**")
            st.info(" [ Zone de Signature Tactile Empreinte / Stylet ] ")

        if st.button("✅ VALIDER L'ÉMARGEMENT DU PDP", type="primary", use_container_width=True):
            if not nom_pdp:
                st.error("Veuillez saisir votre Nom & Prénom.")
            elif "N2" in statut_pdp and (not tel_pdp or tel_pdp == "Non requis (N1)"):
                st.error("Veuillez renseigner le N° de téléphone du responsable N2.")
            else:
                st.balloons()
                st.success(f"Émargement validé avec succès pour {nom_pdp} ({statut_pdp}) sur le {pdp_sel} !")
                st.session_state.kiosk_mode = "HOME"

    elif st.session_state.kiosk_mode == "PERMIS":

        current_step = st.session_state.step
        stepper_html = "<div class='stepper-bar'>"
        for idx, name in enumerate(etapes_noms, 1):
            if idx == current_step:
                stepper_html += f"<span style='color:#003366; background:#dbeafe; padding:6px 12px; border-radius:15px; margin:0 4px;'><b>{name}</b></span> "
            elif idx < current_step:
                stepper_html += f"<span style='color:#10b981; margin:0 4px;'>✓ {name}</span> "
            else:
                stepper_html += f"<span style='color:#94a3b8; margin:0 4px;'>{name}</span> "
        stepper_html += "</div>"
        st.markdown(stepper_html, unsafe_allow_html=True)

        if current_step == 1:
            st.subheader("1. Date d'Intervention & Entreprise Extérieure")
            col_d1, col_d2 = st.columns(2)
            today_date = datetime.date.today()
            tomorrow_date = today_date + datetime.timedelta(days=1)

            with col_d1:
                date_choice = st.radio(
                    "Date de planification du permis :",
                    [f"Aujourd'hui : {today_date.strftime('%d/%m/%Y')}", f"Pour demain : {tomorrow_date.strftime('%d/%m/%Y')}"]
                )
                st.session_state.form_data["date_str"] = tomorrow_date.strftime("%d/%m/%Y") if "demain" in date_choice else today_date.strftime("%d/%m/%Y")

            with col_d2:
                st.session_state.form_data["societe"] = st.selectbox("Entreprise Extérieure (EE) :", db_societes, index=db_societes.index(st.session_state.form_data["societe"]))

            st.divider()
            c_back, c_next = st.columns([1, 1])
            with c_back:
                if st.button("⬅️ Accueil"):
                    st.session_state.kiosk_mode = "HOME"
                    st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"):
                    st.session_state.step = 2
                    st.rerun()

        elif current_step == 2:
            st.subheader(f"2. Plan de Prévention & Mode Opératoire — {st.session_state.form_data['societe']}")
            p_list = db_pdps.get(st.session_state.form_data["societe"], ["PDP Standard"])
            st.session_state.form_data["pdp"] = st.selectbox("Plan de Prévention (PDP) rattaché :", p_list)
            m_list = db_mops.get(st.session_state.form_data["pdp"], ["MoP Standard"])
            st.session_state.form_data["mop"] = st.selectbox("Mode Opératoire (MoP) :", m_list)

            st.divider()
            c_back, c_next = st.columns([1, 1])
            with c_back:
                if st.button("⬅️ Précédent"):
                    st.session_state.step = 1
                    st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"):
                    st.session_state.step = 3
                    st.rerun()

        elif current_step == 3:
            st.subheader("3. Responsable N2 Présent sur le Chantier")
            st.session_state.form_data["n2_nom"] = st.selectbox("Responsable N2 qualifié :", db_n2, index=db_n2.index(st.session_state.form_data["n2_nom"]))

            c_back, c_next = st.columns([1, 1])
            with c_back:
                if st.button("⬅️ Précédent"):
                    st.session_state.step = 2
                    st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"):
                    st.session_state.step = 4
                    st.rerun()

        elif current_step == 4:
            st.subheader("4. Localisation & Assignation Automatique des Urgences")
            st.session_state.form_data["lieu_pdp"] = st.selectbox("Zone du Chantier :", list(db_zones_carto.keys()))
            st.session_state.form_data["lieu_precision"] = st.text_input("Précision d'emplacement (Local, Bureau, Ligne) :", value=st.session_state.form_data["lieu_precision"])
            st.session_state.form_data["description"] = st.text_input("Description détaillée de la tâche :", value=st.session_state.form_data["description"])

            carto = db_zones_carto.get(st.session_state.form_data["lieu_pdp"], {})
            st.warning(f"""
            📍 **Assignation Sécurité Secteur Automatisée :**
            - **Point de Rassemblement (PR) :** `{carto.get('pr')}`
            - **Zone de Confinement :** `{carto.get('confinement')}`
            - **Poste d'Urgence :** `{carto.get('urgence')}`
            """)

            c_back, c_next = st.columns([1, 1])
            with c_back:
                if st.button("⬅️ Précédent"):
                    st.session_state.step = 3
                    st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"):
                    st.session_state.step = 5
                    st.rerun()

        elif current_step == 5:
            st.subheader("5. Check-list Intégrale, STA, Dangers & EPIs Normés P&G")

            meteo_live = obtenir_meteo_amiens_live()
            is_demain = ("demain" in st.session_state.form_data["date_str"]) or (st.session_state.form_data["date_str"] != datetime.date.today().strftime("%d/%m/%Y"))
            vitesse_vent = meteo_live["vent_j1"] if is_demain else meteo_live["vent_j0"]

            if vitesse_vent < 30:
                badge_bg = "#dcfce7"; badge_border = "#22c55e"; badge_color = "#166534"
                badge_status = "🟢 <b>Vigilance Vent : Conforme (< 30 km/h)</b>"
                badge_msg = "Conditions favorables (Hauteur / Grutage / Nacelles)"
            elif 30 <= vitesse_vent < 36:
                badge_bg = "#ffedd5"; badge_border = "#f97316"; badge_color = "#9a3412"
                badge_status = "🟠 <b>Vigilance Vent : Vigilance Absolue (30 à 35 km/h)</b>"
                badge_msg = "Surveillance continue requise sur zone"
            else:
                badge_bg = "#fee2e2"; badge_border = "#ef4444"; badge_color = "#991b1b"
                badge_status = "🔴 <b>Vigilance Vent : SEUIL ATTEINT (>= 36 km/h)</b>"
                badge_msg = "ARRÊT IMMÉDIAT (Hauteur / Grutage / Nacelles)"

            st.markdown(f"""
            <div class="weather-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <span style="font-size: 0.95rem;">🌤️ <b>Aujourd'hui :</b> {meteo_live['temp_j0']}°C | Rafales Vent : <b>{meteo_live['vent_j0']} km/h</b></span>
                    <span style="background:{badge_bg}; color:{badge_color}; border:1px solid {badge_border}; padding:3px 10px; border-radius:6px; font-size:0.82rem; font-weight:bold;">{badge_status}</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.95rem;">☀️ <b>Demain :</b> {meteo_live['temp_j1']}°C | Rafales Vent : <b>{meteo_live['vent_j1']} km/h</b> <i style="font-size:0.75rem; opacity:0.8;">({meteo_live['source']})</i></span>
                    <span style="font-size: 0.78rem; color: #475569; font-weight: 500;">{badge_msg}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.error("🚨 **Identification des Risques Principaux ➔ Déclencheurs de Permis Spécifiques (HRT)**")
            c_rp1, c_rp2 = st.columns(2)
            with c_rp1:
                st.session_state.form_data["p_hauteur"] = st.checkbox("Travail en hauteur / échafaudage / nacelle ➔ Permis Hauteur", value=st.session_state.form_data["p_hauteur"])
                st.session_state.form_data["p_toiture"] = st.checkbox("Accès toiture ➔ Permis Accès Toiture", value=st.session_state.form_data["p_toiture"])
                
                if st.session_state.form_data.get("sta_meuleuse", False):
                    st.session_state.form_data["p_points_chauds"] = True
                    st.session_state.form_data["r_feu_flamme"] = True
                    st.session_state.form_data["r_metaux_chaud"] = True

                st.session_state.form_data["p_points_chauds"] = st.checkbox(
                    "Génération de points chauds / flamme ➔ Permis Point Chaud" + (" 🔒 (Automatique : Utilisation de la Meuleuse)" if st.session_state.form_data.get("sta_meuleuse") else ""), 
                    value=st.session_state.form_data["p_points_chauds"]
                )
                st.session_state.form_data["p_excavation"] = st.checkbox("Tranchée, BTP, Ouverture de sol ➔ Permis Excavation", value=st.session_state.form_data["p_excavation"])
                st.session_state.form_data["p_grutage"] = st.checkbox("Grutage ➔ Permis Grutage", value=st.session_state.form_data["p_grutage"])
                st.session_state.form_data["p_confine"] = st.checkbox("Espace confiné, risque asphyxie / anoxie (azote) ➔ Permis Espace Confiné", value=st.session_state.form_data["p_confine"])
                st.session_state.form_data["p_electrique"] = st.checkbox("Travail électrique ➔ Permis Travail Électrique", value=st.session_state.form_data["p_electrique"])

            with c_rp2:
                st.session_state.form_data["p_consignation_pression"] = st.checkbox("Ouverture circuit sous pression (vapeur, air, gaz, fluides) ➔ Permis Consignation", value=st.session_state.form_data["p_consignation_pression"])
                st.session_state.form_data["p_consignation_mecanique"] = st.checkbox("Machines en mouvement / parties mobiles ➔ Permis Consignation", value=st.session_state.form_data["p_consignation_mecanique"])
                st.session_state.form_data["p_consignation_equipement"] = st.checkbox("Équipement sous pression ➔ Permis Consignation", value=st.session_state.form_data["p_consignation_equipement"])
                st.session_state.form_data["p_consignation_laser"] = st.checkbox("Travaux à proximité de lasers classe IV ➔ Permis Consignation", value=st.session_state.form_data["p_consignation_laser"])
                st.session_state.form_data["p_chimique"] = st.checkbox("Risque Chimique particulier", value=st.session_state.form_data["p_chimique"])
                st.session_state.form_data["p_demolition"] = st.checkbox("Démolition", value=st.session_state.form_data["p_demolition"])

            st.divider()

            st.info("📋 **Analyse STA & Spécificités Outillage**")
            c_s1, c_s2 = st.columns(2)

            with c_s1:
                st.session_state.form_data["sta_prod_chimique"] = st.checkbox("Utilisation de Produits Chimiques dans le MoP / FDS", value=st.session_state.form_data["sta_prod_chimique"])
                if st.session_state.form_data["sta_prod_chimique"]:
                    st.session_state.form_data["produits_liste"] = st.text_input("Saisir les produits chimiques utilisés :", value=st.session_state.form_data["produits_liste"], placeholder="ex: Solvant, Acétone, Colle PU...")

                st.session_state.form_data["sta_dta"] = st.checkbox("Consultation DTA (Dossier Technique Amiante) effectuée", value=st.session_state.form_data["sta_dta"])
                st.session_state.form_data["sta_pirl_nacelle"] = st.checkbox("Utilisation Gazelle (PIRL) ou Nacelle", value=st.session_state.form_data["sta_pirl_nacelle"])

            with c_s2:
                st.session_state.form_data["sta_electroportatif"] = st.checkbox("Utilisation de matériel électroportatif", value=st.session_state.form_data["sta_electroportatif"])
                if st.session_state.form_data["sta_electroportatif"]:
                    
                    meul_check = st.checkbox("Utilisation d'une Meuleuse d'angle ➔ Dérogation Meuleuse", value=st.session_state.form_data["sta_meuleuse"])
                    st.session_state.form_data["sta_meuleuse"] = meul_check

                    if meul_check:
                        st.session_state.form_data["p_points_chauds"] = True
                        st.session_state.form_data["r_feu_flamme"] = True
                        st.session_state.form_data["r_metaux_chaud"] = True
                        st.session_state.form_data["epi_visiere_idra"] = True
                        st.session_state.form_data["epi_casque_auditif"] = True
                        st.session_state.form_data["epi_gants_coupure"] = True

                st.session_state.form_data["sta_couteau_lame"] = st.checkbox("Utilisation de couteau / lame ouverte ➔ Dérogation Casque Rouge", value=st.session_state.form_data["sta_couteau_lame"])
                if st.session_state.form_data["sta_couteau_lame"]:
                    st.session_state.form_data["r_bords_tranchants"] = True

                st.session_state.form_data["sta_echelle_escabeau"] = st.checkbox("Utilisation d'échelle / escabeau / marche-pied ➔ Dérogation Casque Rouge", value=st.session_state.form_data["sta_echelle_escabeau"])

            is_travail_hauteur = (
                st.session_state.form_data["p_hauteur"] or 
                st.session_state.form_data["p_toiture"] or 
                st.session_state.form_data["sta_pirl_nacelle"] or 
                st.session_state.form_data["sta_echelle_escabeau"]
            )
            if is_travail_hauteur:
                st.session_state.form_data["epi_casque_jugulaire"] = True

            st.divider()

            st.write("##### ⚠️ Liste de Contrôle & Évaluation des Dangers Potentiels")
            c_d1, c_d2, c_d3 = st.columns(3)
            with c_d1:
                st.caption("**Conditions de travail & Exposition**")
                st.session_state.form_data["r_exigu"] = st.checkbox("Travail en espace exigu", value=st.session_state.form_data["r_exigu"])
                st.session_state.form_data["r_superpose"] = st.checkbox("Travail superposé", value=st.session_state.form_data["r_superpose"])
                st.session_state.form_data["r_inconfortable"] = st.checkbox("Position inconfortable (TMS)", value=st.session_state.form_data["r_inconfortable"])
                st.session_state.form_data["r_fumee_poussiere"] = st.checkbox("Fumée / Poussière", value=st.session_state.form_data["r_fumee_poussiere"])
                st.session_state.form_data["r_bruit_80db"] = st.checkbox("Bruit > 80 dB", value=st.session_state.form_data["r_bruit_80db"])

            with c_d2:
                st.caption("**Chocs, Heurts & Glissades**")
                st.session_state.form_data["r_eq_mouvement"] = st.checkbox("Équipement en mouvement", value=st.session_state.form_data["r_eq_mouvement"])
                st.session_state.form_data["r_chute_objets"] = st.checkbox("Chute d'objets", value=st.session_state.form_data["r_chute_objets"])
                st.session_state.form_data["r_vehicule"] = st.checkbox("Véhicule / Chariot en mouvement", value=st.session_state.form_data["r_vehicule"])
                st.session_state.form_data["r_escalier"] = st.checkbox("Présence d'escalier", value=st.session_state.form_data["r_escalier"])

            with c_d3:
                st.caption("**Contacts, Chaleur & Zone**")
                st.session_state.form_data["r_bords_tranchants"] = st.checkbox("Objets / bords tranchants", value=st.session_state.form_data["r_bords_tranchants"])
                st.session_state.form_data["r_metaux_chaud"] = st.checkbox("Métaux soudés à chaud ➔ Point Chaud", value=st.session_state.form_data["r_metaux_chaud"])
                st.session_state.form_data["r_feu_flamme"] = st.checkbox("Feu / Flamme ➔ Point Chaud", value=st.session_state.form_data["r_feu_flamme"])
                st.session_state.form_data["r_cables_sol"] = st.checkbox("Gestion des câbles au sol", value=st.session_state.form_data["r_cables_sol"])

            st.divider()

            st.warning("""
            📢 **Consigne Sécurité Chantier P&G Amiens :**  
            *Les chaussures de sécurité montantes, le casque avec jugulaire, les lunettes de sécurité à protection latérale (EN 166), le gilet haute visibilité (sauf pour travaux électriques ou point chaud) et les gants anti-coupure sont OBLIGATOIRES sur le chantier de construction.*
            """)

            st.write("##### 🥽 Équipements de Protection Individuelle (EPIs Normés P&G)")

            col_e1, col_e2, col_e3, col_e4 = st.columns(4)

            with col_e1:
                st.markdown("**👓 Lunettes (EN 166)**")
                st.session_state.form_data["epi_lunettes_chantier_visiere"] = st.checkbox("Chantier ou Visière", value=st.session_state.form_data["epi_lunettes_chantier_visiere"])
                st.session_state.form_data["epi_lunettes_etanches"] = st.checkbox("Étanches", value=st.session_state.form_data["epi_lunettes_etanches"])

                st.markdown("**🛡️ Protection Faciale (EN 166B)**")
                st.session_state.form_data["epi_visiere_idra"] = st.checkbox(
                    "Visière / Écran facial" + (" 🔒 (Automatique : Meuleuse)" if st.session_state.form_data.get("sta_meuleuse") else ""), 
                    value=st.session_state.form_data["epi_visiere_idra"]
                )
                st.session_state.form_data["epi_pare_visage"] = st.checkbox("Lunette + Pare-visage", value=st.session_state.form_data["epi_pare_visage"])

            with col_e2:
                st.markdown("**🪖 Casques (EN 387/A1)**")
                st.session_state.form_data["epi_casque_jugulaire"] = st.checkbox(
                    "Avec jugulaire" + (" 🔒 (Obligatoire : Travail en Hauteur)" if is_travail_hauteur else ""), 
                    value=st.session_state.form_data["epi_casque_jugulaire"]
                )
                st.session_state.form_data["epi_casque_auditif"] = st.checkbox(
                    "Avec protection auditive" + (" 🔒 (Automatique : Meuleuse)" if st.session_state.form_data.get("sta_meuleuse") else ""), 
                    value=st.session_state.form_data["epi_casque_auditif"]
                )

                st.markdown("**🎧 Bouchons d'oreilles**")
                st.session_state.form_data["epi_bouchons_jetables"] = st.checkbox("Jetables", value=st.session_state.form_data["epi_bouchons_jetables"])
                st.session_state.form_data["epi_bouchons_moules"] = st.checkbox("Moulés sur mesure", value=st.session_state.form_data["epi_bouchons_moules"])

            with col_e3:
                st.markdown("**🧤 Gants de Protection**")
                st.session_state.form_data["epi_gants_coupure"] = st.checkbox(
                    "Anti-coupures (4543 / 4X43D)" + (" 🔒 (Automatique : Meuleuse)" if st.session_state.form_data.get("sta_meuleuse") else ""), 
                    value=st.session_state.form_data["epi_gants_coupure"]
                )
                st.session_state.form_data["epi_gants_manutention"] = st.checkbox("Manutention (Cuir bovin/chèvre)", value=st.session_state.form_data["epi_gants_manutention"])
                st.session_state.form_data["epi_gants_chimique"] = st.checkbox("Chimiques (EN 374-1/2)", value=st.session_state.form_data["epi_gants_chimique"])
                st.session_state.form_data["epi_gants_electrique"] = st.checkbox("Électriques isolants / Surgants (EN 60903)", value=st.session_state.form_data["epi_gants_electrique"])

            with col_e4:
                st.markdown("**🫁 Protections Respiratoires**")
                st.session_state.form_data["epi_ffp1_ffp2"] = st.checkbox("FFP1 / FFP2", value=st.session_state.form_data["epi_ffp1_ffp2"])
                st.session_state.form_data["epi_3m6000"] = st.checkbox("3M 6000", value=st.session_state.form_data["epi_3m6000"])
                st.session_state.form_data["epi_versaflo"] = st.checkbox("Versaflo", value=st.session_state.form_data["epi_versaflo"])
                st.session_state.form_data["epi_cartouche_abek"] = st.checkbox("Cartouche ABEK (EN 14387)", value=st.session_state.form_data["epi_cartouche_abek"])

                st.markdown("**➕ Autre EPI Spécifique**")
                st.session_state.form_data["epi_autre"] = st.text_input("À préciser en texte libre :", value=st.session_state.form_data["epi_autre"])

            c_back, c_next = st.columns([1, 1])
            with c_back:
                if st.button("⬅️ Précédent"):
                    st.session_state.step = 4
                    st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"):
                    st.session_state.step = 6
                    st.rerun()

        # =====================================================
        # ÉTAPE 6 : FORMULAIRES DÉTAILLÉS PAR PERMIS SPÉCIFIQUE
        # =====================================================
        elif current_step == 6:
            st.subheader("6. Formulaires Spécifiques (HRT) & Données Obligatoires à Remplir")

            has_spe = False

            if st.session_state.form_data["p_confine"]:
                has_spe = True
                st.info("🦺 **PERMIS ESPACE CONFINÉ (CBA 105)** — Données d'Analyse d'Atmosphère")
                c1, c2, c3 = st.columns(3)
                with c1: st.session_state.form_data["confine_o2"] = st.text_input("Taux O2 mesuré (Normal 20.9%) :", value=st.session_state.form_data["confine_o2"])
                with c2: st.session_state.form_data["confine_co_h2s"] = st.text_input("Seuil CO / H2S / Explosimétrie :", value=st.session_state.form_data["confine_co_h2s"])
                with c3: st.session_state.form_data["confine_vigie"] = st.text_input("Nom & Prénom Vigie Extérieure Obligatoire :", value=st.session_state.form_data["confine_vigie"])
                st.session_state.form_data["confine_ventilation"] = st.checkbox("Ventilation forcée / Extraction d'air active", value=st.session_state.form_data["confine_ventilation"])
                st.divider()

            if st.session_state.form_data["p_points_chauds"] or st.session_state.form_data["r_feu_flamme"] or st.session_state.form_data["r_metaux_chaud"]:
                has_spe = True
                st.warning("🔥 **PERMIS POINTS CHAUDS / SOUDURE / MEULAGE** — Consignes Incendie")
                c1, c2 = st.columns(2)
                with c1: st.session_state.form_data["chaud_travaux"] = st.text_input("Nature des travaux de chauffe / outils :", value=st.session_state.form_data["chaud_travaux"])
                with c2: st.session_state.form_data["chaud_extincteur"] = st.text_input("Moyens d'extinction présents sur zone :", value=st.session_state.form_data["chaud_extincteur"])
                st.session_state.form_data["chaud_ronde_post"] = st.text_input("Procédure Ronde Sécurité Post-Chauffe :", value=st.session_state.form_data["chaud_ronde_post"])
                st.divider()

            if st.session_state.form_data["p_consignation_pression"] or st.session_state.form_data["p_consignation_mecanique"] or st.session_state.form_data["p_consignation_equipement"] or st.session_state.form_data["p_consignation_laser"]:
                has_spe = True
                st.success("⚡ **PERMIS CONSIGNATION / DECONSIGNATION (LOTO)** — Identifiants Sécurité")
                c1, c2, c3 = st.columns(3)
                with c1: st.session_state.form_data["loto_cadenas"] = st.text_input("Numéro de Cadenas LOTO appliqué :", value=st.session_state.form_data["loto_cadenas"])
                with c2: st.session_state.form_data["loto_charge"] = st.text_input("Chargé de Consignation Responsable :", value=st.session_state.form_data["loto_charge"])
                with c3: st.session_state.form_data["loto_fluide_elec"] = st.text_input("Énergies / Fluides consignés :", value=st.session_state.form_data["loto_fluide_elec"])
                st.divider()

            if st.session_state.form_data["p_hauteur"] or st.session_state.form_data["p_toiture"]:
                has_spe = True
                st.error("🧗 **PERMIS TRAVAIL EN HAUTEUR / ACCÈS TOITURE** — Contrôle des Équipements")
                c1, c2 = st.columns(2)
                with c1: st.session_state.form_data["hauteur_ancrage"] = st.text_input("Point d'ancrage / Ligne de vie vérifiée :", value=st.session_state.form_data["hauteur_ancrage"])
                with c2: st.session_state.form_data["hauteur_harnais"] = st.text_input("Type de Harnais & Longes :", value=st.session_state.form_data["hauteur_harnais"])
                if st.session_state.form_data["p_toiture"]:
                    st.session_state.form_data["toiture_balisage"] = st.text_input("Balisage / Sécurisation accès toiture :", value=st.session_state.form_data["toiture_balisage"])
                st.divider()

            if st.session_state.form_data["p_excavation"]:
                has_spe = True
                st.warning("🚜 **PERMIS EXCAVATION / TRANCHÉE / OUVERTURE DE SOL**")
                c1, c2 = st.columns(2)
                with c1: st.session_state.form_data["excav_reseaux"] = st.text_input("Contrôle réseaux enterrés (DICT / Détection) :", value=st.session_state.form_data["excav_reseaux"])
                with c2: st.session_state.form_data["excav_blindage"] = st.text_input("Moyens de blindage / talutage prévus :", value=st.session_state.form_data["excav_blindage"])
                st.divider()

            if st.session_state.form_data["p_grutage"]:
                has_spe = True
                st.info("🏗️ **PERMIS GRUTAGE & OPÉRATION DE LEVAGE**")
                c1, c2 = st.columns(2)
                with c1: st.session_state.form_data["grutage_capacite"] = st.text_input("Capacité & Plan de levage validé :", value=st.session_state.form_data["grutage_capacite"])
                with c2: st.session_state.form_data["grutage_sol"] = st.text_input("Stabilisation & Répartition au sol :", value=st.session_state.form_data["grutage_sol"])
                st.divider()

            # --- DÉROGATION MEULEUSE D'ANGLE AVEC CONSIGNES SÉCURITÉ DÉTAILLÉES ---
            if st.session_state.form_data["sta_meuleuse"]:
                has_spe = True
                st.error("⚠️ **DÉROGATION UTILISATION MEULEUSE D'ANGLE — PROTOCOLE SÉCURITÉ P&G**")
                
                st.markdown("##### 1. Identification & Opérateurs Habilités du Plan de Prévention")
                c_m0, c_m1, c_m2 = st.columns([2, 2, 2])
                with c_m0:
                    st.session_state.form_data["meuleuse_diametre"] = st.selectbox("Diamètre de la meuleuse d'angle :", ["125 mm", "230 mm"], index=0)
                with c_m1:
                    st.session_state.form_data["meuleuse_operateurs"] = st.multiselect(
                        "Personnes habilitées à utiliser la meuleuse (ayant émargé le Plan de Prévention) :",
                        options=st.session_state.form_data["intervenants"],
                        default=st.session_state.form_data["intervenants"]
                    )
                with c_m2:
                    st.session_state.form_data["meuleuse_marque"] = st.text_input("Marque de la meuleuse :", value=st.session_state.form_data["meuleuse_marque"])

                c_m3, c_m4, c_m5 = st.columns(3)
                with c_m3:
                    st.session_state.form_data["meuleuse_alim"] = st.selectbox("Type d'alimentation électrique :", ["Batterie 18V/54V", "Filaire 230V", "Pneumatique"], index=0)
                with c_m4:
                    st.session_state.form_data["meuleuse_ref"] = st.text_input("Référence interne ou numéro de série :", value=st.session_state.form_data["meuleuse_ref"])
                with c_m5:
                    st.session_state.form_data["meuleuse_vitesse"] = st.text_input("Vitesse maximale de la meuleuse (tr/min) :", value=st.session_state.form_data["meuleuse_vitesse"])

                st.warning("⚠️ **Rappels de Sécurité Obligatoires concernant les Disques :**\n"
                           "- La **vitesse de rotation maximale inscrite sur le disque** doit être STRICTEMENT SUPÉRIEURE à la vitesse de rotation maximale de la meuleuse.\n"
                           "- Les disques utilisés doivent avoir une **date de validité non dépassée** (vérification systématique de la gravure sur la bague centrale).")

                st.markdown("##### 2. Environnement de Travail & Position de l'Opérateur")
                ce1, ce2, ce3, ce4 = st.columns(4)
                with ce1:
                    st.session_state.form_data["meu_env_plain_pied"] = st.checkbox("Travail de plain-pied", value=st.session_state.form_data["meu_env_plain_pied"])
                    st.session_state.form_data["meu_env_hauteur"] = st.checkbox("Travail en hauteur", value=st.session_state.form_data["meu_env_hauteur"])
                with ce2:
                    st.session_state.form_data["meu_env_confine"] = st.checkbox("Utilisation en espace confiné", value=st.session_state.form_data["meu_env_confine"])
                    st.session_state.form_data["meu_env_excavation"] = st.checkbox("Utilisation dans une excavation", value=st.session_state.form_data["meu_env_excavation"])
                with ce3:
                    st.session_state.form_data["meu_env_stable"] = st.checkbox("Position de l'opérateur stable", value=st.session_state.form_data["meu_env_stable"])
                    st.session_state.form_data["meu_env_maintien_2mains"] = st.checkbox("Permet un maintien ferme à 2 mains", value=st.session_state.form_data["meu_env_maintien_2mains"])
                with ce4:
                    st.session_state.form_data["meu_env_piece_fixee"] = st.checkbox("Pièce à travailler fixée ou bridée", value=st.session_state.form_data["meu_env_piece_fixee"])
                    st.session_state.form_data["meu_env_hors_ligne_tir"] = st.checkbox("Opérateur positionné hors de la ligne de tir", value=st.session_state.form_data["meu_env_hors_ligne_tir"])

                st.session_state.form_data["meu_position_op"] = st.selectbox(
                    "Position principale de l'opérateur durant l'intervention :",
                    ["Debout", "À genoux", "Accroupi", "En hauteur sur plateforme sécurisée ou nacelle", "Accès restreint ou encombré"]
                )

                st.markdown("##### 3. Sélection du ou des types d'utilisation de la meuleuse :")
                
                cm_u1, cm_u2, cm_u3, cm_u4 = st.columns(4)
                with cm_u1:
                    st.session_state.form_data["meuleuse_u_decoupe"] = st.checkbox("✂️ **Découpes**", value=st.session_state.form_data["meuleuse_u_decoupe"])
                with cm_u2:
                    st.session_state.form_data["meuleuse_u_ebavurage"] = st.checkbox("🛠️ **Ébavurage**", value=st.session_state.form_data["meuleuse_u_ebavurage"])
                with cm_u3:
                    st.session_state.form_data["meuleuse_u_flap"] = st.checkbox("🌀 **Flap (Lamelles)**", value=st.session_state.form_data["meuleuse_u_flap"])
                with cm_u4:
                    st.session_state.form_data["meuleuse_u_blanchiment"] = st.checkbox("✨ **Blanchiment**", value=st.session_state.form_data["meuleuse_u_blanchiment"])

                if st.session_state.form_data["meuleuse_u_decoupe"]:
                    st.info("📌 **Détails pour l'activité DÉCOUPES :**")
                    cd1, cd2 = st.columns(2)
                    with cd1:
                        st.session_state.form_data["meuleuse_mat_decoupe"] = st.selectbox("Type de matériau à découper :", db_materiaux, key="mat_dec")
                    with cd2:
                        st.write("• **Type de disque sélectionné :** Disque à tronçonner fin ou disque diamant (attribution automatique).")
                        st.error("🔒 **Protection carter :** DOUBLE CARTER OBLIGATOIRE sur la meuleuse d'angle.")
                        st.caption("📐 **Angle de travail :** Respect strict de l'angle à **90°** par rapport au matériau.")

                if st.session_state.form_data["meuleuse_u_ebavurage"]:
                    st.info("📌 **Détails pour l'activité ÉBAVURAGE :**")
                    ce1_d, ce2_d = st.columns(2)
                    with ce1_d:
                        st.session_state.form_data["meuleuse_mat_ebavurage"] = st.selectbox("Type de matériau à ébavurer :", db_materiaux, key="mat_eba")
                    with ce2_d:
                        st.write("• **Type de disque sélectionné :** Disque à ébavurer épais à moyeu déporté (attribution automatique).")
                        st.warning("🔒 **Protection carter :** SIMPLE CARTER obligatoire.")
                        st.caption("📐 **Angle de travail :** Respect strict d'un angle de **30° à 40°** par rapport au matériau.")

                if st.session_state.form_data["meuleuse_u_flap"]:
                    st.info("📌 **Détails pour l'activité FLAP :**")
                    st.write("• **Type de disque sélectionné :** Disque à lamelles abrasives (Flap).")
                    st.warning("🔒 **Protection carter :** SIMPLE CARTER obligatoire.")
                    st.caption("📐 **Angle de travail :** Respect strict d'un angle de **15° à 25°** par rapport au matériau.")

                if st.session_state.form_data["meuleuse_u_blanchiment"]:
                    st.info("📌 **Détails pour l'activité BLANCHIMENT :**")
                    cb1, cb2 = st.columns(2)
                    with cb1:
                        st.session_state.form_data["meuleuse_disque_blanchiment"] = st.selectbox("Sélection du disque de blanchiment :", db_disques_blanchiment)
                    with cb2:
                        st.warning("🔒 **Protection carter :** SIMPLE CARTER obligatoire.")
                        st.caption("📐 **Positionnement :** Application à plat par rapport au matériau.")

                st.divider()

            if st.session_state.form_data["sta_couteau_lame"] or st.session_state.form_data["sta_echelle_escabeau"]:
                has_spe = True
                st.warning("⚠️ **DÉROGATION CASQUE ROUGE (Cutter à Lame Ouverte / Échelle / Escabeau)**")
                st.write("- Validation accordée après inspection terrain et confirmation de l'absence d'alternative technique.")

            if not has_spe:
                st.success("✅ **Aucun permis spécifique supplémentaire ni dérogation requis pour ce chantier.**")

            c_back, c_next = st.columns([1, 1])
            with c_back:
                if st.button("⬅️ Précédent"):
                    st.session_state.step = 5
                    st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"):
                    st.session_state.step = 7
                    st.rerun()

        # =====================================================
        # ÉTAPE 7 : SYNTHÈSE, PDF DIRECT & CO-SIGNATURES TACTILES
        # =====================================================
        elif current_step == 7:
            st.subheader("7. Synthèse Globale, Téléchargement PDF & Co-signatures Tactiles")

            st.markdown("<div class='status-pending'>⚠️ PERMIS EN ATTENTE DE VALIDATION BATCH (07h30)</div>", unsafe_allow_html=True)

            st.write("##### 📊 1. Tableau Récapitulatif : Activités, Risques Identifiés & Moyens de Prévention")
            
            epis_list_txt = []
            if st.session_state.form_data["epi_lunettes_chantier_visiere"]: epis_list_txt.append("Lunettes EN 166")
            if st.session_state.form_data["epi_visiere_idra"]: epis_list_txt.append("Visière IDRA EN 166B")
            if st.session_state.form_data["epi_casque_jugulaire"]: epis_list_txt.append("Casque Jugulaire EN 387")
            if st.session_state.form_data["epi_gants_coupure"]: epis_list_txt.append("Gants Anti-coupure 4543")
            if st.session_state.form_data["epi_gants_chimique"]: epis_list_txt.append("Gants Chimiques EN 374")
            if st.session_state.form_data["epi_bouchons_moules"]: epis_list_txt.append("Bouchons Moulés")
            elif st.session_state.form_data["epi_bouchons_jetables"]: epis_list_txt.append("Bouchons Jetables")
            if st.session_state.form_data["epi_cartouche_abek"]: epis_list_txt.append("Masque Cartouche ABEK EN 14387")
            if st.session_state.form_data["epi_ffp1_ffp2"]: epis_list_txt.append("Masque FFP1/FFP2")

            epis_str_summary = ", ".join(epis_list_txt) if epis_list_txt else "EPIs Obligatoires Chantier P&G"

            tableau_data = []
            if st.session_state.form_data["sta_prod_chimique"]:
                tableau_data.append({"activite": "Utilisation Produits Chimiques", "risque": "Inhalation / Contact FDS", "prevention": f"Produits: {st.session_state.form_data['produits_liste']} - {epis_str_summary}"})
            
            if st.session_state.form_data["sta_meuleuse"]:
                util_meu = []
                if st.session_state.form_data["meuleuse_u_decoupe"]: util_meu.append(f"Découpe ({st.session_state.form_data['meuleuse_mat_decoupe']} - Double carter - Angle 90°)")
                if st.session_state.form_data["meuleuse_u_ebavurage"]: util_meu.append(f"Ébavurage ({st.session_state.form_data['meuleuse_mat_ebavurage']} - Simple carter - Angle 30-40°)")
                if st.session_state.form_data["meuleuse_u_flap"]: util_meu.append("Flap (Simple carter - Angle 15-25°)")
                if st.session_state.form_data["meuleuse_u_blanchiment"]: util_meu.append(f"Blanchiment ({st.session_state.form_data['meuleuse_disque_blanchiment']} - Application à plat)")
                
                details_meu_txt = " + ".join(util_meu) if util_meu else "Meulage standard"
                op_list_str = ", ".join(st.session_state.form_data["meuleuse_operateurs"]) if st.session_state.form_data["meuleuse_operateurs"] else "Opérateurs Habilités PDP"
                
                tableau_data.append({
                    "activite": f"Meuleuse d'angle {st.session_state.form_data['meuleuse_diametre']} ({st.session_state.form_data['meuleuse_marque']})",
                    "risque": "Projections d'étincelles / Éclatement de disque",
                    "prevention": f"Opérateurs habilités : {op_list_str} | Utilisation : {details_meu_txt} | Position : {st.session_state.form_data['meu_position_op']} | Protection faciale + Gants anti-coupures + Protection auditive"
                })

            if st.session_state.form_data["p_confine"]:
                tableau_data.append({"activite": "Espace Confiné (CBA 105)", "risque": "Asphyxie / Anoxie (Azote)", "prevention": f"O2 ({st.session_state.form_data['confine_o2']}) + Vigie ({st.session_state.form_data['confine_vigie']})"})
            if st.session_state.form_data["p_points_chauds"] or st.session_state.form_data["r_feu_flamme"]:
                tableau_data.append({"activite": "Points Chauds / Soudure", "risque": "Incendie / Brûlures", "prevention": f"{st.session_state.form_data['chaud_extincteur']} + {st.session_state.form_data['chaud_ronde_post']}"})
            if st.session_state.form_data["p_hauteur"] or st.session_state.form_data["sta_echelle_escabeau"]:
                tableau_data.append({"activite": "Travail en Hauteur / Échelle", "risque": "Chute de hauteur / Chute d'objets", "prevention": f"{st.session_state.form_data['hauteur_ancrage']} + {st.session_state.form_data['hauteur_harnais']} + Casque Jugulaire"})

            if not tableau_data:
                tableau_data.append({"activite": "Travaux Généraux du PDP", "risque": "Risques standards de chantier", "prevention": epis_str_summary})

            st.table(tableau_data)

            st.divider()

            st.write("##### 🦺 2. Cartes Visuelles des Permis Spécifiques & Rappels des Consignes")
            c_card1, c_card2 = st.columns(2)
            with c_card1:
                spe_list = []
                if st.session_state.form_data["p_points_chauds"]: spe_list.append("Permis Point Chaud")
                if st.session_state.form_data["p_confine"]: spe_list.append("Permis Espace Confiné")
                if st.session_state.form_data["p_hauteur"]: spe_list.append("Permis Travail en Hauteur")
                if st.session_state.form_data["p_consignation_pression"]: spe_list.append("Permis Consignation LOTO")
                if st.session_state.form_data["p_excavation"]: spe_list.append("Permis Excavation")
                if st.session_state.form_data["p_grutage"]: spe_list.append("Permis Grutage")

                if spe_list:
                    for s in spe_list:
                        st.info(f"**{s}** — Données spécifiques renseignées et consignes actives.")
                else:
                    st.success("✅ Aucun permis spécifique requis.")

            with c_card2:
                derog_list = []
                if st.session_state.form_data["sta_meuleuse"]: derog_list.append("Dérogation Meuleuse d'angle")
                if st.session_state.form_data["sta_couteau_lame"]: derog_list.append("Dérogation Cutter Lame Ouverte")
                if st.session_state.form_data["sta_echelle_escabeau"]: derog_list.append("Dérogation Échelle / Escabeau")

                if derog_list:
                    for d in derog_list:
                        st.warning(f"**{d}** — Dérogation enregistrée sous contrôle du Responsable N2 et Casque Rouge.")
                else:
                    st.success("✅ Aucune dérogation particulière.")

            st.divider()

            st.write("##### ✍️ 3. Co-signatures Tactiles de l'Équipe")
            c_add1, c_add2 = st.columns([3, 1])
            with c_add1:
                nouveau_nom = st.text_input("Ajouter un compagnon à la liste des signataires :", key="new_compagnon")
            with c_add2:
                st.write("")
                st.write("")
                if st.button("+ Ajouter Signataire"):
                    if nouveau_nom and nouveau_nom not in st.session_state.form_data["intervenants"]:
                        st.session_state.form_data["intervenants"].append(nouveau_nom)
                        st.rerun()

            for idx, nom in enumerate(st.session_state.form_data["intervenants"]):
                role_label = "RESPONSABLE N2" if idx == 0 else f"INTERVENANT {idx+1}"
                st.write(f"✍️ **Signature {role_label} : {nom}**")
                st.info(f" [ Signature Tactile Horodatée : {nom} ] ")

            st.divider()

            permis_temp = {
                "id": f"PT-2026-0928-0{len(st.session_state.permis_db)+1}",
                "date_travaux": st.session_state.form_data["date_str"],
                "societe": st.session_state.form_data["societe"],
                "pdp": st.session_state.form_data["pdp"],
                "mop": st.session_state.form_data["mop"],
                "n2": st.session_state.form_data["n2_nom"],
                "zone": st.session_state.form_data["lieu_pdp"],
                "emplacement": st.session_state.form_data["lieu_precision"],
                "pr": "PR-2 (Parking Ouest)",
                "confinement": "ZC-01 (Hall M1)",
                "urg": "03.22.54.30.00",
                "statut": "EN_ATTENTE_BATCH",
                "heure": datetime.datetime.now().strftime("%H:%M"),
                "intervenants": list(st.session_state.form_data["intervenants"]),
                "derogations": derog_list,
                "permis_specifiques": spe_list,
                "tableau_risques": tableau_data
            }

            pdf_bytes = generer_pdf_bytes(permis_temp)

            c_back, c_sub, c_pdf = st.columns([1, 2, 2])
            with c_back:
                if st.button("⬅️ Précédent"):
                    st.session_state.step = 6
                    st.rerun()

            with c_pdf:
                st.download_button(
                    label="📄 TÉLÉCHARGER LE PERMIS PDF (PRÉ-VALIDATION)",
                    data=pdf_bytes,
                    file_name=f"Permis_P_and_G_{permis_temp['id']}_EnAttente.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            with c_sub:
                if st.button(f"🚀 SOUMETTRE LE PERMIS ({st.session_state.form_data['date_str']})", type="primary", use_container_width=True):
                    carto = db_zones_carto.get(st.session_state.form_data["lieu_pdp"], {})

                    nouveau_pt = {
                        "id": f"PT-2026-0928-0{len(st.session_state.permis_db)+1}",
                        "date_travaux": st.session_state.form_data["date_str"],
                        "societe": st.session_state.form_data["societe"],
                        "pdp": st.session_state.form_data["pdp"],
                        "mop": st.session_state.form_data["mop"],
                        "n2": st.session_state.form_data["n2_nom"],
                        "zone": st.session_state.form_data["lieu_pdp"],
                        "emplacement": st.session_state.form_data["lieu_precision"],
                        "pr": carto.get("pr"),
                        "confinement": carto.get("confinement"),
                        "urg": carto.get("urgence"),
                        "statut": "EN_ATTENTE_BATCH",
                        "heure": datetime.datetime.now().strftime("%H:%M"),
                        "intervenants": list(st.session_state.form_data["intervenants"]),
                        "derogations": derog_list,
                        "permis_specifiques": spe_list,
                        "tableau_risques": tableau_data
                    }

                    st.session_state.permis_db.append(nouveau_pt)
                    st.balloons()
                    st.success(f"Permis {nouveau_pt['id']} créé avec succès ! Transmis au DO P&G pour le batch de 07h30.")
                    st.session_state.kiosk_mode = "HOME"

# ==============================================================================
# INTERFACE 2 : DDS BOARD & BATCH 07H30 (DO / HSE)
# ==============================================================================
elif role == "📊 DDS Board & Batch 07h30 (DO / HSE)":
    st.markdown("""
    <div class="pg-header" style='background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);'>
        <h2 style='margin:0;'>DDS BOARD & TABLEAU DE BORD DONNEUR D'ORDRE (DO)</h2>
        <p style='margin:0; opacity:0.8;'>Supervision Temps Réel & Validation Automatisée de la Fournée du Matin</p>
    </div>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    tot = len(st.session_state.permis_db)
    att = sum(1 for p in st.session_state.permis_db if p["statut"] == "EN_ATTENTE_BATCH")
    val = sum(1 for p in st.session_state.permis_db if p["statut"] == "VALIDÉ")
    der = sum(1 for p in st.session_state.permis_db if len(p.get("derogations", [])) > 0)

    k1.metric("Chantiers Totaux", tot)
    k2.metric("En Attente Batch (07h30)", att)
    k3.metric("Permis Validés Actifs", val)
    k4.metric("Dérogations Actives", der)

    st.divider()

    st.subheader("⚡ Validation Globale du Batch de 07h30")
    c_txt, c_btn = st.columns([3, 1])
    with c_txt:
        st.write("Le traitement serveur exécute la fournée quotidienne à 07h30. Cliquez sur le bouton ci-contre pour valider l'ensemble des permis du secteur : l'encart passe au vert 'PERMIS VALIDÉ' et le PDF est régénéré avec le statut officiel.")
    with c_btn:
        if st.button("✅ VALIDER LE BATCH (07h30)", type="primary", use_container_width=True):
            for p in st.session_state.permis_db:
                p["statut"] = "VALIDÉ"
            st.success("Fournée de 07h30 validée avec succès ! PDFs mis à jour avec l'encart vert 'PERMIS VALIDÉ'.")

    st.subheader("📋 Liste des Permis Émis & Téléchargement des PDFs Officiels")
    
    for pt in st.session_state.permis_db:
        with st.expander(f"Permis Ref: {pt['id']} — {pt['societe']} ({pt['date_travaux']}) — Statut: {pt['statut']}"):
            if pt['statut'] == 'VALIDÉ':
                st.markdown("<div class='status-validated'>✅ PERMIS VALIDÉ PAR LE DONNEUR D'ORDRE</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='status-pending'>⚠️ PERMIS EN ATTENTE DE VALIDATION BATCH (07h30)</div>", unsafe_allow_html=True)

            st.write(f"**Responsable N2 :** {pt['n2']} | **Zone :** {pt['zone']}")
            st.write(f"**Intervenants :** {', '.join(pt.get('intervenants', []))}")
            st.write(f"**Permis Spécifiques / Dérogations :** {', '.join(pt.get('permis_specifiques', []) + pt.get('derogations', [])) if (pt.get('permis_specifiques') or pt.get('derogations')) else 'Aucun'}")

            pdf_valid_bytes = generer_pdf_bytes(pt)
            st.download_button(
                label=f"📄 Télécharger le Permis PDF Officiel ({pt['id']})",
                data=pdf_valid_bytes,
                file_name=f"Permis_P_and_G_{pt['id']}_{pt['statut']}.pdf",
                mime="application/pdf",
                key=f"btn_pdf_{pt['id']}"
            )

# ==============================================================================
# INTERFACE 3 : INSPECTION TERRAIN QR CODE (CASQUE ROUGE)
# ==============================================================================
else:
    st.markdown("""
    <div class="pg-header" style='background: linear-gradient(135deg, #b91c1c 0%, #7f1d1d 100%);'>
        <h2 style='margin:0;'>AUDIT TERRAIN & SCAN QR CODE — CASQUE ROUGE</h2>
        <p style='margin:0; opacity:0.8;'>Contrôle de Conformité Instantané sur Zone de Chantier</p>
    </div>
    """, unsafe_allow_html=True)

    c_sc1, c_sc2 = st.columns([1, 2])
    with c_sc1:
        st.subheader("📱 Contrôle Smartphone")
        pt_sel = st.selectbox("Permis à contrôler sur zone :", [p["id"] for p in st.session_state.permis_db])
        if st.button("🔍 Simuler Scan QR Code", type="primary", use_container_width=True):
            st.session_state.scanned_item = next(p for p in st.session_state.permis_db if p["id"] == pt_sel)

    with c_sc2:
        st.subheader("📄 Document Officiel Numérisé")
        if "scanned_item" in st.session_state:
            p = st.session_state.scanned_item
            
            if p['statut'] == 'VALIDÉ':
                st.markdown("<div class='status-validated'>✅ PERMIS VALIDÉ PAR LE DONNEUR D'ORDRE</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='status-pending'>⚠️ PERMIS EN ATTENTE DE VALIDATION BATCH (07h30)</div>", unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background: white; border: 2px solid #003366; padding: 20px; border-radius: 8px;">
                <h3 style="color:#003366; margin:0;">PERMIS DE TRAVAIL GÉNÉRAL (STA) — P&G AMIENS</h3>
                <hr>
                <p><b>Réf :</b> {p['id']} | <b>Date Intervention :</b> {p.get('date_travaux', 'Aujourd\'hui')} | <b>Horodatage :</b> {p['heure']}</p>
                <p><b>Entreprise :</b> {p['societe']} | <b>PDP :</b> {p['pdp']} | <b>MoP :</b> {p.get('mop', 'MoP Standard')}</p>
                <p><b>Responsable N2 :</b> {p['n2']}</p>
                <p><b>Emplacement :</b> {p['zone']} ({p.get('emplacement', '1er étage')})</p>
                <p><b>Point de Rassemblement :</b> {p.get('pr')} | <b>Confinement :</b> {p.get('confinement')}</p>
                <p><b>Poste d'Urgence Secteur :</b> {p.get('urg')}</p>
                <p><b>Intervenants Signataires :</b> {', '.join(p.get('intervenants', []))}</p>
                <p><b>Permis Spécifiques / Dérogations :</b> {', '.join(p.get('permis_specifiques', []) + p.get('derogations', [])) if (p.get('permis_specifiques') or p.get('derogations')) else 'Aucun'}</p>
                <hr>
                <p style="text-align:center; color:#003366; font-weight:bold; margin:0;">
                    ✅ SIGNATURES VECTORIELLES AUDITÉES & HORODATÉES EN BDD
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.write("")
            pdf_audit_bytes = generer_pdf_bytes(p)
            st.download_button(
                label="📄 TÉLÉCHARGER LE PERMIS AUDITÉ EN PDF",
                data=pdf_audit_bytes,
                file_name=f"Permis_P_and_G_{p['id']}_{p['statut']}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.info("Cliquez sur 'Simuler Scan QR Code' pour afficher la fiche numérisée.")
