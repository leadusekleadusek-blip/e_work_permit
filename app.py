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
    .status-validated {
        background-color: #dcfce7; color: #166534; border: 2px solid #22c55e;
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

db_materiaux = ["Acier / Carbone", "Inox 316L / 304L", "Aluminium", "Béton / Maçonnerie", "PVC / Plastique"]
db_disques_blanchiment = ["Disque fibre abrasif", "Brosse métallique torsadée", "Clean & Strip"]

etapes_noms = ["Date & EE", "PDP & MoP", "Responsable N2", "Zone & Urgences", "Check-list & EPIs", "Permis Spécifiques (HRT)", "Synthèse & Signatures"]

if "permis_db" not in st.session_state:
    st.session_state.permis_db = []

if "kiosk_mode" not in st.session_state:
    st.session_state.kiosk_mode = "HOME"
if "step" not in st.session_state:
    st.session_state.step = 1

# INITIALISATION EXHAUSTIVE DE FORM_DATA
VALEURS_PAR_DEFAUT = {
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
    
    # 1. RISQUES PRINCIPAUX / PERMIS SPÉCIFIQUES (ÉTAPES 5 & 6)
    "p_hauteur": False,
    "p_toiture": False,
    "p_points_chauds": False,
    "p_excavation": False,
    "p_grutage": False,
    "p_confine": False,
    "p_electrique": False,
    "p_ouverture_circuit": False,
    "p_machines_mouvement": False,
    "p_equipement_pression": False,
    "p_laser_classe_iv": False,
    "p_demolition": False,
    "dta_consultation": False,
    "p_consignation": False,
    "p_systeme_risque": False,

    # 2. STA (SAFETY TASK ASSIGNMENT)
    "sta_prod_chimiques": False,
    "sta_prod_chimiques_nom": "",
    
    "sta_meuleuse": False,
    "meuleuse_diametre": "125 mm", "meuleuse_operateurs": ["Léa DUSEK"], "meuleuse_marque": "Bosch Pro", "meuleuse_alim": "Batterie 18V", "meuleuse_ref": "MEU-042", "meuleuse_vitesse": "11000",
    "meu_env_plain_pied": True, "meu_env_hauteur": False, "meu_env_confine": False, "meu_env_excavation": False, "meu_env_stable": True, "meu_env_maintien_2mains": True, "meu_env_piece_fixee": True, "meu_env_hors_ligne_tir": True, "meu_position_op": "Debout",
    "meuleuse_u_decoupe": False, "meuleuse_mat_decoupe": db_materiaux[0], "meuleuse_u_ebavurage": False, "meuleuse_mat_ebavurage": db_materiaux[0], "meuleuse_u_flap": False, "meuleuse_u_blanchiment": False, "meuleuse_disque_blanchiment": db_disques_blanchiment[0],

    "t_outils_electro": True,
    "t_meulage_poncage": False,
    "t_travaux_manuels": True,
    "t_manutention_lourde": False,
    "t_nettoyage_chantiers": True,

    # EPIs DE BASE SITE P&G
    "epi_lunettes_securite": True,
    "epi_chaussures_s3": True,
    "epi_casque_chantiers": True,
    "epi_gants_manutention": True,
    "epi_protections_auditives": False,
    "epi_casque_jugulaire_obli": False,

    # FORMULAIRES HRT (ÉTAPES 6)
    "h_pirl": False, "h_pirl_vgp": True, "h_pirl_soc": "ABYLSEN",
    "h_nacelle": False, "h_nacelle_vgp": True, "h_nacelle_checklist": True, "h_nacelle_caces": True, "h_nacelle_aut": True, "h_nacelle_harnais": True, "h_nacelle_soc": "ABYLSEN",
    "h_echaf": False, "h_echaf_montage": False, "h_echaf_montage_qualif": True, "h_echaf_montage_harnais": True, "h_echaf_util": False, "h_echaf_util_qualif": True, "h_echaf_ctrl_regle": True, "h_echaf_certif_affiche": True, "h_echaf_verif_j": True, "h_echaf_soc_util": "ABYLSEN",
    "toiture_protection": "Garde-corps", "toiture_valideur": "Matthieu MARTIN (Habilité ePDP Accès Toiture)",
    "chaud_gants_soudeur": False, "chaud_gants_chaleur": False, "chaud_gants_anticoupure": True, "chaud_extincteur1": "Eau + additifs", "chaud_extincteur2": "CO2", "chaud_degage_10m": True, "chaud_baches": False, "chaud_traverse_mur": False, "chaud_vigie_opposee": False, "chaud_ouverture_10m": False, "chaud_obstruction": False, "chaud_vigie_autre_cote": False, "chaud_vigie_nom": "Matthieu MARTIN", "chaud_personne_surv_60m": "Léa DUSEK", "chaud_heure_fin": "15:00", "chaud_heure_depart": "16:00", "chaud_commentaires": "",
    "excav_plans_eaux_indus": True, "excav_plans_eaux_usees": True, "excav_plans_eaux_pluv": True, "excav_plans_eaux_incendie": True, "excav_plans_ht": True, "excav_plans_bt": True, "excav_plans_gaz": True, "excav_struct_proximite": False, "excav_architecte": False, "excav_dict": True, "excav_effondrement": False, "excav_eau_pompe": False, "excav_balisage": True, "excav_vehicule_3m": True, "excav_deblais": True, "excav_acces": "Escalier / Rampe", "excav_profondeur_130": False, "excav_blindage": False, "excav_schema_commentaires": "", "excav_chef_manoeuvre": "Léa DUSEK", "excav_do": "Matthieu MARTIN", "excav_casque_rouge": "Alexandre LEFEBVRE",
    "grut_desc_mop": "Levage groupe froid rooftop", "grut_poids_charge": 2500.0, "grut_poids_acc": 200.0, "grut_unite": "kg", "grut_immat": "GRUE-AMIENS-88", "grut_fleche": 35.0, "grut_portee": 20.0, "grut_pression_patin": "12 T/m²", "grut_rayon": 15.0, "grut_balisage": True, "grut_plan_vue": True, "grut_plan_elev": True, "grut_obstacles": True, "grut_anemometre": True, "grut_vent_val": 18.0, "grut_vent_unite": "km/h", "grut_pesage": True, "grut_centre_gravite": True, "grut_angles_elingue": True, "grut_plaques_rep": True, "grut_chef_m_nom": "Léa DUSEK", "grut_chef_m_soc": "ABYLSEN", "grut_elingueur_nom": "Matthieu MARTIN", "grut_elingueur_soc": "ABYLSEN", "grut_grutier_nom": "Jean LEVAGE", "grut_grutier_soc": "APAVE", "grut_certif_grue": True, "grut_certif_acc": True, "grut_certif_plaques": True, "grut_check_j_grue": True, "grut_check_j_acc": True, "grut_pattes_concu": True, "grut_pattes_defaut": False, "grut_pattes_adequation": True, "grut_charges_annexes": True, "grut_schema_commentaires": "", "grut_do_sign": "Matthieu MARTIN", "grut_casque_rouge_sign": "Alexandre LEFEBVRE",
    "conf_lieu": "Cuve C-102 Ligne 3", "conf_r_atmo": True, "conf_r_chimique": False, "conf_r_inflam": False, "conf_r_orga": False, "conf_r_meca": False, "conf_r_thermiq": False, "conf_r_bruit": False, "conf_troudhomme_610": True, "conf_catec": True, "conf_hauteur": False, "conf_m20": True, "conf_secouriste": "Attribution automatique suivant la localisation", "conf_medical": "Attribution automatique suivant la localisation", "conf_action_chaud": False, "conf_ventilation_nat": True, "conf_ventilation_forcee": True, "conf_ventilation_debit": "Minimum 56m3/h par personne", "conf_consignation_gaz": True, "conf_cuve_vide": True, "conf_vol_caches": False, "conf_eclairage_24v": True, "conf_blocage_ouvert": True, "conf_echaf_echelle": False, "conf_prod_chim": False, "conf_laser": False, "conf_comm_type": "Talkie Walkie", "conf_o2": 20.9, "conf_o2_contre_mesure": 20.9, "conf_h2s_check": False, "conf_h2s": 0.0, "conf_co_check": False, "conf_co": 0.0, "conf_explo_check": False, "conf_explo": 0.0, "conf_temp_cuve": 22.0, "conf_verif_temp": "N2", "conf_inflam_lel": 0.0, "conf_verif_lel": "N2", "conf_schema_commentaires": "", "conf_entrant": "Léa DUSEK", "conf_standby": "Matthieu MARTIN", "conf_do": "Alexandre LEFEBVRE",
    "elec_modife": False, "elec_armoire": True, "elec_voisinage_tension": True, "elec_courant_faible": False, "elec_releve": True, "elec_chemins": False, "elec_voisinage_nues": False, "elec_valideur_ei": "E&I / PT E&I (B2, H2, BC, HC)",
    "loto_ouverture_methode": "2 vannes et vanne de drain", "loto_ouvert_loc1": "Vanne V-101 Amont", "loto_ouvert_loc2": "Vanne V-102 Aval / Drain D-01", "loto_is_elec": True, "loto_is_elec_loc1": "TGBT-M1-Armoire 4", "loto_is_elec_loc2": "Cadenas LOTO #884", "loto_fusible": False, "loto_fusible_loc1": "", "loto_fusible_loc2": "", "loto_cable": False, "loto_cable_loc1": "", "loto_cable_loc2": "", "loto_pneu": False, "loto_pneu_loc1": "", "loto_pneu_loc2": "", "loto_hydra": False, "loto_hydra_loc1": "", "loto_hydra_loc2": "", "loto_residu": True, "loto_residu_loc1": "Purge pression résiduelle", "loto_residu_loc2": "Manomètre à 0 bar", "loto_drain_ouvert": True, "loto_eq_ouvert": True, "loto_eq_lave": True, "loto_eq_sanitise": True,
    "sr_chimique_c1": False, "sr_chimique_nom": "", "sr_fluide_dang": False, "sr_fluide_nom": "", "sr_atex": False, "sr_atex_nom": "", "sr_balisage": True, "sr_douche_rince": True, "sr_ramonage": False, "sr_ramonage_dt": "01/10/2026 08:00", "sr_isolement": True, "sr_feuille_loto": True, "sr_zonage_atex": True, "sr_epi_ecran": True, "sr_epi_lunettes": False, "sr_epi_gants_chim": True, "sr_epi_comb1": False, "sr_epi_comb2": True, "sr_epi_bottes": True, "sr_epi_cartouche": True, "sr_epi_ari": False, "sr_epi_3m6000": False, "sr_epi_versaflo": False, "sr_epi_no_versaflo": True, "sr_auxiliaire_equipe": True, "sr_comm_moyen": "Talkie-Walkie ATEX", "sr_inspect_remise": True, "sr_inspect_nom": "Léa DUSEK", "sr_inspect_dt": "01/10/2026 17:00", "sr_schema_commentaires": "", "sr_sign_intervenant": "Léa DUSEK", "sr_sign_do": "Matthieu MARTIN", "sr_sign_operations": "Alexandre LEFEBVRE"
}

if "form_data" not in st.session_state:
    st.session_state.form_data = dict(VALEURS_PAR_DEFAUT)
else:
    for k, v in VALEURS_PAR_DEFAUT.items():
        if k not in st.session_state.form_data:
            st.session_state.form_data[k] = v

def get_val(key, default=None):
    if default is None:
        default = VALEURS_PAR_DEFAUT.get(key, False)
    return st.session_state.form_data.get(key, default)

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

    if permis.get('statut') == 'VALIDÉ':
        pdf.set_fill_color(220, 252, 231); pdf.set_draw_color(34, 197, 94); pdf.set_text_color(22, 101, 52)
        status_str = "PERMIS VALIDE & AUDITABLE SUR COMPTE ePDP"
    else:
        pdf.set_fill_color(254, 240, 138); pdf.set_draw_color(234, 179, 8); pdf.set_text_color(133, 77, 14)
        status_str = "PERMIS EN ATTENTE DE VALIDATION BATCH (07h30)"

    pdf.rect(10, 38, 190, 10, 'DF')
    pdf.set_font("Helvetica", "B", 11)
    pdf.text(15, 44.5, sanitize_text(status_str))
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

    elif st.session_state.kiosk_mode == "PDP":
        if st.button("⬅️ Retour à l'accueil"): st.session_state.kiosk_mode = "HOME"; st.rerun()
        st.subheader("📝 Émargement d'un Plan de Prévention (PDP)")
        st.divider()
        soc_pdp = st.selectbox("1. Sélectionnez votre Entreprise Extérieure (EE) :", db_societes)
        pdp_sel = st.selectbox(f"2. Plans de Prévention enregistrés pour {soc_pdp} :", db_pdps.get(soc_pdp, ["Aucun PDP"]))
        nom_pdp = st.text_input("Nom & Prénom de l'intervenant :")
        statut_pdp = st.selectbox("Statut sur le chantier :", ["N1 (Compagnon)", "N2 (Responsable)"])
        
        tel_pdp = ""
        if statut_pdp == "N2 (Responsable)":
            tel_pdp = st.text_input("Numéro de téléphone portable (Obligatoire pour le Responsable N2) :", placeholder="ex: 06 12 34 56 78")

        st.info(" [ Zone de Signature Tactile / Empreinte Stylet ] ")
        if st.button("✅ VALIDER L'ÉMARGEMENT DU PDP", type="primary", use_container_width=True):
            if statut_pdp == "N2 (Responsable)" and not tel_pdp.strip():
                st.error("⚠️ Veuillez renseigner votre numéro de téléphone avant de valider.")
            else:
                st.balloons(); st.success(f"Émargement validé pour {nom_pdp} ({statut_pdp}) !"); st.session_state.kiosk_mode = "HOME"

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
                st.session_state.form_data["societe"] = st.selectbox("Entreprise Extérieure (EE) :", db_societes, index=db_societes.index(get_val("societe", "ABYLSEN")) if get_val("societe") in db_societes else 0)

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button("⬅️ Accueil"): st.session_state.kiosk_mode = "HOME"; st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"): st.session_state.step = 2; st.rerun()

        elif current_step == 2:
            st.subheader("2. Plan de Prévention, Mode Opératoire & Règle de Sous-Traitance")
            p_list = db_pdps.get(get_val("societe"), ["PDP Standard"])
            st.session_state.form_data["pdp"] = st.selectbox("Plan de Prévention (PDP) rattaché :", p_list, index=p_list.index(get_val("pdp")) if get_val("pdp") in p_list else 0)
            
            m_obj_list = db_mops.get(get_val("pdp"), [{"titre": "MoP Standard", "st": False}])
            m_titles = [m["titre"] for m in m_obj_list]
            selected_mop_title = st.selectbox("Mode Opératoire (MoP) :", m_titles, index=m_titles.index(get_val("mop")) if get_val("mop") in m_titles else 0)
            st.session_state.form_data["mop"] = selected_mop_title
            
            mop_info = next((m for m in m_obj_list if m["titre"] == selected_mop_title), {"st": False})
            st.session_state.form_data["is_subcontractor"] = mop_info.get("st", False)

            if get_val("is_subcontractor"):
                st.warning(f"⚠️ **SOUS-TRAITANCE CONNU GRÂCE AU PDP ET MOP :** L'entreprise sélectionnée est en sous-traitance pour **{mop_info.get('titulaire', 'ABYLSEN')}**.")
                st.session_state.form_data["titulaire_n2"] = st.text_input("Nom & Prénom du N2 de la société principale (qui devra également valider et signer le permis à la fin) :", value=get_val("titulaire_n2", mop_info.get('titulaire', 'ABYLSEN') + " - Représentant N2"))
            else:
                st.success("✅ Intervention directe par la société titulaire du PDP.")

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button("⬅️ Précédent"): st.session_state.step = 1; st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"): st.session_state.step = 3; st.rerun()

        elif current_step == 3:
            st.subheader("3. Responsable N2 Présent sur le Chantier")
            st.session_state.form_data["n2_nom"] = st.selectbox("Responsable N2 qualifié sur site :", db_n2, index=db_n2.index(get_val("n2_nom")) if get_val("n2_nom") in db_n2 else 0)
            c_back, c_next = st.columns(2)
            with c_back:
                if st.button("⬅️ Précédent"): st.session_state.step = 2; st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"): st.session_state.step = 4; st.rerun()

        elif current_step == 4:
            st.subheader("4. Localisation & NUMÉROS DE TÉLÉPHONE D'URGENCE DU SITE")
            
            st.markdown("""
            <div class='urgence-card'>
                📞 <b>NUMÉROS DE TÉLÉPHONE D'URGENCE DU SITE P&G AMIENS :</b><br>
                • <b>Poste de Garde :</b> 03.22.54.32.00<br>
                • <b>Infirmerie :</b> 03.22.54.30.00 ou 06.75.16.05.54<br>
                • <b>Incendie / Environnement :</b> 03.22.54.33.33
            </div>
            """, unsafe_allow_html=True)

            zones_keys = list(db_zones_carto.keys())
            st.session_state.form_data["lieu_pdp"] = st.selectbox("Zone du Chantier :", zones_keys, index=zones_keys.index(get_val("lieu_pdp")) if get_val("lieu_pdp") in zones_keys else 0)
            st.session_state.form_data["lieu_precision"] = st.text_input("Précision d'emplacement (Local, Bureau, Ligne) :", value=get_val("lieu_precision"))
            st.session_state.form_data["description"] = st.text_input("Description détaillée de la tâche :", value=get_val("description"))

            carto = db_zones_carto.get(get_val("lieu_pdp"), {})
            st.warning(f"📍 **Secours Secteur :** PR: `{carto.get('pr')}` | Confinement: `{carto.get('confinement')}`")

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button("⬅️ Précédent"): st.session_state.step = 3; st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"): st.session_state.step = 5; st.rerun()

        # ==============================================================================
        # ÉTAPE 5 : RESTRUCTURÉE (1. RISQUES PRINCIPAUX -> 2. STA -> 3. EPIS)
        # ==============================================================================
        elif current_step == 5:
            st.subheader("5. Liste des Risques Principaux, STA (Safety Task Assignment) & EPIs")

            # ------------------------------------------------------------------
            # 1. LISTE DES RISQUES PRINCIPAUX (EN PREMIER)
            # ------------------------------------------------------------------
            st.error("🚨 **1. LISTE DES RISQUES PRINCIPAUX (Déclenchant un Permis Spécifique HRT à l'Étape 6) :**")
            
            cr1, cr2 = st.columns(2)
            with cr1:
                st.session_state.form_data["p_hauteur"] = st.checkbox("Travail en hauteur", value=get_val("p_hauteur"))
                st.session_state.form_data["p_toiture"] = st.checkbox("Accès toiture", value=get_val("p_toiture"))
                st.session_state.form_data["p_points_chauds"] = st.checkbox("Génération de points chauds", value=get_val("p_points_chauds"))
                st.session_state.form_data["p_excavation"] = st.checkbox("Tranchée, BTP, ouverture de sol", value=get_val("p_excavation"))
                st.session_state.form_data["p_grutage"] = st.checkbox("Grutage", value=get_val("p_grutage"))
                st.session_state.form_data["p_confine"] = st.checkbox("Espace confiné, risque asphyxie, anoxie (Azote)", value=get_val("p_confine"))

            with cr2:
                st.session_state.form_data["p_electrique"] = st.checkbox("Travail électrique", value=get_val("p_electrique"))
                st.session_state.form_data["p_ouverture_circuit"] = st.checkbox("Ouverture de circuit sous pression (vapeur, air, gaz, fluides chimiques)", value=get_val("p_ouverture_circuit"))
                st.session_state.form_data["p_machines_mouvement"] = st.checkbox("Machines en mouvement, parties mobiles, risque mécaniques", value=get_val("p_machines_mouvement"))
                st.session_state.form_data["p_equipement_pression"] = st.checkbox("Équipement sous pression", value=get_val("p_equipement_pression"))
                st.session_state.form_data["p_laser_classe_iv"] = st.checkbox("Travaux à proximité de Lasers Classe IV", value=get_val("p_laser_classe_iv"))
                st.session_state.form_data["p_demolition"] = st.checkbox("Démolition", value=get_val("p_demolition"))

            # Synchronisation automatique avec la logique Consignation LOTO (3 phases)
            if get_val("p_ouverture_circuit") or get_val("p_machines_mouvement") or get_val("p_equipement_pression") or get_val("p_laser_classe_iv"):
                st.session_state.form_data["p_consignation"] = True
            else:
                st.session_state.form_data["p_consignation"] = False

            # Répercussion conditionnelle Démolition -> Consultation DTA
            if get_val("p_demolition"):
                st.warning("🧱 **Condition Activée (Démolition) :**")
                st.session_state.form_data["dta_consultation"] = st.checkbox("Consultation DTA (Dossier Technique Amiante) effectuée et validée", value=get_val("dta_consultation"))

            st.divider()

            # ------------------------------------------------------------------
            # 2. STA (SAFETY TASK ASSIGNMENT)
            # ------------------------------------------------------------------
            st.write("##### 🛠️ 2. STA (Safety Task Assignment) & Caractérisation des Outils :")

            # STA 1: Produits chimiques
            st.session_state.form_data["sta_prod_chimiques"] = st.checkbox("Produits chimiques utilisés ou manipulés lors de l'intervention", value=get_val("sta_prod_chimiques"))
            if get_val("sta_prod_chimiques"):
                st.session_state.form_data["sta_prod_chimiques_nom"] = st.text_input("Veuillez indiquer le(s) produit(s) chimique(s) concerné(s) :", value=get_val("sta_prod_chimiques_nom"), placeholder="ex: Solvant, Acide Chlorhydrique, Soude...")
                st.session_state.form_data["p_systeme_risque"] = True
                st.info("☣ **Répercussion :** L'utilisation de produits chimiques déclenche l'ouverture du permis Systèmes à Risques.")

            # STA 2: Meuleuse / Tronçonneuse
            st.session_state.form_data["sta_meuleuse"] = st.checkbox("Utilisation d'une Meuleuse / Tronçonneuse", value=get_val("sta_meuleuse"))
            if get_val("sta_meuleuse"):
                st.session_state.form_data["p_points_chauds"] = True
                st.info("🔥 **Répercussion :** L'utilisation de la meuleuse déclenche automatiquement l'ouverture du Permis Point Chaud.")
                
                with st.expander("⚙️ Détails et Caractéristiques Complètes de la Meuleuse / Tronçonneuse", expanded=True):
                    c_m1, c_m2 = st.columns(2)
                    with c_m1:
                        st.session_state.form_data["meuleuse_diametre"] = st.selectbox("Diamètre du disque :", ["125 mm", "230 mm"], index=0 if get_val("meuleuse_diametre") == "125 mm" else 1)
                        st.session_state.form_data["meuleuse_marque"] = st.text_input("Marque et Modèle :", value=get_val("meuleuse_marque"))
                    with c_m2:
                        st.session_state.form_data["meuleuse_alim"] = st.selectbox("Alimentation :", ["Batterie 18V", "Filaire 230V", "Pneumatique"], index=0)
                        st.session_state.form_data["meuleuse_ref"] = st.text_input("Référence / N° de série :", value=get_val("meuleuse_ref"))

                    st.write("##### Opérations effectuées avec la meuleuse :")
                    cm_op1, cm_op2 = st.columns(2)
                    with cm_op1:
                        st.session_state.form_data["meuleuse_u_decoupe"] = st.checkbox("Découpe", value=get_val("meuleuse_u_decoupe"))
                        if get_val("meuleuse_u_decoupe"):
                            st.session_state.form_data["meuleuse_mat_decoupe"] = st.selectbox("Matériau découpé :", db_materiaux, index=0)
                        
                        st.session_state.form_data["meuleuse_u_ebavurage"] = st.checkbox("Ébavurage / Meulage", value=get_val("meuleuse_u_ebavurage"))
                        if get_val("meuleuse_u_ebavurage"):
                            st.session_state.form_data["meuleuse_mat_ebavurage"] = st.selectbox("Matériau ébavuré :", db_materiaux, index=0)

                    with cm_op2:
                        st.session_state.form_data["meuleuse_u_flap"] = st.checkbox("Ponçage disque à lamelles (Flap)", value=get_val("meuleuse_u_flap"))
                        st.session_state.form_data["meuleuse_u_blanchiment"] = st.checkbox("Blanchiment / Nettoyage de surface", value=get_val("meuleuse_u_blanchiment"))
                        if get_val("meuleuse_u_blanchiment"):
                            st.session_state.form_data["meuleuse_disque_blanchiment"] = st.selectbox("Type de disque blanchiment :", db_disques_blanchiment, index=0)

            # STA 3: Autres Tâches et Outils Courants
            st.write("##### Autres tâches courantes et outillages prévus :")
            ct1, ct2 = st.columns(2)
            with ct1:
                st.session_state.form_data["t_outils_electro"] = st.checkbox("Utilisation d'outils électroportatifs généraux (perceuse, visseuse...)", value=get_val("t_outils_electro"))
                st.session_state.form_data["t_meulage_poncage"] = st.checkbox("Ponçage / Meulage manuel", value=get_val("t_meulage_poncage"))
                st.session_state.form_data["t_travaux_manuels"] = st.checkbox("Travaux manuels généraux et d'outillage à main", value=get_val("t_travaux_manuels"))
            with ct2:
                st.session_state.form_data["t_manutention_lourde"] = st.checkbox("Manutention manuelle de charges ou matériel", value=get_val("t_manutention_lourde"))
                st.session_state.form_data["t_nettoyage_chantiers"] = st.checkbox("Nettoyage et rangement de zone de chantier", value=get_val("t_nettoyage_chantiers"))

            st.divider()

            # ------------------------------------------------------------------
            # 3. EPIS DE BASE SITE P&G
            # ------------------------------------------------------------------
            st.write("##### 🥽 3. Équipements de Protection Individuelle (EPIs de Base P&G) :")
            cepi_b1, cepi_b2 = st.columns(2)
            with cepi_b1:
                st.session_state.form_data["epi_lunettes_securite"] = st.checkbox("Lunettes de sécurité avec protections latérales (Obligatoire)", value=get_val("epi_lunettes_securite"))
                st.session_state.form_data["epi_chaussures_s3"] = st.checkbox("Chaussures de sécurité S3 (Obligatoire)", value=get_val("epi_chaussures_s3"))
                st.session_state.form_data["epi_casque_chantiers"] = st.checkbox("Casque de chantier standard", value=get_val("epi_casque_chantiers"))
            with cepi_b2:
                st.session_state.form_data["epi_gants_manutention"] = st.checkbox("Gants de manutention anti-coupure / mécaniques", value=get_val("epi_gants_manutention"))
                st.session_state.form_data["epi_protections_auditives"] = st.checkbox("Protections auditives (bouchons / casque antibruit)", value=get_val("epi_protections_auditives"))

            st.write("##### ➕ Ajustement Automatique des EPIs Spécifiques :")
            if get_val("p_hauteur") or get_val("p_toiture"):
                st.session_state.form_data["epi_casque_jugulaire_obli"] = True
                st.warning("🥽 **EPI rajouté automatiquement :** Casque avec jugulaire obligatoire.")
            else:
                st.session_state.form_data["epi_casque_jugulaire_obli"] = False

            if get_val("p_electrique"):
                st.info("🥽 **EPIs de base Électrique rajoutés :** Casque d'électricien, Gants isolants électriques (EN 60903) + Surgants cuir + Vêtements 100% coton/ignifugés.")

            if get_val("p_points_chauds"):
                st.info("🥽 **EPIs de base Point Chaud rajoutés :** Écran facial EN166B ou cagoule de soudure + Gants ignifugés + Vêtements ignifugés.")

            if get_val("p_confine"):
                st.info("🥽 **EPI Espace Confiné rajouté :** Masque auto-sauveteur (type M20).")

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button("⬅️ Précédent"): st.session_state.step = 4; st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"): st.session_state.step = 6; st.rerun()

        # ==============================================================================
        # ÉTAPE 6 : FORMULAIRES SPÉCIFIQUES (HRT)
        # ==============================================================================
        elif current_step == 6:
            st.subheader("6. Ouverture des Permis Spécifiques")

            # 1. HAUTEUR
            if get_val("p_hauteur"):
                st.error("🧗 **PERMIS TRAVAIL EN HAUTEUR / ÉCHAFAUDAGE / NACELLE**")
                st.info("🥽 **EPI :** Casque avec jugulaire obligatoire")

                st.write("##### Cases à cocher (entre PIRL / Nacelle / Echafaudage) :")
                st.session_state.form_data["h_pirl"] = st.checkbox("SI PIRL est coché", value=get_val("h_pirl"))
                if get_val("h_pirl"):
                    cp1, cp2 = st.columns(2)
                    with cp1: st.session_state.form_data["h_pirl_vgp"] = st.checkbox("VGP + contrôle visuel avant utilisation", value=get_val("h_pirl_vgp"))
                    with cp2: st.session_state.form_data["h_pirl_soc"] = st.text_input("Identification par le nom de la société :", value=get_val("h_pirl_soc"))

                st.session_state.form_data["h_nacelle"] = st.checkbox("Si Nacelle est coché", value=get_val("h_nacelle"))
                if get_val("h_nacelle"):
                    st.warning("🥽 **EPI = Harnais + longe**")
                    cn1, cn2 = st.columns(2)
                    with cn1:
                        st.session_state.form_data["h_nacelle_vgp"] = st.checkbox("VGP + Check list journalière", value=get_val("h_nacelle_vgp"))
                        st.session_state.form_data["h_nacelle_caces"] = st.checkbox("CACES pour utilisateur et vigie", value=get_val("h_nacelle_caces"))
                        st.session_state.form_data["h_nacelle_aut"] = st.checkbox("Autorisation de conduite", value=get_val("h_nacelle_aut"))
                    with cn2:
                        st.session_state.form_data["h_nacelle_harnais"] = st.checkbox("Qualification pour le travail en hauteur (port du harnais)", value=get_val("h_nacelle_harnais"))
                        st.session_state.form_data["h_nacelle_soc"] = st.text_input("Identification par le nom de la société (Nacelle) :", value=get_val("h_nacelle_soc"))

                st.session_state.form_data["h_echaf"] = st.checkbox("Si Echafaudage est coché", value=get_val("h_echaf"))
                if get_val("h_echaf"):
                    st.write("Cases à cocher pour Échafaudage :")
                    ce1, ce2 = st.columns(2)
                    with ce1:
                        st.session_state.form_data["h_echaf_montage"] = st.checkbox("Montage / Démontage / Modification", value=get_val("h_echaf_montage"))
                        if get_val("h_echaf_montage"):
                            st.checkbox("Qualification de montage d'échafaudage", value=True)
                            st.checkbox("Qualification pour le travail en hauteur (port du harnais)", value=True)
                            st.error("🥽 **EPI = Harnais + double longe + Connecteurs + absorbeurs ou stop chute + gants**")

                    with ce2:
                        st.session_state.form_data["h_echaf_util"] = st.checkbox("Utilisation", value=get_val("h_echaf_util"))
                        if get_val("h_echaf_util"):
                            st.checkbox("Qualification d'utilisation et d'inspection d'échafaudage", value=True)

                    st.session_state.form_data["h_echaf_ctrl_regle"] = st.checkbox("Contrôle périodique réglementaire", value=get_val("h_echaf_ctrl_regle"))
                    st.session_state.form_data["h_echaf_certif_affiche"] = st.checkbox("Certificat de montage affiché", value=get_val("h_echaf_certif_affiche"))
                    st.session_state.form_data["h_echaf_verif_j"] = st.checkbox("Vérification journalière par société", value=get_val("h_echaf_verif_j"))
                    st.session_state.form_data["h_echaf_soc_util"] = st.text_input("Identification de la société utilisatrice :", value=get_val("h_echaf_soc_util"))
                st.divider()

            # 2. TOITURE
            if get_val("p_toiture"):
                st.error("🏢 **PERMIS ACCÈS TOITURE**")
                st.info("🥽 **EPI = Casque avec jugulaire obligatoire**")
                st.info(f"📍 **Encart localisation de la toiture (lieu gardé en mémoire) :** `{get_val('lieu_pdp')}` ({get_val('lieu_precision')})")

                opts_protect = ["Garde-corps", "Ligne de vie / Point d'ancrage", "Pas de protection collective fixe"]
                st.session_state.form_data["toiture_protection"] = st.selectbox(
                    "Identifier les moyens de protection de la zone (ex : garde-corps) :",
                    opts_protect, index=opts_protect.index(get_val("toiture_protection")) if get_val("toiture_protection") in opts_protect else 0
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
                    st.session_state.form_data["toiture_valideur"] = st.text_input("Validation de l'accès toiture par une personne habilité à signer les accès toiture (Attribution dans le profil ePDP) :", value=get_val("toiture_valideur"))
                st.divider()

            # 3. POINT CHAUD
            if get_val("p_points_chauds"):
                st.warning("🔥 **PERMIS POINT CHAUD**")
                st.info("🥽 **EPI de base =** Ecran facial contre les projections chaudes (EN166B) ou cagoule si soudures + Vêtement ignifugés")
                
                st.write("##### Possibilité de choisir entre les différents gants (mais au moins 1 obligatoire) :")
                cg1, cg2, cg3 = st.columns(3)
                with cg1: st.session_state.form_data["chaud_gants_soudeur"] = st.checkbox("Gants soudeur", value=get_val("chaud_gants_soudeur"))
                with cg2: st.session_state.form_data["chaud_gants_chaleur"] = st.checkbox("Gants résistant à la chaleur", value=get_val("chaud_gants_chaleur"))
                with cg3: st.session_state.form_data["chaud_gants_anticoupure"] = st.checkbox("Gants anti coupure (suivant l'outil qui génère le point chaud)", value=get_val("chaud_gants_anticoupure"))

                carto = db_zones_carto.get(get_val("lieu_pdp"), {})
                st.write("##### Détection des moyens de lutte contre l'incendie de la zone (Automatique suivant localisation de l'intervention) :")
                st.write(f"- Présence de sprinklers en fonctionnement ? **{'OUI' if carto.get('sprinkler') else 'NON'}**")
                if not carto.get('sprinkler'):
                    st.error("🚨 **si NON :** Surveillance par P&G de 60minutes supplémentaire après la surveillance de l'EE : clôture du permis quand l'heure de surveillance est passée + commentaire")

                st.write(f"- Présence de détection de fumée ? **{'OUI' if carto.get('detection') else 'NON'}**")
                if not carto.get('detection'):
                    st.error("🚨 **si NON :** Surveillance par P&G de 60minutes supplémentaire après la surveillance de l'EE")

                st.write("##### Quels sont les types de vos 2 extincteurs présents sur la zone ?")
                opts_ext = ["Poudre ABC", "Eau + additifs", "CO2"]
                cext1, cext2 = st.columns(2)
                with cext1: st.session_state.form_data["chaud_extincteur1"] = st.selectbox("1er extincteur :", opts_ext, index=opts_ext.index(get_val("chaud_extincteur1")) if get_val("chaud_extincteur1") in opts_ext else 0)
                with cext2: st.session_state.form_data["chaud_extincteur2"] = st.selectbox("2ème extincteur :", opts_ext, index=opts_ext.index(get_val("chaud_extincteur2")) if get_val("chaud_extincteur2") in opts_ext else 1)

                st.session_state.form_data["chaud_degage_10m"] = st.checkbox("La zone est dégagée de tous matériaux combustibles sur un rayon de 10m", value=get_val("chaud_degage_10m"))
                if not get_val("chaud_degage_10m"):
                    st.error("🔒 **si NON = installation de bâches ignifugées**")

                st.session_state.form_data["chaud_traverse_mur"] = st.checkbox("Les travaux traversent ils une paroi ou un mur ?", value=get_val("chaud_traverse_mur"))
                if get_val("chaud_traverse_mur"):
                    st.error("🔒 **si OUI = vigie en place de l'autre côté du mur**")

                st.session_state.form_data["chaud_ouverture_10m"] = st.checkbox("Les travaux se trouvent ils à moins de 10m d'une ouverture ou de planchers ?", value=get_val("chaud_ouverture_10m"))
                if get_val("chaud_ouverture_10m"):
                    st.write("Si OUI :")
                    st.session_state.form_data["chaud_obstruction"] = st.checkbox("Obstruction des ouvertures", value=True)
                    st.session_state.form_data["chaud_vigie_autre_cote"] = st.checkbox("OU Vigie de l'autre côté", value=False)

                st.write("##### Vigie du point chaud :")
                interv_list = get_val("intervenants", ["Léa DUSEK"])
                st.session_state.form_data["chaud_vigie_nom"] = st.selectbox("Désignation d'un intervenant parmi ceux qui ont signé le mode opératoire en vigie du travail :", interv_list, index=interv_list.index(get_val("chaud_vigie_nom")) if get_val("chaud_vigie_nom") in interv_list else 0)
                st.session_state.form_data["chaud_personne_surv_60m"] = st.selectbox("Personne réalisant la surveillance 60minutes après le travail :", interv_list, index=interv_list.index(get_val("chaud_personne_surv_60m")) if get_val("chaud_personne_surv_60m") in interv_list else 0)

                chf1, chf2 = st.columns(2)
                with chf1: st.session_state.form_data["chaud_heure_fin"] = st.text_input("Heure de fin des travaux à chaud :", value=get_val("chaud_heure_fin"))
                with chf2: st.session_state.form_data["chaud_heure_depart"] = st.text_input("Heure de départ (clôture du permis quand l'heure de surveillance est passée) :", value=get_val("chaud_heure_depart"))
                st.session_state.form_data["chaud_commentaires"] = st.text_area("Commentaire obligatoire pour clôture :", value=get_val("chaud_commentaires"))
                st.divider()

            # 4. EXCAVATION
            if get_val("p_excavation"):
                st.warning("🚜 **PERMIS EXCAVATION**")
                
                st.write("##### Risques liés aux réseaux souterrains — Connaissance des plans (case à cocher 'Oui' ou 'Non') :")
                cx1, cx2, cx3, cx4 = st.columns(4)
                with cx1:
                    st.session_state.form_data["excav_plans_eaux_indus"] = st.checkbox("Eaux industrielle et potable", value=get_val("excav_plans_eaux_indus"))
                    st.session_state.form_data["excav_plans_eaux_usees"] = st.checkbox("Eaux usées", value=get_val("excav_plans_eaux_usees"))
                with cx2:
                    st.session_state.form_data["excav_plans_eaux_pluv"] = st.checkbox("Eaux pluviales", value=get_val("excav_plans_eaux_pluv"))
                    st.session_state.form_data["excav_plans_eaux_incendie"] = st.checkbox("Eaux incendie", value=get_val("excav_plans_eaux_incendie"))
                with cx3:
                    st.session_state.form_data["excav_plans_ht"] = st.checkbox("Haute tension", value=get_val("excav_plans_ht"))
                    st.session_state.form_data["excav_plans_bt"] = st.checkbox("Basse tension", value=get_val("excav_plans_bt"))
                with cx4:
                    st.session_state.form_data["excav_plans_gaz"] = st.checkbox("Gaz", value=get_val("excav_plans_gaz"))

                st.write("##### Risques liés à l'environnement :")
                ceenv1, ceenv2, ceenv3 = st.columns(3)
                with ceenv1: st.session_state.form_data["excav_struct_proximite"] = st.checkbox("Proximité d'éléments structurels (rack, fondation…)", value=get_val("excav_struct_proximite"))
                with ceenv2: st.session_state.form_data["excav_architecte"] = st.checkbox("Architecte consulté", value=get_val("excav_architecte"))
                with ceenv3: st.session_state.form_data["excav_dict"] = st.checkbox("DICT émise", value=get_val("excav_dict"))

                st.write("##### Risques liés à l'effondrement (case à cocher 'Oui' ou 'Non') :")
                ceeff1, ceeff2 = st.columns(2)
                with ceeff1:
                    st.session_state.form_data["excav_eau_pompe"] = st.checkbox("Présence d'eau, utilisation d'une pompe de relevage", value=get_val("excav_eau_pompe"))
                    st.session_state.form_data["excav_balisage"] = st.checkbox("Balisage et dégagement de la zone", value=get_val("excav_balisage"))
                with ceeff2:
                    st.session_state.form_data["excav_vehicule_3m"] = st.checkbox("Placement des véhicules à plus de 3 mètres", value=get_val("excav_vehicule_3m"))
                    st.session_state.form_data["excav_deblais"] = st.checkbox("Dépose des déblais identifiées et communiquées", value=get_val("excav_deblais"))

                st.write("##### Moyens d'accès à la tranchée :")
                opts_acces = ["Escalier / Rampe", "Échelle", "Passerelle"]
                st.session_state.form_data["excav_acces"] = st.selectbox("Si oui : Liste déroulante avec choix obligatoire :", opts_acces, index=opts_acces.index(get_val("excav_acces")) if get_val("excav_acces") in opts_acces else 0)
                if get_val("excav_acces") == "Échelle":
                    st.error("🚨 **Si échelle -> dérogation casque rouge**")

                st.session_state.form_data["excav_profondeur_130"] = st.checkbox("Profondeur de la tranchée > 1,30m", value=get_val("excav_profondeur_130"))
                if get_val("excav_profondeur_130"):
                    st.error("🔒 **Si oui : Blindage obligatoire**")

                st.session_state.form_data["excav_schema_commentaires"] = st.text_area("Champs libre pour faire schéma de l'excavation ou commentaires :", value=get_val("excav_schema_commentaires"))

                st.write("##### 3 signatures obligatoires :")
                st.session_state.form_data["excav_chef_manoeuvre"] = st.text_input("• Chef de manœuvre de la société extérieure :", value=get_val("excav_chef_manoeuvre"))
                st.session_state.form_data["excav_do"] = st.text_input("• Le donneur d'ordre (après celle-ci début d'installation autorisé) :", value=get_val("excav_do"))
                st.session_state.form_data["excav_casque_rouge"] = st.text_input("• Le casque rouge (obligatoire pour commencer l'intervention) :", value=get_val("excav_casque_rouge"))
                st.divider()

            # 5. GRUTAGE
            if get_val("p_grutage"):
                st.info("🏗️ **PERMIS GRUTAGE**")
                
                st.write("##### Description du matériel et de la charge :")
                st.write("*Charges maximale à gruter :*")
                st.session_state.form_data["grut_desc_mop"] = st.text_area("Description de la charge (MOP) ou texte libre :", value=get_val("grut_desc_mop"))
                
                cg1, cg2 = st.columns(2)
                with cg1: st.session_state.form_data["grut_poids_charge"] = st.number_input("Poids de la charge (Encart numérique) :", value=float(get_val("grut_poids_charge")))
                opts_unite = ["kg", "T"]
                with cg2: st.session_state.form_data["grut_unite"] = st.selectbox("Choix de l'unité :", opts_unite, index=opts_unite.index(get_val("grut_unite")) if get_val("grut_unite") in opts_unite else 0)

                st.session_state.form_data["grut_poids_acc"] = st.number_input(f"Poids des accessoires (Encart numérique dans la même unité : {get_val('grut_unite')}) :", value=float(get_val("grut_poids_acc")))
                poids_tot = get_val("grut_poids_charge") + get_val("grut_poids_acc")
                st.write(f"⚖️ **Poids total = Poids de la charge + Poids des accessoires :** `{poids_tot} {get_val('grut_unite')}`")

                st.write("*Matériels :*")
                cmat1, cmat2, cmat3 = st.columns(3)
                with cmat1: st.session_state.form_data["grut_immat"] = st.text_input("Identification de la grue (immatriculation) = texte libre :", value=get_val("grut_immat"))
                with cmat2: st.session_state.form_data["grut_fleche"] = st.number_input("Hauteur de flèche à la charge maximale (m) :", value=float(get_val("grut_fleche")))
                with cmat3: st.session_state.form_data["grut_portee"] = st.number_input("Portée maximale pour la charge maximale (m) :", value=float(get_val("grut_portee")))

                cmat4, cmat5 = st.columns(2)
                with cmat4: st.session_state.form_data["grut_pression_patin"] = st.text_input("Pression maximale sur patin :", value=get_val("grut_pression_patin"))
                with cmat5: st.session_state.form_data["grut_rayon"] = st.number_input("Rayon de grutage :", value=float(get_val("grut_rayon")))

                st.write("##### Organisation du levage (cases à cocher 'Oui' ou 'Non') :")
                st.session_state.form_data["grut_balisage"] = st.checkbox("Balisage de la zone conforme au plan de grutage", value=get_val("grut_balisage"))
                st.session_state.form_data["grut_plan_vue"] = st.checkbox("Plan de grutage vue en plan avec zone de survol interdite (MOP)", value=get_val("grut_plan_vue"))
                st.session_state.form_data["grut_plan_elev"] = st.checkbox("Plan de grutage en élévation (MOP)", value=get_val("grut_plan_elev"))
                st.session_state.form_data["grut_obstacles"] = st.checkbox("Identification des obstacles ou lignes électriques conforme au plan de grutage", value=get_val("grut_obstacles"))

                st.write("##### Anémomètre & Vitesse du vent :")
                st.session_state.form_data["grut_anemometre"] = st.checkbox("Anémomètre en bout de flèche", value=get_val("grut_anemometre"))
                cv1, cv2 = st.columns(2)
                opts_vent_u = ["km/h", "m/S"]
                with cv1: st.session_state.form_data["grut_vent_val"] = st.number_input("Vérification via grutier/anémomètre = encart numérique :", value=float(get_val("grut_vent_val")))
                with cv2: st.session_state.form_data["grut_vent_unite"] = st.selectbox("Sélection de l'unité :", opts_vent_u, index=opts_vent_u.index(get_val("grut_vent_unite")) if get_val("grut_vent_unite") in opts_vent_u else 0)

                if (get_val("grut_vent_unite") == "km/h" and get_val("grut_vent_val") > 36) or (get_val("grut_vent_unite") == "m/S" and get_val("grut_vent_val") > 10):
                    st.error("❌ **Indication par météo + Alerte suivant les seuils + Blocage de l'intervention si >36km/h (peut bloquer le remplissage du permis dès son ouverture avec motif renseigné)**")

                st.session_state.form_data["grut_pesage"] = st.checkbox("Dispositif de mesure de charge", value=get_val("grut_pesage"))
                if get_val("grut_pesage"):
                    st.info("Si oui : Charge totale maxi < 90% charge de la grue")
                else:
                    st.warning("Si non : Charge totale maxi < 80% charge de la grue")

                st.session_state.form_data["grut_centre_gravite"] = st.checkbox("Prise en compte du centre de gravité de la grue", value=get_val("grut_centre_gravite"))
                st.session_state.form_data["grut_angles_elingue"] = st.checkbox("Prise en compte des angles d'élingage au plan de grutage", value=get_val("grut_angles_elingue"))
                st.session_state.form_data["grut_plaques_rep"] = st.checkbox("Descente de charge sur plaque de répartition en ligne avec analyse de sol", value=get_val("grut_plaques_rep"))

                st.write("##### Signatures organisation levage (automatique) :")
                st.write(f"• Chef de manœuvre : `{get_val('grut_chef_m_nom')} - {get_val('grut_chef_m_soc')}`")
                st.write(f"• Élingueur : `{get_val('grut_elingueur_nom')} - {get_val('grut_elingueur_soc')}`")
                st.write(f"• Grutier : `{get_val('grut_grutier_nom')} - {get_val('grut_grutier_soc')}`")

                st.write("##### Vérification du matériel et charge :")
                st.write("*Matériel de levage (cases à cocher 'Oui' ou 'Non') :*")
                st.session_state.form_data["grut_certif_grue"] = st.checkbox(f"Certificat de conformité de la grue (ajouter automatiquement l'immatriculation renseignée en amont : {get_val('grut_immat')})", value=get_val("grut_certif_grue"))
                st.session_state.form_data["grut_certif_acc"] = st.checkbox("Certificat de conformité des accessoires de levage utilisés", value=get_val("grut_certif_acc"))
                st.session_state.form_data["grut_certif_plaques"] = st.checkbox("Certificat de conformité des plaques de répartition", value=get_val("grut_certif_plaques"))
                st.session_state.form_data["grut_check_j_grue"] = st.checkbox("Check list de vérification journalière de la grue", value=get_val("grut_check_j_grue"))
                st.session_state.form_data["grut_check_j_acc"] = st.checkbox("Check list de vérification journalière des accessoires.", value=get_val("grut_check_j_acc"))

                st.write("*Patte de levage et charge (cases à cocher 'Oui' ou 'Non') :*")
                st.session_state.form_data["grut_pattes_concu"] = st.checkbox("Pattes de fixation conçues pour le levage", value=get_val("grut_pattes_concu"))
                st.session_state.form_data["grut_pattes_defaut"] = st.checkbox("Pattes de levage exemptes de défauts", value=get_val("grut_pattes_defaut"))
                st.session_state.form_data["grut_pattes_adequation"] = st.checkbox("Adéquation pattes de levage / crochet manille", value=get_val("grut_pattes_adequation"))
                st.session_state.form_data["grut_charges_annexes"] = st.checkbox("Les charges annexes sont correctement fixées à la charge principale", value=get_val("grut_charges_annexes"))

                st.session_state.form_data["grut_schema_commentaires"] = st.text_area("Champs libre pour faire schéma de levage… ou commentaires :", value=get_val("grut_schema_commentaires"))

                st.write("##### 3 signatures obligatoires grutage :")
                st.text_input("1. Chef de manœuvre de la société extérieure :", value=get_val("grut_chef_m_nom"))
                st.session_state.form_data["grut_do_sign"] = st.text_input("2. Le donneur d'ordre (après celle-ci début d'installation autorisé) :", value=get_val("grut_do_sign"))
                st.session_state.form_data["grut_casque_rouge_sign"] = st.text_input("3. Le casque rouge (obligatoire pour commencer l'intervention) :", value=get_val("grut_casque_rouge_sign"))
                st.divider()

            # 6. ESPACE CONFINÉ
            if get_val("p_confine"):
                st.info("🦺 **PERMIS ESPACE CONFINÉ**")
                st.error("🥽 **EPI = Masque auto-sauveteur (type M20)**")

                st.session_state.form_data["conf_lieu"] = st.text_input("Lieu précis de l'entrée en espace confiné : Texte libre :", value=get_val("conf_lieu"))

                st.write("##### Risques liés à l'intervention (cases à cocher 'Oui' ou 'Non') :")
                cr1, cr2, cr3 = st.columns(3)
                with cr1:
                    st.session_state.form_data["conf_r_atmo"] = st.checkbox("Atmosphère dangereuse", value=get_val("conf_r_atmo"))
                    st.session_state.form_data["conf_r_chimique"] = st.checkbox("Substance chimique ou résidus dans la cuve", value=get_val("conf_r_chimique"))
                    st.session_state.form_data["conf_r_inflam"] = st.checkbox("Substances Inflammables/Combustibles", value=get_val("conf_r_inflam"))
                with cr2:
                    st.session_state.form_data["conf_r_orga"] = st.checkbox("Matières organiques décomposant", value=get_val("conf_r_orga"))
                    st.session_state.form_data["conf_r_meca"] = st.checkbox("Équipement mécanique en mouvement", value=get_val("conf_r_meca"))
                    st.session_state.form_data["conf_r_thermiq"] = st.checkbox("Risques thermiques/Brûlures", value=get_val("conf_r_thermiq"))
                with cr3:
                    st.session_state.form_data["conf_r_bruit"] = st.checkbox("Bruit important pouvant perturber la communication", value=get_val("conf_r_bruit"))
                    st.session_state.form_data["conf_troudhomme_610"] = st.checkbox("Trou d'homme > ou égal 610mm", value=get_val("conf_troudhomme_610"))

                if not get_val("conf_troudhomme_610"):
                    st.error("🚨 **Si 'Non' = Plan de secours spécifique**")

                st.write("##### EPI et formations 'cases à cocher 'Oui' ou 'Non' :")
                st.session_state.form_data["conf_catec"] = st.checkbox("Intervenants formés et qualifiés CATEC", value=get_val("conf_catec"))
                st.session_state.form_data["conf_hauteur"] = st.checkbox("Travail en hauteur", value=get_val("conf_hauteur"))
                st.session_state.form_data["conf_m20"] = st.checkbox("Masque auto-sauveteur (type M20)", value=get_val("conf_m20"))

                st.write("##### Check list obligatoire pour une entrée en espace confiné :")
                st.write(f"• Secouriste de la zone = `{get_val('conf_secouriste')}`")
                st.write(f"• Service médical de l'intervention = `{get_val('conf_medical')}`")

                st.session_state.form_data["conf_action_chaud"] = st.checkbox("Allez-vous couper, poncer, souder, riveter, gratter à l'intérieur de l'espace confiné ?", value=get_val("conf_action_chaud"))
                if get_val("conf_action_chaud"):
                    st.warning("⚠️ **Si oui = Renvoi au permis point chaud**")
                    st.session_state.form_data["p_points_chauds"] = True

                st.session_state.form_data["conf_ventilation_nat"] = st.checkbox("Vérification que la ventilation naturelle est suffisante et présente (48h avant) ??", value=get_val("conf_ventilation_nat"))
                st.session_state.form_data["conf_ventilation_forcee"] = st.checkbox("Allez-vous installer une ventilation forcée auxiliaire ?", value=get_val("conf_ventilation_forcee"))
                if get_val("conf_ventilation_forcee"):
                    st.info("Si oui = Minimum 56m3/h par personne")

                st.session_state.form_data["conf_consignation_gaz"] = st.checkbox("Vérification de la fermeture et de la consignation de toutes les arrivées de produits ou gaz", value=get_val("conf_consignation_gaz"))
                if get_val("conf_consignation_gaz"):
                    st.info("Renvoi au permis consignation et coche Consignation/séparation OU pose de joints pleins (PG)")
                    st.session_state.form_data["p_consignation"] = True

                st.session_state.form_data["conf_cuve_vide"] = st.checkbox("Vérifier que les cuves ou espaces sont vides pour éviter les risques de noyade", value=get_val("conf_cuve_vide"))
                st.session_state.form_data["conf_vol_caches"] = st.checkbox("Vérifier que tous les espaces sont contrôlés et qu'il n'y a pas de volumes cachés qui emprisonneraient un gaz ou un liquide.", value=get_val("conf_vol_caches"))
                st.session_state.form_data["conf_eclairage_24v"] = st.checkbox("Vérifier le niveau d'éclairage est suffisant (Eclairage 24 VOLT TBT ou autonome)", value=get_val("conf_eclairage_24v"))
                st.session_state.form_data["conf_blocage_ouvert"] = st.checkbox("Bloquer l'ouverture en position ouverte pour éviter la fermeture accidentelle", value=get_val("conf_blocage_ouvert"))

                st.session_state.form_data["conf_echaf_echelle"] = st.checkbox("Allez-vous installer un échafaudage ou une échelle dans cet espace ?", value=get_val("conf_echaf_echelle"))
                if get_val("conf_echaf_echelle"):
                    st.caption("(Contrôle d'accès et d'encombrement spécifique)")

                st.session_state.form_data["conf_prod_chim"] = st.checkbox("La zone contenait ou contient des produits chimiques ?", value=get_val("conf_prod_chim"))
                if get_val("conf_prod_chim"):
                    st.warning("⚠️ **Si oui = Vérifier les VLEP dans les FDS.**")

                st.session_state.form_data["conf_laser"] = st.checkbox("Vérifier qu'il n'y a pas d'émission Laser dans cet environnement", value=get_val("conf_laser"))
                
                opts_comm = ["Talkie Walkie", "Visuelle", "téléphone"]
                st.session_state.form_data["conf_comm_type"] = st.selectbox("La communication entre l'entrant et le stand by est efficace et fonctionnel (Case à cocher) :", opts_comm, index=opts_comm.index(get_val("conf_comm_type")) if get_val("conf_comm_type") in opts_comm else 0)

                st.write("##### Mesures à prendre :")
                co1, co2 = st.columns(2)
                with co1:
                    st.session_state.form_data["conf_o2"] = st.number_input("Niveau d'oxygène (19,5% < O2 < 23%) : encart numérique %O2 :", value=float(get_val("conf_o2")))
                    st.session_state.form_data["conf_o2_contre_mesure"] = st.number_input("+ contre-mesure à faire donc encart numérique %O2 dans la partie validation du permis avec le donneur d'ordre :", value=float(get_val("conf_o2_contre_mesure")))
                with co2:
                    st.session_state.form_data["conf_h2s_check"] = st.checkbox("Présence de H2S", value=get_val("conf_h2s_check"))
                    if get_val("conf_h2s_check"):
                        st.session_state.form_data["conf_h2s"] = st.number_input("Si 'Oui' = Encart numérique %H2S :", value=float(get_val("conf_h2s")))

                    st.session_state.form_data["conf_co_check"] = st.checkbox("Présence de CO", value=get_val("conf_co_check"))
                    if get_val("conf_co_check"):
                        st.session_state.form_data["conf_co"] = st.number_input("Si 'Oui' = Encart numérique %CO :", value=float(get_val("conf_co")))

                    st.session_state.form_data["conf_explo_check"] = st.checkbox("Explosimétrie", value=get_val("conf_explo_check"))
                    if get_val("conf_explo_check"):
                        st.session_state.form_data["conf_explo"] = st.number_input("Si 'Oui' = Encart numérique % :", value=float(get_val("conf_explo")))

                st.session_state.form_data["conf_temp_cuve"] = st.number_input("Vérifier que la cuve ou les produits dans la zone ne dépassent pas 45°C - Température : encart numérique °C :", value=float(get_val("conf_temp_cuve")))
                opts_n2_do = ["N2", "DO"]
                st.session_state.form_data["conf_verif_temp"] = st.selectbox("Vérificateur : Choix entre le N2 et le DO :", opts_n2_do, index=opts_n2_do.index(get_val("conf_verif_temp")) if get_val("conf_verif_temp") in opts_n2_do else 0)

                st.session_state.form_data["conf_inflam_lel"] = st.number_input("En cas de produit inflammable - Mesures : encart numérique % de LEL (Vérification du seuil < 10% LEL) :", value=float(get_val("conf_inflam_lel")))
                st.session_state.form_data["conf_verif_lel"] = st.selectbox("Vérificateur LEL : Choix entre le N2 et le DO :", opts_n2_do, index=opts_n2_do.index(get_val("conf_verif_lel")) if get_val("conf_verif_lel") in opts_n2_do else 0)

                st.session_state.form_data["conf_schema_commentaires"] = st.text_area("Champs libre pour faire schéma ou commentaires :", value=get_val("conf_schema_commentaires"))

                st.write("##### 3 signatures obligatoires :")
                st.session_state.form_data["conf_entrant"] = st.text_input("• Entrants :", value=get_val("conf_entrant"))
                st.session_state.form_data["conf_standby"] = st.text_input("• Stand by :", value=get_val("conf_standby"))
                st.session_state.form_data["conf_do"] = st.text_input("• Donneur d'ordre :", value=get_val("conf_do"))
                st.divider()

            # 7. TRAVAIL ÉLECTRIQUE
            if get_val("p_electrique"):
                st.error("⚡ **PERMIS TRAVAUX ÉLECTRIQUE**")
                st.warning("🥽 **EPI (de base) =** Casque d'électricien, Gants isolants électriques (EN 60903) + Surgants en cuir de protection mécanique + Vêtements de travail 100 % coton ou ignifugés (interdiction du synthétique)")
                st.info("📣 **Rappel :** 'Les travaux électriques sous tension sont interdits. Les travaux au voisinage de pièces nues sous tension doivent être validés. Les outils utilisés doivent être isolés'")

                st.write("##### Liste à cocher :")
                ce1, ce2 = st.columns(2)
                with ce1:
                    st.session_state.form_data["elec_modife"] = st.checkbox("Modification d'installation", value=get_val("elec_modife"))
                    st.session_state.form_data["elec_armoire"] = st.checkbox("Intervention dans les armoires, enveloppe, coffret", value=get_val("elec_armoire"))
                    st.session_state.form_data["elec_voisinage_tension"] = st.checkbox("Travail au voisinage de la tension", value=get_val("elec_voisinage_tension"))
                    st.session_state.form_data["elec_courant_faible"] = st.checkbox("Courants faibles, instrumentation", value=get_val("elec_courant_faible"))
                with ce2:
                    st.session_state.form_data["elec_releve"] = st.checkbox("Relevés / Mesures ou essais", value=get_val("elec_releve"))
                    st.session_state.form_data["elec_chemins"] = st.checkbox("Chemins de câbles / câbles et raccordement", value=get_val("elec_chemins"))
                    st.session_state.form_data["elec_voisinage_nues"] = st.checkbox("Travail au voisinage de pièces nues sous tension", value=get_val("elec_voisinage_nues"))

                if get_val("elec_voisinage_nues"):
                    st.error("🔒 **Si Travail au voisinage de pièces nues sous tension est coché :** Alors : Validation par E&I ou PT E&I habilité B2 ou H2, BC ou HC suivant la tension.")
                    st.error("🥽 **EPI (en plus de ceux de base) =** Écran facial / Visière panoramique anti-arc électrique (EN 166B / GS-ET-29 Class 1 ou 2) + Vestes/vêtements de protection anti-arc électrique (Arc Flash EN ISO 11612) + Nappes isolantes et tapis isolant de sol (EN 61112) pour recouvrir les parties sous tension adjacentes.")
                    st.session_state.form_data["elec_valideur_ei"] = st.text_input("Validation E&I / PT E&I :", value=get_val("elec_valideur_ei"))
                st.divider()

            # 8. CONSIGNATION LOTO (3 PHASES)
            if get_val("p_consignation"):
                st.success("⚡ **PERMIS CONSIGNATION EN 3 PHASES**")
                
                opts_loto_m = ["2 vannes et vanne de drain", "2 vannes", "vanne simple", "vanne et désolidarisation de la conduite", "joint plein", "joint plein et désolidarisation de la conduite"]
                st.write("##### Ouverture de circuit : méthode et points d'isolation retenus")
                st.session_state.form_data["loto_ouverture_methode"] = st.selectbox(
                    "Méthode d'isolation :",
                    opts_loto_m, index=opts_loto_m.index(get_val("loto_ouverture_methode")) if get_val("loto_ouverture_methode") in opts_loto_m else 0
                )
                
                clo1, clo2 = st.columns(2)
                with clo1: st.session_state.form_data["loto_ouvert_loc1"] = st.text_input("Localisation 1 :", value=get_val("loto_ouvert_loc1"))
                with clo2:
                    if "vanne simple" not in get_val("loto_ouverture_methode") and "joint plein" != get_val("loto_ouverture_methode"):
                        st.session_state.form_data["loto_ouvert_loc2"] = st.text_input("Localisation 2 :", value=get_val("loto_ouvert_loc2"))

                st.write("##### Isolation des énergies : méthode de points d'isolation retenus")
                cis1, cis2 = st.columns(2)
                with cis1:
                    st.session_state.form_data["loto_is_elec"] = st.checkbox("Si 'IS électrique' coché", value=get_val("loto_is_elec"))
                    if get_val("loto_is_elec"):
                        st.session_state.form_data["loto_is_elec_loc1"] = st.text_input("2 encarts texte libre : Localisation 1 :", value=get_val("loto_is_elec_loc1"))
                        st.session_state.form_data["loto_is_elec_loc2"] = st.text_input("Localisation 2 :", value=get_val("loto_is_elec_loc2"))

                    st.session_state.form_data["loto_fusible"] = st.checkbox("Si 'Fusibles enlevés' coché", value=get_val("loto_fusible"))
                    if get_val("loto_fusible"):
                        st.session_state.form_data["loto_fusible_loc1"] = st.text_input("Localisation 1 (Fusibles) :", value=get_val("loto_fusible_loc1"))
                        st.session_state.form_data["loto_fusible_loc2"] = st.text_input("Localisation 2 (Fusibles) :", value=get_val("loto_fusible_loc2"))

                    st.session_state.form_data["loto_cable"] = st.checkbox("Si 'Câble électrique déconnecté' coché", value=get_val("loto_cable"))
                    if get_val("loto_cable"):
                        st.session_state.form_data["loto_cable_loc1"] = st.text_input("Localisation 1 (Câble) :", value=get_val("loto_cable_loc1"))
                        st.session_state.form_data["loto_cable_loc2"] = st.text_input("Localisation 2 (Câble) :", value=get_val("loto_cable_loc2"))

                with cis2:
                    st.session_state.form_data["loto_pneu"] = st.checkbox("Si 'IS pneumatique' coché", value=get_val("loto_pneu"))
                    if get_val("loto_pneu"):
                        st.session_state.form_data["loto_pneu_loc1"] = st.text_input("Localisation 1 (Pneu) :", value=get_val("loto_pneu_loc1"))
                        st.session_state.form_data["loto_pneu_loc2"] = st.text_input("Localisation 2 (Pneu) :", value=get_val("loto_pneu_loc2"))

                    st.session_state.form_data["loto_hydra"] = st.checkbox("Si 'IS hydraulique' coché", value=get_val("loto_hydra"))
                    if get_val("loto_hydra"):
                        st.session_state.form_data["loto_hydra_loc1"] = st.text_input("Localisation 1 (Hydra) :", value=get_val("loto_hydra_loc1"))
                        st.session_state.form_data["loto_hydra_loc2"] = st.text_input("Localisation 2 (Hydra) :", value=get_val("loto_hydra_loc2"))

                    st.session_state.form_data["loto_residu"] = st.checkbox("Si 'énergies résiduelles' coché", value=get_val("loto_residu"))
                    if get_val("loto_residu"):
                        st.session_state.form_data["loto_residu_loc1"] = st.text_input("Localisation 1 (Résiduelles) :", value=get_val("loto_residu_loc1"))
                        st.session_state.form_data["loto_residu_loc2"] = st.text_input("Localisation 2 (Résiduelles) :", value=get_val("loto_residu_loc2"))

                st.write("##### Nettoyage des équipements :")
                cn1, cn2 = st.columns(2)
                with cn1:
                    st.session_state.form_data["loto_drain_ouvert"] = st.checkbox("Vanne de drain ouverte", value=get_val("loto_drain_ouvert"))
                    st.session_state.form_data["loto_eq_ouvert"] = st.checkbox("Equipement ouvert", value=get_val("loto_eq_ouvert"))
                with cn2:
                    st.session_state.form_data["loto_eq_lave"] = st.checkbox("Equipement lavé", value=get_val("loto_eq_lave"))
                    st.session_state.form_data["loto_eq_sanitise"] = st.checkbox("Equipement sanitisé", value=get_val("loto_eq_sanitise"))
                st.divider()

            # 9. SYSTÈME À RISQUES / ATEX / CHIMIQUE
            if get_val("p_systeme_risque"):
                st.error("☣ **PERMIS SYSTÈME À RISQUE**")
                st.info("Ouverture du permis consignation (renvoi au même truc au-dessus) effectuée.")

                st.write("##### Case à cocher :")
                st.session_state.form_data["sr_chimique_c1"] = st.checkbox("Chimique de classe 1 (BFA, Ethanol, Néodol/OG base, Acide chlorydrique)", value=get_val("sr_chimique_c1"))
                if get_val("sr_chimique_c1"):
                    st.session_state.form_data["sr_chimique_nom"] = st.text_input("Nom du produit : texte libre :", value=get_val("sr_chimique_nom"))

                st.session_state.form_data["sr_fluide_dang"] = st.checkbox("Fluides dangereux (Parfum, soude, Caustique, Azote, Vapeur, Gaz Naturel)", value=get_val("sr_fluide_dang"))
                if get_val("sr_fluide_dang"):
                    st.session_state.form_data["sr_fluide_nom"] = st.text_input("Nom du produit : texte libre (Fluides) :", value=get_val("sr_fluide_nom"))

                st.session_state.form_data["sr_atex"] = st.checkbox("Zone ATEX", value=get_val("sr_atex"))
                if get_val("sr_atex"):
                    st.session_state.form_data["sr_atex_nom"] = st.text_input("Nom du produit : texte libre (ATEX) :", value=get_val("sr_atex_nom"))

                st.write("##### Evaluation des risques :")
                st.write("*Avant le démarrage des travaux (Case à cocher 'Oui' ou 'Non') :*")
                cera1, cera2 = st.columns(2)
                with cera1:
                    st.session_state.form_data["sr_balisage"] = st.checkbox("Balisage de la zone", value=get_val("sr_balisage"))
                    st.session_state.form_data["sr_douche_rince"] = st.checkbox("Vérification fonctionnement douche et lave œil", value=get_val("sr_douche_rince"))
                    st.session_state.form_data["sr_ramonage"] = st.checkbox("Ramonage de conduite", value=get_val("sr_ramonage"))
                    if get_val("sr_ramonage"):
                        st.session_state.form_data["sr_ramonage_dt"] = st.text_input("Effectué le : (date et heure à choisir) :", value=get_val("sr_ramonage_dt"))
                with cera2:
                    st.session_state.form_data["sr_isolement"] = st.checkbox("Vérification d'isolement des circuits", value=get_val("sr_isolement"))
                    st.session_state.form_data["sr_feuille_loto"] = st.checkbox("Feuille de consignation disponible, complétée et signée", value=get_val("sr_feuille_loto"))
                    if get_val("sr_atex"):
                        st.session_state.form_data["sr_zonage_atex"] = st.checkbox("Vérification du plan de zonage ATEX (zone 0, 1, 2) (si ATEX coché)", value=get_val("sr_zonage_atex"))

                st.write("*Pendant l'exécution des travaux — EPI (Case à cocher 'Oui' ou 'Non') :*")
                cepi1, cepi2 = st.columns(2)
                with cepi1:
                    st.session_state.form_data["sr_epi_ecran"] = st.checkbox("Ecran facial", value=get_val("sr_epi_ecran"))
                    st.session_state.form_data["sr_epi_lunettes"] = st.checkbox("Lunettes étanches", value=get_val("sr_epi_lunettes"))
                    st.session_state.form_data["sr_epi_gants_chim"] = st.checkbox("Gants chimiques adaptés", value=get_val("sr_epi_gants_chim"))
                    st.session_state.form_data["sr_epi_comb1"] = st.checkbox("Combinaison 1 pièce en viton neoprene", value=get_val("sr_epi_comb1"))
                    st.session_state.form_data["sr_epi_comb2"] = st.checkbox("Combinaise 2 pièce anti-acide", value=get_val("sr_epi_comb2"))
                    st.session_state.form_data["sr_epi_bottes"] = st.checkbox("Bottes anti-acide (sous pantalon)", value=get_val("sr_epi_bottes"))
                with cepi2:
                    st.session_state.form_data["sr_epi_cartouche"] = st.checkbox("Masque à cartouche approprié", value=get_val("sr_epi_cartouche"))
                    st.session_state.form_data["sr_epi_ari"] = st.checkbox("ARI (Appareil Respiratoire Isolant)", value=get_val("sr_epi_ari"))
                    st.session_state.form_data["sr_epi_3m6000"] = st.checkbox("Masque 3M 6000", value=get_val("sr_epi_3m6000"))
                    st.session_state.form_data["sr_epi_versaflo"] = st.checkbox("Casque ventilé Jupiter avec cartouche chimique (Versaflo)", value=get_val("sr_epi_versaflo"))
                    st.session_state.form_data["sr_epi_no_versaflo"] = st.checkbox("Pas de versaflo", value=get_val("sr_epi_no_versaflo"))

                st.session_state.form_data["sr_auxiliaire_equipe"] = st.checkbox("Auxiliaire équipé comme intervenant", value=get_val("sr_auxiliaire_equipe"))
                st.session_state.form_data["sr_comm_moyen"] = st.text_input("Moyen de communication adapté : Texte libre :", value=get_val("sr_comm_moyen"))

                st.write("*Après l'exécution des travaux :*")
                st.session_state.form_data["sr_inspect_remise"] = st.checkbox("Inspection du circuit après remise en service", value=get_val("sr_inspect_remise"))
                if get_val("sr_inspect_remise"):
                    st.session_state.form_data["sr_inspect_nom"] = st.text_input("Nom du vérificateur : Texte libre ou liste :", value=get_val("sr_inspect_nom"))
                    st.session_state.form_data["sr_inspect_dt"] = st.text_input("Fait le : Date et heure à choisir :", value=get_val("sr_inspect_dt"))

                st.session_state.form_data["sr_schema_commentaires"] = st.text_area("Champs libre pour faire schéma de levage… ou commentaires :", value=get_val("sr_schema_commentaires"))

                st.write("##### 3 signatures obligatoires Systèmes à Risques :")
                st.session_state.form_data["sr_sign_intervenant"] = st.text_input("• Intervenants qualifiés sur le système à risques :", value=get_val("sr_sign_intervenant"))
                st.session_state.form_data["sr_sign_do"] = st.text_input("• Le donneur d'ordre :", value=get_val("sr_sign_do"))
                st.session_state.form_data["sr_sign_operations"] = st.text_input("• Opération (également obligatoire pour commencer l'intervention) :", value=get_val("sr_sign_operations"))
                st.divider()

            st.info("📣 **Tous les EPIs dans ces permis spécifiques sont ceux à porter en plus des EPIs de base du permis de travail général.**")

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button("⬅️ Précédent"): st.session_state.step = 5; st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"): st.session_state.step = 7; st.rerun()

        # ==============================================================================
        # ÉTAPE 7 : SYNTHÈSE & SOUMISSION
        # ==============================================================================
        elif current_step == 7:
            st.subheader("7. Synthèse & Signatures")

            st.markdown("<div class='status-pending'>⚠️ PERMIS EN ATTENTE DE VALIDATION BATCH (07h30)</div>", unsafe_allow_html=True)

            if get_val("is_subcontractor"):
                st.warning(f"🤝 **Gestion de la sous-traitance (connue grâce au PDP et MOP) :** L'entreprise sélectionnée étant en sous-traitance, à la fin du permis de travail, le N2 de la société principale (**{get_val('titulaire_n2')}**) doit également valider le permis de travail et le signer.")

            st.write("##### Tableau Synthétique des Risques & Permis Spécifiques Renseignés :")
            
            tableau_data = []
            if get_val("p_hauteur"):
                tableau_data.append({"activite": "Travail en hauteur / Échafaudage / Nacelle", "risque": "Chute de hauteur", "prevention": "Casque jugulaire obligatoire + VGP / Qualifications"})
            if get_val("p_toiture"):
                tableau_data.append({"activite": "Accès Toiture", "risque": "Chute / Conditions Météo", "prevention": f"{get_val('toiture_protection')} + Binôme + Valideur ePDP"})
            if get_val("p_points_chauds"):
                tableau_data.append({"activite": "Point Chaud / Flamme", "risque": "Incendie", "prevention": f"Visière EN166B + Extincteurs ({get_val('chaud_extincteur1')}/{get_val('chaud_extincteur2')}) + Vigie {get_val('chaud_vigie_nom')}"})
            if get_val("p_excavation"):
                tableau_data.append({"activite": "Excavation / Tranchée", "risque": "Réseaux / Effondrement", "prevention": f"Plans 7 réseaux OK + DICT + 3 Signatures ({get_val('excav_chef_manoeuvre')}/{get_val('excav_do')}/{get_val('excav_casque_rouge')})"})
            if get_val("p_grutage"):
                tableau_data.append({"activite": "Grutage", "risque": "Chute de charge", "prevention": f"Poids Total {get_val('grut_poids_charge')+get_val('grut_poids_acc')} {get_val('grut_unite')} + Anémomètre OK + 3 Signatures"})
            if get_val("p_confine"):
                tableau_data.append({"activite": "Espace Confiné", "risque": "Asphyxie / Gaz", "prevention": f"Masque M20 + CATEC + O2 ({get_val('conf_o2')}%) + Standby {get_val('conf_standby')}"})
            if get_val("p_electrique"):
                tableau_data.append({"activite": "Travail Électrique", "risque": "Arc Flash / Électrocution", "prevention": "Casque électricien + Gants EN 60903 + Vêtements 100% coton/ignifugés"})
            if get_val("p_consignation"):
                tableau_data.append({"activite": "Consignation (LOTO 3 phases)", "risque": "Énergie résiduelle", "prevention": f"Méthode {get_val('loto_ouverture_methode')} + Nettoyage OK"})
            if get_val("p_systeme_risque"):
                tableau_data.append({"activite": "Systèmes à Risques / ATEX", "risque": "Produits chimiques / Explosion", "prevention": f"Balisage + Douche/Rince-œil + EPIs lourds + 3 Signatures ({get_val('sr_sign_intervenant')}/{get_val('sr_sign_do')}/{get_val('sr_sign_operations')})"})

            if not tableau_data:
                tableau_data.append({"activite": "Permis Général Standard", "risque": "Risques standards PDP", "prevention": "EPIs de base"})

            st.table(tableau_data)

            permis_final = {
                "id": f"PT-2026-EXACT-0{len(st.session_state.permis_db)+1}",
                "date_travaux": get_val("date_str"),
                "societe": get_val("societe"),
                "pdp": get_val("pdp"),
                "mop": get_val("mop"),
                "is_subcontractor": get_val("is_subcontractor"),
                "titulaire_n2": get_val("titulaire_n2"),
                "n2": get_val("n2_nom"),
                "zone": get_val("lieu_pdp"),
                "emplacement": get_val("lieu_precision"),
                "statut": "EN_ATTENTE_BATCH",
                "heure": datetime.datetime.now().strftime("%H:%M"),
                "intervenants": list(get_val("intervenants", [])),
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
    if st.button("✅ VALIDER LE BATCH DE 07h30 (AUTORISER TOUS LES PERMIS)", type="primary"):
        for p in st.session_state.permis_db: p["statut"] = "VALIDÉ"
        st.success("Fournée quotidienne validée ! Tous les permis soumis sont maintenant officiellement actifs.")

    for p in st.session_state.permis_db:
        with st.expander(f"Permis {p['id']} - {p['societe']} ({p['statut']})"):
            st.write(f"**Zone :** {p['zone']} | **N2 :** {p['n2']}")
            st.table(p.get("tableau_risques", []))
            pdf_valid_bytes = generer_pdf_bytes(p)
            st.download_button("📄 Télécharger PDF Officiel", data=pdf_valid_bytes, file_name=f"Permis_{p['id']}.pdf", mime="application/pdf", key=f"btn_{p['id']}")

# ==============================================================================
# INTERFACE 3 : INSPECTION TERRAIN (CASQUE ROUGE)
# ==============================================================================
else:
    st.markdown("<div class='pg-header' style='background: #b91c1c;'><h2>AUDIT TERRAIN & SCAN QR CODE — CASQUE ROUGE</h2></div>", unsafe_allow_html=True)
    if st.session_state.permis_db:
        pt_sel = st.selectbox("Sélectionner un permis scanné sur zone :", [p["id"] for p in st.session_state.permis_db])
        p = next(p for p in st.session_state.permis_db if p["id"] == pt_sel)
        
        st.write(f"### Permis Ref : {p['id']} ({p['statut']})")
        st.write(f"**Entreprise :** {p['societe']} | **PDP :** {p['pdp']}")
        st.write(f"**Signataires :** {', '.join(p['intervenants'])}")
        
        st.table(p.get("tableau_risques", []))
        
        if st.button("✍️ Valider la Ronde de Sécurité Point Chaud (60 min)"):
            st.success("Ronde de sécurité validée et horodatée par le Casque Rouge.")
    else:
        st.info("Aucun permis émis pour le moment. Veuillez créer un permis sur la borne Kiosk.")
