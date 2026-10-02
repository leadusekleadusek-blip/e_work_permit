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
    .weather-container {
        border-radius: 12px; padding: 18px 24px; margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: all 0.3s ease;
    }
    .weather-ok { background-color: #dcfce7; border: 2px solid #22c55e; color: #15803d; }
    .weather-warning { background-color: #fef08a; border: 2px solid #eab308; color: #a16207; }
    .weather-alert { background-color: #fef2f2; border: 2px solid #ef4444; color: #b91c1c; }
    
    .weather-flex { display: flex; align-items: center; gap: 25px; }
    .weather-icon-large { font-size: 4rem; line-height: 1; }
    .weather-details { flex-grow: 1; }
    
    .urgence-card {
        background-color: #fef2f2; border: 2px solid #ef4444; color: #991b1b;
        padding: 18px; border-radius: 10px; margin-bottom: 20px;
    }
    .notice-epi-card {
        background-color: #fffbebf8; border: 2px solid #f59e0b; color: #92400e;
        padding: 16px; border-radius: 10px; margin-bottom: 15px; font-weight: 600;
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
    
    .permis-header-card {
        background: #f1f5f9;
        border-left: 6px solid #003366;
        padding: 12px 18px;
        border-radius: 6px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# MÉTÉO EN DIRECT — ZONE INDUSTRIELLE AMIENS NORD
# ---------------------------------------------------------
@st.cache_data(ttl=1800)
def obtenir_meteo_amiens_live():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=49.9250&longitude=2.2900&daily=temperature_2m_max,temperature_2m_min,windgusts_10m_max,weathercode&timezone=Europe%2FParis"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            code = data['daily']['weathercode'][0]
            
            if code in [0, 1]: icon = "☀️"
            elif code in [2, 3]: icon = "⛅"
            elif code in [45, 48]: icon = "🌫️"
            elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: icon = "🌧️"
            elif code in [95, 96, 99]: icon = "🌩️"
            else: icon = "☁"

            vent = round(data['daily']['windgusts_10m_max'][0])
            if vent >= 30: icon = "💨"

            return {
                "temp_max_j0": round(data['daily']['temperature_2m_max'][0]),
                "temp_min_j0": round(data['daily']['temperature_2m_min'][0]),
                "vent_j0": vent,
                "code_w_j0": code,
                "icon_j0": icon,
                "temp_max_j1": round(data['daily']['temperature_2m_max'][1]),
                "vent_j1": round(data['daily']['windgusts_10m_max'][1]),
                "source": "Open-Meteo Live API (ZI Amiens Nord)"
            }
    except Exception:
        return {"temp_max_j0": 18, "temp_min_j0": 8, "vent_j0": 14, "code_w_j0": 0, "icon_j0": "☀️", "temp_max_j1": 19, "vent_j1": 12, "source": "Mode Secours (ZI Amiens Nord)"}

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
    
    # 1. RISQUES PRINCIPAUX (ÉTAPE 5)
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
    "p_meuleuse": False,
    "dta_consultation": False,
    "p_consignation": False,
    "p_systeme_risque": False,

    # 2. STA (SAFETY TASK ASSIGNMENT - ÉTAPE 5)
    "sta_prod_chimiques": False,
    "sta_prod_chimiques_nom": "",
    "t_outils_electro": False,
    "t_travaux_manuels": True,
    "t_manutention_lourde": False,
    "t_nettoyage_chantiers": True,

    # SPÉCIFICITÉS MEULEUSE (POUR ÉTAPE 6 PERMIS SPÉCIFIQUE)
    "meuleuse_diametre": "125 mm", "meuleuse_operateurs": ["Léa DUSEK"], "meuleuse_marque": "Bosch Pro", "meuleuse_alim": "Batterie 18V", "meuleuse_ref": "MEU-042", "meuleuse_vitesse": "11000",
    "meu_env_plain_pied": True, "meu_env_hauteur": False, "meu_env_confine": False, "meu_env_excavation": False, "meu_env_stable": True, "meu_env_maintien_2mains": True, "meu_env_piece_fixee": True, "meu_env_hors_ligne_tir": True, "meu_position_op": "Debout",
    "meuleuse_u_decoupe": False, "meuleuse_mat_decoupe": db_materiaux[0], "meuleuse_u_ebavurage": False, "meuleuse_mat_ebavurage": db_materiaux[0], "meuleuse_u_flap": False, "meuleuse_u_blanchiment": False, "meuleuse_disque_blanchiment": db_disques_blanchiment[0],

    # 3. LISTE EXHAUSTIVE DES EPIS (AVEC NORMES EXACTES)
    "epi_lunettes_chantier_en166": True,
    "epi_lunettes_etanches": False,
    "epi_visiere_idra_en166b": False,
    "epi_lunettes_pare_visage": False,
    "epi_casque_jugulaire": True,
    "epi_casque_protection_auditive_en387": False,
    "epi_gants_anticoupure_4x43d": True,
    "epi_gants_manutention_cuir": True,
    "epi_gants_chimiques_en374": False,
    "epi_gants_elec_en60903": False,
    "epi_bouchons_oreilles": False,
    "epi_resp_ffp1_ffp2": False,
    "epi_resp_3m6000": False,
    "epi_resp_versaflo": False,
    "epi_resp_cartouche_abek_en14387": False,
    "epi_autre_texte": "",

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
        # ÉTAPE 5 : MÉTÉO -> RISQUES PRINCIPAUX -> STA -> EPIS DE BASE P&G
        # ==============================================================================
        elif current_step == 5:
            st.subheader("5. Analyse des Risques, STA & Équipements de Protection Individuelle")

            meteo_live = obtenir_meteo_amiens_live()
            temp_max = meteo_live['temp_max_j0']
            vent = meteo_live['vent_j0']
            
            if vent > 36 or temp_max < 3 or temp_max > 30:
                weather_class = "weather-alert"
                status_msg = "❌ <b>CONDITIONS DÉFAVORABLES / ALERTE MÉTÉO</b> (Vent > 36 km/h ou T° extrême) — Travaux spécifiques soumis à restriction/dérogation Casque Rouge."
            elif 30 <= vent <= 36:
                weather_class = "weather-warning"
                status_msg = "⚠️ <b>VIGILANCE MÉTÉO</b> (Vent entre 30 et 36 km/h) — Attention renforcée pour les travaux en extérieur et en hauteur."
            else:
                weather_class = "weather-ok"
                status_msg = "✅ <b>CONDITIONS FAVORABLES</b> — Tous les travaux extérieurs et en hauteur sont autorisés."

            # MODIFICATION MÉTÉO : Suppression de "(J+1)"
            st.markdown(f"""
            <div class='weather-container {weather_class}'>
                <div class='weather-flex'>
                    <div class='weather-icon-large'>{meteo_live['icon_j0']}</div>
                    <div class='weather-details'>
                        <div style='font-size:1.1rem; font-weight:bold; margin-bottom:4px;'>
                            MÉTÉO EN DIRECT — ZONE INDUSTRIELLE AMIENS NORD
                        </div>
                        <div>
                            • <b>Aujourd'hui :</b> Temp. Min <b>{meteo_live['temp_min_j0']}°C</b> / Max <b>{meteo_live['temp_max_j0']}°C</b> | 💨 Rafales de vent max : <b>{vent} km/h</b><br>
                            • <b>Demain :</b> Temp. Max {meteo_live['temp_max_j1']}°C | 💨 Rafales : {meteo_live['vent_j1']} km/h
                        </div>
                        <div style='margin-top:8px;'>{status_msg}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.error("🚨 **1. LISTE DES RISQUES PRINCIPAUX (Déclenchant un Permis Spécifique HRT à l'Étape 6) :**")
            
            cr1, cr2 = st.columns(2)
            with cr1:
                p_hauteur = st.checkbox("Travail en hauteur", value=get_val("p_hauteur"))
                p_toiture = st.checkbox("Accès toiture", value=get_val("p_toiture"))
                p_points_chauds_val = get_val("p_points_chauds")
                p_excavation = st.checkbox("Tranchée, BTP, ouverture de sol", value=get_val("p_excavation"))
                p_grutage = st.checkbox("Grutage", value=get_val("p_grutage"))
                p_confine = st.checkbox("Espace confiné, risque asphyxie, anoxie (Azote)", value=get_val("p_confine"))

            with cr2:
                p_electrique = st.checkbox("Travail électrique", value=get_val("p_electrique"))
                p_ouverture_circuit = st.checkbox("Ouverture de circuit sous pression (vapeur, air, gaz, fluides chimiques)", value=get_val("p_ouverture_circuit"))
                p_machines_mouvement = st.checkbox("Machines en mouvement, parties mobiles, risque mécaniques", value=get_val("p_machines_mouvement"))
                p_equipement_pression = st.checkbox("Équipement sous pression", value=get_val("p_equipement_pression"))
                p_laser_classe_iv = st.checkbox("Travaux à proximité de Lasers Classe IV", value=get_val("p_laser_classe_iv"))
                p_demolition = st.checkbox("Démolition", value=get_val("p_demolition"))
                p_meuleuse = st.checkbox("Utilisation de la meuleuse", value=get_val("p_meuleuse"))

            if p_meuleuse:
                p_points_chauds_val = True
                st.session_state.form_data["t_outils_electro"] = True

            with cr1:
                p_points_chauds = st.checkbox("Génération de points chauds", value=p_points_chauds_val)

            st.session_state.form_data["p_hauteur"] = p_hauteur
            st.session_state.form_data["p_toiture"] = p_toiture
            st.session_state.form_data["p_points_chauds"] = p_points_chauds
            st.session_state.form_data["p_excavation"] = p_excavation
            st.session_state.form_data["p_grutage"] = p_grutage
            st.session_state.form_data["p_confine"] = p_confine
            st.session_state.form_data["p_electrique"] = p_electrique
            st.session_state.form_data["p_ouverture_circuit"] = p_ouverture_circuit
            st.session_state.form_data["p_machines_mouvement"] = p_machines_mouvement
            st.session_state.form_data["p_equipement_pression"] = p_equipement_pression
            st.session_state.form_data["p_laser_classe_iv"] = p_laser_classe_iv
            st.session_state.form_data["p_demolition"] = p_demolition
            st.session_state.form_data["p_meuleuse"] = p_meuleuse

            if p_ouverture_circuit or p_machines_mouvement or p_equipement_pression or p_laser_classe_iv:
                st.session_state.form_data["p_consignation"] = True

            if p_demolition:
                st.session_state.form_data["dta_consultation"] = st.checkbox("Consultation DTA (Dossier Technique Amiante) effectuée et validée", value=get_val("dta_consultation"))

            st.divider()

            st.write("##### 🛠️ 2. STA (Safety Task Assignment) & Outillage de Chantier :")

            st.session_state.form_data["sta_prod_chimiques"] = st.checkbox("Produits chimiques", value=get_val("sta_prod_chimiques"))
            if get_val("sta_prod_chimiques"):
                st.session_state.form_data["sta_prod_chimiques_nom"] = st.text_input("Nom(s) du/des produit(s) chimique(s) utilisé(s) :", value=get_val("sta_prod_chimiques_nom"), placeholder="ex: Solvant, Acide Chlorhydrique, Soude...")
                st.session_state.form_data["p_systeme_risque"] = True

            ct1, ct2 = st.columns(2)
            with ct1:
                st.session_state.form_data["t_outils_electro"] = st.checkbox("Utilisation d'outils électroportatifs", value=get_val("t_outils_electro"))
                st.session_state.form_data["t_travaux_manuels"] = st.checkbox("Travaux manuels généraux et d'outillage à main", value=get_val("t_travaux_manuels"))
            with ct2:
                st.session_state.form_data["t_manutention_lourde"] = st.checkbox("Manutention manuelle de charges ou matériel", value=get_val("t_manutention_lourde"))
                st.session_state.form_data["t_nettoyage_chantiers"] = st.checkbox("Nettoyage, rangement de zone de chantier", value=get_val("t_nettoyage_chantiers"))

            st.divider()

            st.write("##### 🥽 3. Équipements de Protection Individuelle (EPIs) :")

            st.markdown("""
            <div class='notice-epi-card'>
                ⚠️ <b>Rappel Obligatoire :</b> Les chaussures de sécurité montantes, casque avec jugulaire, lunette de sécurité à protection latérale (EN166), gilet haute visibilité (sauf pour les travaux électriques ou par point chaud), et gants anti-coupure sont obligatoires sur le chantier de construction.
            </div>
            """, unsafe_allow_html=True)

            auto_jugulaire = p_hauteur or p_toiture
            auto_visiere = p_points_chauds or p_meuleuse or p_laser_classe_iv
            auto_gants_elec = p_electrique
            auto_gants_coupure = p_meuleuse or p_points_chauds
            auto_resp_cartouche = p_confine or get_val("sta_prod_chimiques")

            cepi_col1, cepi_col2 = st.columns(2)

            with cepi_col1:
                st.write("**• Lunettes & Protections Faciales :**")
                st.session_state.form_data["epi_lunettes_chantier_en166"] = st.checkbox("Lunettes Chantier ou Visière — EN 166 (Obligatoire)", value=get_val("epi_lunettes_chantier_en166", True))
                st.session_state.form_data["epi_lunettes_etanches"] = st.checkbox("Lunettes étanches", value=get_val("epi_lunettes_etanches"))
                st.session_state.form_data["epi_visiere_idra_en166b"] = st.checkbox("Protection faciale : Visière (casque type IDRA) — EN 166B", value=auto_visiere or get_val("epi_visiere_idra_en166b"))
                st.session_state.form_data["epi_lunettes_pare_visage"] = st.checkbox("Lunette + pare visage", value=get_val("epi_lunettes_pare_visage"))

                st.write("**• Casques :**")
                st.session_state.form_data["epi_casque_jugulaire"] = st.checkbox("Casque avec jugulaire (Obligatoire)", value=auto_jugulaire or get_val("epi_casque_jugulaire", True))
                st.session_state.form_data["epi_casque_protection_auditive_en387"] = st.checkbox("Casque avec protection auditive — EN 387/A1", value=get_val("epi_casque_protection_auditive_en387"))

                st.write("**• Protections Auditives :**")
                st.session_state.form_data["epi_bouchons_oreilles"] = st.checkbox("Bouchons d'oreilles / Protections moulées", value=get_val("epi_bouchons_oreilles"))

            with cepi_col2:
                st.write("**• Gants de Protection :**")
                st.session_state.form_data["epi_gants_anticoupure_4x43d"] = st.checkbox("Gants Anti-coupures — 4543 / 4x43D", value=auto_gants_coupure or get_val("epi_gants_anticoupure_4x43d", True))
                st.session_state.form_data["epi_gants_manutention_cuir"] = st.checkbox("Gants Manutention — Cuir bovin ou chèvre", value=get_val("epi_gants_manutention_cuir"))
                st.session_state.form_data["epi_gants_chimiques_en374"] = st.checkbox("Gants Chimiques — EN 374-1/2", value=get_val("sta_prod_chimiques") or get_val("epi_gants_chimiques_en374"))
                st.session_state.form_data["epi_gants_elec_en60903"] = st.checkbox("Gants Électrique isolants / surgants — EN 60903", value=auto_gants_elec or get_val("epi_gants_elec_en60903"))

                st.write("**• Protections Respiratoires :**")
                st.session_state.form_data["epi_resp_ffp1_ffp2"] = st.checkbox("Masque FFP1 / FFP2", value=get_val("epi_resp_ffp1_ffp2"))
                st.session_state.form_data["epi_resp_3m6000"] = st.checkbox("Masque demi-facial 3M6000", value=get_val("epi_resp_3m6000"))
                st.session_state.form_data["epi_resp_versaflo"] = st.checkbox("Système à adduction / ventilation assistée Versaflo", value=get_val("epi_resp_versaflo"))
                st.session_state.form_data["epi_resp_cartouche_abek_en14387"] = st.checkbox("Cartouche ABEK — EN 14387", value=auto_resp_cartouche or get_val("epi_resp_cartouche_abek_en14387"))

            st.write("**• Autre :**")
            st.session_state.form_data["epi_autre_texte"] = st.text_input("Autre protection spécifique (à préciser) :", value=get_val("epi_autre_texte"), placeholder="ex: Tablier de protection, harnais de maintien...")

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button("⬅️ Précédent"): st.session_state.step = 4; st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"): st.session_state.step = 6; st.rerun()

        # ==============================================================================
        # ÉTAPE 6 : FORMULAIRES SPÉCIFIQUES (MODIFICATIONS SÉPARATION & PHRASÉ SANS "SI")
        # ==============================================================================
        elif current_step == 6:
            st.subheader("6. Ouverture des Permis Spécifiques")

            # MEULEUSE
            if get_val("p_meuleuse"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#003366;'>⚙️ MEULEUSE — SPÉCIFICITÉS & CARACTÉRISTIQUES</h3></div>", unsafe_allow_html=True)
                    c_m1, c_m2 = st.columns(2)
                    with c_m1:
                        st.session_state.form_data["meuleuse_diametre"] = st.selectbox("Diamètre du disque :", ["125 mm", "230 mm"], index=0 if get_val("meuleuse_diametre") == "125 mm" else 1)
                        st.session_state.form_data["meuleuse_marque"] = st.text_input("Marque et Modèle de l'appareil :", value=get_val("meuleuse_marque"))
                    with c_m2:
                        st.session_state.form_data["meuleuse_alim"] = st.selectbox("Type d'alimentation :", ["Batterie 18V", "Filaire 230V", "Pneumatique"], index=0)
                        st.session_state.form_data["meuleuse_ref"] = st.text_input("Référence / N° de série :", value=get_val("meuleuse_ref"))

                    st.write("##### Opérations prévues :")
                    cm_op1, cm_op2 = st.columns(2)
                    with cm_op1:
                        st.session_state.form_data["meuleuse_u_decoupe"] = st.checkbox("Découpe / Tronçonnage", value=get_val("meuleuse_u_decoupe"))
                        if get_val("meuleuse_u_decoupe"):
                            st.session_state.form_data["meuleuse_mat_decoupe"] = st.selectbox("Matériau à découper :", db_materiaux, index=0)
                        
                        st.session_state.form_data["meuleuse_u_ebavurage"] = st.checkbox("Ébavurage / Meulage", value=get_val("meuleuse_u_ebavurage"))
                        if get_val("meuleuse_u_ebavurage"):
                            st.session_state.form_data["meuleuse_mat_ebavurage"] = st.selectbox("Matériau ébavuré :", db_materiaux, index=0)

                    with cm_op2:
                        st.session_state.form_data["meuleuse_u_flap"] = st.checkbox("Ponçage disque à lamelles (Flap)", value=get_val("meuleuse_u_flap"))
                        st.session_state.form_data["meuleuse_u_blanchiment"] = st.checkbox("Blanchiment / Nettoyage de surface", value=get_val("meuleuse_u_blanchiment"))
                        if get_val("meuleuse_u_blanchiment"):
                            st.session_state.form_data["meuleuse_disque_blanchiment"] = st.selectbox("Type de disque blanchiment :", db_disques_blanchiment, index=0)

            # 1. HAUTEUR
            if get_val("p_hauteur"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#b91c1c;'>🧗 TRAVAIL EN HAUTEUR / ÉCHAFAUDAGE / NACELLE</h3></div>", unsafe_allow_html=True)
                    st.info("🥽 **EPI obligatoire :** Casque avec jugulaire")

                    st.write("##### Équipements de travail en hauteur utilisés :")
                    
                    # Remplacement du phrasé "Si PIRL est coché"
                    st.session_state.form_data["h_pirl"] = st.checkbox("PIRL (Plateforme Individuelle Roulante Légère)", value=get_val("h_pirl"))
                    if get_val("h_pirl"):
                        cp1, cp2 = st.columns(2)
                        with cp1: st.session_state.form_data["h_pirl_vgp"] = st.checkbox("VGP et contrôle visuel préalable effectués", value=get_val("h_pirl_vgp"))
                        with cp2: st.session_state.form_data["h_pirl_soc"] = st.text_input("Nom de la société propriétaire/utilisatrice :", value=get_val("h_pirl_soc"))

                    # Remplacement du phrasé "Si Nacelle élévatrice est coché"
                    st.session_state.form_data["h_nacelle"] = st.checkbox("Nacelle élévatrice (PEMP)", value=get_val("h_nacelle"))
                    if get_val("h_nacelle"):
                        st.warning("🥽 **EPI requis :** Harnais + longe de maintien/anti-chute")
                        cn1, cn2 = st.columns(2)
                        with cn1:
                            st.session_state.form_data["h_nacelle_vgp"] = st.checkbox("VGP et checklist journalière validées", value=get_val("h_nacelle_vgp"))
                            st.session_state.form_data["h_nacelle_caces"] = st.checkbox("CACES valide (Opérateur et Vigie)", value=get_val("h_nacelle_caces"))
                            st.session_state.form_data["h_nacelle_aut"] = st.checkbox("Autorisation de conduite délivrée", value=get_val("h_nacelle_aut"))
                        with cn2:
                            st.session_state.form_data["h_nacelle_harnais"] = st.checkbox("Habilitation / Formation au port du harnais", value=get_val("h_nacelle_harnais"))
                            st.session_state.form_data["h_nacelle_soc"] = st.text_input("Nom de la société utilisatrice de la nacelle :", value=get_val("h_nacelle_soc"))

                    # Remplacement du phrasé "Si Échafaudage est coché"
                    st.session_state.form_data["h_echaf"] = st.checkbox("Échafaudage fixe ou roulant", value=get_val("h_echaf"))
                    if get_val("h_echaf"):
                        st.write("##### Exigences spécifiques pour Échafaudage :")
                        ce1, ce2 = st.columns(2)
                        with ce1:
                            st.session_state.form_data["h_echaf_montage"] = st.checkbox("Opération de Montage / Démontage / Modification", value=get_val("h_echaf_montage"))
                            if get_val("h_echaf_montage"):
                                st.checkbox("Qualification monteur d'échafaudage validée", value=True)
                                st.checkbox("Habilitation port du harnais validée", value=True)
                                st.error("🥽 **EPI requis :** Harnais + double longe + connecteurs + absorbeur/stop-chute + gants")

                        with ce2:
                            st.session_state.form_data["h_echaf_util"] = st.checkbox("Utilisation simple", value=get_val("h_echaf_util"))
                            if get_val("h_echaf_util"):
                                st.checkbox("Formation à l'utilisation et l'inspection d'échafaudage validée", value=True)

                        st.session_state.form_data["h_echaf_ctrl_regle"] = st.checkbox("Contrôle périodique réglementaire à jour", value=get_val("h_echaf_ctrl_regle"))
                        st.session_state.form_data["h_echaf_certif_affiche"] = st.checkbox("Certificat de montage et d'affichage en place (Procès-Verbal)", value=get_val("h_echaf_certif_affiche"))
                        st.session_state.form_data["h_echaf_verif_j"] = st.checkbox("Vérification journalière réalisée par l'entreprise", value=get_val("h_echaf_verif_j"))
                        st.session_state.form_data["h_echaf_soc_util"] = st.text_input("Nom de la société utilisatrice de l'échafaudage :", value=get_val("h_echaf_soc_util"))

            # 2. TOITURE
            if get_val("p_toiture"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#b91c1c;'>🏢 ACCÈS TOITURE</h3></div>", unsafe_allow_html=True)
                    st.info("🥽 **EPI obligatoire :** Casque avec jugulaire")
                    st.info(f"📍 **Localisation de la toiture retenue :** `{get_val('lieu_pdp')}` ({get_val('lieu_precision')})")

                    opts_protect = ["Garde-corps", "Ligne de vie / Point d'ancrage", "Pas de protection collective fixe"]
                    st.session_state.form_data["toiture_protection"] = st.selectbox(
                        "Moyen de protection collective ou individuelle présent sur la zone :",
                        opts_protect, index=opts_protect.index(get_val("toiture_protection")) if get_val("toiture_protection") in opts_protect else 0
                    )
                    
                    st.warning("🥽 **Consigne EPIs :** Harnais et système d'arrêt de chute obligatoires à moins de 3m du bord en l'absence de garde-corps. Balisage physique requis.")

                    meteo_live = obtenir_meteo_amiens_live()
                    st.write("##### Conditions météorologiques en direct :")
                    
                    temp_val = meteo_live["temp_max_j0"]
                    vent_val = meteo_live["vent_j0"]
                    
                    refus = False
                    reasons = []

                    if temp_val < 3 or temp_val > 30:
                        refus = True; reasons.append(f"Température extrême ({temp_val}°C)")
                    if vent_val > 36:
                        refus = True; reasons.append(f"Vent supérieur à 36 km/h ({vent_val} km/h)")
                    
                    chk_orage = st.checkbox("Risque d'orage identifié", value=False)
                    chk_pluie = st.checkbox("Pluie battante prévue", value=False)

                    if chk_orage: refus = True; reasons.append("Orage")
                    if chk_pluie: refus = True; reasons.append("Pluie battante")

                    if refus:
                        st.error(f"❌ **ACCÈS REFUSÉ EN RAISON DES CONDITIONS MÉTÉOROLOGIQUES :** {', '.join(reasons)}")
                    else:
                        if 30 <= vent_val <= 36:
                            st.warning(f"⚠️ **Vigilance météo (vent entre 30 et 36 km/h) :** {vent_val} km/h")
                        else:
                            st.success("✅ **CONDITIONS FAVORABLES**")
                        st.info("📣 **Règle d'accès :** Présence obligatoire de deux personnes minimum (travail en binôme strict).")
                        st.session_state.form_data["toiture_valideur"] = st.text_input("Personne habilitée validant l'accès toiture (Profil ePDP) :", value=get_val("toiture_valideur"))

            # 3. POINT CHAUD
            if get_val("p_points_chauds"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#d97706;'>🔥 PERMIS POINT CHAUD</h3></div>", unsafe_allow_html=True)
                    st.info("🥽 **EPIs requis :** Écran facial EN166B (ou cagoule de soudage) + Vêtements ignifugés")
                    
                    st.write("##### Gants de protection recommandés (sélectionner au moins un type) :")
                    cg1, cg2, cg3 = st.columns(3)
                    with cg1: st.session_state.form_data["chaud_gants_soudeur"] = st.checkbox("Gants de soudeur", value=get_val("chaud_gants_soudeur"))
                    with cg2: st.session_state.form_data["chaud_gants_chaleur"] = st.checkbox("Gants haute température", value=get_val("chaud_gants_chaleur"))
                    with cg3: st.session_state.form_data["chaud_gants_anticoupure"] = st.checkbox("Gants anti-coupure adaptés à l'outil", value=get_val("chaud_gants_anticoupure"))

                    carto = db_zones_carto.get(get_val("lieu_pdp"), {})
                    st.write("##### Moyens de protection incendie fixes de la zone :")
                    st.write(f"- Système Sprinkler opérationnel : **{'OUI' if carto.get('sprinkler') else 'NON'}**")
                    if not carto.get('sprinkler'):
                        st.error("🚨 **Absence de Sprinkler :** Surveillance P&G obligatoire de 60 min à l'issue de la surveillance de l'entreprise intervenante.")

                    st.write(f"- Détection Automatique d'Incendie (DAI) : **{'OUI' if carto.get('detection') else 'NON'}**")
                    if not carto.get('detection'):
                        st.error("🚨 **Absence de DAI :** Surveillance P&G obligatoire de 60 min à l'issue de la surveillance de l'entreprise intervenante.")

                    st.write("##### Extincteurs portatifs présents sur le chantier (2 obligatoires) :")
                    opts_ext = ["Poudre ABC", "Eau + additifs", "CO2"]
                    cext1, cext2 = st.columns(2)
                    with cext1: st.session_state.form_data["chaud_extincteur1"] = st.selectbox("1er extincteur :", opts_ext, index=opts_ext.index(get_val("chaud_extincteur1")) if get_val("chaud_extincteur1") in opts_ext else 0)
                    with cext2: st.session_state.form_data["chaud_extincteur2"] = st.selectbox("2ème extincteur :", opts_ext, index=opts_ext.index(get_val("chaud_extincteur2")) if get_val("chaud_extincteur2") in opts_ext else 1)

                    st.session_state.form_data["chaud_degage_10m"] = st.checkbox("Zone dégagée de tout matériau combustible dans un rayon de 10 mètres", value=get_val("chaud_degage_10m"))
                    if not get_val("chaud_degage_10m"):
                        st.error("🔒 **Protection requise :** Mise en place obligatoire de bâches ou écrans ignifugés.")

                    st.session_state.form_data["chaud_traverse_mur"] = st.checkbox("Travaux traversant une paroi, un mur ou un plancher", value=get_val("chaud_traverse_mur"))
                    if get_val("chaud_traverse_mur"):
                        st.error("🔒 **Mesure requise :** Positionner une vigie du côté opposé de la paroi.")

                    st.session_state.form_data["chaud_ouverture_10m"] = st.checkbox("Proximité (<10m) d'ouvertures, de canalisations ou de caniveaux", value=get_val("chaud_ouverture_10m"))
                    if get_val("chaud_ouverture_10m"):
                        st.session_state.form_data["chaud_obstruction"] = st.checkbox("Obstruction et obturation hermétique des ouvertures", value=True)
                        st.session_state.form_data["chaud_vigie_autre_cote"] = st.checkbox("Vigie complémentaire en zone adjacente", value=False)

                    st.write("##### Organisation de la surveillance Incendie :")
                    interv_list = get_val("intervenants", ["Léa DUSEK"])
                    st.session_state.form_data["chaud_vigie_nom"] = st.selectbox("Vigie désignée pendant les travaux (signataire du MoP) :", interv_list, index=interv_list.index(get_val("chaud_vigie_nom")) if get_val("chaud_vigie_nom") in interv_list else 0)
                    st.session_state.form_data["chaud_personne_surv_60m"] = st.selectbox("Responsable de la ronde de sécurité (60 min post-travaux) :", interv_list, index=interv_list.index(get_val("chaud_personne_surv_60m")) if get_val("chaud_personne_surv_60m") in interv_list else 0)

                    chf1, chf2 = st.columns(2)
                    with chf1: st.session_state.form_data["chaud_heure_fin"] = st.text_input("Heure prévisionnelle de fin des travaux à chaud :", value=get_val("chaud_heure_fin"))
                    with chf2: st.session_state.form_data["chaud_heure_depart"] = st.text_input("Heure de clôture (après fin de la période de surveillance) :", value=get_val("chaud_heure_depart"))
                    st.session_state.form_data["chaud_commentaires"] = st.text_area("Commentaires ou observations de clôture :", value=get_val("chaud_commentaires"))

            # 4. EXCAVATION
            if get_val("p_excavation"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#003366;'>🚜 EXCAVATION & GÉNIE CIVIL</h3></div>", unsafe_allow_html=True)
                    
                    st.write("##### Vérification des réseaux souterrains et plans de récolement :")
                    cx1, cx2, cx3, cx4 = st.columns(4)
                    with cx1:
                        st.session_state.form_data["excav_plans_eaux_indus"] = st.checkbox("Eau industrielle & potable", value=get_val("excav_plans_eaux_indus"))
                        st.session_state.form_data["excav_plans_eaux_usees"] = st.checkbox("Eaux usées", value=get_val("excav_plans_eaux_usees"))
                    with cx2:
                        st.session_state.form_data["excav_plans_eaux_pluv"] = st.checkbox("Eaux pluviales", value=get_val("excav_plans_eaux_pluv"))
                        st.session_state.form_data["excav_plans_eaux_incendie"] = st.checkbox("Réseau incendie (RIA/Sprinkler)", value=get_val("excav_plans_eaux_incendie"))
                    with cx3:
                        st.session_state.form_data["excav_plans_ht"] = st.checkbox("Haute Tension (HTA/HTB)", value=get_val("excav_plans_ht"))
                        st.session_state.form_data["excav_plans_bt"] = st.checkbox("Basse Tension (BT) & Commandes", value=get_val("excav_plans_bt"))
                    with cx4:
                        st.session_state.form_data["excav_plans_gaz"] = st.checkbox("Réseau Gaz", value=get_val("excav_plans_gaz"))

                    st.write("##### Analyse de l'environnement immédiat :")
                    ceenv1, ceenv2, ceenv3 = st.columns(3)
                    with ceenv1: st.session_state.form_data["excav_struct_proximite"] = st.checkbox("Proximité de fondations, raccordements ou racks", value=get_val("excav_struct_proximite"))
                    with ceenv2: st.session_state.form_data["excav_architecte"] = st.checkbox("Avis de l'architecte / Ingénieur structure obtenu", value=get_val("excav_architecte"))
                    with ceenv3: st.session_state.form_data["excav_dict"] = st.checkbox("DICT enregistrée et validée", value=get_val("excav_dict"))

                    st.write("##### Prévention des risques de glissement et d'effondrement :")
                    ceeff1, ceeff2 = st.columns(2)
                    with ceeff1:
                        st.session_state.form_data["excav_eau_pompe"] = st.checkbox("Infiltration d'eau / Utilisation d'une pompe de relevage", value=get_val("excav_eau_pompe"))
                        st.session_state.form_data["excav_balisage"] = st.checkbox("Balisage rigide et dégagement des abords du chantier", value=get_val("excav_balisage"))
                    with ceeff2:
                        st.session_state.form_data["excav_vehicule_3m"] = st.checkbox("Maintien des engins et véhicules à plus de 3 mètres du bord", value=get_val("excav_vehicule_3m"))
                        st.session_state.form_data["excav_deblais"] = st.checkbox("Stockage des déblais sur une zone définie et sécurisée", value=get_val("excav_deblais"))

                    st.write("##### Accès à la fouille :")
                    opts_acces = ["Escalier / Rampe", "Échelle", "Passerelle"]
                    st.session_state.form_data["excav_acces"] = st.selectbox("Dispositif d'accès retenu :", opts_acces, index=opts_acces.index(get_val("excav_acces")) if get_val("excav_acces") in opts_acces else 0)
                    if get_val("excav_acces") == "Échelle":
                        st.error("🚨 **Utilisation d'une échelle :** Dérogation et accord préalable Casque Rouge requis.")

                    st.session_state.form_data["excav_profondeur_130"] = st.checkbox("Profondeur d'excavation supérieure à 1,30m", value=get_val("excav_profondeur_130"))
                    if get_val("excav_profondeur_130"):
                        st.error("🔒 **Exigence de sécurité :** Blindage, blindage caisson ou talutage obligatoire.")

                    st.session_state.form_data["excav_schema_commentaires"] = st.text_area("Schéma de l'excavation ou commentaires techniques :", value=get_val("excav_schema_commentaires"))

                    st.write("##### Signatures d'autorisation de l'excavation :")
                    st.session_state.form_data["excav_chef_manoeuvre"] = st.text_input("1. Chef de manœuvre de l'entreprise intervenante :", value=get_val("excav_chef_manoeuvre"))
                    st.session_state.form_data["excav_do"] = st.text_input("2. Donneur d'Ordre (Autorise l'installation du chantier) :", value=get_val("excav_do"))
                    st.session_state.form_data["excav_casque_rouge"] = st.text_input("3. Casque Rouge P&G (Autorise le démarrage des travaux) :", value=get_val("excav_casque_rouge"))

            # 5. GRUTAGE
            if get_val("p_grutage"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#003366;'>🏗️ LEVAGE ET GRUTAGE</h3></div>", unsafe_allow_html=True)
                    
                    st.write("##### Caractéristiques du matériel et des charges :")
                    st.session_state.form_data["grut_desc_mop"] = st.text_area("Description de la charge à lever (selon MoP) :", value=get_val("grut_desc_mop"))
                    
                    cg1, cg2 = st.columns(2)
                    with cg1: st.session_state.form_data["grut_poids_charge"] = st.number_input("Poids de la charge principale :", value=float(get_val("grut_poids_charge")))
                    opts_unite = ["kg", "T"]
                    with cg2: st.session_state.form_data["grut_unite"] = st.selectbox("Unité de mesure :", opts_unite, index=opts_unite.index(get_val("grut_unite")) if get_val("grut_unite") in opts_unite else 0)

                    st.session_state.form_data["grut_poids_acc"] = st.number_input(f"Poids des accessoires de levage ({get_val('grut_unite')}) :", value=float(get_val("grut_poids_acc")))
                    poids_tot = get_val("grut_poids_charge") + get_val("grut_poids_acc")
                    st.info(f"⚖️ **Poids total à gruter (Charge + Accessoires) :** `{poids_tot} {get_val('grut_unite')}`")

                    st.write("##### Spécifications techniques de la grue :")
                    cmat1, cmat2, cmat3 = st.columns(3)
                    with cmat1: st.session_state.form_data["grut_immat"] = st.text_input("Identification / Immatriculation de la grue :", value=get_val("grut_immat"))
                    with cmat2: st.session_state.form_data["grut_fleche"] = st.number_input("Hauteur de flèche utile (m) :", value=float(get_val("grut_fleche")))
                    with cmat3: st.session_state.form_data["grut_portee"] = st.number_input("Portée maximale de travail (m) :", value=float(get_val("grut_portee")))

                    cmat4, cmat5 = st.columns(2)
                    with cmat4: st.session_state.form_data["grut_pression_patin"] = st.text_input("Pression maximale au sol sous patin :", value=get_val("grut_pression_patin"))
                    with cmat5: st.session_state.form_data["grut_rayon"] = st.number_input("Rayon d'action / Giration (m) :", value=float(get_val("grut_rayon")))

                    st.write("##### Organisation et périmètre de sécurité :")
                    st.session_state.form_data["grut_balisage"] = st.checkbox("Balisage physique conforme au plan de grutage", value=get_val("grut_balisage"))
                    st.session_state.form_data["grut_plan_vue"] = st.checkbox("Plan de grutage (vue en plan avec zones d'interdiction)", value=get_val("grut_plan_vue"))
                    st.session_state.form_data["grut_plan_elev"] = st.checkbox("Plan de grutage en élévation annexé", value=get_val("grut_plan_elev"))
                    st.session_state.form_data["grut_obstacles"] = st.checkbox("Lignes électriques et obstacles aériens identifiés", value=get_val("grut_obstacles"))

                    st.write("##### Contrôle anémométrique du vent :")
                    st.session_state.form_data["grut_anemometre"] = st.checkbox("Anémomètre en bout de flèche opérationnel", value=get_val("grut_anemometre"))
                    cv1, cv2 = st.columns(2)
                    opts_vent_u = ["km/h", "m/S"]
                    with cv1: st.session_state.form_data["grut_vent_val"] = st.number_input("Vitesse du vent mesurée sur site :", value=float(get_val("grut_vent_val")))
                    with cv2: st.session_state.form_data["grut_vent_unite"] = st.selectbox("Unité de mesure du vent :", opts_vent_u, index=opts_vent_u.index(get_val("grut_vent_unite")) if get_val("grut_vent_unite") in opts_vent_u else 0)

                    if (get_val("grut_vent_unite") == "km/h" and get_val("grut_vent_val") > 36) or (get_val("grut_vent_unite") == "m/S" and get_val("grut_vent_val") > 10):
                        st.error("❌ **ALERTE SÉCURITÉ VENT :** Vitesse supérieure au seuil critique (>36 km/h). Interdiction stricte de gruter.")

                    st.session_state.form_data["grut_pesage"] = st.checkbox("Indicateur / Limiteur de charge automatique présent", value=get_val("grut_pesage"))
                    if get_val("grut_pesage"):
                        st.info("Règle appliquée : Charge totale < 90% de la capacité maximale de la grue.")
                    else:
                        st.warning("Règle appliquée sans pesage automatique : Charge totale < 80% de la capacité maximale.")

                    st.session_state.form_data["grut_centre_gravite"] = st.checkbox("Validation de la position du centre de gravité", value=get_val("grut_centre_gravite"))
                    st.session_state.form_data["grut_angles_elingue"] = st.checkbox("Angles d'élingage conformes aux abaques de levage", value=get_val("grut_angles_elingue"))
                    st.session_state.form_data["grut_plaques_rep"] = st.checkbox("Plaques de répartition posées après vérification de la portance du sol", value=get_val("grut_plaques_rep"))

                    st.write("##### Équipe de levage désignée :")
                    st.write(f"• Chef de manœuvre : `{get_val('grut_chef_m_nom')} ({get_val('grut_chef_m_soc')})`")
                    st.write(f"• Élingueur qualifié : `{get_val('grut_elingueur_nom')} ({get_val('grut_elingueur_soc')})`")
                    st.write(f"• Grutier habilité : `{get_val('grut_grutier_nom')} ({get_val('grut_grutier_soc')})`")

                    st.write("##### Conformité réglementaire des équipements :")
                    st.session_state.form_data["grut_certif_grue"] = st.checkbox(f"Rapport de VGP de la grue à jour ({get_val('grut_immat')})", value=get_val("grut_certif_grue"))
                    st.session_state.form_data["grut_certif_acc"] = st.checkbox("Certificats de conformité des accessoires de levage (élingues, manilles)", value=get_val("grut_certif_acc"))
                    st.session_state.form_data["grut_certif_plaques"] = st.checkbox("Conformité des plaques de répartition", value=get_val("grut_certif_plaques"))
                    st.session_state.form_data["grut_check_j_grue"] = st.checkbox("Checklist de prise de poste de la grue réalisée", value=get_val("grut_check_j_grue"))
                    st.session_state.form_data["grut_check_j_acc"] = st.checkbox("Inspection visuelle quotidienne des élingues réalisée", value=get_val("grut_check_j_acc"))

                    st.write("##### Contrôle des points d'ancrage et de la charge :")
                    st.session_state.form_data["grut_pattes_concu"] = st.checkbox("Pattes et oreilles de levage homologuées", value=get_val("grut_pattes_concu"))
                    st.session_state.form_data["grut_pattes_defaut"] = st.checkbox("Absence de fissures ou déformations sur les points d'ancrage", value=get_val("grut_pattes_defaut"))
                    st.session_state.form_data["grut_pattes_adequation"] = st.checkbox("Adéquation crochets / manilles / points d'ancrage", value=get_val("grut_pattes_adequation"))
                    st.session_state.form_data["grut_charges_annexes"] = st.checkbox("Sécurisation contre la chute d'éléments amovibles sur la charge", value=get_val("grut_charges_annexes"))

                    st.session_state.form_data["grut_schema_commentaires"] = st.text_area(
                        "Schéma de la trajectoire du levage ou remarques particulières :", 
                        value=get_val("grut_schema_commentaires"), 
                        key="grut_schema_commentaires_input"
                    )

                    st.write("##### Validations obligatoires :")
                    st.text_input("1. Chef de manœuvre (Société extérieure) :", value=get_val("grut_chef_m_nom"))
                    st.session_state.form_data["grut_do_sign"] = st.text_input("2. Donneur d'Ordre P&G :", value=get_val("grut_do_sign"))
                    st.session_state.form_data["grut_casque_rouge_sign"] = st.text_input("3. Casque Rouge P&G :", value=get_val("grut_casque_rouge_sign"))

            # 6. ESPACE CONFINÉ
            if get_val("p_confine"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#003366;'>🦺 ESPACE CONFINÉ</h3></div>", unsafe_allow_html=True)
                    st.error("🥽 **EPI obligatoire :** Masque auto-sauveteur à évacuation rapide (type M20)")

                    st.session_state.form_data["conf_lieu"] = st.text_input("Désignation précise de la cuve, capacité ou de la zone fermée :", value=get_val("conf_lieu"))

                    st.write("##### Identification des risques atmosphériques et physiques :")
                    cr1, cr2, cr3 = st.columns(3)
                    with cr1:
                        st.session_state.form_data["conf_r_atmo"] = st.checkbox("Risque d'atmosphère anoxique ou toxique", value=get_val("conf_r_atmo"))
                        st.session_state.form_data["conf_r_chimique"] = st.checkbox("Présence de résidus chimiques", value=get_val("conf_r_chimique"))
                        st.session_state.form_data["conf_r_inflam"] = st.checkbox("Vapeurs ou poussières inflammables", value=get_val("conf_r_inflam"))
                    with cr2:
                        st.session_state.form_data["conf_r_orga"] = st.checkbox("Décomposition de matières organiques", value=get_val("conf_r_orga"))
                        st.session_state.form_data["conf_r_meca"] = st.checkbox("Équipement mécanique / mobile interne", value=get_val("conf_r_meca"))
                        st.session_state.form_data["conf_r_thermiq"] = st.checkbox("Fluides chauds / Risque de brûlure", value=get_val("conf_r_thermiq"))
                    with cr3:
                        st.session_state.form_data["conf_r_bruit"] = st.checkbox("Niveau sonore entravant la communication", value=get_val("conf_r_bruit"))
                        st.session_state.form_data["conf_troudhomme_610"] = st.checkbox("Dimension du trou d'homme ≥ 610 mm", value=get_val("conf_troudhomme_610"))

                    if not get_val("conf_troudhomme_610"):
                        st.error("🚨 **Accès étroit (<610mm) :** Déploiement d'un plan d'extraction et de secours spécifique.")

                    st.write("##### Qualifications et équipements individuels :")
                    st.session_state.form_data["conf_catec"] = st.checkbox("Attestation CATEC valide pour tous les intervenants", value=get_val("conf_catec"))
                    st.session_state.form_data["conf_hauteur"] = st.checkbox("Dispositif anti-chute / Harnais d'extraction", value=get_val("conf_hauteur"))
                    st.session_state.form_data["conf_m20"] = st.checkbox("Dotation individuelle du masque auto-sauveteur M20", value=get_val("conf_m20"))

                    st.write("##### Organisation des secours et de la prévention :")
                    st.write(f"• Secouriste désigné sur la zone : `{get_val('conf_secouriste')}`")
                    st.write(f"• Service médical d'urgence rattaché : `{get_val('conf_medical')}`")

                    st.session_state.form_data["conf_action_chaud"] = st.checkbox("Réalisation de travaux de découpe, ponçage ou soudage à l'intérieur", value=get_val("conf_action_chaud"))
                    if get_val("conf_action_chaud"):
                        st.warning("⚠️ **Travaux à chaud en milieu confiné :** Délivrance parallèle du Permis Point Chaud requise.")
                        st.session_state.form_data["p_points_chauds"] = True

                    st.session_state.form_data["conf_ventilation_nat"] = st.checkbox("Aération naturelle préalable suffisante (débutée 48h avant)", value=get_val("conf_ventilation_nat"))
                    st.session_state.form_data["conf_ventilation_forcee"] = st.checkbox("Mise en place d'une ventilation mécanique forcée", value=get_val("conf_ventilation_forcee"))
                    if get_val("conf_ventilation_forcee"):
                        st.info("Débit de renouvellement d'air requis : Minimum 56 m³/h par intervenant.")

                    st.session_state.form_data["conf_consignation_gaz"] = st.checkbox("Consignation et obturation rigide des tuyauteries de fluides/gaz", value=get_val("conf_consignation_gaz"))
                    if get_val("conf_consignation_gaz"):
                        st.info("Renvoi au permis de Consignation LOTO / Pose de joints pleins.")
                        st.session_state.form_data["p_consignation"] = True

                    st.session_state.form_data["conf_cuve_vide"] = st.checkbox("Vidange complète et absence de risque d'ennoyage", value=get_val("conf_cuve_vide"))
                    st.session_state.form_data["conf_vol_caches"] = st.checkbox("Absence de pannes ou zones mortes susceptibles de retenir des gaz", value=get_val("conf_vol_caches"))
                    st.session_state.form_data["conf_eclairage_24v"] = st.checkbox("Éclairage Très Basse Tension de Sécurité (TBT 24V ou ATEX)", value=get_val("conf_eclairage_24v"))
                    st.session_state.form_data["conf_blocage_ouvert"] = st.checkbox("Verrouillage physique des accès en position ouverte", value=get_val("conf_blocage_ouvert"))

                    st.session_state.form_data["conf_echaf_echelle"] = st.checkbox("Montage d'une échelle ou d'un échafaudage intérieur", value=get_val("conf_echaf_echelle"))

                    st.session_state.form_data["conf_prod_chim"] = st.checkbox("Antécédent de stockage de produits chimiques dans l'équipement", value=get_val("conf_prod_chim"))
                    if get_val("conf_prod_chim"):
                        st.warning("⚠ **Produits chimiques :** Contrôler la Valeur Limite d'Exposition Professionnelle (VLEP) sur la FDS.")

                    st.session_state.form_data["conf_laser"] = st.checkbox("Absence de sources laser active à l'intérieur", value=get_val("conf_laser"))
                    
                    opts_comm = ["Talkie Walkie", "Visuelle", "téléphone"]
                    st.session_state.form_data["conf_comm_type"] = st.selectbox("Moyen de communication permanent entre l'entrant et le surveillant (Standby) :", opts_comm, index=opts_comm.index(get_val("conf_comm_type")) if get_val("conf_comm_type") in opts_comm else 0)

                    st.write("##### Mesures et contrôles d'atmosphère :")
                    co1, co2 = st.columns(2)
                    with co1:
                        st.session_state.form_data["conf_o2"] = st.number_input("Taux d'Oxygène O₂ mesuré (Seuils : 19,5% < O₂ < 23,0%) :", value=float(get_val("conf_o2")))
                        st.session_state.form_data["conf_o2_contre_mesure"] = st.number_input("Taux d'Oxygène O₂ de contre-mesure (Validation DO) :", value=float(get_val("conf_o2_contre_mesure")))
                    with co2:
                        st.session_state.form_data["conf_h2s_check"] = st.checkbox("Contrôle H₂S requis", value=get_val("conf_h2s_check"))
                        if get_val("conf_h2s_check"):
                            st.session_state.form_data["conf_h2s"] = st.number_input("Concentration en H₂S (ppm) :", value=float(get_val("conf_h2s")))

                        st.session_state.form_data["conf_co_check"] = st.checkbox("Contrôle CO requis", value=get_val("conf_co_check"))
                        if get_val("conf_co_check"):
                            st.session_state.form_data["conf_co"] = st.number_input("Concentration en CO (ppm) :", value=float(get_val("conf_co")))

                        st.session_state.form_data["conf_explo_check"] = st.checkbox("Contrôle d'explosimétrie requis", value=get_val("conf_explo_check"))
                        if get_val("conf_explo_check"):
                            st.session_state.form_data["conf_explo"] = st.number_input("Niveau d'explosimétrie (% LIE) :", value=float(get_val("conf_explo")))

                    st.session_state.form_data["conf_temp_cuve"] = st.number_input("Température interne mesurée (°C) — Limite max 45°C :", value=float(get_val("conf_temp_cuve")))
                    opts_n2_do = ["N2", "DO"]
                    st.session_state.form_data["conf_verif_temp"] = st.selectbox("Responsable de la mesure de température :", opts_n2_do, index=opts_n2_do.index(get_val("conf_verif_temp")) if get_val("conf_verif_temp") in opts_n2_do else 0)

                    st.session_state.form_data["conf_inflam_lel"] = st.number_input("Mesure des vapeurs inflammables (% LEL) — Doit être < 10% LEL :", value=float(get_val("conf_inflam_lel")))
                    st.session_state.form_data["conf_verif_lel"] = st.selectbox("Responsable du contrôle LEL :", opts_n2_do, index=opts_n2_do.index(get_val("conf_verif_lel")) if get_val("conf_verif_lel") in opts_n2_do else 0)

                    st.session_state.form_data["conf_schema_commentaires"] = st.text_area("Observations ou croquis de la zone confinée :", value=get_val("conf_schema_commentaires"))

                    st.write("##### Signatures d'autorisation d'entrée :")
                    st.session_state.form_data["conf_entrant"] = st.text_input("1. Intervenant(s) entrant(s) :", value=get_val("conf_entrant"))
                    st.session_state.form_data["conf_standby"] = st.text_input("2. Surveillant de trou d'homme (Standby) :", value=get_val("conf_standby"))
                    st.session_state.form_data["conf_do"] = st.text_input("3. Donneur d'Ordre P&G :", value=get_val("conf_do"))

            # 7. TRAVAIL ÉLECTRIQUE
            if get_val("p_electrique"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#b91c1c;'>⚡ TRAVAUX ÉLECTRIQUES</h3></div>", unsafe_allow_html=True)
                    st.warning("🥽 **EPIs de base :** Casque électricien + Gants isolants EN60903 + Surgants cuir + Tenue 100% coton ou ignifugée")
                    st.info("📣 **Règles d'or :** Travaux sous tension interdits. Habilitation obligatoire. Outillage isolé 1000V obligatoire.")

                    st.write("##### Nature de l'opération électrique :")
                    ce1, ce2 = st.columns(2)
                    with ce1:
                        st.session_state.form_data["elec_modife"] = st.checkbox("Modification d'une installation existante", value=get_val("elec_modife"))
                        st.session_state.form_data["elec_armoire"] = st.checkbox("Intervention dans une armoire, coffret ou enveloppe", value=get_val("elec_armoire"))
                        st.session_state.form_data["elec_voisinage_tension"] = st.checkbox("Travail en zone de voisinage simple", value=get_val("elec_voisinage_tension"))
                        st.session_state.form_data["elec_courant_faible"] = st.checkbox("Travaux en courants faibles / Automatisme", value=get_val("elec_courant_faible"))
                    with ce2:
                        st.session_state.form_data["elec_releve"] = st.checkbox("Relevés, mesures de tension ou essais", value=get_val("elec_releve"))
                        st.session_state.form_data["elec_chemins"] = st.checkbox("Pose de chemins de câbles et raccordements hors tension", value=get_val("elec_chemins"))
                        st.session_state.form_data["elec_voisinage_nues"] = st.checkbox("Intervention au voisinage de pièces nues sous tension", value=get_val("elec_voisinage_nues"))

                    if get_val("elec_voisinage_nues"):
                        st.error("🔒 **Voisinage renforcé sous tension :** Validation écrite obligatoire par une personne chargée d'aménagements (Habilité B2/H2, BC/HC).")
                        st.error("🥽 **EPIs complémentaires :** Écran facial anti-arc (EN166B / GS-ET-29) + Veste anti-arc (EN ISO 11612) + Tapis isolant (EN 61112).")
                        st.session_state.form_data["elec_valideur_ei"] = st.text_input("Nom de la personne chargée d'essais / Chargé de consignation (E&I) :", value=get_val("elec_valideur_ei"))

            # 8. CONSIGNATION LOTO
            if get_val("p_consignation"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#15803d;'>⚡ CONSIGNATION ÉNERGIES (LOTO 3 PHASES)</h3></div>", unsafe_allow_html=True)
                    
                    opts_loto_m = ["2 vannes et vanne de drain", "2 vannes", "vanne simple", "vanne et désolidarisation de la conduite", "joint plein", "joint plein et désolidarisation de la conduite"]
                    st.write("##### Isolation de tuyauterie et ouverture de circuit :")
                    st.session_state.form_data["loto_ouverture_methode"] = st.selectbox(
                        "Méthode d'isolement fluide sélectionnée :",
                        opts_loto_m, index=opts_loto_m.index(get_val("loto_ouverture_methode")) if get_val("loto_ouverture_methode") in opts_loto_m else 0
                    )
                    
                    clo1, clo2 = st.columns(2)
                    with clo1: st.session_state.form_data["loto_ouvert_loc1"] = st.text_input("Point d'isolation principal (Localisation 1) :", value=get_val("loto_ouvert_loc1"))
                    with clo2:
                        if "vanne simple" not in get_val("loto_ouverture_methode") and "joint plein" != get_val("loto_ouverture_methode"):
                            st.session_state.form_data["loto_ouvert_loc2"] = st.text_input("Point d'isolation secondaire (Localisation 2) :", value=get_val("loto_ouvert_loc2"))

                    st.write("##### Neutralisation des sources d'énergie :")
                    cis1, cis2 = st.columns(2)
                    with cis1:
                        st.session_state.form_data["loto_is_elec"] = st.checkbox("Consignation Électrique (Cadenassage du disjoncteur)", value=get_val("loto_is_elec"))
                        if get_val("loto_is_elec"):
                            st.session_state.form_data["loto_is_elec_loc1"] = st.text_input("Repère armoire / Organe de coupure :", value=get_val("loto_is_elec_loc1"))
                            st.session_state.form_data["loto_is_elec_loc2"] = st.text_input("Numéro du cadenas de condamnation :", value=get_val("loto_is_elec_loc2"))

                        st.session_state.form_data["loto_fusible"] = st.checkbox("Retrait physique de fusibles de puissance", value=get_val("loto_fusible"))
                        if get_val("loto_fusible"):
                            st.session_state.form_data["loto_fusible_loc1"] = st.text_input("Localisation du coffret à fusibles :", value=get_val("loto_fusible_loc1"))
                            st.session_state.form_data["loto_fusible_loc2"] = st.text_input("Référence du cadenas / Condamnation :", value=get_val("loto_fusible_loc2"))

                        st.session_state.form_data["loto_cable"] = st.checkbox("Déconnexion mécanique de câbles de puissance", value=get_val("loto_cable"))
                        if get_val("loto_cable"):
                            st.session_state.form_data["loto_cable_loc1"] = st.text_input("Point de déconnexion du câble :", value=get_val("loto_cable_loc1"))
                            st.session_state.form_data["loto_cable_loc2"] = st.text_input("Consigne d'isolement :", value=get_val("loto_cable_loc2"))

                    with cis2:
                        st.session_state.form_data["loto_pneu"] = st.checkbox("Consignation Pneumatique (Purge + Cadenas)", value=get_val("loto_pneu"))
                        if get_val("loto_pneu"):
                            st.session_state.form_data["loto_pneu_loc1"] = st.text_input("Vanne de purge pneumatique :", value=get_val("loto_pneu_loc1"))
                            st.session_state.form_data["loto_pneu_loc2"] = st.text_input("Emplacement cadenas LOTO :", value=get_val("loto_pneu_loc2"))

                        st.session_state.form_data["loto_hydra"] = st.checkbox("Consignation Hydraulique", value=get_val("loto_hydra"))
                        if get_val("loto_hydra"):
                            st.session_state.form_data["loto_hydra_loc1"] = st.text_input("Organe d'isolement hydraulique :", value=get_val("loto_hydra_loc1"))
                            st.session_state.form_data["loto_hydra_loc2"] = st.text_input("Contrôle de zéro pression :", value=get_val("loto_hydra_loc2"))

                        st.session_state.form_data["loto_residu"] = st.checkbox("Dissipation des Énergies Résiduelles (Mise à la terre, purge...)", value=get_val("loto_residu"))
                        if get_val("loto_residu"):
                            st.session_state.form_data["loto_residu_loc1"] = st.text_input("Méthode de purge / dépressurisation :", value=get_val("loto_residu_loc1"))
                            st.session_state.form_data["loto_residu_loc2"] = st.text_input("Contrôle visuel (ex: Manomètre à 0) :", value=get_val("loto_residu_loc2"))

                    st.write("##### Nettoyage et préparation de la zone d'intervention :")
                    cn1, cn2 = st.columns(2)
                    with cn1:
                        st.session_state.form_data["loto_drain_ouvert"] = st.checkbox("Vanne de vidange / drain maintenue ouverte", value=get_val("loto_drain_ouvert"))
                        st.session_state.form_data["loto_eq_ouvert"] = st.checkbox("Équipement ouvert à l'atmosphère", value=get_val("loto_eq_ouvert"))
                    with cn2:
                        st.session_state.form_data["loto_eq_lave"] = st.checkbox("Équipement rincé et lavé", value=get_val("loto_eq_lave"))
                        st.session_state.form_data["loto_eq_sanitise"] = st.checkbox("Équipement sanitisé / décontaminé", value=get_val("loto_eq_sanitise"))

            # 9. SYSTÈME À RISQUES / ATEX / CHIMIQUE
            if get_val("p_systeme_risque"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#b91c1c;'>☣ SYSTÈMES À RISQUES / CHIMIQUE / ATEX</h3></div>", unsafe_allow_html=True)
                    st.info("Consignation et neutralisation préalable des fluides obligatoires.")

                    st.write("##### Nature du risque produit :")
                    st.session_state.form_data["sr_chimique_c1"] = st.checkbox("Produit chimique de Classe 1 (BFA, Éthanol, Néodol, Acide Chlorhydrique)", value=get_val("sr_chimique_c1"))
                    if get_val("sr_chimique_c1"):
                        st.session_state.form_data["sr_chimique_nom"] = st.text_input("Désignation exacte du produit Classe 1 :", value=get_val("sr_chimique_nom"))

                    st.session_state.form_data["sr_fluide_dang"] = st.checkbox("Fluides dangereux (Parfum, Soude Caustique, Azote, Vapeur, Gaz Naturel)", value=get_val("sr_fluide_dang"))
                    if get_val("sr_fluide_dang"):
                        st.session_state.form_data["sr_fluide_nom"] = st.text_input("Désignation du fluide dangereux :", value=get_val("sr_fluide_nom"))

                    st.session_state.form_data["sr_atex"] = st.checkbox("Intervention en Zone ATEX (Atmosphère Explosible)", value=get_val("sr_atex"))
                    if get_val("sr_atex"):
                        st.session_state.form_data["sr_atex_nom"] = st.text_input("Identifiant du produit ou gaz responsable de la zone ATEX :", value=get_val("sr_atex_nom"))

                    st.write("##### Contrôles préventifs avant démarrage :")
                    cera1, cera2 = st.columns(2)
                    with cera1:
                        st.session_state.form_data["sr_balisage"] = st.checkbox("Balisage de sécurité étendu mis en place", value=get_val("sr_balisage"))
                        st.session_state.form_data["sr_douche_rince"] = st.checkbox("Test préalable de la douche de sécurité et du rince-œil", value=get_val("sr_douche_rince"))
                        st.session_state.form_data["sr_ramonage"] = st.checkbox("Ramonage / Purge préalable de conduite réalisée", value=get_val("sr_ramonage"))
                        if get_val("sr_ramonage"):
                            st.session_state.form_data["sr_ramonage_dt"] = st.text_input("Horodatage du ramonage (Date et Heure) :", value=get_val("sr_ramonage_dt"))
                    with cera2:
                        st.session_state.form_data["sr_isolement"] = st.checkbox("Validation de l'isolement effectif des circuits", value=get_val("sr_isolement"))
                        st.session_state.form_data["sr_feuille_loto"] = st.checkbox("Fiche de consignation LOTO complétée et affichée sur site", value=get_val("sr_feuille_loto"))
                        if get_val("sr_atex"):
                            st.session_state.form_data["sr_zonage_atex"] = st.checkbox("Vérification du plan de zonage ATEX (Zone 0, 1 ou 2)", value=get_val("sr_zonage_atex"))

                    st.write("##### Équipements de Protection Individuelle Spécifiques (EPIs Chimiques/ATEX) :")
                    cepi1, cepi2 = st.columns(2)
                    with cepi1:
                        st.session_state.form_data["sr_epi_ecran"] = st.checkbox("Écran facial hermétique aux éclaboussures", value=get_val("sr_epi_ecran"))
                        st.session_state.form_data["sr_epi_lunettes"] = st.checkbox("Lunettes de sécurité étanches", value=get_val("sr_epi_lunettes"))
                        st.session_state.form_data["sr_epi_gants_chim"] = st.checkbox("Gants de protection chimique homologués (EN374)", value=get_val("sr_epi_gants_chim"))
                        st.session_state.form_data["sr_epi_comb1"] = st.checkbox("Combinaison étanche intégrale 1 pièce (Viton / Néoprène)", value=get_val("sr_epi_comb1"))
                        st.session_state.form_data["sr_epi_comb2"] = st.checkbox("Combinaison anti-acide 2 pièces", value=get_val("sr_epi_comb2"))
                        st.session_state.form_data["sr_epi_bottes"] = st.checkbox("Bottes de sécurité anti-acide (portées sous le pantalon)", value=get_val("sr_epi_bottes"))
                    with cepi2:
                        st.session_state.form_data["sr_epi_cartouche"] = st.checkbox("Masque de protection à cartouche chimique adaptée", value=get_val("sr_epi_cartouche"))
                        st.session_state.form_data["sr_epi_ari"] = st.checkbox("Appareil Respiratoire Isolant (ARI)", value=get_val("sr_epi_ari"))
                        st.session_state.form_data["sr_epi_3m6000"] = st.checkbox("Masque demi-facial panoramique 3M Serie 6000", value=get_val("sr_epi_3m6000"))
                        st.session_state.form_data["sr_epi_versaflo"] = st.checkbox("Casque à ventilation assistée Versaflo avec cartouche chimique", value=get_val("sr_epi_versaflo"))
                        st.session_state.form_data["sr_epi_no_versaflo"] = st.checkbox("Absence d'obligation de casque Versaflo", value=get_val("sr_epi_no_versaflo"))

                    st.session_state.form_data["sr_auxiliaire_equipe"] = st.checkbox("Auxiliaire / Vigie équipé des mêmes EPIs que l'intervenant", value=get_val("sr_auxiliaire_equipe"))
                    st.session_state.form_data["sr_comm_moyen"] = st.text_input("Moyen de communication certifié (ex: Talkie-Walkie ATEX) :", value=get_val("sr_comm_moyen"))

                    st.write("##### Inspections de fin de travaux :")
                    st.session_state.form_data["sr_inspect_remise"] = st.checkbox("Inspection et contrôle d'étanchéité du circuit après intervention", value=get_val("sr_inspect_remise"))
                    if get_val("sr_inspect_remise"):
                        st.session_state.form_data["sr_inspect_nom"] = st.text_input("Nom de l'inspecteur qualifié :", value=get_val("sr_inspect_nom"))
                        st.session_state.form_data["sr_inspect_dt"] = st.text_input("Date et heure de l'inspection :", value=get_val("sr_inspect_dt"))

                    st.session_state.form_data["sr_schema_commentaires"] = st.text_area(
                        "Schéma ou remarques particulières concernant le système à risques :", 
                        value=get_val("sr_schema_commentaires"), 
                        key="sr_schema_commentaires_input"
                    )

                    st.write("##### Signatures tripartites Systèmes à Risques :")
                    st.session_state.form_data["sr_sign_intervenant"] = st.text_input("1. Intervenant habilité au risque chimique/ATEX :", value=get_val("sr_sign_intervenant"))
                    st.session_state.form_data["sr_sign_do"] = st.text_input("2. Donneur d'Ordre P&G :", value=get_val("sr_sign_do"))
                    st.session_state.form_data["sr_sign_operations"] = st.text_input("3. Responsable Opérations / Fabrication :", value=get_val("sr_sign_operations"))

            st.info("📣 **Rappel :** Les EPIs demandés dans ces permis spécifiques complètent les EPIs de base exigés pour le permis général.")

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
            if get_val("p_meuleuse"):
                tableau_data.append({"activite": "Meuleuse / Tronçonneuse", "risque": "Projections / Coupure", "prevention": f"Écran facial EN166B + Disque {get_val('meuleuse_diametre')} + Point Chaud"})
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
