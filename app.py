import datetime
import streamlit as st
import io

# ---------------------------------------------------------
# CONFIGURATION DE LA PAGE STREAMLIT
# ---------------------------------------------------------
st.set_page_config(
    page_title="P&G Amiens — e-Work Permit System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS P&G (Fond adouci #f1f5f9, Style Cartes & Stepper)
st.markdown("""
<style>
    .stApp {
        background-color: #f1f5f9 !important;
    }
    .main {
        background-color: #f1f5f9;
    }
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
    .stButton>button {
        border-radius: 8px; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

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
        "pr": "PR-2 (Parking Ouest)",
        "confinement": "ZC-01 (Hall M1)",
        "urgence": "03.22.54.33.33 (Poste Garde M1)"
    },
    "Bâtiment M1 - Bureaux": {
        "pr": "PR-2 (Parking Ouest)",
        "confinement": "ZC-01 (Hall M1)",
        "urgence": "03.22.54.30.00 (Infirmerie M1)"
    },
    "Bâtiment M2 - Conditionnement": {
        "pr": "PR-4 (Zone Nord)",
        "confinement": "ZC-03 (Atrium M2)",
        "urgence": "03.22.54.33.34 (Poste Garde M2)"
    },
    "Zone Extérieure / Logistique": {
        "pr": "PR-1 (Entrée Principale)",
        "confinement": "ZC-00 (Poste Central)",
        "urgence": "03.22.54.33.33 (SAMU Site)"
    }
}

activites_meuleuse = [
    "Ajustement découpe tuyauterie / profilé acier",
    "Arasement de cordon de soudure",
    "Tronçonnage de tige filetée / supportage",
    "Ébavurage de pièce métallique",
    "Saignée dans béton / maçonnerie",
    "Autre activité (Préciser en texte libre)"
]

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
                {"activite": "Rénovation Peinture", "risque": "Inhalation solvants / Espace exigu", "prevention": "Masque FFP2 / ABEK + Ventilation"},
                {"activite": "Découpe supportage", "risque": "Projections étincelles / Bruit", "prevention": "Lunettes EN 166 + Bouchons d'oreilles"}
            ]
        }
    ]

# Navigation Kiosk
if "kiosk_mode" not in st.session_state:
    st.session_state.kiosk_mode = "HOME" # HOME, PDP, PERMIS
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
        "intervenants": ["Léa DUSEK"],
        
        # Permis Spécifiques
        "p_hauteur": False,
        "p_toiture": False,
        "p_points_chauds": False,
        "p_excavation": False,
        "p_grutage": False,
        "p_confine": False,
        "p_electrique": False,
        "p_consignation_pression": False,
        "p_consignation_mecanique": False,
        "p_consignation_equipement": False,
        "p_consignation_laser": False,
        "p_chimique": False,
        "p_demolition": False,

        # STA & Outils
        "sta_prod_chimique": False,
        "produits_liste": "",
        "sta_dta": False,
        "sta_electroportatif": False,
        "sta_meuleuse": False,
        "meuleuse_activite": activites_meuleuse[0],
        "meuleuse_texte_libre": "",
        "sta_pirl_nacelle": False,
        "sta_couteau_lame": False,
        "sta_echelle_escabeau": False,

        # Dangers & Risques
        "r_exigu": False,
        "r_superpose": False,
        "r_inconfortable": False,
        "r_fumee_poussiere": False,
        "r_bruit_80db": False,
        "r_rayonnement": False,
        "r_enzymes": False,
        "r_eq_mouvement": False,
        "r_chute_objets": False,
        "r_vehicule": False,
        "r_escalier": False,
        "r_liquide_sol": False,
        "r_ouverture_sol": False,
        "r_stockage_sol": False,
        "r_bords_tranchants": False,
        "r_perforation": False,
        "r_metaux_chaud": False,
        "r_metaux_froid": False,
        "r_feu_flamme": False,
        "r_cables_sol": False,
        "r_voies_circulation": False,
        "r_stockage_defini": True,

        # TMS
        "tms_lourd": False,
        "tms_repetitif": False,
        "tms_torsion": False,
        "tms_statique": False,

        # EPIs
        "epi_lunettes_en166": True,
        "epi_lunettes_etanches": False,
        "epi_visiere_idra": False,
        "epi_pare_visage": False,
        "epi_casque_jugulaire": True,
        "epi_casque_auditif": False,
        "epi_gants_coupure": True,
        "epi_gants_manutention": False,
        "epi_gants_chimique": False,
        "epi_gants_electrique": False,
        "epi_bouchons_type": "Jetables",
        "epi_ffp1_ffp2": True,
        "epi_3m6000": False,
        "epi_versaflo": False,
        "epi_cartouche_abek": False,
        "epi_autre": "",

        # Détails Spécifiques
        "confine_o2": "20.9 %",
        "confine_vigie": "Matthieu MARTIN",
        "chaud_travaux": "Soudure Chalumeau / Meulage",
        "loto_cadenas": "LOTO-PG-884"
    }

# ---------------------------------------------------------
# BARRE LATÉRALE - SÉLECTION DES INTERFACES
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

# Fonction Génération Fichier PDF Texte/Récapitulatif
def generer_contenu_pdf(permis):
    st_text = f"=== PROCTER & GAMBLE AMIENS - PERMIS DE TRAVAIL OFFICIEL ===\n"
    st_text += f"REF PERMIS : {permis['id']} | DATE : {permis['date_travaux']}\n"
    st_text += f"STATUT : {'VALIDÉ' if permis['statut'] == 'VALIDÉ' else 'PERMIS EN ATTENTE DE VALIDATION'}\n"
    st_text += f"-----------------------------------------------------------\n"
    st_text += f"ENTREPRISE : {permis['societe']} | PDP : {permis['pdp']}\n"
    st_text += f"MODE OPÉRATOIRE : {permis.get('mop', 'MoP Standard')}\n"
    st_text += f"RESPONSABLE N2 : {permis['n2']}\n"
    st_text += f"LOCALISATION : {permis['zone']} ({permis.get('emplacement', 'N/A')})\n"
    st_text += f"POINT DE RASSEMBLEMENT : {permis.get('pr')} | CONFINEMENT : {permis.get('confinement')}\n"
    st_text += f"POSTE URGENCE SECTEUR : {permis.get('urg')}\n"
    st_text += f"-----------------------------------------------------------\n"
    st_text += f"INTERVENANTS SIGNATAIRES :\n"
    for sign in permis.get('intervenants', []):
        st_text += f" - {sign} [Signature Tactile Horodatée]\n"
    st_text += f"-----------------------------------------------------------\n"
    st_text += f"PERMIS SPÉCIFIQUES & DÉROGATIONS :\n"
    spe_all = permis.get('permis_specifiques', []) + permis.get('derogations', [])
    if spe_all:
        for s in spe_all:
            st_text += f" - [!] {s}\n"
    else:
        st_text += " - Aucun permis spécifique requis\n"
    st_text += f"-----------------------------------------------------------\n"
    st_text += f"VALIDATIONS ET APPROBATIONS :\n"
    if permis['statut'] == 'VALIDÉ':
        st_text += f" [OK] VALIDATION BATCH DONNEUR D'ORDRE (DO) : Validé à 07h30\n"
        st_text += f" [OK] VALIDATION EHS / CASQUE ROUGE : Conforme sur zone\n"
    else:
        st_text += f" [PENDING] VALIDATION BATCH DONNEUR D'ORDRE (DO) : En attente du batch 07h30\n"
    return st_text.encode('utf-8')

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

    # PAGE D'ACCUEIL VRAIE
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
            if st.button("🚀 COMMANCER UN PERMIS DE TRAVAIL", type="primary", use_container_width=True):
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

    # PARCOURS 1 : ÉMARGEMENT PDP
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

    # PARCOURS 2 : PERMIS DE TRAVAIL (PERMIS)
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

        # ÉTAPE 1 : DATE & ENTREPRISE
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

        # ÉTAPE 2 : PDP & MoP
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

        # ÉTAPE 3 : RESPONSABLE N2
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

        # ÉTAPE 4 : CARTOGRAPHIE & URGENCES
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

        # ÉTAPE 5 : CHECK-LIST INTEGRALE & EPIs
        elif current_step == 5:
            st.subheader("5. Check-list Intégrale, STA, Dangers & EPIs Normés")

            st.error("🚨 **Identification des Risques Principaux ➔ Déclencheurs de Permis Spécifiques (HRT)**")
            c_rp1, c_rp2 = st.columns(2)
            with c_rp1:
                st.session_state.form_data["p_hauteur"] = st.checkbox("Travail en hauteur / échafaudage / nacelle ➔ Permis Hauteur", value=st.session_state.form_data["p_hauteur"])
                st.session_state.form_data["p_toiture"] = st.checkbox("Accès toiture ➔ Permis Accès Toiture", value=st.session_state.form_data["p_toiture"])
                st.session_state.form_data["p_points_chauds"] = st.checkbox("Génération de points chauds / flamme ➔ Permis Point Chaud", value=st.session_state.form_data["p_points_chauds"])
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
                    st.session_state.form_data["sta_meuleuse"] = st.checkbox("Utilisation d'une Meuleuse d'angle ➔ Dérogation Meuleuse", value=st.session_state.form_data["sta_meuleuse"])
                    if st.session_state.form_data["sta_meuleuse"]:
                        st.session_state.form_data["meuleuse_activite"] = st.selectbox("Activité réalisée à la meuleuse :", activites_meuleuse)
                        if "Autre" in st.session_state.form_data["meuleuse_activite"]:
                            st.session_state.form_data["meuleuse_texte_libre"] = st.text_input("Préciser l'activité meuleuse :")

                st.session_state.form_data["sta_couteau_lame"] = st.checkbox("Utilisation de couteau / lame ouverte ➔ Dérogation Casque Rouge", value=st.session_state.form_data["sta_couteau_lame"])
                if st.session_state.form_data["sta_couteau_lame"]:
                    st.session_state.form_data["r_bords_tranchants"] = True

                st.session_state.form_data["sta_echelle_escabeau"] = st.checkbox("Utilisation d'échelle / escabeau / marche-pied ➔ Dérogation Casque Rouge", value=st.session_state.form_data["sta_echelle_escabeau"])

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
                st.session_state.form_data["r_metaux_chaud"] = st.checkbox("Métaux soudés à chaud ➔ Pt Chaud", value=st.session_state.form_data["r_metaux_chaud"])
                st.session_state.form_data["r_feu_flamme"] = st.checkbox("Feu / Flamme ➔ Pt Chaud", value=st.session_state.form_data["r_feu_flamme"])
                st.session_state.form_data["r_cables_sol"] = st.checkbox("Gestion des câbles au sol", value=st.session_state.form_data["r_cables_sol"])

            st.divider()

            st.warning("""
            📢 **Consigne Sécurité Chantier P&G Amiens :**  
            *Les chaussures de sécurité montantes, le casque avec jugulaire, les lunettes de sécurité à protection latérale (EN 166), le gilet haute visibilité (sauf pour travaux électriques ou point chaud) et les gants anti-coupure sont OBLIGATOIRES sur le chantier de construction.*
            """)

            st.write("##### 🥽 Équipements de Protection Individuelle (EPIs Normés)")
            col_e1, col_e2, col_e3 = st.columns(3)
            with col_e1:
                st.markdown("**👓 Protection Oculaire**")
                st.session_state.form_data["epi_lunettes_en166"] = st.checkbox("Lunettes EN 166 (Chantier)", value=st.session_state.form_data["epi_lunettes_en166"])
                st.session_state.form_data["epi_visiere_idra"] = st.checkbox("Visière Casque IDRA (EN 166B)", value=st.session_state.form_data["epi_visiere_idra"])

                st.markdown("**🪖 Casque de Sécurité**")
                st.session_state.form_data["epi_casque_jugulaire"] = st.checkbox("Casque avec Jugulaire (EN 387/A1)", value=st.session_state.form_data["epi_casque_jugulaire"])

            with col_e2:
                st.markdown("**🧤 Protection des Mains**")
                st.session_state.form_data["epi_gants_coupure"] = st.checkbox("Gants Anti-coupures (4543 / 4X43D)", value=st.session_state.form_data["epi_gants_coupure"])
                st.session_state.form_data["epi_gants_chimique"] = st.checkbox("Gants Chimiques (EN 374-1/2)", value=st.session_state.form_data["epi_gants_chimique"])

                st.markdown("**🎧 Protection Auditive**")
                st.session_state.form_data["epi_bouchons_type"] = st.radio("Bouchons d'oreilles :", ["Non requis", "Jetables", "Moulés sur mesure"], horizontal=True)

            with col_e3:
                st.markdown("**🫁 Protection Respiratoire**")
                st.session_state.form_data["epi_ffp1_ffp2"] = st.checkbox("Masque FFP1 / FFP2", value=st.session_state.form_data["epi_ffp1_ffp2"])
                st.session_state.form_data["epi_3m6000"] = st.checkbox("Masque demi-face 3M 6000", value=st.session_state.form_data["epi_3m6000"])

            c_back, c_next = st.columns([1, 1])
            with c_back:
                if st.button("⬅️ Précédent"):
                    st.session_state.step = 4
                    st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"):
                    st.session_state.step = 6
                    st.rerun()

        # ÉTAPE 6 : PERMIS & DÉROGATIONS SPÉCIFIQUES DÉCLENCHÉS
        elif current_step == 6:
            st.subheader("6. Permis Spécifiques (HRT) & Dérogations Générés")

            if st.session_state.form_data["p_confine"]:
                st.info("🦺 **PERMIS ESPACE CONFINÉ (CBA 105)**")
                c_c1, c_c2 = st.columns(2)
                with c_c1: st.session_state.form_data["confine_o2"] = st.text_input("Taux O2 mesuré :", value=st.session_state.form_data["confine_o2"])
                with c_c2: st.session_state.form_data["confine_vigie"] = st.text_input("Nom de la Vigie Extérieure :", value=st.session_state.form_data["confine_vigie"])

            if st.session_state.form_data["p_points_chauds"] or st.session_state.form_data["r_feu_flamme"] or st.session_state.form_data["r_metaux_chaud"]:
                st.warning("🔥 **PERMIS POINTS CHAUDS / SOUDURE**")
                st.session_state.form_data["chaud_travaux"] = st.text_input("Nature des travaux de chauffe :", value=st.session_state.form_data["chaud_travaux"])

            if st.session_state.form_data["p_consignation_pression"] or st.session_state.form_data["p_consignation_mecanique"]:
                st.success("⚡ **CONSIGNATION / DECONSIGNATION (LOTO)**")
                st.session_state.form_data["loto_cadenas"] = st.text_input("Numéro de Cadenas LOTO :", value=st.session_state.form_data["loto_cadenas"])

            if st.session_state.form_data["sta_meuleuse"]:
                st.error("⚠️ **DÉROGATION UTILISATION MEULEUSE D'ANGLE**")
                st.write(f"- **Activité enregistrée :** {st.session_state.form_data['meuleuse_activite']}")

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
        # ÉTAPE 7 : SYNTHÈSE, PDF & CO-SIGNATURES TACTILES
        # =====================================================
        elif current_step == 7:
            st.subheader("7. Synthèse Globale, Visualisation & Co-signatures Tactiles")

            # ENCART VISUEL STATUT TEMPORAIRE
            st.markdown("<div class='status-pending'>⚠️ ENCART TEMPORAIRE : PERMIS EN ATTENTE DE VALIDATION BATCH (07h30)</div>", unsafe_allow_html=True)

            st.write("##### 📊 1. Tableau Récapitulatif : Activités, Risques Identifiés & Moyens de Prévention")
            
            # Construction du tableau de synthèse dynamique
            tableau_data = []
            if st.session_state.form_data["sta_prod_chimique"]:
                tableau_data.append({"Activités Cochées": "Utilisation Produits Chimiques", "Risques Identifiés": "Inhalation / Contact FDS", "Moyens de Prévention / EPIs": f"Produits: {st.session_state.form_data['produits_liste']} - Masque FFP2/ABEK + Gants EN 374"})
            if st.session_state.form_data["sta_meuleuse"]:
                tableau_data.append({"Activités Cochées": "Meuleuse d'angle", "Risques Identifiés": "Projections étincelles / Éclatement disque", "Moyens de Prévention / EPIs": "Visière EN 166B + Gants Anti-coupure 4543 + Carter"})
            if st.session_state.form_data["p_confine"]:
                tableau_data.append({"Activités Cochées": "Espace Confiné (CBA 105)", "Risques Identifiés": "Asphyxie / Anoxie (Azote)", "Moyens de Prévention / EPIs": f"Mesure O2 ({st.session_state.form_data['confine_o2']}) + Vigie ({st.session_state.form_data['confine_vigie']})"})
            if st.session_state.form_data["p_points_chauds"] or st.session_state.form_data["r_feu_flamme"]:
                tableau_data.append({"Activités Cochées": "Points Chauds / Soudure", "Risques Identifiés": "Incendie / Brûlures", "Moyens de Prévention / EPIs": "Extincteur sur zone + Ronde sécurité 2h après travaux"})
            if st.session_state.form_data["p_hauteur"] or st.session_state.form_data["sta_echelle_escabeau"]:
                tableau_data.append({"Activités Cochées": "Travail en Hauteur / Échelle", "Risques Identifiés": "Chute de hauteur / Chute d'objets", "Moyens de Prévention / EPIs": "Harnais 2 longes + Casque Jugulaire EN 387"})

            if not tableau_data:
                tableau_data.append({"Activités Cochées": "Travaux Généraux du PDP", "Risques Identifiés": "Risques standards de chantier", "Moyens de Prévention / EPIs": "EPIs Obligatoires P&G (Chaussures, Casque jugulaire, Lunettes EN 166, Gants)"})

            st.table(tableau_data)

            st.divider()

            st.write("##### 🦺 2. Cartes Visuelles des Permis Spécifiques & Rappels des Consignes")
            
            c_card1, c_card2 = st.columns(2)
            with c_card1:
                spe_list = []
                if st.session_state.form_data["p_points_chauds"]: spe_list.append("🔥 Permis Point Chaud")
                if st.session_state.form_data["p_confine"]: spe_list.append("🦺 Permis Espace Confiné")
                if st.session_state.form_data["p_hauteur"]: spe_list.append("🧗 Permis Travail en Hauteur")
                if st.session_state.form_data["p_consignation_pression"]: spe_list.append("⚡ Permis Consignation LOTO")

                if spe_list:
                    for s in spe_list:
                        st.info(f"**{s}** — Consignes complémentaires validées et actives sur la zone.")
                else:
                    st.success("✅ Aucun permis spécifique requis.")

            with c_card2:
                derog_list = []
                if st.session_state.form_data["sta_meuleuse"]: derog_list.append("⚠️ Dérogation Meuleuse d'angle")
                if st.session_state.form_data["sta_couteau_lame"]: derog_list.append("⚠️ Dérogation Cutter Lame Ouverte")
                if st.session_state.form_data["sta_echelle_escabeau"]: derog_list.append("⚠️ Dérogation Échelle / Escabeau")

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

            c_back, c_sub, c_pdf = st.columns([1, 2, 2])
            with c_back:
                if st.button("⬅️ Précédent"):
                    st.session_state.step = 6
                    st.rerun()

            with c_sub:
                if st.button(f"🚀 SOUMETTRE LE PERMIS ({st.session_state.form_data['date_str']})", type="primary", use_container_width=True):
                    carto = db_zones_carto.get(st.session_state.form_data["lieu_pdp"], {})

                    derog_final = []
                    if st.session_state.form_data["sta_meuleuse"]: derog_final.append("Meuleuse d'angle")
                    if st.session_state.form_data["sta_couteau_lame"]: derog_final.append("Cutter lame ouverte")
                    if st.session_state.form_data["sta_echelle_escabeau"]: derog_final.append("Échelle/Escabeau")

                    spe_final = []
                    if st.session_state.form_data["p_points_chauds"]: spe_final.append("Points Chauds")
                    if st.session_state.form_data["p_confine"]: spe_final.append("Espace Confiné")
                    if st.session_state.form_data["p_hauteur"]: spe_final.append("Travail Hauteur")
                    if st.session_state.form_data["p_consignation_pression"]: spe_final.append("Consignation (LOTO)")

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
                        "derogations": derog_final,
                        "permis_specifiques": spe_final,
                        "tableau_risques": tableau_data
                    }

                    st.session_state.permis_db.append(nouveau_pt)
                    st.balloons()
                    st.success(f"Permis {nouveau_pt['id']} créé avec succès ! Transmis au DO P&G pour le batch de 07h30.")
                    st.session_state.kiosk_mode = "HOME"

            with c_pdf:
                # Permis temporaire pour génération immédiate du PDF
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
                    "derogations": [],
                    "permis_specifiques": []
                }
                pdf_bytes = generer_contenu_pdf(permis_temp)
                st.download_button(
                    label="📄 TÉLÉCHARGER LE PERMIS PDF (PRÉ-VALIDATION)",
                    data=pdf_bytes,
                    file_name=f"Permis_P_and_G_{permis_temp['id']}_EnAttente.txt",
                    mime="text/plain",
                    use_container_width=True
                )

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
        st.write("Le traitement serveur exécute la fournée quotidienne à 07h30. Cliquez sur le bouton ci-contre pour valider l'ensemble des permis du secteur : l'encart passe au vert 'PERMIS VALIDÉ' et les signatures officielles sont apposées sur les PDFs.")
    with c_btn:
        if st.button("✅ VALIDER LE BATCH (07h30)", type="primary", use_container_width=True):
            for p in st.session_state.permis_db:
                p["statut"] = "VALIDÉ"
            st.success("Fournée de 07h30 validée avec succès ! Les e-mails de notification ont été envoyés avec le PDF mis à jour avec l'encart vert 'PERMIS VALIDÉ' et les signatures de validation.")

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

            # Bouton de téléchargement du PDF mis à jour
            pdf_data = generer_contenu_pdf(pt)
            st.download_button(
                label=f"📄 Télécharger le Permis PDF Officiel ({pt['id']})",
                data=pdf_data,
                file_name=f"Permis_P_and_G_{pt['id']}_{pt['statut']}.txt",
                mime="text/plain",
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
        st.subheader("📄 Document Officiel A4 Numérisé")
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

            # Téléchargement direct du PDF depuis le smartphone Casque Rouge
            pdf_data = generer_contenu_pdf(p)
            st.download_button(
                label="📄 TÉLÉCHARGER LE PERMIS AUDITÉ EN PDF",
                data=pdf_data,
                file_name=f"Permis_P_and_G_{p['id']}_{p['statut']}.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:
            st.info("Cliquez sur 'Simuler Scan QR Code' pour afficher la fiche numérisée.")
