import streamlit as st
import datetime

# Configuration de la page Streamlit (Largeur industrielle)
st.set_page_config(
    page_title="P&G e-Work Permit System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS Industriel P&G (Modern SaaS)
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    .pg-header {
        background: linear-gradient(135deg, #003366 0%, #0056b3 100%);
        color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;
    }
    .metric-card {
        background: white; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; text-align: center;
    }
    .stButton>button {
        background-color: #003366; color: white; border-radius: 8px; font-weight: bold; border: none;
    }
    .stButton>button:hover { background-color: #0056b3; color: white; }
</style>
""", unsafe_allow_html=True)

# ✅ CODE CORRIGÉ :
if "permis_db" not in st.session_state:
    st.session_state.permis_db = [
        {
            "id": "PT-2026-0928-01",
            "societe": "ABYLSEN",
            "pdp": "PDP-2026-042 (Bâtiment M1)",
            "n2": "Léa DUSEK",
            "zone": "Bâtiment M1 - Zone Production",
            "statut": "EN_ATTENTE_BATCH",
            "heure": "06:45",
            "derogation": True,
            "motif_derog": "Dérogation Meuleuse d'angle"
        },
        {
            "id": "PT-2026-0928-02",
            "societe": "APAVE",
            "pdp": "PDP-2026-104 (Tuyauterie)",
            "n2": "Marc DUPONT",
            "zone": "Bâtiment M2 - Conditionnement",
            "statut": "VALIDÉ",
            "heure": "07:15",
            "derogation": False,
            "motif_derog": "Aucune"
        }
    ]
            "id": "PT-2026-0928-01",
            "societe": "ABYLSEN",
            "pdp": "PDP-2026-042 (Bâtiment M1)",
            "n2": "Léa DUSEK",
            "zone": "Bâtiment M1 - Zone Production",
            "statut": "EN_ATTENTE_BATCH",
            "heure": "06:45",
            "derogation": True,
            "motif_derog": "Dérogation Meuleuse d'angle"
        },
        {
            "id": "PT-2026-0928-02",
            "societe": "APAVE",
            "pdp": "PDP-2026-104 (Tuyauterie)",
            "n2": "Marc DUPONT",
            "zone": "Bâtiment M2 - Conditionnement",
            "statut": "VALIDÉ",
            "heure": "07:15",
            "derogation": False,
            "motif_derog": "Aucune"
        }
    ]

# Navigation Latérale
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Procter_%26_Gamble_logo.svg/1024px-Procter_%26_Gamble_logo.svg.png", width=80)
st.sidebar.title("e-Work Permit P&G")
st.sidebar.caption("Système Numérique Intégré — Amiens")

role = st.sidebar.radio(
    "Sélectionner l'Interface à démontrer :",
    ["🖥️ Borne Kiosk (Intervenant EE)", "📊 Dashboard Live & Batch 07h30 (DO / HSE)", "📱 Inspection Terrain QR Code (Casque Rouge)"]
)

# ==============================================================================
# INTERFACE 1 : BORNE KIOSK TACTILE (EE / N2)
# ==============================================================================
if role == "🖥️ Borne Kiosk (Intervenant EE)":
    st.markdown("""
    <div class="pg-header">
        <h2 style='margin:0;'>PROCTER & GAMBLE — BORNE KIOSK PERMIS DE TRAVAIL</h2>
        <p style='margin:0; opacity: 0.8;'>Accueil Sécurité & Émission Numérique des Permis (STA)</p>
    </div>
    """, unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        st.button("📝 Signer un Plan de Prévention (PDP)", use_container_width=True)
    with col_btn2:
        st.button("🚀 Commencer un Permis de Travail (WorkPermit)", use_container_width=True, type="primary")

    st.divider()

    # Démo Effet WOW : Badging RFID
    st.subheader("1. Identification du Responsable N2")
    col_rfid, col_form = st.columns([1, 2])

    with col_rfid:
        st.info("💡 **Démo Effet WOW**")
        if st.button("💳 Simuler Passage Badge RFID / NFC", use_container_width=True):
            st.session_state.badge_active = True
            st.success("Badge P&G Détecté : Léa DUSEK (ABYLSEN)")

    default_soc = "ABYLSEN" if st.session_state.get("badge_active") else "Sélectionner..."
    default_n2 = "Léa DUSEK" if st.session_state.get("badge_active") else ""

    with col_form:
        soc = st.selectbox("Société Intervenante", ["ABYLSEN", "APAVE", "AXIMA", "ENGIE"], index=0 if st.session_state.get("badge_active") else 0)
        pdp = st.selectbox("Plan de Prévention Rattaché", ["PDP-2026-042 (Bâtiment M1 - Rénovation)", "PDP-2026-089 (Conditionnement)"])
        n2_name = st.text_input("Responsable N2 Qualifié", value=default_n2, placeholder="Scannez votre badge ou saisissez votre nom")

    st.subheader("2. Localisation & Cartographie Automatique")
    col_loc, col_map = st.columns(2)
    
    with col_loc:
        zone = st.selectbox("Zone du Chantier", ["Bâtiment M1 - Zone Production", "Bâtiment M2 - Conditionnement", "Zone Extérieure / Logistique"])
        pr = "PR-2 (Parking Ouest)" if "M1" in zone else "PR-4 (Zone Nord)"
        zc = "ZC-01 (Hall M1)" if "M1" in zone else "ZC-03 (Atrium M2)"
        
        st.markdown(f"""
        **Mapping Sécurité Automatique :**
        - 📍 **Point de Rassemblement :** `{pr}`
        - 🏢 **Zone de Confinement :** `{zc}`
        - 📞 **N° Urgence Secteur :** `03.22.54.33.33`
        """)

    with col_map:
        st.warning("⚠️ **STA & Permis Spécifiques Déclenchés**")
        chk_haut = st.checkbox("Travail en Hauteur / Nacelle")
        chk_chaud = st.checkbox("Points Chauds / Soudure")
        chk_meuleuse = st.checkbox("Utilisation Meuleuse d'angle (Dérogation Casque Rouge)")

    st.subheader("3. Co-signatures Tactiles de l'Équipe")
    col_sig1, col_sig2 = st.columns(2)
    with col_sig1:
        st.text_input("Nom du Compagnon 1", value="Léa DUSEK (N2)")
        st.caption("✍️ Signature tactile enregistrée à l'émargement PDP")
    with col_sig2:
        st.text_input("Nom du Compagnon 2", value="Matthieu MARTIN (N1)")
        st.caption("✍️ Signature tactile apposée sur borne à 06:48")

    if st.button("🚀 SOUMETTRE LE PERMIS (Batch 07h30)", type="primary", use_container_width=True):
        nouveau_pt = {
            "id": f"PT-2026-0928-0{len(st.session_state.permis_db)+1}",
            "societe": soc,
            "pdp": pdp,
            "n2": n2_name if n2_name else "Inconnu",
            "zone": zone,
            "statut": "EN_ATTENTE_BATCH",
            "heure": datetime.datetime.now().strftime("%H:%M"),
            "derogation": chk_meuleuse,
            "motif_derog": "Dérogation Meuleuse d'angle" if chk_meuleuse else "Aucune"
        }
        st.session_state.permis_db.append(nouveau_pt)
        st.balloons()
        st.success(f"Permis {nouveau_pt['id']} enregistré avec succès ! Transmis au Donneur d'Ordre pour le batch de 07h30.")

# ==============================================================================
# INTERFACE 2 : DASHBOARD LIVE & BATCH 07H30 (DO / HSE)
# ==============================================================================
elif role == "📊 Dashboard Live & Batch 07h30 (DO / HSE)":
    st.markdown("""
    <div class="pg-header" style='background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);'>
        <h2 style='margin:0;'>DDS BOARD & TABLEAU DE BORD DONNEUR D'ORDRE (DO)</h2>
        <p style='margin:0; opacity: 0.8;'>Supervision Temps Réel des Activités & Validation Automatisée</p>
    </div>
    """, unsafe_allow_html=True)

    # Indicateurs Métiers (KPIs)
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    total_permis = len(st.session_state.permis_db)
    en_attente = sum(1 for p in st.session_state.permis_db if p["statut"] == "EN_ATTENTE_BATCH")
    valides = sum(1 for p in st.session_state.permis_db if p["statut"] == "VALIDÉ")
    derogations = sum(1 for p in st.session_state.permis_db if p["derogation"])

    col_kpi1.metric("Chantiers Totaux", total_permis)
    col_kpi2.metric("En Attente Batch (07h30)", en_attente, delta_color="inverse")
    col_kpi3.metric("Permis Validés Actifs", valides)
    col_kpi4.metric("Dérogations Casque Rouge", derogations, delta="-1 Critique" if derogations > 0 else "Normal")

    st.divider()

    st.subheader("⚡ Validation Globale de la Fournée du Matin (07h30)")
    col_batch_text, col_batch_btn = st.columns([3, 1])
    with col_batch_text:
        st.write("Le script serveur exécute le traitement automatique chaque matin à 07h30. En tant que DO, vous pouvez valider la fournée des chantiers de votre secteur en un clic.")
    with col_batch_btn:
        if st.button("✅ VALIDER TOUT LE BATCH (07h30)", type="primary"):
            for p in st.session_state.permis_db:
                p["statut"] = "VALIDÉ"
            st.success("Tous les permis en attente ont été validés et transmis par e-mail avec QR Code !")

    st.subheader("📋 Liste des Permis de Travail de la Journée")
    st.dataframe(st.session_state.permis_db, use_container_width=True)

# ==============================================================================
# INTERFACE 3 : INSPECTION TERRAIN QR CODE (CASQUE ROUGE)
# ==============================================================================
else:
    st.markdown("""
    <div class="pg-header" style='background: linear-gradient(135deg, #b91c1c 0%, #7f1d1d 100%);'>
        <h2 style='margin:0;'>AUDIT TERRAIN & SCAN QR CODE — CASQUE ROUGE</h2>
        <p style='margin:0; opacity: 0.8;'>Contrôle de Conformité Instantané sur Zone de Chantier</p>
    </div>
    """, unsafe_allow_html=True)

    col_scan, col_doc = st.columns([1, 2])

    with col_scan:
        st.subheader("📱 Contrôle Smartphone")
        pt_select = st.selectbox("Sélectionner un permis à scanner sur zone :", [p["id"] for p in st.session_state.permis_db])
        
        if st.button("🔍 Simuler le Scan du QR Code", type="primary", use_container_width=True):
            st.session_state.scanned_pt = next(p for p in st.session_state.permis_db if p["id"] == pt_select)

    with col_doc:
        st.subheader("📄 Document Officiel A4 Numérisé")
        if "scanned_pt" in st.session_state:
            p = st.session_state.scanned_pt
            color_status = "#10b981" if p["statut"] == "VALIDÉ" else "#f59e0b"
            
            st.markdown(f"""
            <div style="background: white; border: 2px solid #003366; padding: 20px; border-radius: 10px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="color:#003366; margin:0;">PERMIS DE TRAVAIL (STA)</h3>
                    <span style="background:{color_status}; color:white; padding:4px 12px; border-radius:12px; font-weight:bold;">{p['statut']}</span>
                </div>
                <hr>
                <p><b>Réf :</b> {p['id']} | <b>Horodatage :</b> {p['heure']}</p>
                <p><b>Entreprise :</b> {p['societe']} | <b>N2 Responsable :</b> {p['n2']}</p>
                <p><b>Emplacement :</b> {p['zone']}</p>
                <p><b>Dérogation :</b> {p['motif_derog']}</p>
                <hr>
                <div style="text-align:center; color:#003366; font-weight:bold;">
                    ✅ CO-SIGNATURES VECTORIELLES AUDITÉES & HORODATÉES EN BDD
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Cliquez sur 'Simuler le Scan du QR Code' pour afficher le document officiel P&G.")
