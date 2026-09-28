import datetime
import streamlit as st

# ---------------------------------------------------------
# CONFIGURATION DE LA PAGE STREAMLIT
# ---------------------------------------------------------
st.set_page_config(
    page_title="P&G Amiens — e-Work Permit System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS P&G (Fond doux #f1f5f9, Cartes & Stepper)
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
        background: white; border: 1px solid #cbd5e1; padding: 25px; border-radius: 12px;
        text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 15px;
    }
    .stepper-bar {
        background: white; border: 1px solid #cbd5e1; padding: 12px; border-radius: 10px;
        margin-bottom: 20px; text-align: center; font-weight: bold;
    }
    .stButton>button {
        border-radius: 8px; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# REFERENTIELS & BASES DE DONNÉES P&G
# ---------------------------------------------------------
db_societes = ["ABYLSEN", "APAVE", "AXIMA", "ENGIE", "EULER"]
db_pdps = {
    "ABYLSEN": ["PDP-2026-042 (Bâtiment M1)", "PDP-2026-089 (Bâtiment M2)"],
    "APAVE": ["PDP-2026-104 (Inspection Pression)", "PDP-2026-112 (Conformité Électrique)"],
    "AXIMA": ["PDP-2026-015 (HVAC Zone Production)"],
    "ENGIE": ["PDP-2026-067 (Chaufferie Vapeur)"],
    "EULER": ["PDP-2026-090 (Génie Civil Extérieur)"]
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

etapes_noms = [
    "1. Entreprise", 
    "2. PDP", 
    "3. Responsable N2", 
    "4. Zone & Urgences", 
    "5. STA & EPI", 
    "6. Formulaires Spécifiques", 
    "7. Signatures"
]

# Initialisation de la BDD des permis émis
if "permis_db" not in st.session_state:
    st.session_state.permis_db = [
        {
            "id": "PT-2026-0928-01",
            "societe": "ABYLSEN",
            "pdp": "PDP-2026-042 (Bâtiment M1)",
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
            "permis_specifiques": []
        }
    ]

# Initialisation de l'état du formulaire Kiosk
if "kiosk_mode" not in st.session_state:
    st.session_state.kiosk_mode = "HOME" # HOME, PDP, PERMIS
if "step" not in st.session_state:
    st.session_state.step = 1

# Initialisation des données de saisie
if "form_data" not in st.session_state:
    st.session_state.form_data = {
        "societe": "ABYLSEN",
        "pdp": "PDP-2026-042 (Bâtiment M1)",
        "n2_nom": "Léa DUSEK",
        "lieu_pdp": "Bâtiment M1 - Bureaux",
        "lieu_precision": "1er étage, Bureau 104",
        "description": "Peinture acrylique mur nord bureau 104",
        "intervenants": ["Léa DUSEK"],
        # STA
        "sta_espace_exigu": True,
        "sta_bruit_80db": False,
        "sta_travail_hauteur": False,
        "sta_escalier_tremie": True,
        "sta_fds_presente": True,
        "sta_ventilation_ok": True,
        "sta_sol_glissant": False,
        "sta_outillage_electro": True,
        # EPI
        "epi_chaussures": True,
        "epi_casque_jugulaire": True,
        "epi_lunettes_en166": True,
        "epi_gants_coupure": True,
        "epi_gilet_visibilite": True,
        "epi_masque_ffp2": True,
        "epi_harnais": False,
        "epi_bouchons": False,
        # Risques Spécifiques & Dérogations
        "spe_points_chauds": False,
        "spe_espace_confine": False,
        "spe_consignation_loto": False,
        "spe_grutage": False,
        "derog_meuleuse": False,
        "derog_cutter": False,
        "derog_echelle": False,
        # Détails Spécifiques
        "confine_o2": "20.9 %",
        "confine_h2s": "0 ppm",
        "confine_co": "0 ppm",
        "confine_vigie": "Matthieu MARTIN",
        "chaud_travaux": "Soudure Chalumeau / Meulage",
        "chaud_extincteur": True,
        "loto_cadenas": "LOTO-PG-884"
    }

# ---------------------------------------------------------
# BARRE DE NAVIGATION LATÉRALE (SELECTION DES 3 INTERFACES)
# ---------------------------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Procter_%26_Gamble_logo.svg/1024px-Procter_%26_Gamble_logo.svg.png", width=80)
st.sidebar.title("e-Work Permit P&G")
st.sidebar.caption("Site d'Amiens — Solution Unifiée")

role = st.sidebar.radio(
    "Interface à démonter :",
    [
        "🖥️ Borne Kiosk Tactile (EE / N2)",
        "📊 DDS Board & Batch 07h30 (DO / HSE)",
        "📱 Inspection Terrain QR Code (Casque Rouge)"
    ]
)

# ---------------------------------------------------------
# INTERFACE 1 : BORNE KIOSK TACTILE (EE / N2)
# ---------------------------------------------------------
if role == "🖥️ Borne Kiosk Tactile (EE / N2)":

    st.markdown("""
    <div class="pg-header">
        <h1 style='margin:0; font-size: 2rem;'>PROCTER & GAMBLE — AMIENS</h1>
        <p style='margin:4px 0 0 0; opacity:0.85; font-size: 1rem;'>WORK PERMIT IT | BORNE TACTILE KIOSK</p>
    </div>
    """, unsafe_allow_html=True)

    # ACCUEIL KIOSK
    if st.session_state.kiosk_mode == "HOME":
        st.write("### Bienvenue sur la borne d'accueil sécurité. Choisissez votre opération :")
        st.write("")

        col_act1, col_act2 = st.columns(2)

        with col_act1:
            st.markdown("""
            <div class="welcome-card">
                <h2 style="color:#003366;">🚀 Permis de Travail (PT)</h2>
                <p>Émettre un nouveau Permis de Travail complet (STA, EPI, Cartographie & Formulaires Spécifiques).</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 COMMANCER MON PERMIS DE TRAVAIL", type="primary", use_container_width=True):
                st.session_state.kiosk_mode = "PERMIS"
                st.session_state.step = 1
                st.rerun()

        with col_act2:
            st.markdown("""
            <div class="welcome-card">
                <h2 style="color:#003366;">📝 Émargement PDP</h2>
                <p>Signer la prise de connaissance d'un Plan de Prévention avant intervention sur le site.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📝 SIGNER UN PLAN DE PRÉVENTION (PDP)", use_container_width=True):
                st.session_state.kiosk_mode = "PDP"
                st.rerun()

    # FORMULAIRE ÉMARGEMENT PDP
    elif st.session_state.kiosk_mode == "PDP":
        if st.button("⬅️ Retour à l'accueil"):
            st.session_state.kiosk_mode = "HOME"
            st.rerun()

        st.subheader("📝 Émargement d'un Plan de Prévention (PDP)")
        st.divider()

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            soc_pdp = st.selectbox("Entreprise Extérieure", db_societes)
            pdp_list = db_pdps.get(soc_pdp, ["PDP Standard"])
            pdp_sel = st.selectbox("Plan de Prévention rattaché", pdp_list)
            nom_pdp = st.text_input("Nom & Prénom de l'intervenant")

        with col_p2:
            statut_pdp = st.selectbox("Statut de l'intervenant", ["N1 (Compagnon)", "N2 (Responsable)"])
            tel_pdp = st.text_input("N° Téléphone du Responsable N2", placeholder="06 XX XX XX XX") if "N2" in statut_pdp else "Non requis"
            st.write("✍️ **Signature Tactile de l'Émargement :**")
            st.info(" [ Zone de Signature Tactile Empreinte / Stylet ] ")

        if st.button("✅ VALIDER L'ÉMARGEMENT DU PDP", type="primary", use_container_width=True):
            if not nom_pdp:
                st.error("Veuillez renseigner votre Nom & Prénom.")
            else:
                st.balloons()
                st.success(f"Émargement enregistré avec succès pour {nom_pdp} ({statut_pdp}) sur le {pdp_sel} !")
                st.session_state.kiosk_mode = "HOME"

    # FORMULAIRE PERMIS DE TRAVAIL PAR STEPPER (7 ÉTAPES)
    elif st.session_state.kiosk_mode == "PERMIS":

        # Affichage du Stepper dynamique
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

        # -----------------------------------------------------
        # ÉTAPE 1 : SOCIÉTÉ
        # -----------------------------------------------------
        if current_step == 1:
            st.subheader("1. Entreprise Extérieure (EE)")
            st.session_state.form_data["societe"] = st.selectbox("Sélectionnez votre entreprise :", db_societes, index=db_societes.index(st.session_state.form_data["societe"]))

            c_back, c_next = st.columns([1, 1])
            with c_back:
                if st.button("⬅️ Accueil"):
                    st.session_state.kiosk_mode = "HOME"
                    st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"):
                    st.session_state.step = 2
                    st.rerun()

        # -----------------------------------------------------
        # ÉTAPE 2 : PDP
        # -----------------------------------------------------
        elif current_step == 2:
            st.subheader(f"2. Plan de Prévention (PDP) — {st.session_state.form_data['societe']}")
            p_list = db_pdps.get(st.session_state.form_data["societe"], ["PDP-2026-042 (Bâtiment M1)"])
            st.session_state.form_data["pdp"] = st.selectbox("Plan de Prévention rattaché :", p_list)

            c_back, c_next = st.columns([1, 1])
            with c_back:
                if st.button("⬅️ Précédent"):
                    st.session_state.step = 1
                    st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"):
                    st.session_state.step = 3
                    st.rerun()

        # -----------------------------------------------------
        # ÉTAPE 3 : RESPONSABLE N2
        # -----------------------------------------------------
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

        # -----------------------------------------------------
        # ÉTAPE 4 : CARTOGRAPHIE & URGENCES AUTOMATIQUES
        # -----------------------------------------------------
        elif current_step == 4:
            st.subheader("4. Localisation & Assignation Automatique des Urgences")

            st.session_state.form_data["lieu_pdp"] = st.selectbox("Zone du PDP :", list(db_zones_carto.keys()))
            st.session_state.form_data["lieu_precision"] = st.text_input("Précision d'emplacement (Bureau, Ligne, Local) :", value=st.session_state.form_data["lieu_precision"])
            st.session_state.form_data["description"] = st.text_input("Description détaillée de la tâche :", value=st.session_state.form_data["description"])

            carto = db_zones_carto.get(st.session_state.form_data["lieu_pdp"], {})
            st.warning(f"""
            📍 **Assignation Sécurité Secteur (Automatique) :**
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

        # -----------------------------------------------------
        # ÉTAPE 5 : STA / EPI / RISQUES SPÉCIFIQUES
        # -----------------------------------------------------
        elif current_step == 5:
            st.subheader("5. Analyse STA, EPI & Risques Spécifiques")

            st.markdown("##### 1. STA — Risques Environnementaux")
            col_sta1, col_sta2 = st.columns(2)
            with col_sta1:
                st.session_state.form_data["sta_espace_exigu"] = st.checkbox("Espace exigu", value=st.session_state.form_data["sta_espace_exigu"])
                st.session_state.form_data["sta_bruit_80db"] = st.checkbox("Bruit > 80 dB", value=st.session_state.form_data["sta_bruit_80db"])
                st.session_state.form_data["sta_escalier_tremie"] = st.checkbox("Proximité escalier / trémie", value=st.session_state.form_data["sta_escalier_tremie"])
            with col_sta2:
                st.session_state.form_data["sta_fds_presente"] = st.checkbox("FDS présente pour produits chimiques", value=st.session_state.form_data["sta_fds_presente"])
                st.session_state.form_data["sta_ventilation_ok"] = st.checkbox("Ventilation zone conforme", value=st.session_state.form_data["sta_ventilation_ok"])

            st.markdown("##### 2. Équipements de Protection Individuelle (EPI)")
            col_epi1, col_epi2 = st.columns(2)
            with col_epi1:
                st.session_state.form_data["epi_chaussures"] = st.checkbox("Chaussures montantes EN 20345", value=st.session_state.form_data["epi_chaussures"])
                st.session_state.form_data["epi_casque_jugulaire"] = st.checkbox("Casque + Jugulaire", value=st.session_state.form_data["epi_casque_jugulaire"])
                st.session_state.form_data["epi_masque_ffp2"] = st.checkbox("Masque FFP2 / Respiratoire", value=st.session_state.form_data["epi_masque_ffp2"])
            with col_epi2:
                st.session_state.form_data["epi_lunettes_en166"] = st.checkbox("Lunettes de sécurité EN 166", value=st.session_state.form_data["epi_lunettes_en166"])
                st.session_state.form_data["epi_gants_coupure"] = st.checkbox("Gants Anti-coupure", value=st.session_state.form_data["epi_gants_coupure"])

            st.markdown("##### 3. Permis Spécifiques (HRT) & Dérogations Déclenchés")
            col_spe1, col_spe2 = st.columns(2)
            with col_spe1:
                st.session_state.form_data["spe_points_chauds"] = st.checkbox("🔥 Points Chauds / Soudure", value=st.session_state.form_data["spe_points_chauds"])
                st.session_state.form_data["spe_espace_confine"] = st.checkbox("🦺 Espace Confiné (CBA 105)", value=st.session_state.form_data["spe_espace_confine"])
                st.session_state.form_data["spe_consignation_loto"] = st.checkbox("⚡ Consignation (LOTO)", value=st.session_state.form_data["spe_consignation_loto"])
            with col_spe2:
                st.session_state.form_data["derog_meuleuse"] = st.checkbox("⚠️ Dérogation Meuleuse d'angle", value=st.session_state.form_data["derog_meuleuse"])
                st.session_state.form_data["derog_cutter"] = st.checkbox("⚠️ Dérogation Cutter lame ouverte", value=st.session_state.form_data["derog_cutter"])

            c_back, c_next = st.columns([1, 1])
            with c_back:
                if st.button("⬅️ Précédent"):
                    st.session_state.step = 4
                    st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"):
                    # Si aucun permis spécifique n'est coché, passer directement aux signatures (Étape 7)
                    has_spe = (
                        st.session_state.form_data["spe_points_chauds"] or 
                        st.session_state.form_data["spe_espace_confine"] or 
                        st.session_state.form_data["spe_consignation_loto"] or 
                        st.session_state.form_data["derog_meuleuse"] or 
                        st.session_state.form_data["derog_cutter"]
                    )
                    st.session_state.step = 6 if has_spe else 7
                    st.rerun()

        # -----------------------------------------------------
        # ÉTAPE 6 : FORMULAIRES SPÉCIFIQUES & DÉROGATIONS
        # -----------------------------------------------------
        elif current_step == 6:
            st.subheader("6. Formulaires Spécifiques & Dérogations")

            if st.session_state.form_data["spe_espace_confine"]:
                st.info("🦺 **PERMIS ESPACE CONFINÉ (CBA 105)**")
                c_c1, c_c2 = st.columns(2)
                with c_c1:
                    st.session_state.form_data["confine_o2"] = st.text_input("Taux O2 mesuré :", value=st.session_state.form_data["confine_o2"])
                with c_c2:
                    st.session_state.form_data["confine_vigie"] = st.text_input("Nom de la Vigie Extérieure :", value=st.session_state.form_data["confine_vigie"])

            if st.session_state.form_data["spe_points_chauds"]:
                st.warning("🔥 **PERMIS POINTS CHAUDS / SOUDURE**")
                st.session_state.form_data["chaud_travaux"] = st.text_input("Nature des travaux de chauffe :", value=st.session_state.form_data["chaud_travaux"])
                st.session_state.form_data["chaud_extincteur"] = st.checkbox("Extincteur présent sur zone", value=st.session_state.form_data["chaud_extincteur"])

            if st.session_state.form_data["spe_consignation_loto"]:
                st.success("⚡ **CONSIGNATION / DECONSIGNATION (LOTO)**")
                st.session_state.form_data["loto_cadenas"] = st.text_input("Numéro de Cadenas LOTO :", value=st.session_state.form_data["loto_cadenas"])

            c_back, c_next = st.columns([1, 1])
            with c_back:
                if st.button("⬅️ Précédent"):
                    st.session_state.step = 5
                    st.rerun()
            with c_next:
                if st.button("Suivant ➔", type="primary"):
                    st.session_state.step = 7
                    st.rerun()

        # -----------------------------------------------------
        # ÉTAPE 7 : INTERVENANTS & SIGNATURES MULTIPLES
        # -----------------------------------------------------
        elif current_step == 7:
            st.subheader("7. Liste des Intervenants & Co-signatures Tactiles")

            st.write("##### Ajout dynamique des compagnons :")
            c_add1, c_add2 = st.columns([3, 1])
            with c_add1:
                nouveau_nom = st.text_input("Nom & Prénom de l'intervenant", key="new_compagnon")
            with c_add2:
                st.write("")
                st.write("")
                if st.button("+ Ajouter"):
                    if nouveau_nom and nouveau_nom not in st.session_state.form_data["intervenants"]:
                        st.session_state.form_data["intervenants"].append(nouveau_nom)
                        st.rerun()

            st.divider()

            for idx, nom in enumerate(st.session_state.form_data["intervenants"]):
                role_label = "RESPONSABLE N2" if idx == 0 else f"INTERVENANT {idx+1}"
                st.write(f"✍️ **Signature {role_label} : {nom}**")
                st.info(f" [ Emplacement Signature Tactile Horodatée : {nom} ] ")

            st.divider()

            c_back, c_sub = st.columns([1, 2])
            with c_back:
                if st.button("⬅️ Précédent"):
                    has_spe = (
                        st.session_state.form_data["spe_points_chauds"] or 
                        st.session_state.form_data["spe_espace_confine"] or 
                        st.session_state.form_data["spe_consignation_loto"] or 
                        st.session_state.form_data["derog_meuleuse"] or 
                        st.session_state.form_data["derog_cutter"]
                    )
                    st.session_state.step = 6 if has_spe else 5
                    st.rerun()

            with c_sub:
                if st.button("🚀 SOUMETTRE ET SIGNER LE PERMIS (Batch 07h30)", type="primary", use_container_width=True):
                    carto = db_zones_carto.get(st.session_state.form_data["lieu_pdp"], {})

                    derog_list = []
                    if st.session_state.form_data["derog_meuleuse"]: derog_list.append("Meuleuse d'angle")
                    if st.session_state.form_data["derog_cutter"]: derog_list.append("Cutter lame ouverte")

                    spe_list = []
                    if st.session_state.form_data["spe_points_chauds"]: spe_list.append("Points Chauds")
                    if st.session_state.form_data["spe_espace_confine"]: spe_list.append("Espace Confiné")
                    if st.session_state.form_data["spe_consignation_loto"]: spe_list.append("Consignation (LOTO)")

                    nouveau_pt = {
                        "id": f"PT-2026-0928-0{len(st.session_state.permis_db)+1}",
                        "societe": st.session_state.form_data["societe"],
                        "pdp": st.session_state.form_data["pdp"],
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
                        "permis_specifiques": spe_list
                    }

                    st.session_state.permis_db.append(nouveau_pt)
                    st.balloons()
                    st.success(f"Permis {nouveau_pt['id']} créé avec succès ! Transmis au DO P&G pour le batch de 07h30.")
                    st.session_state.kiosk_mode = "HOME"

# ---------------------------------------------------------
# INTERFACE 2 : DDS BOARD & BATCH 07H30 (DO / HSE)
# ---------------------------------------------------------
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
        st.write("Le script serveur exécute le traitement quotidien à 07h30. Cliquez pour valider la fournée des permis de votre secteur.")
    with c_btn:
        if st.button("✅ VALIDER LE BATCH (07h30)", type="primary", use_container_width=True):
            for p in st.session_state.permis_db:
                p["statut"] = "VALIDÉ"
            st.success("Fournée de 07h30 validée ! QR Codes et permis A4 transmis par e-mail.")

    st.subheader("📋 Liste des Permis Émis")
    st.dataframe(st.session_state.permis_db, use_container_width=True)

# ---------------------------------------------------------
# INTERFACE 3 : INSPECTION TERRAIN QR CODE (CASQUE ROUGE)
# ---------------------------------------------------------
else:
    st.markdown("""
    <div class="pg-header" style='background: linear-gradient(135deg, #b91c1c 0%, #7f1d1d 100%);'>
        <h2 style='margin:0;'>AUDIT TERRAIN & SCAN QR CODE — CASQUE ROUGE</h2>
        <p style='margin:0; opacity:0.8;'>Contrôle de Conformité Instantané sur Zone de Chantier</p>
    </div>
    """, unsafe_allow_html=True)

    c_sc1, c_sc2 = st.columns([1, 2])
    with c_sc1:
        st.subheader("📱 Control Smartphone")
        pt_sel = st.selectbox("Permis à controller sur zone :", [p["id"] for p in st.session_state.permis_db])
        if st.button("🔍 Simuler Scan QR Code", type="primary", use_container_width=True):
            st.session_state.scanned_item = next(p for p in st.session_state.permis_db if p["id"] == pt_sel)

    with c_sc2:
        st.subheader("📄 Document Officiel A4 Numérisé")
        if "scanned_item" in st.session_state:
            p = st.session_state.scanned_item
            color = "#10b981" if p["statut"] == "VALIDÉ" else "#f59e0b"
            st.markdown(f"""
            <div style="background: white; border: 2px solid #003366; padding: 20px; border-radius: 8px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="color:#003366; margin:0;">PERMIS DE TRAVAIL GÉNÉRAL (STA)</h3>
                    <span style="background:{color}; color:white; padding:4px 12px; border-radius:12px; font-weight:bold;">{p['statut']}</span>
                </div>
                <hr>
                <p><b>Réf :</b> {p['id']} | <b>Horodatage :</b> {p['heure']}</p>
                <p><b>Entreprise :</b> {p['societe']} | <b>PDP :</b> {p['pdp']}</p>
                <p><b>Responsable N2 :</b> {p['n2']}</p>
                <p><b>Emplacement :</b> {p['zone']} ({p.get('emplacement', '1er étage')})</p>
                <p><b>Point de Rassemblement :</b> {p.get('pr')} | <b>Confinement :</b> {p.get('confinement')}</p>
                <p><b>Poste d'Urgence Secteur :</b> {p.get('urg')}</p>
                <p><b>Intervenants Signataires :</b> {', '.join(p.get('intervenants', []))}</p>
                <p><b>Permis Spécifiques / Dérogations :</b> {', '.join(p.get('permis_specifiques', []) + p.get('derogations', [])) if (p.get('permis_specifiques') or p.get('derogations')) else 'Aucun'}</p>
                <hr>
                <p style="text-align:center; color:#003366; font-weight:bold; margin:0;">
                    ✅ CO-SIGNATURES VECTORIELLES AUDITÉES & HORODATÉES EN BDD
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Cliquez sur 'Simuler Scan QR Code' pour afficher la fiche numérisée.")
