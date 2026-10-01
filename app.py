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

# Style CSS P&G
st.markdown("""
<style>
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
    .weather-card {
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
        border: 1px solid #0284c7; padding: 12px 18px; border-radius: 10px;
        margin-bottom: 20px; color: #0369a1;
    }
    .urgence-card {
        background-color: #fef2f2; border: 2px solid #ef4444; color: #991b1b;
        padding: 18px; border-radius: 10px; margin-bottom: 20px;
    }
    .status-pending {
        background-color: #fef08a; color: #854d0e; border: 2px solid #eab308;
        padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 1.1rem;
        margin-bottom: 15px;
    }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    div[data-baseweb="input"] { background-color: #e0f2fe !important; border: 1.5px solid #0284c7 !important; border-radius: 8px !important; }
    div[data-baseweb="select"] > div { background-color: #e0f2fe !important; border: 1.5px solid #0284c7 !important; border-radius: 8px !important; }
    .stepper-container { background: white; border: 1px solid #cbd5e1; border-radius: 12px; padding: 24px 20px 18px 20px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.03); }
    .stepper-wrapper { position: relative; display: flex; justify-content: space-between; align-items: flex-start; }
    .progress-track { position: absolute; top: 13px; left: 5%; right: 5%; height: 4px; background-color: #e2e8f0; z-index: 1; }
    .progress-fill { height: 100%; background-color: #10b981; transition: width 0.4s ease-in-out; }
    .step-item { display: flex; flex-direction: column; align-items: center; flex: 1; font-size: 0.8rem; font-weight: 600; color: #64748b; text-align: center; z-index: 2; }
    .step-badge { width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: bold; margin-bottom: 8px; background-color: white; border: 3px solid #cbd5e1; color: #64748b; transition: all 0.3s ease; }
    .step-completed .step-badge { background-color: #10b981; border-color: #10b981; color: white; }
    .step-completed { color: #059669; }
    .step-active .step-badge { background-color: #003366; border-color: #003366; color: white; box-shadow: 0 0 0 4px rgba(0, 51, 102, 0.2); }
    .step-active { color: #003366; font-weight: bold; }
    .step-upcoming .step-badge { background-color: white; border-color: #cbd5e1; color: #94a3b8; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# MÉTÉO EN DIRECT (OPEN-METEO API)
# ---------------------------------------------------------
@st.cache_data(ttl=1800)
def obtenir_meteo_amiens_live():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=49.8941&longitude=2.2957&daily=temperature_2m_max,temperature_2m_min,windgusts_10m_max,weathercode&timezone=Europe%2FParis"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            return {
                "temp_max_j0": round(data['daily']['temperature_2m_max'][0]),
                "temp_min_j0": round(data['daily']['temperature_2m_min'][0]),
                "vent_j0": round(data['daily']['windgusts_10m_max'][0]),
                "code_w_j0": data['daily']['weathercode'][0],
                "temp_max_j1": round(data['daily']['temperature_2m_max'][1]),
                "vent_j1": round(data['daily']['windgusts_10m_max'][1]),
                "source": "Open-Meteo Live API"
            }
    except Exception:
        return {"temp_max_j0": 18, "temp_min_j0": 8, "vent_j0": 14, "code_w_j0": 0, "temp_max_j1": 19, "vent_j1": 12, "source": "Mode Secours"}

# ---------------------------------------------------------
# RÉFÉRENTIELS & BDD P&G
# ---------------------------------------------------------
db_societes = ["ABYLSEN", "APAVE", "AXIMA", "ENGIE", "EULER", "SOUS-TRAITANCE-EXPERT"]

db_pdps = {
    "ABYLSEN": ["PDP-2026-042 (Bâtiment M1 - Rénovation)"],
    "APAVE": ["PDP-2026-104 (Inspection Pression Tuyauterie)"],
    "AXIMA": ["PDP-2026-015 (HVAC Zone Production M1)"],
    "ENGIE": ["PDP-2026-067 (Chaufferie Vapeur Nord)"],
    "EULER": ["PDP-2026-090 (Génie Civil & Terrassement TP)"],
    "SOUS-TRAITANCE-EXPERT": ["PDP-2026-042 (Sous-traitant rattaché à ABYLSEN)"]
}

db_mops = {
    "PDP-2026-042 (Bâtiment M1 - Rénovation)": [{"titre": "MoP-01: Peinture & Finitions", "st": False}],
    "PDP-2026-042 (Sous-traitant rattaché à ABYLSEN)": [{"titre": "MoP-02-ST: Électromécanique Spécialisée", "st": True, "titulaire": "ABYLSEN"}],
    "PDP-2026-104 (Inspection Pression Tuyauterie)": [{"titre": "MoP-01: Épreuve Hydraulique Tuyauterie", "st": False}],
    "PDP-2026-015 (HVAC Zone Production M1)": [{"titre": "MoP-01: Nettoyage Filtres CTA", "st": False}],
    "PDP-2026-067 (Chaufferie Vapeur Nord)": [{"titre": "MoP-01: Isoler Purgeur Vapeur", "st": False}],
    "PDP-2026-090 (Génie Civil & Terrassement TP)": [{"titre": "MoP-01: Fouille Terrassement TP", "st": False}]
}

db_n2 = ["Léa DUSEK", "Matthieu MARTIN", "Alexandre LEFEBVRE", "Cindy BERNARD"]

db_zones_carto = {
    "Bâtiment M1 - Zone Production": {"pr": "PR-2 (Parking Ouest)", "confinement": "ZC-01 (Hall M1)", "sprinkler": True, "detection": True},
    "Bâtiment M1 - Bureaux / Toiture": {"pr": "PR-2 (Parking Ouest)", "confinement": "ZC-01 (Hall M1)", "sprinkler": False, "detection": True},
    "Bâtiment M2 - Conditionnement": {"pr": "PR-4 (Zone Nord)", "confinement": "ZC-03 (Atrium M2)", "sprinkler": True, "detection": True},
    "Zone Extérieure / Logistique / TP": {"pr": "PR-1 (Entrée Principale)", "confinement": "ZC-00 (Poste Central)", "sprinkler": False, "detection": False}
}

etapes_noms = ["Date & EE", "PDP & MoP", "Responsable N2", "Zone & Urgences", "Check-list & EPIs", "Permis Spécifiques (HRT)", "Synthèse & Signatures"]

if "permis_db" not in st.session_state:
    st.session_state.permis_db = []

if "kiosk_mode" not in st.session_state:
    st.session_state.kiosk_mode = "HOME"
if "step" not in st.session_state:
    st.session_state.step = 1

# INITIALISATION EXHAUSTIVE FORM_DATA
if "form_data" not in st.session_state:
    st.session_state.form_data = {
        "date_str": datetime.date.today().strftime("%d/%m/%Y"),
        "societe": "ABYLSEN",
        "pdp": "PDP-2026-042 (Bâtiment M1 - Rénovation)",
        "mop": "MoP-01: Peinture & Finitions",
        "is_subcontractor": False,
        "titulaire_n2": "",
        "n2_nom": "Léa DUSEK",
        "lieu_pdp": "Bâtiment M1 - Bureaux / Toiture",
        "lieu_precision": "1er étage, Bureau 104",
        "description": "Maintenance et travaux sur site",
        "intervenants": ["Léa DUSEK", "Matthieu MARTIN"],
        
        # PERMIS SPÉCIFIQUES DÉCLENCHEURS (ÉTAPE 5)
        "p_hauteur": False, "p_toiture": False, "p_points_chauds": False, "p_excavation": False,
        "p_grutage": False, "p_confine": False, "p_electrique": False, "p_consignation": False, "p_systeme_risque": False,

        # CONDITIONNEL DEMOLITION & DTA (ÉTAPE 5)
        "act_demolition": False,
        "dta_consultation": False,

        # EPIs DE BASE & RAJOUTS AUTOMATIQUES
        "epi_casque_jugulaire_obli": False,

        # 1. HAUTEUR / NACELLE / ÉCHAFAUDAGE
        "h_pirl": False, "h_pirl_vgp": True, "h_pirl_soc": "ABYLSEN",
        "h_nacelle": False, "h_nacelle_vgp": True, "h_nacelle_checklist": True, "h_nacelle_caces": True, "h_nacelle_aut": True, "h_nacelle_harnais": True, "h_nacelle_soc": "ABYLSEN",
        "h_echaf": False,
        "h_echaf_montage": False, "h_echaf_montage_qualif": True, "h_echaf_montage_harnais": True,
        "h_echaf_util": False, "h_echaf_util_qualif": True,
        "h_echaf_ctrl_regle": True, "h_echaf_certif_affiche": True, "h_echaf_verif_j": True, "h_echaf_soc_util": "ABYLSEN",

        # 2. ACCÈS TOITURE
        "toiture_protection": "Garde-corps",
        "toiture_valideur": "Matthieu MARTIN (Habilité ePDP Accès Toiture)",

        # 3. POINT CHAUD
        "chaud_gants_soudeur": False, "chaud_gants_chaleur": False, "chaud_gants_anticoupure": True,
        "chaud_extincteur1": "Eau + additifs", "chaud_extincteur2": "CO2",
        "chaud_degage_10m": True, "chaud_baches": False,
        "chaud_traverse_mur": False, "chaud_vigie_opposee": False,
        "chaud_ouverture_10m": False, "chaud_obstruction": False, "chaud_vigie_autre_cote": False,
        "chaud_vigie_nom": "Matthieu MARTIN",
        "chaud_personne_surv_60m": "Léa DUSEK",
        "chaud_heure_fin": "15:00", "chaud_heure_depart": "16:00", "chaud_commentaires": "",

        # 4. EXCAVATION / TRANCHÉE
        "excav_plans_eaux_indus": True, "excav_plans_eaux_usees": True, "excav_plans_eaux_pluv": True, "excav_plans_eaux_incendie": True,
        "excav_plans_ht": True, "excav_plans_bt": True, "excav_plans_gaz": True,
        "excav_struct_proximite": False, "excav_architecte": False, "excav_dict": True,
        "excav_effondrement": False, "excav_eau_pompe": False, "excav_balisage": True, "excav_vehicule_3m": True, "excav_deblais": True,
        "excav_acces": "Escalier / Rampe",
        "excav_profondeur_130": False, "excav_blindage": False,
        "excav_schema_commentaires": "",
        "excav_chef_manoeuvre": "Léa DUSEK", "excav_do": "Matthieu MARTIN", "excav_casque_rouge": "Alexandre LEFEBVRE",

        # 5. GRUTAGE
        "grut_desc_mop": "Levage groupe froid rooftop",
        "grut_poids_charge": 2500.0, "grut_poids_acc": 200.0, "grut_unite": "kg",
        "grut_immat": "GRUE-AMIENS-88", "grut_fleche": 35.0, "grut_portee": 20.0, "grut_pression_patin": "12 T/m²", "grut_rayon": 15.0,
        "grut_balisage": True, "grut_plan_vue": True, "grut_plan_elev": True, "grut_obstacles": True,
        "grut_anemometre": True, "grut_vent_val": 18.0, "grut_vent_unite": "km/h",
        "grut_pesage": True, "grut_centre_gravite": True, "grut_angles_elingue": True, "grut_plaques_rep": True,
        "grut_chef_m_nom": "Léa DUSEK", "grut_chef_m_soc": "ABYLSEN",
        "grut_elingueur_nom": "Matthieu MARTIN", "grut_elingueur_soc": "ABYLSEN",
        "grut_grutier_nom": "Jean LEVAGE", "grut_grutier_soc": "APAVE",
        "grut_certif_grue": True, "grut_certif_acc": True, "grut_certif_plaques": True, "grut_check_j_grue": True, "grut_check_j_acc": True,
        "grut_pattes_concu": True, "grut_pattes_defaut": False, "grut_pattes_adequation": True, "grut_charges_annexes": True,
        "grut_schema_commentaires": "",
        "grut_do_sign": "Matthieu MARTIN", "grut_casque_rouge_sign": "Alexandre LEFEBVRE",

        # 6. ESPACE CONFINÉ
        "conf_lieu": "Cuve C-102 Ligne 3",
        "conf_r_atmo": True, "conf_r_chimique": False, "conf_r_inflam": False, "conf_r_orga": False,
        "conf_r_meca": False, "conf_r_thermiq": False, "conf_r_bruit": False, "conf_troudhomme_610": True,
        "conf_catec": True, "conf_hauteur": False, "conf_m20": True,
        "conf_secouriste": "Attribution automatique suivant la localisation", "conf_medical": "Attribution automatique suivant la localisation",
        "conf_action_chaud": False, "conf_ventilation_nat": True, "conf_ventilation_forcee": True, "conf_ventilation_debit": "Minimum 56m3/h par personne",
        "conf_consignation_gaz": True, "conf_cuve_vide": True, "conf_vol_caches": False, "conf_eclairage_24v": True, "conf_blocage_ouvert": True,
        "conf_echaf_echelle": False, "conf_prod_chim": False, "conf_laser": False, "conf_comm_type": "Talkie Walkie",
        "conf_o2": 20.9, "conf_o2_contre_mesure": 20.9,
        "conf_h2s_check": False, "conf_h2s": 0.0,
        "conf_co_check": False, "conf_co": 0.0,
        "conf_explo_check": False, "conf_explo": 0.0,
        "conf_temp_cuve": 22.0, "conf_verif_temp": "N2", "conf_inflam_lel": 0.0, "conf_verif_lel": "N2",
        "conf_schema_commentaires": "",
        "conf_entrant": "Léa DUSEK", "conf_standby": "Matthieu MARTIN", "conf_do": "Alexandre LEFEBVRE",

        # 7. TRAVAIL ÉLECTRIQUE
        "elec_modife": False, "elec_armoire": True, "elec_voisinage_tension": True, "elec_courant_faible": False,
        "elec_releve": True, "elec_chemins": False, "elec_voisinage_nues": False, "elec_valideur_ei": "E&I / PT E&I (B2, H2, BC, HC)",

        # 8. CONSIGNATION LOTO (3 PHASES)
        "loto_ouverture_methode": "2 vannes et vanne de drain", "loto_ouvert_loc1": "Vanne V-101 Amont", "loto_ouvert_loc2": "Vanne V-102 Aval / Drain D-01",
        "loto_is_elec": True, "loto_is_elec_loc1": "TGBT-M1-Armoire 4", "loto_is_elec_loc2": "Cadenas LOTO #884",
        "loto_fusible": False, "loto_fusible_loc1": "", "loto_fusible_loc2": "",
        "loto_cable": False, "loto_cable_loc1": "", "loto_cable_loc2": "",
        "loto_pneu": False, "loto_pneu_loc1": "", "loto_pneu_loc2": "",
        "loto_hydra": False, "loto_hydra_loc1": "", "loto_hydra_loc2": "",
        "loto_residu": True, "loto_residu_loc1": "Purge pression résiduelle", "loto_residu_loc2": "Manomètre à 0 bar",
        "loto_drain_ouvert": True, "loto_eq_ouvert": True, "loto_eq_lave": True, "loto_eq_sanitise": True,

        # 9. SYSTÈME À RISQUES / ATEX / CHIMIQUE
        "sr_chimique_c1": False, "sr_chimique_nom": "", "sr_fluide_dang": False, "sr_fluide_nom": "", "sr_atex": False, "sr_atex_nom": "",
        "sr_balisage": True, "sr_douche_rince": True, "sr_ramonage": False, "sr_ramonage_dt": "01/10/2026 08:00",
        "sr_isolement": True, "sr_feuille_loto": True, "sr_zonage_atex": True,
        "sr_epi_ecran": True, "sr_epi_lunettes": False, "sr_epi_gants_chim": True, "sr_epi_comb1": False, "sr_epi_comb2": True,
        "sr_epi_bottes": True, "sr_epi_cartouche": True, "sr_epi_ari": False, "sr_epi_3m6000": False, "sr_epi_versaflo": False, "sr_epi_no_versaflo": True,
        "sr_auxiliaire_equipe": True, "sr_comm_moyen": "Talkie-Walkie ATEX",
        "sr_inspect_remise": True, "sr_inspect_nom": "Léa DUSEK", "sr_inspect_dt": "01/10/2026 17:00",
        "sr_schema_commentaires": "",
        "sr_sign_intervenant": "Léa DUSEK", "sr_sign_do": "Matthieu MARTIN", "sr_sign_operations": "Alexandre LEFEBVRE"
    }

def sanitize_text(text):
    if not isinstance(text, str): text = str(text)
    text = text.replace("🔥", "[Pt Chaud]").replace("🦺", "[Confiné]").replace("🧗", "[Hauteur]").replace("⚡", "[LOTO]").replace("⚠️", "[!]").replace("✅", "[OK]").replace("🚜", "[Excavation]")
    normalized = unicodedata.normalize('NFKD', text)
    cleaned = ''.join(c for c in normalized if not unicodedata.combining(c))
    return cleaned.encode('latin-1', 'ignore').decode('latin-1')

def generer_pdf_bytes(permis):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_fill_color(0, 51, 102); pdf.rect(10, 10, 190, 22, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("Helvetica", "B", 14)
    pdf.text(15, 20, sanitize_text("PROCTER & GAMBLE AMIENS - e-Work Permit System"))
    pdf.set_font("Helvetica", "", 10)
    pdf.text(15, 27, sanitize_text(f"Ref: {permis['id']} | Date: {permis['date_travaux']} | Heure: {permis['heure']}"))
    pdf.set_y(38)

    pdf.set_fill_color(220, 252, 231); pdf.set_draw_color(34, 197, 94); pdf.set_text_color(22, 101, 52)
    pdf.rect(10, 38, 190, 10, 'DF')
    pdf.set_font("Helvetica", "B", 11)
    pdf.text(15, 44.5, sanitize_text("PERMIS VALIDE & AUDITABLE SUR COMPTE ePDP"))
    pdf.set_text_color(0, 0, 0); pdf.set_y(54)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, sanitize_text("1. INFORMATIONS GENERALES & SOUS-TRAITANCE"), 0, 1)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, sanitize_text(f"Societe: {permis['societe']} | PDP: {permis['pdp']} | MoP: {permis['mop']}"), 0, 1)
    if permis.get("is_subcontractor"):
        pdf.cell(0, 5, sanitize_text(f"[SOUS-TRAITANCE DETECTEE] N2 Titulaire Valideur: {permis.get('titulaire_n2')}"), 0, 1)
    pdf.cell(0, 5, sanitize_text(f"Responsable N2: {permis['n2']} | Lieu: {permis['zone']} ({permis.get('emplacement', '')})"), 0, 1)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, sanitize_text("2. SYNTHESE COMPLÈTE DES RISQUES ET PERMIS SPECIFIQUES"), 0, 1)
    pdf.set_font("Helvetica", "B", 8); pdf.set_fill_color(241, 245, 249)
    pdf.cell(60, 6, sanitize_text("Activite Cochee"), 1, 0, 'L', True)
    pdf.cell(65, 6, sanitize_text("Risque Identifie"), 1, 0, 'L', True)
    pdf.cell(65, 6, sanitize_text("Moyens de Prevention / EPIs / Signatures"), 1, 1, 'L', True)

    pdf.set_font("Helvetica", "", 8)
    for r in permis.get("tableau_risques", []):
        pdf.cell(60, 6, sanitize_text(str(r.get("activite", "")))[:32], 1, 0)
        pdf.cell(65, 6, sanitize_text(str(r.get("risque", "")))[:36], 1, 0)
        pdf.cell(65, 6, sanitize_text(str(r.get("prevention", "")))[:36], 1, 1)

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, sanitize_text("3. SIGNATURES AUDITEES DANS ePDP"), 0, 1)
    pdf.set_font("Helvetica", "", 8)
    for sign in permis.get("intervenants", []):
        pdf.cell(0, 5, sanitize_text(f" [OK] Signature horodatee intervenant : {sign}"), 1, 1)

    return bytes(pdf.output())

# BARRE LATÉRALE
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Procter_%26_Gamble_logo.svg/1024px-Procter_%26_Gamble_logo.svg.png", width=80)
st.sidebar.title("e-Work Permit P&G")
st.sidebar.caption("Site d'Amiens — Solution Unifiée")

role = st.sidebar.radio("Interface à démontrer :", ["🖥️ Borne Kiosk Tactile (EE / N2)", "📊 DDS Board & Batch 07h30 (DO / HSE)", "📱 Inspection Terrain QR Code (Casque Rouge)"])

# ==============================================================================
# INTERFACE 1 : BORNE KIOSK TACTILE (EE / N2)
# ==============================================================================
if role == "🖥️ Borne Kiosk Tactile (EE / N2)":

    st.markdown("<div class='pg-header'><h1 style='margin:0;'>PROCTER & GAMBLE — AMIENS</h1><p style='margin:0;'>WORK PERMIT IT | BORNE TACTILE KIOSK</p></div>", unsafe_allow_html=True)

    if st.session_state.kiosk_mode == "HOME":
        st.write("### Veuillez sélectionner votre démarche :")
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            st.markdown("<div class='welcome-card'><h2 style='color:#003366;'>🚀 Permis de Travail</h2><p>Émettre un nouveau Permis de Travail complet.</p></div>", unsafe_allow_html=True)
            if st.button("🚀 COMMENCER UN PERMIS DE TRAVAIL", type="primary", use_container_width=True):
                st.session_state.kiosk_mode = "PERMIS"; st.session_state.step = 1; st.rerun()
        with col_act2:
            st.markdown("<div class='welcome-card'><h2 style='color:#003366;'>📝 Émargement PDP</h2><p>Émarger un Plan de Prévention.</p></div>", unsafe_allow_html=True)
            if st.button("📝 SIGNER UN PLAN DE PRÉVENTION (PDP)", use_container_width=True):
                st.session_state.kiosk_mode = "PDP"; st.rerun()

    elif st.session_state.kiosk_mode == "PERMIS":
        current_step = st.session_state.step
        total_steps = len(etapes_noms)
        progress_pct = int(((current_step - 1) / (total_steps - 1)) * 100)

        steps_items_html = ""
        for idx, name in enumerate(etapes_noms, 1):
            if idx < current_step: steps_items_html += f'<div class="step-item step-completed"><div class="step-badge">✓</div><span>{name}</span></div>'
            elif idx == current_step: steps_items_html += f'<div class="step-item step-active"><div class="step-badge">{idx}</div><span>{name}</span></div>'
            else: steps_items_html += f'<div class="step-item step-upcoming"><div class="step-badge">{idx}</div><span>{name}</span></div>'

        st.markdown(f'<div class="stepper-container"><div class="stepper-wrapper"><div class="progress-track"><div class="progress-fill" style="width: {progress_pct}%;"></div></div>{steps_items_html}</div></div>', unsafe_allow_html=True)

        if current_step == 1:
            st.subheader("1. Date d'Intervention & Entreprise Extérieure")
            c1, c2 = st.columns(2)
            today_date = datetime.date.today(); tomorrow_date = today_date + datetime.timedelta(days=1)
            with c1:
                date_choice = st.radio("Date de planification du permis :", [f"Aujourd'hui : {today_date.strftime('%d/%m/%Y')}", f"Pour demain : {tomorrow_date.strftime('%d/%m/%Y')}"])
                st.session_state.form_data["date_str"] = tomorrow_date.strftime("%d/%m/%Y") if "demain" in date_choice else today_date.strftime("%d/%m/%Y")
            with c2:
                st.session_state.form_data["societe"] = st.selectbox("Entreprise Extérieure (EE) :", db_societes)

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button("⬅️ Accueil"): st.session_state.kiosk_mode = "HOME"; st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"): st.session_state.step = 2; st.rerun()

        elif current_step == 2:
            st.subheader("2. Plan de Prévention, Mode Opératoire & Règle de Sous-Traitance")
            p_list = db_pdps.get(st.session_state.form_data["societe"], ["PDP Standard"])
            st.session_state.form_data["pdp"] = st.selectbox("Plan de Prévention (PDP) rattaché :", p_list)
            
            m_obj_list = db_mops.get(st.session_state.form_data["pdp"], [{"titre": "MoP Standard", "st": False}])
            m_titles = [m["titre"] for m in m_obj_list]
            selected_mop_title = st.selectbox("Mode Opératoire (MoP) :", m_titles)
            st.session_state.form_data["mop"] = selected_mop_title
            
            mop_info = next((m for m in m_obj_list if m["titre"] == selected_mop_title), {"st": False})
            st.session_state.form_data["is_subcontractor"] = mop_info.get("st", False)

            if st.session_state.form_data["is_subcontractor"]:
                st.warning(f"⚠️️ **SOUS-TRAITANCE CONNU GRÂCE AU PDP ET MOP :** L'entreprise sélectionnée est en sous-traitance pour **{mop_info.get('titulaire', 'ABYLSEN')}**.")
                st.session_state.form_data["titulaire_n2"] = st.text_input("Nom & Prénom du N2 de la société principale (qui devra également valider et signer le permis à la fin) :", value=mop_info.get('titulaire', 'ABYLSEN') + " - Représentant N2")
            else:
                st.success("✅ Intervention directe par la société titulaire du PDP.")

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button("⬅️ Précédent"): st.session_state.step = 1; st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"): st.session_state.step = 3; st.rerun()

        elif current_step == 3:
            st.subheader("3. Responsable N2 Présent sur le Chantier")
            st.session_state.form_data["n2_nom"] = st.selectbox("Responsable N2 qualifié sur site :", db_n2)
            c_back, c_next = st.columns(2)
            with c_back:
                if st.button("⬅️ Précédent"): st.session_state.step = 2; st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"): st.session_state.step = 4; st.rerun()

        # ==============================================================================
        # ÉTAPE 4 : LOCALISATION & ENCART SÉCURITÉ URGENCE (POSTE DE GARDE + INFIRMERIE + INCENDIE)
        # ==============================================================================
        elif current_step == 4:
            st.subheader("4. Localisation & NUMÉROS DE TÉLÉPHONE D'URGENCE DU SITE")
            
            # Encart Numéros d'urgence rajouté strictement selon tes consignes
            st.markdown("""
            <div class='urgence-card'>
                📞 <b>NUMÉROS DE TÉLÉPHONE D'URGENCE DU SITE P&G AMIENS :</b><br>
                • <b>Poste de Garde :</b> 03.22.54.32.00<br>
                • <b>Infirmerie :</b> 03.22.54.30.00 ou 06.75.16.05.54<br>
                • <b>Incendie / Environnement :</b> 03.22.54.33.33
            </div>
            """, unsafe_allow_html=True)

            st.session_state.form_data["lieu_pdp"] = st.selectbox("Zone du Chantier :", list(db_zones_carto.keys()))
            st.session_state.form_data["lieu_precision"] = st.text_input("Précision d'emplacement (Local, Bureau, Ligne) :", value=st.session_state.form_data["lieu_precision"])
            st.session_state.form_data["description"] = st.text_input("Description détaillée de la tâche :", value=st.session_state.form_data["description"])

            carto = db_zones_carto.get(st.session_state.form_data["lieu_pdp"], {})
            st.warning(f"📍 **Secours Secteur :** PR: `{carto.get('pr')}` | Confinement: `{carto.get('confinement')}`")

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button("⬅️ Précédent"): st.session_state.step = 3; st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"): st.session_state.step = 5; st.rerun()

        # ==============================================================================
        # ÉTAPE 5 : COCHES ACTIVITÉS, DÉMOLITION/DTA & RAJOUTS SYSTEMATIQUES D'EPIs
        # ==============================================================================
        elif current_step == 5:
            st.subheader("5. Check-list, Permis Spécifiques à Déclencher & EPIs")

            st.error("🚨 **Sélectionnez les activités de votre intervention :**")
            c_rp1, c_rp2 = st.columns(2)
            with c_rp1:
                st.session_state.form_data["p_hauteur"] = st.checkbox("travail en hauteur / échafaudage / nacelle", value=st.session_state.form_data["p_hauteur"])
                st.session_state.form_data["p_toiture"] = st.checkbox("Accès toiture", value=st.session_state.form_data["p_toiture"])
                st.session_state.form_data["p_points_chauds"] = st.checkbox("Génération de point chaud / flamme", value=st.session_state.form_data["p_points_chauds"])
                st.session_state.form_data["p_excavation"] = st.checkbox("tranchée, BTP, Ouverture de sol", value=st.session_state.form_data["p_excavation"])
                st.session_state.form_data["p_grutage"] = st.checkbox("Grutage", value=st.session_state.form_data["p_grutage"])

            with c_rp2:
                st.session_state.form_data["p_confine"] = st.checkbox("Espace confiné", value=st.session_state.form_data["p_confine"])
                st.session_state.form_data["p_electrique"] = st.checkbox("travail électrique", value=st.session_state.form_data["p_electrique"])
                st.session_state.form_data["p_consignation"] = st.checkbox("ouverture circuit sous pression OU machine en mouvement / parties mobiles OU équipement sous pression OU travaux à proximité de laser classe IV", value=st.session_state.form_data["p_consignation"])
                st.session_state.form_data["p_systeme_risque"] = st.checkbox("risque chimique particulier, Zone ATEX, Fluides dangereux", value=st.session_state.form_data["p_systeme_risque"])
                if st.session_state.form_data["p_systeme_risque"]:
                    st.session_state.form_data["p_consignation"] = True

            st.divider()

            # CONDITIONNEL DEMOLITION & DTA
            st.write("##### 🧱 Activités Spécifiques de Structure / Bâtiment :")
            st.session_state.form_data["act_demolition"] = st.checkbox("Démolition", value=st.session_state.form_data["act_demolition"])

            # La question "Consultation DTA" doit être affichée uniquement si la case "Démolition" est cochée.
            if st.session_state.form_data["act_demolition"]:
                st.warning("⚠️ **Condition Activée :** Démolition sélectionnée.")
                st.session_state.form_data["dta_consultation"] = st.checkbox("Consultation DTA (Dossier Technique Amiante) effectuée et validée", value=st.session_state.form_data["dta_consultation"])

            st.divider()
            st.write("##### 🥽 Équipements de Protection Individuelle (EPIs) :")

            # Application stricte de la règle d'EPI à ajouter dans l'étape 5 si coché
            if st.session_state.form_data["p_hauteur"] or st.session_state.form_data["p_toiture"]:
                st.session_state.form_data["epi_casque_jugulaire_obli"] = True
                st.warning("🥽 **EPI rajouté automatiquement dans l'étape 5 :** Casque avec jugulaire obligatoire.")
            else:
                st.session_state.form_data["epi_casque_jugulaire_obli"] = False

            if st.session_state.form_data["p_electrique"]:
                st.info("🥽 **EPIs de base Électrique rajoutés :** Casque d'électricien, Gants isolants électriques (EN 60903) + Surgants cuir + Vêtements 100% coton/ignifugés.")

            if st.session_state.form_data["p_points_chauds"]:
                st.info("🥽 **EPIs de base Point Chaud rajoutés :** Écran facial EN166B ou cagoule de soudure + Gants ignifugés + Vêtements ignifugés.")

            if st.session_state.form_data["p_confine"]:
                st.info("🥽 **EPI Espace Confiné rajouté :** Masque auto-sauveteur (type M20).")

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button("⬅️ Précédent"): st.session_state.step = 4; st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"): st.session_state.step = 6; st.rerun()

        # ==============================================================================
        # ÉTAPE 6 : FORMULAIRES SPÉCIFIQUES (100% CONFORME À TON ARBORESCENCE)
        # ==============================================================================
        elif current_step == 6:
            st.subheader("6. Ouverture des Permis Spécifiques")

            # ---------------------------------------------------------
            # 1. PERMIS TRAVAIL EN HAUTEUR / ÉCHAFAUDAGE / NACELLE
            # ---------------------------------------------------------
            if st.session_state.form_data["p_hauteur"]:
                st.error("🧗 **PERMIS TRAVAIL EN HAUTEUR / ÉCHAFAUDAGE / NACELLE**")
                st.info("🥽 **EPI :** Casque avec jugulaire obligatoire")

                st.write("##### Cases à cocher (entre PIRL / Nacelle / Echafaudage) :")
                st.session_state.form_data["h_pirl"] = st.checkbox("SI PIRL est coché", value=st.session_state.form_data["h_pirl"])
                if st.session_state.form_data["h_pirl"]:
                    cp1, cp2 = st.columns(2)
                    with cp1: st.session_state.form_data["h_pirl_vgp"] = st.checkbox("VGP + contrôle visuel avant utilisation", value=st.session_state.form_data["h_pirl_vgp"])
                    with cp2: st.session_state.form_data["h_pirl_soc"] = st.text_input("Identification par le nom de la société :", value=st.session_state.form_data["h_pirl_soc"])

                st.session_state.form_data["h_nacelle"] = st.checkbox("Si Nacelle est coché", value=st.session_state.form_data["h_nacelle"])
                if st.session_state.form_data["h_nacelle"]:
                    st.warning("🥽 **EPI = Harnais + longe**")
                    cn1, cn2 = st.columns(2)
                    with cn1:
                        st.session_state.form_data["h_nacelle_vgp"] = st.checkbox("VGP + Check list journalière", value=st.session_state.form_data["h_nacelle_vgp"])
                        st.session_state.form_data["h_nacelle_caces"] = st.checkbox("CACES pour utilisateur et vigie", value=st.session_state.form_data["h_nacelle_caces"])
                        st.session_state.form_data["h_nacelle_aut"] = st.checkbox("Autorisation de conduite", value=st.session_state.form_data["h_nacelle_aut"])
                    with cn2:
                        st.session_state.form_data["h_nacelle_harnais"] = st.checkbox("Qualification pour le travail en hauteur (port du harnais)", value=st.session_state.form_data["h_nacelle_harnais"])
                        st.session_state.form_data["h_nacelle_soc"] = st.text_input("Identification par le nom de la société (Nacelle) :", value=st.session_state.form_data["h_nacelle_soc"])

                st.session_state.form_data["h_echaf"] = st.checkbox("Si Echafaudage est coché", value=st.session_state.form_data["h_echaf"])
                if st.session_state.form_data["h_echaf"]:
                    st.write("Cases à cocher pour Échafaudage :")
                    ce1, ce2 = st.columns(2)
                    with ce1:
                        st.session_state.form_data["h_echaf_montage"] = st.checkbox("Montage / Démontage / Modification", value=st.session_state.form_data["h_echaf_montage"])
                        if st.session_state.form_data["h_echaf_montage"]:
                            st.checkbox("Qualification de montage d'échafaudage", value=True)
                            st.checkbox("Qualification pour le travail en hauteur (port du harnais)", value=True)
                            st.error("🥽 **EPI = Harnais + double longe + Connecteurs + absorbeurs ou stop chute + gants**")

                    with ce2:
                        st.session_state.form_data["h_echaf_util"] = st.checkbox("Utilisation", value=st.session_state.form_data["h_echaf_util"])
                        if st.session_state.form_data["h_echaf_util"]:
                            st.checkbox("Qualification d'utilisation et d'inspection d'échafaudage", value=True)

                    st.session_state.form_data["h_echaf_ctrl_regle"] = st.checkbox("Contrôle périodique réglementaire", value=st.session_state.form_data["h_echaf_ctrl_regle"])
                    st.session_state.form_data["h_echaf_certif_affiche"] = st.checkbox("Certificat de montage affiché", value=st.session_state.form_data["h_echaf_certif_affiche"])
                    st.session_state.form_data["h_echaf_verif_j"] = st.checkbox("Vérification journalière par société", value=st.session_state.form_data["h_echaf_verif_j"])
                    st.session_state.form_data["h_echaf_soc_util"] = st.text_input("Identification de la société utilisatrice :", value=st.session_state.form_data["h_echaf_soc_util"])
                st.divider()

            # ---------------------------------------------------------
            # 2. PERMIS ACCÈS TOITURE
            # ---------------------------------------------------------
            if st.session_state.form_data["p_toiture"]:
                st.error("🏢 **PERMIS ACCÈS TOITURE**")
                st.info("🥽 **EPI = Casque avec jugulaire obligatoire**")
                st.info(f"📍 **Encart localisation de la toiture (lieu gardé en mémoire) :** `{st.session_state.form_data['lieu_pdp']}` ({st.session_state.form_data['lieu_precision']})")

                st.session_state.form_data["toiture_protection"] = st.selectbox(
                    "Identifier les moyens de protection de la zone (ex : garde-corps) :",
                    ["Garde-corps", "Ligne de vie / Point d'ancrage", "Pas de protection collective fixe"]
                )
                
                st.warning("🥽 **Adaptation des EPIs en fonction des protections de la zone :** Harnais + système d'arrêt de chute si <3m du bord, signalisation physique des 3m du bord.")

                meteo_live = obtenir_meteo_amiens_live()
                st.write("##### Flag des conditions météos :")
                
                temp_val = meteo_live["temp_max_j0"]
                vent_val = meteo_live["vent_j0"]
                
                refus = False
                reasons = []

                if temp_val < 3 or temp_val > 30:
                    refus = True; reasons.append(f"Température <3° ou >30°C dans la journée de travail ({temp_val}°C)")
                if vent_val > 36:
                    refus = True; reasons.append(f"Vent >36km/h ({vent_val} km/h)")
                
                chk_orage = st.checkbox("Si orage", value=False)
                chk_pluie = st.checkbox("Si pluie battante prévue", value=False)

                if chk_orage: refus = True; reasons.append("Orage")
                if chk_pluie: refus = True; reasons.append("Pluie battante prévue")

                if refus:
                    st.error(f"❌ **ACCÈS REFUSÉ POUR CAUSE DE CONDITIONS MÉTÉOROLOGIQUES :** {', '.join(reasons)}")
                else:
                    if 30 <= vent_val <= 36:
                        st.warning(f"⚠️ **Entre 30 et 36 km/h : vigilance** ({vent_val} km/h)")
                    st.success("✅ **CONDITIONS FAVORABLES**")
                    st.info("📣 **Rappel des conditions :** Accès à deux personnes impérativement - un intervenant ne doit jamais rester seul sur la toiture")
                    st.session_state.form_data["toiture_valideur"] = st.text_input("Validation de l'accès toiture par une personne habilité à signer les accès toiture (Attribution dans le profil ePDP) :", value=st.session_state.form_data["toiture_valideur"])
                st.divider()

            # ---------------------------------------------------------
            # 3. PERMIS POINT CHAUD
            # ---------------------------------------------------------
            if st.session_state.form_data["p_points_chauds"]:
                st.warning("🔥 **PERMIS POINT CHAUD**")
                st.info("🥽 **EPI de base =** Ecran facial contre les projections chaudes (EN166B) ou cagoule si soudures + Vêtement ignifugés")
                
                st.write("##### Possibilité de choisir entre les différents gants (mais au moins 1 obligatoire) :")
                cg1, cg2, cg3 = st.columns(3)
                with cg1: st.session_state.form_data["chaud_gants_soudeur"] = st.checkbox("Gants soudeur", value=st.session_state.form_data["chaud_gants_soudeur"])
                with cg2: st.session_state.form_data["chaud_gants_chaleur"] = st.checkbox("Gants résistant à la chaleur", value=st.session_state.form_data["chaud_gants_chaleur"])
                with cg3: st.session_state.form_data["chaud_gants_anticoupure"] = st.checkbox("Gants anti coupure (suivant l'outil qui génère le point chaud)", value=st.session_state.form_data["chaud_gants_anticoupure"])

                carto = db_zones_carto.get(st.session_state.form_data["lieu_pdp"], {})
                st.write("##### Détection des moyens de lutte contre l'incendie de la zone (Automatique suivant localisation de l'intervention) :")
                st.write(f"- Présence de sprinklers en fonctionnement ? **{'OUI' if carto.get('sprinkler') else 'NON'}**")
                if not carto.get('sprinkler'):
                    st.error("🚨 **si NON :** Surveillance par P&G de 60minutes supplémentaire après la surveillance de l'EE : clôture du permis quand l'heure de surveillance est passée + commentaire")

                st.write(f"- Présence de détection de fumée ? **{'OUI' if carto.get('detection') else 'NON'}**")
                if not carto.get('detection'):
                    st.error("🚨 **si NON :** Surveillance par P&G de 60minutes supplémentaire après la surveillance de l'EE")

                st.write("##### Quels sont les types de vos 2 extincteurs présents sur la zone ?")
                cext1, cext2 = st.columns(2)
                with cext1: st.session_state.form_data["chaud_extincteur1"] = st.selectbox("1er extincteur :", ["Poudre ABC", "Eau + additifs", "CO2"])
                with cext2: st.session_state.form_data["chaud_extincteur2"] = st.selectbox("2ème extincteur :", ["CO2", "Eau + additifs", "Poudre ABC"])

                st.session_state.form_data["chaud_degage_10m"] = st.checkbox("La zone est dégagée de tous matériaux combustibles sur un rayon de 10m", value=st.session_state.form_data["chaud_degage_10m"])
                if not st.session_state.form_data["chaud_degage_10m"]:
                    st.error("🔒 **si NON = installation de bâches ignifugées**")

                st.session_state.form_data["chaud_traverse_mur"] = st.checkbox("Les travaux traversent ils une paroi ou un mur ?", value=st.session_state.form_data["chaud_traverse_mur"])
                if st.session_state.form_data["chaud_traverse_mur"]:
                    st.error("🔒 **si OUI = vigie en place de l'autre côté du mur**")

                st.session_state.form_data["chaud_ouverture_10m"] = st.checkbox("Les travaux se trouvent ils à moins de 10m d'une ouverture ou de planchers ?", value=st.session_state.form_data["chaud_ouverture_10m"])
                if st.session_state.form_data["chaud_ouverture_10m"]:
                    st.write("Si OUI :")
                    st.session_state.form_data["chaud_obstruction"] = st.checkbox("Obstruction des ouvertures", value=True)
                    st.session_state.form_data["chaud_vigie_autre_cote"] = st.checkbox("OU Vigie de l'autre côté", value=False)

                st.write("##### Vigie du point chaud :")
                st.session_state.form_data["chaud_vigie_nom"] = st.selectbox("Désignation d'un intervenant parmi ceux qui ont signé le mode opératoire en vigie du travail :", st.session_state.form_data["intervenants"])
                st.session_state.form_data["chaud_personne_surv_60m"] = st.selectbox("Personne réalisant la surveillance 60minutes après le travail :", st.session_state.form_data["intervenants"])

                chf1, chf2 = st.columns(2)
                with chf1: st.session_state.form_data["chaud_heure_fin"] = st.text_input("Heure de fin des travaux à chaud :", value=st.session_state.form_data["chaud_heure_fin"])
                with chf2: st.session_state.form_data["chaud_heure_depart"] = st.text_input("Heure de départ (clôture du permis quand l'heure de surveillance est passée) :", value=st.session_state.form_data["chaud_heure_depart"])
                st.session_state.form_data["chaud_commentaires"] = st.text_area("Commentaire obligatoire pour clôture :", value=st.session_state.form_data["chaud_commentaires"])
                st.divider()

            # ---------------------------------------------------------
            # 4. PERMIS EXCAVATION / TRANCHÉE / BTP
            # ---------------------------------------------------------
            if st.session_state.form_data["p_excavation"]:
                st.warning("🚜 **PERMIS EXCAVATION**")
                
                st.write("##### Risques liés aux réseaux souterrains — Connaissance des plans (case à cocher 'Oui' ou 'Non') :")
                cx1, cx2, cx3, cx4 = st.columns(4)
                with cx1:
                    st.session_state.form_data["excav_plans_eaux_indus"] = st.checkbox("Eaux industrielle et potable", value=st.session_state.form_data["excav_plans_eaux_indus"])
                    st.session_state.form_data["excav_plans_eaux_usees"] = st.checkbox("Eaux usées", value=st.session_state.form_data["excav_plans_eaux_usees"])
                with cx2:
                    st.session_state.form_data["excav_plans_eaux_pluv"] = st.checkbox("Eaux pluviales", value=st.session_state.form_data["excav_plans_eaux_pluv"])
                    st.session_state.form_data["excav_plans_eaux_incendie"] = st.checkbox("Eaux incendie", value=st.session_state.form_data["excav_plans_eaux_incendie"])
                with cx3:
                    st.session_state.form_data["excav_plans_ht"] = st.checkbox("Haute tension", value=st.session_state.form_data["excav_plans_ht"])
                    st.session_state.form_data["excav_plans_bt"] = st.checkbox("Basse tension", value=st.session_state.form_data["excav_plans_bt"])
                with cx4:
                    st.session_state.form_data["excav_plans_gaz"] = st.checkbox("Gaz", value=st.session_state.form_data["excav_plans_gaz"])

                st.write("##### Risques liés à l'environnement :")
                ceenv1, ceenv2, ceenv3 = st.columns(3)
                with ceenv1: st.session_state.form_data["excav_struct_proximite"] = st.checkbox("Proximité d'éléments structurels (rack, fondation…)", value=st.session_state.form_data["excav_struct_proximite"])
                with ceenv2: st.session_state.form_data["excav_architecte"] = st.checkbox("Architecte consulté", value=st.session_state.form_data["excav_architecte"])
                with ceenv3: st.session_state.form_data["excav_dict"] = st.checkbox("DICT émise", value=st.session_state.form_data["excav_dict"])

                st.write("##### Risques liés à l'effondrement (case à cocher 'Oui' ou 'Non') :")
                ceeff1, ceeff2 = st.columns(2)
                with ceeff1:
                    st.session_state.form_data["excav_eau_pompe"] = st.checkbox("Présence d'eau, utilisation d'une pompe de relevage", value=st.session_state.form_data["excav_eau_pompe"])
                    st.session_state.form_data["excav_balisage"] = st.checkbox("Balisage et dégagement de la zone", value=st.session_state.form_data["excav_balisage"])
                with ceeff2:
                    st.session_state.form_data["excav_vehicule_3m"] = st.checkbox("Placement des véhicules à plus de 3 mètres", value=st.session_state.form_data["excav_vehicule_3m"])
                    st.session_state.form_data["excav_deblais"] = st.checkbox("Dépose des déblais identifiées et communiquées", value=st.session_state.form_data["excav_deblais"])

                st.write("##### Moyens d'accès à la tranchée :")
                st.session_state.form_data["excav_acces"] = st.selectbox("Si oui : Liste déroulante avec choix obligatoire :", ["Escalier / Rampe", "Échelle", "Passerelle"])
                if st.session_state.form_data["excav_acces"] == "Échelle":
                    st.error("🚨 **Si échelle -> dérogation casque rouge**")

                st.session_state.form_data["excav_profondeur_130"] = st.checkbox("Profondeur de la tranchée > 1,30m", value=st.session_state.form_data["excav_profondeur_130"])
                if st.session_state.form_data["excav_profondeur_130"]:
                    st.error("🔒 **Si oui : Blindage obligatoire**")

                st.session_state.form_data["excav_schema_commentaires"] = st.text_area("Champs libre pour faire schéma de l'excavation ou commentaires :", value=st.session_state.form_data["excav_schema_commentaires"])

                st.write("##### 3 signatures obligatoires :")
                st.session_state.form_data["excav_chef_manoeuvre"] = st.text_input("• Chef de manœuvre de la société extérieure :", value=st.session_state.form_data["excav_chef_manoeuvre"])
                st.session_state.form_data["excav_do"] = st.text_input("• Le donneur d'ordre (après celle-ci début d'installation autorisé) :", value=st.session_state.form_data["excav_do"])
                st.session_state.form_data["excav_casque_rouge"] = st.text_input("• Le casque rouge (obligatoire pour commencer l'intervention) :", value=st.session_state.form_data["excav_casque_rouge"])
                st.divider()

            # ---------------------------------------------------------
            # 5. PERMIS GRUTAGE
            # ---------------------------------------------------------
            if st.session_state.form_data["p_grutage"]:
                st.info("🏗️ **PERMIS GRUTAGE**")
                
                st.write("##### Description du matériel et de la charge :")
                st.write("*Charges maximale à gruter :*")
                st.session_state.form_data["grut_desc_mop"] = st.text_area("Description de la charge (MOP) ou texte libre :", value=st.session_state.form_data["grut_desc_mop"])
                
                cg1, cg2 = st.columns(2)
                with cg1: st.session_state.form_data["grut_poids_charge"] = st.number_input("Poids de la charge (Encart numérique) :", value=st.session_state.form_data["grut_poids_charge"])
                with cg2: st.session_state.form_data["grut_unite"] = st.selectbox("Choix de l'unité :", ["kg", "T"])

                st.session_state.form_data["grut_poids_acc"] = st.number_input(f"Poids des accessoires (Encart numérique dans la même unité : {st.session_state.form_data['grut_unite']}) :", value=st.session_state.form_data["grut_poids_acc"])
                poids_tot = st.session_state.form_data["grut_poids_charge"] + st.session_state.form_data["grut_poids_acc"]
                st.write(f"⚖️ **Poids total = Poids de la charge + Poids des accessoires :** `{poids_tot} {st.session_state.form_data['grut_unite']}`")

                st.write("*Matériels :*")
                cmat1, cmat2, cmat3 = st.columns(3)
                with cmat1: st.session_state.form_data["grut_immat"] = st.text_input("Identification de la grue (immatriculation) = texte libre :", value=st.session_state.form_data["grut_immat"])
                with cmat2: st.session_state.form_data["grut_fleche"] = st.number_input("Hauteur de flèche à la charge maximale (m) :", value=st.session_state.form_data["grut_fleche"])
                with cmat3: st.session_state.form_data["grut_portee"] = st.number_input("Portée maximale pour la charge maximale (m) :", value=st.session_state.form_data["grut_portee"])

                cmat4, cmat5 = st.columns(2)
                with cmat4: st.session_state.form_data["grut_pression_patin"] = st.text_input("Pression maximale sur patin :", value=st.session_state.form_data["grut_pression_patin"])
                with cmat5: st.session_state.form_data["grut_rayon"] = st.number_input("Rayon de grutage :", value=st.session_state.form_data["grut_rayon"])

                st.write("##### Organisation du levage (cases à cocher 'Oui' ou 'Non') :")
                st.session_state.form_data["grut_balisage"] = st.checkbox("Balisage de la zone conforme au plan de grutage", value=st.session_state.form_data["grut_balisage"])
                st.session_state.form_data["grut_plan_vue"] = st.checkbox("Plan de grutage vue en plan avec zone de survol interdite (MOP)", value=st.session_state.form_data["grut_plan_vue"])
                st.session_state.form_data["grut_plan_elev"] = st.checkbox("Plan de grutage en élévation (MOP)", value=st.session_state.form_data["grut_plan_elev"])
                st.session_state.form_data["grut_obstacles"] = st.checkbox("Identification des obstacles ou lignes électriques conforme au plan de grutage", value=st.session_state.form_data["grut_obstacles"])

                st.write("##### Anémomètre & Vitesse du vent :")
                st.session_state.form_data["grut_anemometre"] = st.checkbox("Anémomètre en bout de flèche", value=st.session_state.form_data["grut_anemometre"])
                cv1, cv2 = st.columns(2)
                with cv1: st.session_state.form_data["grut_vent_val"] = st.number_input("Vérification via grutier/anémomètre = encart numérique :", value=st.session_state.form_data["grut_vent_val"])
                with cv2: st.session_state.form_data["grut_vent_unite"] = st.selectbox("Sélection de l'unité :", ["km/h", "m/S"])

                if (st.session_state.form_data["grut_vent_unite"] == "km/h" and st.session_state.form_data["grut_vent_val"] > 36) or (st.session_state.form_data["grut_vent_unite"] == "m/S" and st.session_state.form_data["grut_vent_val"] > 10):
                    st.error("❌ **Indication par météo + Alerte suivant les seuils + Blocage de l'intervention si >36km/h (peut bloquer le remplissage du permis dès son ouverture avec motif renseigné)**")

                st.session_state.form_data["grut_pesage"] = st.checkbox("Dispositif de mesure de charge", value=st.session_state.form_data["grut_pesage"])
                if st.session_state.form_data["grut_pesage"]:
                    st.info("Si oui : Charge totale maxi < 90% charge de la grue")
                else:
                    st.warning("Si non : Charge totale maxi < 80% charge de la grue")

                st.session_state.form_data["grut_centre_gravite"] = st.checkbox("Prise en compte du centre de gravité de la grue", value=st.session_state.form_data["grut_centre_gravite"])
                st.session_state.form_data["grut_angles_elingue"] = st.checkbox("Prise en compte des angles d'élingage au plan de grutage", value=st.session_state.form_data["grut_angles_elingue"])
                st.session_state.form_data["grut_plaques_rep"] = st.checkbox("Descente de charge sur plaque de répartition en ligne avec analyse de sol", value=st.session_state.form_data["grut_plaques_rep"])

                st.write("##### Signatures organisation levage (automatique) :")
                st.write(f"• Chef de manœuvre : `{st.session_state.form_data['grut_chef_m_nom']} - {st.session_state.form_data['grut_chef_m_soc']}`")
                st.write(f"• Élingueur : `{st.session_state.form_data['grut_elingueur_nom']} - {st.session_state.form_data['grut_elingueur_soc']}`")
                st.write(f"• Grutier : `{st.session_state.form_data['grut_grutier_nom']} - {st.session_state.form_data['grut_grutier_soc']}`")

                st.write("##### Vérification du matériel et charge :")
                st.write("*Matériel de levage (cases à cocher 'Oui' ou 'Non') :*")
                st.session_state.form_data["grut_certif_grue"] = st.checkbox(f"Certificat de conformité de la grue (ajouter automatiquement l'immatriculation renseignée en amont : {st.session_state.form_data['grut_immat']})", value=st.session_state.form_data["grut_certif_grue"])
                st.session_state.form_data["grut_certif_acc"] = st.checkbox("Certificat de conformité des accessoires de levage utilisés", value=st.session_state.form_data["grut_certif_acc"])
                st.session_state.form_data["grut_certif_plaques"] = st.checkbox("Certificat de conformité des plaques de répartition", value=st.session_state.form_data["grut_certif_plaques"])
                st.session_state.form_data["grut_check_j_grue"] = st.checkbox("Check list de vérification journalière de la grue", value=st.session_state.form_data["grut_check_j_grue"])
                st.session_state.form_data["grut_check_j_acc"] = st.checkbox("Check list de vérification journalière des accessoires.", value=st.session_state.form_data["grut_check_j_acc"])

                st.write("*Patte de levage et charge (cases à cocher 'Oui' ou 'Non') :*")
                st.session_state.form_data["grut_pattes_concu"] = st.checkbox("Pattes de fixation conçues pour le levage", value=st.session_state.form_data["grut_pattes_concu"])
                st.session_state.form_data["grut_pattes_defaut"] = st.checkbox("Pattes de levage exemptes de défauts", value=st.session_state.form_data["grut_pattes_defaut"])
                st.session_state.form_data["grut_pattes_adequation"] = st.checkbox("Adéquation pattes de levage / crochet manille", value=st.session_state.form_data["grut_pattes_adequation"])
                st.session_state.form_data["grut_charges_annexes"] = st.checkbox("Les charges annexes sont correctement fixées à la charge principale", value=st.session_state.form_data["grut_charges_annexes"])

                st.session_state.form_data["grut_schema_commentaires"] = st.text_area("Champs libre pour faire schéma de levage… ou commentaires :", value=st.session_state.form_data["grut_schema_commentaires"])

                st.write("##### 3 signatures obligatoires grutage :")
                st.text_input("1. Chef de manœuvre de la société extérieure :", value=st.session_state.form_data["grut_chef_m_nom"])
                st.session_state.form_data["grut_do_sign"] = st.text_input("2. Le donneur d'ordre (après celle-ci début d'installation autorisé) :", value=st.session_state.form_data["grut_do_sign"])
                st.session_state.form_data["grut_casque_rouge_sign"] = st.text_input("3. Le casque rouge (obligatoire pour commencer l'intervention) :", value=st.session_state.form_data["grut_casque_rouge_sign"])
                st.divider()

            # ---------------------------------------------------------
            # 6. PERMIS ESPACE CONFINÉ
            # ---------------------------------------------------------
            if st.session_state.form_data["p_confine"]:
                st.info("🦺 **PERMIS ESPACE CONFINÉ**")
                st.error("🥽 **EPI = Masque auto-sauveteur (type M20)**")

                st.session_state.form_data["conf_lieu"] = st.text_input("Lieu précis de l'entrée en espace confiné : Texte libre :", value=st.session_state.form_data["conf_lieu"])

                st.write("##### Risques liés à l'intervention (cases à cocher 'Oui' ou 'Non') :")
                cr1, cr2, cr3 = st.columns(3)
                with cr1:
                    st.session_state.form_data["conf_r_atmo"] = st.checkbox("Atmosphère dangereuse", value=st.session_state.form_data["conf_r_atmo"])
                    st.session_state.form_data["conf_r_chimique"] = st.checkbox("Substance chimique ou résidus dans la cuve", value=st.session_state.form_data["conf_r_chimique"])
                    st.session_state.form_data["conf_r_inflam"] = st.checkbox("Substances Inflammables/Combustibles", value=st.session_state.form_data["conf_r_inflam"])
                with cr2:
                    st.session_state.form_data["conf_r_orga"] = st.checkbox("Matières organiques décomposant", value=st.session_state.form_data["conf_r_orga"])
                    st.session_state.form_data["conf_r_meca"] = st.checkbox("Équipement mécanique en mouvement", value=st.session_state.form_data["conf_r_meca"])
                    st.session_state.form_data["conf_r_thermiq"] = st.checkbox("Risques thermiques/Brûlures", value=st.session_state.form_data["conf_r_thermiq"])
                with cr3:
                    st.session_state.form_data["conf_r_bruit"] = st.checkbox("Bruit important pouvant perturber la communication", value=st.session_state.form_data["conf_r_bruit"])
                    st.session_state.form_data["conf_troudhomme_610"] = st.checkbox("Trou d'homme > ou égal 610mm", value=st.session_state.form_data["conf_troudhomme_610"])

                if not st.session_state.form_data["conf_troudhomme_610"]:
                    st.error("🚨 **Si 'Non' = Plan de secours spécifique**")

                st.write("##### EPI et formations 'cases à cocher 'Oui' ou 'Non' :")
                st.session_state.form_data["conf_catec"] = st.checkbox("Intervenants formés et qualifiés CATEC", value=st.session_state.form_data["conf_catec"])
                st.session_state.form_data["conf_hauteur"] = st.checkbox("Travail en hauteur", value=st.session_state.form_data["conf_hauteur"])
                st.session_state.form_data["conf_m20"] = st.checkbox("Masque auto-sauveteur (type M20)", value=st.session_state.form_data["conf_m20"])

                st.write("##### Check list obligatoire pour une entrée en espace confiné :")
                st.write(f"• Secouriste de la zone = `{st.session_state.form_data['conf_secouriste']}`")
                st.write(f"• Service médical de l'intervention = `{st.session_state.form_data['conf_medical']}`")

                st.session_state.form_data["conf_action_chaud"] = st.checkbox("Allez-vous couper, poncer, souder, riveter, gratter à l'intérieur de l'espace confiné ?", value=st.session_state.form_data["conf_action_chaud"])
                if st.session_state.form_data["conf_action_chaud"]:
                    st.warning("⚠️ **Si oui = Renvoi au permis point chaud**")
                    st.session_state.form_data["p_points_chauds"] = True

                st.session_state.form_data["conf_ventilation_nat"] = st.checkbox("Vérification que la ventilation naturelle est suffisante et présente (48h avant) ??", value=st.session_state.form_data["conf_ventilation_nat"])
                st.session_state.form_data["conf_ventilation_forcee"] = st.checkbox("Allez-vous installer une ventilation forcée auxiliaire ?", value=st.session_state.form_data["conf_ventilation_forcee"])
                if st.session_state.form_data["conf_ventilation_forcee"]:
                    st.info("Si oui = Minimum 56m3/h par personne")

                st.session_state.form_data["conf_consignation_gaz"] = st.checkbox("Vérification de la fermeture et de la consignation de toutes les arrivées de produits ou gaz", value=st.session_state.form_data["conf_consignation_gaz"])
                if st.session_state.form_data["conf_consignation_gaz"]:
                    st.info("Renvoi au permis consignation et coche Consignation/séparation OU pose de joints pleins (PG)")
                    st.session_state.form_data["p_consignation"] = True

                st.session_state.form_data["conf_cuve_vide"] = st.checkbox("Vérifier que les cuves ou espaces sont vides pour éviter les risques de noyade", value=st.session_state.form_data["conf_cuve_vide"])
                st.session_state.form_data["conf_vol_caches"] = st.checkbox("Vérifier que tous les espaces sont contrôlés et qu'il n'y a pas de volumes cachés qui emprisonneraient un gaz ou un liquide.", value=st.session_state.form_data["conf_vol_caches"])
                st.session_state.form_data["conf_eclairage_24v"] = st.checkbox("Vérifier le niveau d'éclairage est suffisant (Eclairage 24 VOLT TBT ou autonome)", value=st.session_state.form_data["conf_eclairage_24v"])
                st.session_state.form_data["conf_blocage_ouvert"] = st.checkbox("Bloquer l'ouverture en position ouverte pour éviter la fermeture accidentelle", value=st.session_state.form_data["conf_blocage_ouvert"])

                st.session_state.form_data["conf_echaf_echelle"] = st.checkbox("Allez-vous installer un échafaudage ou une échelle dans cet espace ?", value=st.session_state.form_data["conf_echaf_echelle"])
                if st.session_state.form_data["conf_echaf_echelle"]:
                    st.caption("(Contrôle d'accès et d'encombrement spécifique)")

                st.session_state.form_data["conf_prod_chim"] = st.checkbox("La zone contenait ou contient des produits chimiques ?", value=st.session_state.form_data["conf_prod_chim"])
                if st.session_state.form_data["conf_prod_chim"]:
                    st.warning("⚠️ **Si oui = Vérifier les VLEP dans les FDS.**")

                st.session_state.form_data["conf_laser"] = st.checkbox("Vérifier qu'il n'y a pas d'émission Laser dans cet environnement", value=st.session_state.form_data["conf_laser"])
                st.session_state.form_data["conf_comm_type"] = st.selectbox("La communication entre l'entrant et le stand by est efficace et fonctionnel (Case à cocher) :", ["Talkie Walkie", "Visuelle", "téléphone"])

                st.write("##### Mesures à prendre :")
                co1, co2 = st.columns(2)
                with co1:
                    st.session_state.form_data["conf_o2"] = st.number_input("Niveau d'oxygène (19,5% < O2 < 23%) : encart numérique %O2 :", value=st.session_state.form_data["conf_o2"])
                    st.session_state.form_data["conf_o2_contre_mesure"] = st.number_input("+ contre-mesure à faire donc encart numérique %O2 dans la partie validation du permis avec le donneur d'ordre :", value=st.session_state.form_data["conf_o2_contre_mesure"])
                with co2:
                    st.session_state.form_data["conf_h2s_check"] = st.checkbox("Présence de H2S", value=st.session_state.form_data["conf_h2s_check"])
                    if st.session_state.form_data["conf_h2s_check"]:
                        st.session_state.form_data["conf_h2s"] = st.number_input("Si 'Oui' = Encart numérique %H2S :", value=st.session_state.form_data["conf_h2s"])

                    st.session_state.form_data["conf_co_check"] = st.checkbox("Présence de CO", value=st.session_state.form_data["conf_co_check"])
                    if st.session_state.form_data["conf_co_check"]:
                        st.session_state.form_data["conf_co"] = st.number_input("Si 'Oui' = Encart numérique %CO :", value=st.session_state.form_data["conf_co"])

                    st.session_state.form_data["conf_explo_check"] = st.checkbox("Explosimétrie", value=st.session_state.form_data["conf_explo_check"])
                    if st.session_state.form_data["conf_explo_check"]:
                        st.session_state.form_data["conf_explo"] = st.number_input("Si 'Oui' = Encart numérique % :", value=st.session_state.form_data["conf_explo"])

                st.session_state.form_data["conf_temp_cuve"] = st.number_input("Vérifier que la cuve ou les produits dans la zone ne dépassent pas 45°C - Température : encart numérique °C :", value=st.session_state.form_data["conf_temp_cuve"])
                st.session_state.form_data["conf_verif_temp"] = st.selectbox("Vérificateur : Choix entre le N2 et le DO :", ["N2", "DO"])

                st.session_state.form_data["conf_inflam_lel"] = st.number_input("En cas de produit inflammable - Mesures : encart numérique % de LEL (Vérification du seuil < 10% LEL) :", value=st.session_state.form_data["conf_inflam_lel"])
                st.session_state.form_data["conf_verif_lel"] = st.selectbox("Vérificateur LEL : Choix entre le N2 et le DO :", ["N2", "DO"])

                st.session_state.form_data["conf_schema_commentaires"] = st.text_area("Champs libre pour faire schéma ou commentaires :", value=st.session_state.form_data["conf_schema_commentaires"])

                st.write("##### 3 signatures obligatoires :")
                st.session_state.form_data["conf_entrant"] = st.text_input("• Entrants :", value=st.session_state.form_data["conf_entrant"])
                st.session_state.form_data["conf_standby"] = st.text_input("• Stand by :", value=st.session_state.form_data["conf_standby"])
                st.session_state.form_data["conf_do"] = st.text_input("• Donneur d'ordre :", value=st.session_state.form_data["conf_do"])
                st.divider()

            # ---------------------------------------------------------
            # 7. PERMIS TRAVAUX ÉLECTRIQUES
            # ---------------------------------------------------------
            if st.session_state.form_data["p_electrique"]:
                st.error("⚡ **PERMIS TRAVAUX ÉLECTRIQUE**")
                st.warning("🥽 **EPI (de base) =** Casque d'électricien, Gants isolants électriques (EN 60903) + Surgants en cuir de protection mécanique + Vêtements de travail 100 % coton ou ignifugés (interdiction du synthétique)")
                st.info("📣 **Rappel :** 'Les travaux électriques sous tension sont interdits. Les travaux au voisinage de pièces nues sous tension doivent être validés. Les outils utilisés doivent être isolés'")

                st.write("##### Liste à cocher :")
                ce1, ce2 = st.columns(2)
                with ce1:
                    st.session_state.form_data["elec_modife"] = st.checkbox("Modification d'installation", value=st.session_state.form_data["elec_modife"])
                    st.session_state.form_data["elec_armoire"] = st.checkbox("Intervention dans les armoires, enveloppe, coffret", value=st.session_state.form_data["elec_armoire"])
                    st.session_state.form_data["elec_voisinage_tension"] = st.checkbox("Travail au voisinage de la tension", value=st.session_state.form_data["elec_voisinage_tension"])
                    st.session_state.form_data["elec_courant_faible"] = st.checkbox("Courants faibles, instrumentation", value=st.session_state.form_data["elec_courant_faible"])
                with ce2:
                    st.session_state.form_data["elec_releve"] = st.checkbox("Relevés / Mesures ou essais", value=st.session_state.form_data["elec_releve"])
                    st.session_state.form_data["elec_chemins"] = st.checkbox("Chemins de câbles / câbles et raccordement", value=st.session_state.form_data["elec_chemins"])
                    st.session_state.form_data["elec_voisinage_nues"] = st.checkbox("Travail au voisinage de pièces nues sous tension", value=st.session_state.form_data["elec_voisinage_nues"])

                if st.session_state.form_data["elec_voisinage_nues"]:
                    st.error("🔒 **Si Travail au voisinage de pièces nues sous tension est coché :** Alors : Validation par E&I ou PT E&I habilité B2 ou H2, BC ou HC suivant la tension.")
                    st.error("🥽 **EPI (en plus de ceux de base) =** Écran facial / Visière panoramique anti-arc électrique (EN 166B / GS-ET-29 Class 1 ou 2) + Vestes/vêtements de protection anti-arc électrique (Arc Flash EN ISO 11612) + Nappes isolantes et tapis isolant de sol (EN 61112) pour recouvrir les parties sous tension adjacentes.")
                    st.session_state.form_data["elec_valideur_ei"] = st.text_input("Validation E&I / PT E&I :", value=st.session_state.form_data["elec_valideur_ei"])
                st.divider()

            # ---------------------------------------------------------
            # 8. PERMIS CONSIGNATION EN 3 PHASES
            # ---------------------------------------------------------
            if st.session_state.form_data["p_consignation"]:
                st.success("⚡ **PERMIS CONSIGNATION EN 3 PHASES**")
                
                st.write("##### Ouverture de circuit : méthode et points d'isolation retenus")
                st.session_state.form_data["loto_ouverture_methode"] = st.selectbox(
                    "Méthode d'isolation :",
                    ["2 vannes et vanne de drain", "2 vannes", "vanne simple", "vanne et désolidarisation de la conduite", "joint plein", "joint plein et désolidarisation de la conduite"]
                )
                
                clo1, clo2 = st.columns(2)
                with clo1: st.session_state.form_data["loto_ouvert_loc1"] = st.text_input("Localisation 1 :", value=st.session_state.form_data["loto_ouvert_loc1"])
                with clo2:
                    if "vanne simple" not in st.session_state.form_data["loto_ouverture_methode"] and "joint plein" != st.session_state.form_data["loto_ouverture_methode"]:
                        st.session_state.form_data["loto_ouvert_loc2"] = st.text_input("Localisation 2 :", value=st.session_state.form_data["loto_ouvert_loc2"])

                st.write("##### Isolation des énergies : méthode de points d'isolation retenus")
                cis1, cis2 = st.columns(2)
                with cis1:
                    st.session_state.form_data["loto_is_elec"] = st.checkbox("Si 'IS électrique' coché", value=st.session_state.form_data["loto_is_elec"])
                    if st.session_state.form_data["loto_is_elec"]:
                        st.session_state.form_data["loto_is_elec_loc1"] = st.text_input("2 encarts texte libre : Localisation 1 :", value=st.session_state.form_data["loto_is_elec_loc1"])
                        st.session_state.form_data["loto_is_elec_loc2"] = st.text_input("Localisation 2 :", value=st.session_state.form_data["loto_is_elec_loc2"])

                    st.session_state.form_data["loto_fusible"] = st.checkbox("Si 'Fusibles enlevés' coché", value=st.session_state.form_data["loto_fusible"])
                    if st.session_state.form_data["loto_fusible"]:
                        st.session_state.form_data["loto_fusible_loc1"] = st.text_input("Localisation 1 (Fusibles) :", value=st.session_state.form_data["loto_fusible_loc1"])
                        st.session_state.form_data["loto_fusible_loc2"] = st.text_input("Localisation 2 (Fusibles) :", value=st.session_state.form_data["loto_fusible_loc2"])

                    st.session_state.form_data["loto_cable"] = st.checkbox("Si 'Câble électrique déconnecté' coché", value=st.session_state.form_data["loto_cable"])
                    if st.session_state.form_data["loto_cable"]:
                        st.session_state.form_data["loto_cable_loc1"] = st.text_input("Localisation 1 (Câble) :", value=st.session_state.form_data["loto_cable_loc1"])
                        st.session_state.form_data["loto_cable_loc2"] = st.text_input("Localisation 2 (Câble) :", value=st.session_state.form_data["loto_cable_loc2"])

                with cis2:
                    st.session_state.form_data["loto_pneu"] = st.checkbox("Si 'IS pneumatique' coché", value=st.session_state.form_data["loto_pneu"])
                    if st.session_state.form_data["loto_pneu"]:
                        st.session_state.form_data["loto_pneu_loc1"] = st.text_input("Localisation 1 (Pneu) :", value=st.session_state.form_data["loto_pneu_loc1"])
                        st.session_state.form_data["loto_pneu_loc2"] = st.text_input("Localisation 2 (Pneu) :", value=st.session_state.form_data["loto_pneu_loc2"])

                    st.session_state.form_data["loto_hydra"] = st.checkbox("Si 'IS hydraulique' coché", value=st.session_state.form_data["loto_hydra"])
                    if st.session_state.form_data["loto_hydra"]:
                        st.session_state.form_data["loto_hydra_loc1"] = st.text_input("Localisation 1 (Hydra) :", value=st.session_state.form_data["loto_hydra_loc1"])
                        st.session_state.form_data["loto_hydra_loc2"] = st.text_input("Localisation 2 (Hydra) :", value=st.session_state.form_data["loto_hydra_loc2"])

                    st.session_state.form_data["loto_residu"] = st.checkbox("Si 'énergies résiduelles' coché", value=st.session_state.form_data["loto_residu"])
                    if st.session_state.form_data["loto_residu"]:
                        st.session_state.form_data["loto_residu_loc1"] = st.text_input("Localisation 1 (Résiduelles) :", value=st.session_state.form_data["loto_residu_loc1"])
                        st.session_state.form_data["loto_residu_loc2"] = st.text_input("Localisation 2 (Résiduelles) :", value=st.session_state.form_data["loto_residu_loc2"])

                st.write("##### Nettoyage des équipements :")
                cn1, cn2 = st.columns(2)
                with cn1:
                    st.session_state.form_data["loto_drain_ouvert"] = st.checkbox("Vanne de drain ouverte", value=st.session_state.form_data["loto_drain_ouvert"])
                    st.session_state.form_data["loto_eq_ouvert"] = st.checkbox("Equipement ouvert", value=st.session_state.form_data["loto_eq_ouvert"])
                with cn2:
                    st.session_state.form_data["loto_eq_lave"] = st.checkbox("Equipement lavé", value=st.session_state.form_data["loto_eq_lave"])
                    st.session_state.form_data["loto_eq_sanitise"] = st.checkbox("Equipement sanitisé", value=st.session_state.form_data["loto_eq_sanitise"])
                st.divider()

            # ---------------------------------------------------------
            # 9. PERMIS SYSTÈME À RISQUES / ATEX / FLUIDES DANGEREUX
            # ---------------------------------------------------------
            if st.session_state.form_data["p_systeme_risque"]:
                st.error("☣️ **PERMIS SYSTÈME À RISQUE**")
                st.info("Ouverture du permis consignation (renvoi au même truc au-dessus) effectuée.")

                st.write("##### Case à cocher :")
                st.session_state.form_data["sr_chimique_c1"] = st.checkbox("Chimique de classe 1 (BFA, Ethanol, Néodol/OG base, Acide chlorydrique)", value=st.session_state.form_data["sr_chimique_c1"])
                if st.session_state.form_data["sr_chimique_c1"]:
                    st.session_state.form_data["sr_chimique_nom"] = st.text_input("Nom du produit : texte libre :", value=st.session_state.form_data["sr_chimique_nom"])

                st.session_state.form_data["sr_fluide_dang"] = st.checkbox("Fluides dangereux (Parfum, soude, Caustique, Azote, Vapeur, Gaz Naturel)", value=st.session_state.form_data["sr_fluide_dang"])
                if st.session_state.form_data["sr_fluide_dang"]:
                    st.session_state.form_data["sr_fluide_nom"] = st.text_input("Nom du produit : texte libre (Fluides) :", value=st.session_state.form_data["sr_fluide_nom"])

                st.session_state.form_data["sr_atex"] = st.checkbox("Zone ATEX", value=st.session_state.form_data["sr_atex"])
                if st.session_state.form_data["sr_atex"]:
                    st.session_state.form_data["sr_atex_nom"] = st.text_input("Nom du produit : texte libre (ATEX) :", value=st.session_state.form_data["sr_atex_nom"])

                st.write("##### Evaluation des risques :")
                st.write("*Avant le démarrage des travaux (Case à cocher 'Oui' ou 'Non') :*")
                cera1, cera2 = st.columns(2)
                with cera1:
                    st.session_state.form_data["sr_balisage"] = st.checkbox("Balisage de la zone", value=st.session_state.form_data["sr_balisage"])
                    st.session_state.form_data["sr_douche_rince"] = st.checkbox("Vérification fonctionnement douche et lave œil", value=st.session_state.form_data["sr_douche_rince"])
                    st.session_state.form_data["sr_ramonage"] = st.checkbox("Ramonage de conduite", value=st.session_state.form_data["sr_ramonage"])
                    if st.session_state.form_data["sr_ramonage"]:
                        st.session_state.form_data["sr_ramonage_dt"] = st.text_input("Effectué le : (date et heure à choisir) :", value=st.session_state.form_data["sr_ramonage_dt"])
                with cera2:
                    st.session_state.form_data["sr_isolement"] = st.checkbox("Vérification d'isolement des circuits", value=st.session_state.form_data["sr_isolement"])
                    st.session_state.form_data["sr_feuille_loto"] = st.checkbox("Feuille de consignation disponible, complétée et signée", value=st.session_state.form_data["sr_feuille_loto"])
                    if st.session_state.form_data["sr_atex"]:
                        st.session_state.form_data["sr_zonage_atex"] = st.checkbox("Vérification du plan de zonage ATEX (zone 0, 1, 2) (si ATEX coché)", value=st.session_state.form_data["sr_zonage_atex"])

                st.write("*Pendant l'exécution des travaux — EPI (Case à cocher 'Oui' ou 'Non') :*")
                cepi1, cepi2 = st.columns(2)
                with cepi1:
                    st.session_state.form_data["sr_epi_ecran"] = st.checkbox("Ecran facial", value=st.session_state.form_data["sr_epi_ecran"])
                    st.session_state.form_data["sr_epi_lunettes"] = st.checkbox("Lunettes étanches", value=st.session_state.form_data["sr_epi_lunettes"])
                    st.session_state.form_data["sr_epi_gants_chim"] = st.checkbox("Gants chimiques adaptés", value=st.session_state.form_data["sr_epi_gants_chim"])
                    st.session_state.form_data["sr_epi_comb1"] = st.checkbox("Combinaison 1 pièce en viton neoprene", value=st.session_state.form_data["sr_epi_comb1"])
                    st.session_state.form_data["sr_epi_comb2"] = st.checkbox("Combinaise 2 pièce anti-acide", value=st.session_state.form_data["sr_epi_comb2"])
                    st.session_state.form_data["sr_epi_bottes"] = st.checkbox("Bottes anti-acide (sous pantalon)", value=st.session_state.form_data["sr_epi_bottes"])
                with cepi2:
                    st.session_state.form_data["sr_epi_cartouche"] = st.checkbox("Masque à cartouche approprié", value=st.session_state.form_data["sr_epi_cartouche"])
                    st.session_state.form_data["sr_epi_ari"] = st.checkbox("ARI (Appareil Respiratoire Isolant)", value=st.session_state.form_data["sr_epi_ari"])
                    st.session_state.form_data["sr_epi_3m6000"] = st.checkbox("Masque 3M 6000", value=st.session_state.form_data["sr_epi_3m6000"])
                    st.session_state.form_data["sr_epi_versaflo"] = st.checkbox("Casque ventilé Jupiter avec cartouche chimique (Versaflo)", value=st.session_state.form_data["sr_epi_versaflo"])
                    st.session_state.form_data["sr_epi_no_versaflo"] = st.checkbox("Pas de versaflo", value=st.session_state.form_data["sr_epi_no_versaflo"])

                st.session_state.form_data["sr_auxiliaire_equipe"] = st.checkbox("Auxiliaire équipé comme intervenant", value=st.session_state.form_data["sr_auxiliaire_equipe"])
                st.session_state.form_data["sr_comm_moyen"] = st.text_input("Moyen de communication adapté : Texte libre :", value=st.session_state.form_data["sr_comm_moyen"])

                st.write("*Après l'exécution des travaux :*")
                st.session_state.form_data["sr_inspect_remise"] = st.checkbox("Inspection du circuit après remise en service", value=st.session_state.form_data["sr_inspect_remise"])
                if st.session_state.form_data["sr_inspect_remise"]:
                    st.session_state.form_data["sr_inspect_nom"] = st.text_input("Nom du vérificateur : Texte libre ou liste :", value=st.session_state.form_data["sr_inspect_nom"])
                    st.session_state.form_data["sr_inspect_dt"] = st.text_input("Fait le : Date et heure à choisir :", value=st.session_state.form_data["sr_inspect_dt"])

                st.session_state.form_data["sr_schema_commentaires"] = st.text_area("Champs libre pour faire schéma de levage… ou commentaires :", value=st.session_state.form_data["sr_schema_commentaires"])

                st.write("##### 3 signatures obligatoires Systèmes à Risques :")
                st.session_state.form_data["sr_sign_intervenant"] = st.text_input("• Intervenants qualifiés sur le système à risques :", value=st.session_state.form_data["sr_sign_intervenant"])
                st.session_state.form_data["sr_sign_do"] = st.text_input("• Le donneur d'ordre :", value=st.session_state.form_data["sr_sign_do"])
                st.session_state.form_data["sr_sign_operations"] = st.text_input("• Opération (également obligatoire pour commencer l'intervention) :", value=st.session_state.form_data["sr_sign_operations"])
                st.divider()

            st.info("📣 **Tous les EPIs dans ces permis spécifiques sont ceux à porter en plus des EPIs de base du permis de travail général.**")

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button("⬅️ Précédent"): st.session_state.step = 5; st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"): st.session_state.step = 7; st.rerun()

        # ==============================================================================
        # ÉTAPE 7 : SYNTHÈSE, GESTION SOUS-TRAITANCE & SOUMISSION
        # ==============================================================================
        elif current_step == 7:
            st.subheader("7. Synthèse & Signatures")

            st.markdown("<div class='status-pending'>⚠️ PERMIS EN ATTENTE DE VALIDATION BATCH (07h30)</div>", unsafe_allow_html=True)

            # Règle sous-traitance à la fin du permis
            if st.session_state.form_data["is_subcontractor"]:
                st.warning(f"🤝 **Gestion de la sous-traitance (connue grâce au PDP et MOP) :** L'entreprise sélectionnée étant en sous-traitance, à la fin du permis de travail, le N2 de la société principale (**{st.session_state.form_data['titulaire_n2']}**) doit également valider le permis de travail et le signer.")

            st.write("##### Tableau Synthétique des Risques & Permis Spécifiques Renseignés :")
            
            tableau_data = []
            if st.session_state.form_data["p_hauteur"]:
                tableau_data.append({"activite": "Travail en hauteur / Échafaudage / Nacelle", "risque": "Chute de hauteur", "prevention": "Casque jugulaire obligatoire + VGP / Qualifications"})
            if st.session_state.form_data["p_toiture"]:
                tableau_data.append({"activite": "Accès Toiture", "risque": "Chute / Conditions Météo", "prevention": f"{st.session_state.form_data['toiture_protection']} + Binôme + Valideur ePDP"})
            if st.session_state.form_data["p_points_chauds"]:
                tableau_data.append({"activite": "Point Chaud / Flamme", "risque": "Incendie", "prevention": f"Visière EN166B + Extincteurs ({st.session_state.form_data['chaud_extincteur1']}/{st.session_state.form_data['chaud_extincteur2']}) + Vigie {st.session_state.form_data['chaud_vigie_nom']}"})
            if st.session_state.form_data["p_excavation"]:
                tableau_data.append({"activite": "Excavation / Tranchée", "risque": "Réseaux / Effondrement", "prevention": f"Plans 7 réseaux OK + DICT + 3 Signatures ({st.session_state.form_data['excav_chef_manoeuvre']}/{st.session_state.form_data['excav_do']}/{st.session_state.form_data['excav_casque_rouge']})"})
            if st.session_state.form_data["p_grutage"]:
                tableau_data.append({"activite": "Grutage", "risque": "Chute de charge", "prevention": f"Poids Total {st.session_state.form_data['grut_poids_charge']+st.session_state.form_data['grut_poids_acc']} {st.session_state.form_data['grut_unite']} + Anémomètre OK + 3 Signatures"})
            if st.session_state.form_data["p_confine"]:
                tableau_data.append({"activite": "Espace Confiné", "risque": "Asphyxie / Gaz", "prevention": f"Masque M20 + CATEC + O2 ({st.session_state.form_data['conf_o2']}%) + Standby {st.session_state.form_data['conf_standby']}"})
            if st.session_state.form_data["p_electrique"]:
                tableau_data.append({"activite": "Travail Électrique", "risque": "Arc Flash / Électrocution", "prevention": "Casque électricien + Gants EN 60903 + Vêtements 100% coton/ignifugés"})
            if st.session_state.form_data["p_consignation"]:
                tableau_data.append({"activite": "Consignation (LOTO 3 phases)", "risque": "Énergie résiduelle", "prevention": f"Méthode {st.session_state.form_data['loto_ouverture_methode']} + Nettoyage OK"})
            if st.session_state.form_data["p_systeme_risque"]:
                tableau_data.append({"activite": "Systèmes à Risques / ATEX", "risque": "Produits chimiques / Explosion", "prevention": f"Balisage + Douche/Rince-œil + EPIs lourds + 3 Signatures ({st.session_state.form_data['sr_sign_intervenant']}/{st.session_state.form_data['sr_sign_do']}/{st.session_state.form_data['sr_sign_operations']})"})

            if not tableau_data:
                tableau_data.append({"activite": "Permis Général Standard", "risque": "Risques standards PDP", "prevention": "EPIs de base"})

            st.table(tableau_data)

            permis_final = {
                "id": f"PT-2026-EXACT-0{len(st.session_state.permis_db)+1}",
                "date_travaux": st.session_state.form_data["date_str"],
                "societe": st.session_state.form_data["societe"],
                "pdp": st.session_state.form_data["pdp"],
                "mop": st.session_state.form_data["mop"],
                "is_subcontractor": st.session_state.form_data["is_subcontractor"],
                "titulaire_n2": st.session_state.form_data["titulaire_n2"],
                "n2": st.session_state.form_data["n2_nom"],
                "zone": st.session_state.form_data["lieu_pdp"],
                "emplacement": st.session_state.form_data["lieu_precision"],
                "statut": "EN_ATTENTE_BATCH",
                "heure": datetime.datetime.now().strftime("%H:%M"),
                "intervenants": list(st.session_state.form_data["intervenants"]),
                "tableau_risques": tableau_data
            }

            pdf_bytes = generer_pdf_bytes(permis_final)

            c_back, c_sub, c_pdf = st.columns([1, 2, 2])
            with c_back:
                if st.button("⬅️ Précédent"): st.session_state.step = 6; st.rerun()

            with c_pdf:
                st.download_button("📄 TÉLÉCHARGER PERMIS PDF", data=pdf_bytes, file_name=f"Permis_{permis_final['id']}.pdf", mime="application/pdf", use_container_width=True)

            with c_sub:
                if st.button("🚀 SOUMETTRE AU BATCH DE 07h30", type="primary", use_container_width=True):
                    st.session_state.permis_db.append(permis_final)
                    st.balloons(); st.success(f"Permis {permis_final['id']} soumis au batch avec succès !"); st.session_state.kiosk_mode = "HOME"

# ==============================================================================
# INTERFACE 2 : DDS BOARD (DO / HSE)
# ==============================================================================
elif role == "📊 DDS Board & Batch 07h30 (DO / HSE)":
    st.markdown("<div class='pg-header' style='background: #0f172a;'><h2>DDS BOARD — VALIDATION BATCH DAILY</h2></div>", unsafe_allow_html=True)
    if st.button("✅ VALIDER LE BATCH DE 07h30", type="primary"):
        for p in st.session_state.permis_db: p["statut"] = "VALIDÉ"
        st.success("Toutes les demandes de la fournée ont été validées !")

    for p in st.session_state.permis_db:
        st.write(f"### {p['id']} - {p['societe']} ({p['statut']})")
        st.table(p.get("tableau_risques", []))

# ==============================================================================
# INTERFACE 3 : INSPECTION TERRAIN (CASQUE ROUGE)
# ==============================================================================
else:
    st.markdown("<div class='pg-header' style='background: #b91c1c;'><h2>INSPECTION TERRAIN — CASQUE ROUGE</h2></div>", unsafe_allow_html=True)
    if st.session_state.permis_db:
        pt_sel = st.selectbox("Sélectionner un permis :", [p["id"] for p in st.session_state.permis_db])
        p = next(p for p in st.session_state.permis_db if p["id"] == pt_sel)
        st.write(f"### Contrôle Permis : {p['id']}")
        st.table(p.get("tableau_risques", []))
    else:
        st.info("Aucun permis enregistré pour le moment.")
