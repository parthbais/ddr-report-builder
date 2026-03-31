import streamlit as st
import json
import os
import shutil
from src.extractor import extract_pdf, get_full_text, get_all_images
from src.merger import generate_ddr_json, save_ddr_json
from src.builder import create_ddr_docx

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="DDR Builder · UrbanRoof",
    page_icon="🏗️",
    layout="wide",
)

if "ddr_data" not in st.session_state:
    st.session_state.ddr_data = None
if "docx_bytes" not in st.session_state:
    st.session_state.docx_bytes = None
if "show_success" not in st.session_state:
    st.session_state.show_success = False
# ── Global CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* ─── App background ─── */
    .stApp { background: #0f0f0f; color: #f0f0f0; }

    /* ─── Hide default Streamlit chrome ─── */
    #MainMenu, footer, header { visibility: hidden; }

    /* ─── Top banner ─── */
    .ur-banner {
        background: linear-gradient(135deg, #1a1400 0%, #1f1900 60%, #141000 100%);
        border-bottom: 3px solid #FFC107;
        padding: 0;
        margin: -1rem -1rem 0 -1rem;
        position: relative;
        overflow: hidden;
    }
    .ur-banner::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: repeating-linear-gradient(
            45deg,
            transparent,
            transparent 20px,
            rgba(255,193,7,0.03) 20px,
            rgba(255,193,7,0.03) 40px
        );
    }
    .ur-banner-inner {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.1rem 2rem;
        position: relative;
        z-index: 1;
    }
    .ur-logo-group { display: flex; align-items: center; gap: 1rem; }
    .ur-icon-wrap {
        width: 48px; height: 48px;
        background: linear-gradient(135deg, #FFC107, #FF8F00);
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.5rem;
        box-shadow: 0 4px 14px rgba(255,193,7,0.35);
    }
    .ur-brand { margin: 0; }
    .ur-brand-name {
        font-size: 1.5rem; font-weight: 800;
        background: linear-gradient(90deg, #FFC107, #FFD54F);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
        display: block; line-height: 1.1;
    }
    .ur-brand-tagline {
        font-size: 0.72rem; color: #FF8F00; font-weight: 500;
        letter-spacing: 0.12em; text-transform: uppercase;
        display: block;
    }
    .ur-header-right {
        display: flex; align-items: center; gap: 1.5rem;
    }
    .ur-badge {
        background: rgba(255,193,7,0.12);
        border: 1px solid rgba(255,193,7,0.3);
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.75rem; color: #FFD54F; font-weight: 500;
    }
    .ur-version { font-size: 0.7rem; color: #5a4a00; }

    /* ─── Left panel ─── */
    .panel-label {
        font-size: 0.7rem; font-weight: 700; letter-spacing: 0.12em;
        text-transform: uppercase; color: #FFC107;
        margin: 1.2rem 0 0.5rem;
    }
    .panel-section {
        background: #1a1500;
        border: 1px solid #3a2e00;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .panel-title {
        font-size: 0.85rem; font-weight: 600; color: #FFD54F;
        margin-bottom: 0.3rem;
    }
    .panel-desc {
        font-size: 0.75rem; color: #b09040; font-weight: 500; line-height: 1.5;
    }

    /* ─── File uploaders ─── */
    [data-testid="stFileUploader"] {
        background: #141000 !important;
        border-radius: 10px !important;
        border: 1.5px dashed #3a2e00 !important;
        padding: 0.5rem !important;
        transition: border-color 0.2s;
    }
    [data-testid="stFileUploader"]:hover { border-color: #FFC107 !important; }
    .stFileUploader label { color: #FFC107 !important; font-size: 0.85rem !important; font-weight: 600 !important; }

    /* ─── Generate button ─── */
    .stButton > button {
        background: linear-gradient(135deg, #FFC107, #FF8F00) !important;
        color: #0f0f0f !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        width: 100% !important;
        transition: all 0.25s !important;
        letter-spacing: 0.02em !important;
        box-shadow: 0 4px 16px rgba(255,193,7,0.35) !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #FFD54F, #FFC107) !important;
        box-shadow: 0 6px 22px rgba(255,193,7,0.5) !important;
        transform: translateY(-2px) !important;
    }
    .stButton > button:disabled {
        background: #1a1500 !important;
        color: #3a2e00 !important;
        box-shadow: none !important;
        transform: none !important;
    }

    /* ─── Download buttons ─── */
    .stDownloadButton > button {
        background: #141000 !important;
        color: #FFC107 !important;
        border: 1.5px solid #FFC107 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        width: 100% !important;
        transition: all 0.2s !important;
    }
    .stDownloadButton > button:hover {
        background: #1a1500 !important;
        border-color: #FFD54F !important;
    }

    /* ─── Progress panel ─── */
    .progress-wrap {
        background: #141000;
        border: 1px solid #3a2e00;
        border-radius: 14px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.2rem;
    }
    .progress-title {
        font-size: 0.7rem; font-weight: 700; letter-spacing: 0.1em;
        color: #FFC107; text-transform: uppercase; margin-bottom: 1rem;
    }
    .step-row {
        display: flex; align-items: center; gap: 0.85rem;
        padding: 0.55rem 0;
        border-bottom: 1px solid #1a1500;
        transition: all 0.2s;
    }
    .step-row:last-child { border-bottom: none; }
    .step-icon { font-size: 1.1rem; width: 24px; text-align: center; flex-shrink: 0; }
    .step-text { font-size: 0.88rem; color: #a08030; }
    .step-text.done { color: #FFD54F; }
    .step-text.active { color: #fff8e1; }
    .step-sub { font-size: 0.72rem; color: #8a6820; display: block; }
    .step-sub.done { color: #FFC107; }

    /* ─── Section headers in output ─── */
    .section-header {
        font-size: 0.7rem; font-weight: 700; letter-spacing: 0.12em;
        text-transform: uppercase; color: #FFC107;
        padding: 0.3rem 0; margin: 1.4rem 0 0.6rem;
        border-bottom: 1px solid #2a2000;
    }

    /* ─── Property info card ─── */
    .info-grid {
        display: grid; grid-template-columns: 1fr 1fr;
        gap: 0.5rem; margin-bottom: 1rem;
    }
    .info-cell {
        background: #141000;
        border: 1px solid #2a2000;
        border-radius: 8px;
        padding: 0.6rem 0.9rem;
    }
    .info-key { font-size: 0.7rem; color: #a08030; text-transform: uppercase; letter-spacing: 0.05em; }
    .info-val { font-size: 0.9rem; font-weight: 600; color: #FFC107; margin-top: 2px; }

    /* ─── Observation cards ─── */
    .obs-card {
        background: #141000;
        border: 1px solid #2a2000;
        border-left: 4px solid #FFC107;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        transition: border-color 0.2s;
    }
    .obs-card:hover { border-left-color: #FFD54F; }
    .obs-area {
        font-weight: 700; color: #FFC107; font-size: 0.95rem;
        margin-bottom: 0.6rem; display: flex; align-items: center; gap: 0.5rem;
    }
    .obs-label {
        font-size: 0.68rem; color: #a08030; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.08em; margin-top: 0.5rem;
    }
    .obs-value { font-size: 0.88rem; color: #e0d0a0; margin: 0.2rem 0 0.4rem; line-height: 1.5; }
    .thermal-chip {
        display: inline-block;
        background: rgba(255,193,7,0.1); border: 1px solid rgba(255,193,7,0.25);
        border-radius: 20px; padding: 2px 10px;
        font-size: 0.75rem; color: #FFC107; margin-top: 0.3rem;
    }

    /* ─── Severity badges ─── */
    .badge-critical { background: #b71c1c; color: #fff; padding: 3px 12px; border-radius: 20px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em; }
    .badge-high     { background: #e65100; color: #fff; padding: 3px 12px; border-radius: 20px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em; }
    .badge-moderate { background: #f57f17; color: #000; padding: 3px 12px; border-radius: 20px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em; }
    .badge-low      { background: #1b5e20; color: #fff; padding: 3px 12px; border-radius: 20px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em; }

    /* ─── Severity / action rows ─── */
    .sev-card {
        background: #141000; border: 1px solid #2a2000;
        border-radius: 10px; padding: 0.8rem 1.1rem;
        margin-bottom: 0.6rem;
        display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem;
    }
    .sev-left { flex: 1; }
    .sev-area { font-weight: 600; color: #FFD54F; font-size: 0.88rem; }
    .sev-reason { font-size: 0.8rem; color: #b09040; margin-top: 0.2rem; line-height: 1.4; }

    .action-card {
        background: #141000; border: 1px solid #2a2000;
        border-radius: 10px; padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        display: flex; gap: 0.8rem; align-items: flex-start;
    }
    .action-dot {
        width: 8px; height: 8px; border-radius: 50%;
        background: #FFC107; margin-top: 5px; flex-shrink: 0;
    }
    .action-body { flex: 1; }
    .action-text { font-size: 0.88rem; color: #e0d0a0; }
    .action-meta { font-size: 0.75rem; color: #a08030; margin-top: 0.15rem; }
    .priority-immediate { color: #ef5350; font-weight: 700; }
    .priority-high      { color: #ff7043; font-weight: 700; }
    .priority-medium    { color: #FFC107; }
    .priority-low       { color: #66bb6a; }

    /* ─── Notes card ─── */
    .note-card {
        background: #141000; border: 1px solid #2a2000;
        border-radius: 10px; padding: 1rem 1.2rem;
        font-size: 0.88rem; color: #FFC107; line-height: 1.6;
    }

    /* ─── Empty state ─── */
    .empty-state {
        background: #141000; border: 2px dashed #2a2000;
        border-radius: 16px; padding: 4rem 2rem; text-align: center;
        margin-top: 1rem;
    }

    /* ─── Success notice ─── */
    .ur-success {
        background: linear-gradient(135deg, #1a1400, #221a00);
        border: 1px solid #FFC107; border-radius: 12px;
        padding: 1rem 1.4rem; margin-bottom: 1rem;
        display: flex; align-items: center; gap: 0.8rem;
    }
    .ur-success-icon { font-size: 1.5rem; }
    .ur-success-text { font-size: 0.88rem; color: #FFD54F; }
    .ur-success-title { font-weight: 700; color: #fff8e1; font-size: 0.95rem; }

    /* ─── Tip box ─── */
    .tip-box {
        background: #0f0c00; border: 1px solid #2a2000;
        border-radius: 10px; padding: 0.75rem 1rem;
        font-size: 0.78rem; color: #6a5a00; line-height: 1.6;
        margin-top: 0.6rem;
    }
    .tip-box a { color: #FFC107; }

    /* ─── Dividers ─── */
    hr { border-color: #2a2000 !important; }
    .stSpinner > div { border-top-color: #FFC107 !important; }
</style>
""", unsafe_allow_html=True)

# ── Top Banner ────────────────────────────────────────────────
st.markdown("""
<div class="ur-banner">
  <div class="ur-banner-inner">
    <div class="ur-logo-group">
      <div class="ur-icon-wrap">🏗️</div>
      <div class="ur-brand">
        <span class="ur-brand-name">UrbanRoof</span>
        <span class="ur-brand-tagline">Building Diagnostics &nbsp;·&nbsp; DDR Report Builder</span>
      </div>
    </div>
    <div class="ur-header-right">
      <span class="ur-badge">🤖 AI-Powered Analysis</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

# ── Layout ────────────────────────────────────────────────────
left, right = st.columns([1, 2], gap="large")

# ════════════════════════════════════════════════════════════════
# LEFT PANEL
# ════════════════════════════════════════════════════════════════
with left:
    # ── Upload section ──
    st.markdown('<div class="panel-label">📂 Document Upload</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="panel-section">
        <div class="panel-title">📄 Inspection Report</div>
        <div class="panel-desc" style="color:#8a7020; font-weight:500">Site visual inspection form PDF from the field team.</div>
    </div>
    """, unsafe_allow_html=True)

    inspection_file = st.file_uploader(
        "Inspection Report (PDF)",
        type=["pdf"],
        key="inspection",
        label_visibility="collapsed"
    )

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="panel-section">
        <div class="panel-title">🌡️ Thermal Imaging Report</div>
        <div class="panel-desc" style="color:#8a7020; font-weight:500">IR thermography scan PDF with hotspot & coldspot readings.</div>
    </div>
    """, unsafe_allow_html=True)

    thermal_file = st.file_uploader(
        "Thermal Images Report (PDF)",
        type=["pdf"],
        key="thermal",
        label_visibility="collapsed"
    )

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # ── Generate button ──
    ready = inspection_file and thermal_file
    generate_btn = st.button(
        "⚡ Generate DDR Report",
        disabled=not ready,
        use_container_width=True
    )

    if not ready:
        missing = []
        if not inspection_file: missing.append("Inspection PDF")
        if not thermal_file: missing.append("Thermal PDF")
        st.markdown(f"""
        <div style="text-align:center; color:#3a2e00; font-size:0.75rem; margin-top:0.4rem; padding: 0.5rem;">
            Waiting for: <span style="color:#FFC107">{" · ".join(missing)}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="panel-label">ℹ️ How It Works</div>', unsafe_allow_html=True)

    steps_info = [
        ("📄", "Upload Reports", "Both PDFs Reports"),
        ("🔍", "Extraction", "Extract Context from Text & image anchors"),
        ("🧠", "AI Analyse", "AI Analyses, Merges & Diagnoses"),
        ("📑", "DDR Build", "DDR .docx Generated ! "),
    ]
    for icon, title, desc in steps_info:
        st.markdown(f"""
        <div style="display:flex; gap:0.7rem; align-items:center; padding:0.4rem 0; border-bottom:1px solid #1a1500;">
            <span style="font-size:1rem; flex-shrink:0">{icon}</span>
            <div>
                <span style="font-size:0.82rem; color:#FFC107; font-weight:700">{title}</span>
                <span style="font-size:0.78rem; color:#9a8030; font-weight:500"> — {desc}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.75rem; color:#7a6020; font-weight:600; text-align:center; border-top:1px solid #2a2000; padding-top:0.8rem;">
        UrbanRoof Private Limited · Proprietary<br>
        <span style="font-size:0.7rem; font-weight:400; color:#6a5020">All reports are confidential</span>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# RIGHT PANEL
# ════════════════════════════════════════════════════════════════
with right:

    # ── Empty state ──
    if not generate_btn and st.session_state.ddr_data is None:
        upload_count = sum([inspection_file is not None, thermal_file is not None])
        st.markdown(f"""
        <div class="empty-state">
            <div style="font-size:3.5rem; margin-bottom:1.2rem">🏢🏠</div>
            <p style="color:#FFC107; font-size:1.1rem; font-weight:700; margin:0 0 0.4rem">
                Ready to Diagnose
            </p>
            <p style="color:#9a8030; font-size:0.88rem; font-weight:500; margin:0 0 1.5rem; line-height:1.6">
                Upload both PDFs on the left, then click<br>
                <b style="color:#FFC107">⚡ Generate DDR Report</b> to begin.
            </p>
            <div style="display:flex; gap:0.8rem; justify-content:center;">
                <div style="background:#141000; border:1px solid {'#FFC107' if inspection_file else '#2a2000'};
                    border-radius:8px; padding:0.6rem 1.2rem; font-size:0.8rem;
                    color:{'#FFC107' if inspection_file else '#3a2e00'};">
                    {'✅' if inspection_file else '⬜'} Inspection Report
                </div>
                <div style="background:#141000; border:1px solid {'#FFC107' if thermal_file else '#2a2000'};
                    border-radius:8px; padding:0.6rem 1.2rem; font-size:0.8rem;
                    color:{'#FFC107' if thermal_file else '#3a2e00'};">
                    {'✅' if thermal_file else '⬜'} Thermal Report
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Processing ──
    if generate_btn and inspection_file and thermal_file:
        os.makedirs("uploads/temp", exist_ok=True)
        inspection_path = f"uploads/temp/{inspection_file.name}"
        thermal_path    = f"uploads/temp/{thermal_file.name}"

        with open(inspection_path, "wb") as f: f.write(inspection_file.read())
        with open(thermal_path,    "wb") as f: f.write(thermal_file.read())

        progress_ph = st.empty()

        STEPS = [
            ("📄", "Parsing Inspection Report",    "Extracting text blocks and image anchors…", False),
            ("🌡️", "Parsing Thermal Report",        "Reading hotspot / coldspot readings…",      False),
            ("🧠", "AI Analysis & Merge",           "LLaMA 3.3 70B diagnosing findings…",        False),
            ("📑", "Building DDR Document",         "Formatting structured Word report…",         False),
        ]

        def show_progress(steps, active_idx=-1):
            rows = ""
            for i, (icon, title, sub, done) in enumerate(steps):
                if done:
                    t_cls, s_cls, cur_icon = "done", "done", "✅"
                elif i == active_idx:
                    t_cls, s_cls, cur_icon = "active", "", "⏳"
                else:
                    t_cls, s_cls, cur_icon = "", "", icon
                rows += f"""
                <div class="step-row">
                  <span class="step-icon">{cur_icon}</span>
                  <div>
                    <span class="step-text {t_cls}">{title}</span>
                    <span class="step-sub {s_cls}">{sub}</span>
                  </div>
                </div>"""
            progress_ph.markdown(f"""
            <div class="progress-wrap">
              <div class="progress-title">🏗️ UrbanRoof DDR Pipeline</div>
              {rows}
            </div>""", unsafe_allow_html=True)

        show_progress(STEPS, active_idx=0)

        try:
            # ── Step 1: Inspection ──
            inspection_data   = extract_pdf(inspection_path)
            inspection_text   = get_full_text(inspection_data)
            inspection_images = get_all_images(inspection_data)
            n_img = len(inspection_images)
            STEPS[0] = ("📄", "Inspection Report Parsed",
                        f"{n_img} images · {len(inspection_text.split())} words extracted", True)
            show_progress(STEPS, active_idx=1)

            # ── Step 2: Thermal ──
            thermal_data   = extract_pdf(thermal_path)
            thermal_text   = get_full_text(thermal_data)
            thermal_images = get_all_images(thermal_data)
            n_th = len(thermal_images)
            STEPS[1] = ("🌡️", "Thermal Report Parsed",
                        f"{n_th} thermal images · readings extracted", True)
            show_progress(STEPS, active_idx=2)

            # ── Step 3: AI merge ──
            ddr = generate_ddr_json(inspection_text, thermal_text)
            save_ddr_json(ddr)
            STEPS[2] = ("🧠", "AI Analysis Complete",
                        f"{len(ddr.get('area_wise_observations',[]))} areas diagnosed · report structured", True)
            show_progress(STEPS, active_idx=3)

            # ── Step 4: Build DOCX ──
            docx_path = create_ddr_docx(
                ddr,
                inspection_images=inspection_images,
                thermal_images=thermal_images,
                assets_dir="assets",
                output_path="output/Final_DDR.docx"
            )
            STEPS[3] = ("📑", "DDR Report Ready",
                        "Formatted Word document (.docx) generated", True)
            show_progress(STEPS, active_idx=-1)

            st.session_state.ddr_data = ddr
            with open(docx_path, "rb") as f:
                st.session_state.docx_bytes = f.read()
            st.session_state.show_success = True

        except Exception as e:
            st.error(f"❌ Error during report generation: {str(e)}")
            with st.expander("🔍 Error Details"):
                st.code(str(e))

        finally:
            if 'inspection_path' in locals() and os.path.exists(inspection_path): os.remove(inspection_path)
            if 'thermal_path' in locals() and os.path.exists(thermal_path):    os.remove(thermal_path)


    # ════════════════════════════
    # REPORT OUTPUT
    # ════════════════════════════
    if st.session_state.ddr_data is not None:
        ddr = st.session_state.ddr_data
        
        if st.session_state.show_success:
            area_count = len(ddr.get("area_wise_observations", []))
            action_count = len(ddr.get("recommended_actions", []))
            st.markdown(f'''
            <div class="ur-success">
              <span class="ur-success-icon">✅</span>
              <div>
                <div class="ur-success-title">DDR Report Generated Successfully</div>
                <div class="ur-success-text">
                  {area_count} areas diagnosed · {action_count} recommended actions · Report ready for download
                </div>
              </div>
            </div>
            ''', unsafe_allow_html=True)
            st.session_state.show_success = False
        # Property Info
        st.markdown('<div class="section-header">🏠 Property Information</div>', unsafe_allow_html=True)
        pi = ddr.get("property_info", {})
        field_map = {
            "client_name":      ("👤 Client",          pi.get("client_name", "N/A")),
            "address":          ("📍 Address",          pi.get("address", "N/A")),
            "inspection_date":  ("📅 Inspection Date",  pi.get("inspection_date", "N/A")),
            "inspected_by":     ("👷 Inspected By",     pi.get("inspected_by", "N/A")),
            "property_type":    ("🏗️ Property Type",    pi.get("property_type", "N/A")),
            "floors":           ("🏢 Floors",           pi.get("floors", "N/A")),
            "age_years":        ("📆 Age (years)",      pi.get("age_years", "N/A")),
            "previous_repairs": ("🔧 Prior Repairs",    pi.get("previous_repairs", "N/A")),
        }
        cells_html = "".join(
            f'<div class="info-cell"><div class="info-key">{label}</div><div class="info-val">{val}</div></div>'
            for _, (label, val) in field_map.items()
        )
        st.markdown(f'<div class="info-grid">{cells_html}</div>', unsafe_allow_html=True)

        # Issue Summary
        st.markdown('<div class="section-header">📝 Executive & Issue Summary</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="obs-card">
          <div class="obs-label">📋 Executive Summary</div>
          <div class="obs-value" style="margin-bottom:0.6rem">{ddr.get("executive_summary", "")}</div>
          <div class="obs-label">📝 Issue Overview</div>
          <div class="obs-value" style="margin:0">{ddr.get("property_issue_summary", "")}</div>
        </div>""", unsafe_allow_html=True)

        rc = ddr.get("probable_root_cause")
        ls = ddr.get("leakage_sources")
        if rc or ls:
            rc_html = f'<div class="obs-label">🔎 Probable Root Cause</div><div class="obs-value" style="margin:0.2rem 0 0.6rem">{rc}</div>' if rc else ""
            ls_html = f'<div class="obs-label">💧 Leakage Travel Path</div><div class="obs-value" style="margin:0.2rem 0 0">{ls}</div>' if ls else ""
            st.markdown(f"""
            <div class="obs-card" style="border-left-color:#f57f17; margin-top:-0.4rem">
              {rc_html}
              {ls_html}
            </div>""", unsafe_allow_html=True)

        # Area-wise
        st.markdown('<div class="section-header">🔍 Area-wise Observations</div>', unsafe_allow_html=True)
        for obs in ddr.get("area_wise_observations", []):
            thermal_chip = ""
            if obs.get("thermal_reading") and obs.get("thermal_reading").lower() != "not available":
                thermal_chip = f'<span class="thermal-chip">🌡️ {obs.get("thermal_reading")}</span>'
            floor = obs.get("floor_level", "")
            floor_tag = f' ({floor})' if floor and floor.lower() != "not available" else ""
            
            moisture = obs.get("moisture_readings", "")
            moist_html = f'<div class="obs-label">💧 Moisture / pH</div><div class="obs-value">{moisture}</div>' if moisture and moisture.lower() != "not available" else ""
            
            struct = obs.get("structural_condition", "")
            struct_html = f'<div class="obs-label">🧱 Structural Condition</div><div class="obs-value">{struct}</div>' if struct and struct.lower() != "not available" else ""

            st.markdown(f"""
            <div class="obs-card">
              <div class="obs-area">📍 {obs.get("area","")}{floor_tag}</div>
              <div class="obs-label">⚠️ Negative Observations</div>
              <div class="obs-value">{obs.get("negative_observations","")}</div>
              <div class="obs-label">✅ Positive / Source Side</div>
              <div class="obs-value">{obs.get("positive_observations","")}</div>
              {moist_html}
              {struct_html}
              {thermal_chip}
            </div>""", unsafe_allow_html=True)

        # Severity
        st.markdown('<div class="section-header">⚡ Severity Assessment</div>', unsafe_allow_html=True)
        for s in ddr.get("severity_assessment", []):
            sev = s.get("severity", "").lower()
            badge = f'<span class="badge-{sev}">{sev.upper()}</span>'
            st.markdown(f"""
            <div class="sev-card">
              <div class="sev-left">
                <div class="sev-area">{s.get("area","")}</div>
                <div class="sev-reason">{s.get("reasoning","")}</div>
              </div>
              {badge}
            </div>""", unsafe_allow_html=True)

        # Recommended Actions
        st.markdown('<div class="section-header">🔧 Recommended Actions</div>', unsafe_allow_html=True)
        for action in ddr.get("recommended_actions", []):
            pri = action.get("priority", "").lower()
            pri_class = f"priority-{pri}" if pri in ["immediate","high","medium","low"] else ""
            tm = action.get("treatment_method", "")
            tm_str = f"&nbsp;·&nbsp; 🪄 {tm}" if tm and tm.lower() not in ["not available", ""] else ""
            
            st.markdown(f"""
            <div class="action-card">
              <div class="action-dot"></div>
              <div class="action-body">
                <div class="action-text">{action.get("action","")}</div>
                <div class="action-meta">
                  📍 {action.get("area","")} {tm_str} &nbsp;·&nbsp;
                  <span class="{pri_class}">{action.get("priority","").upper()}</span>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

        # Additional / Missing
        st.markdown('<div class="section-header">📌 Recommendations & Notes</div>', unsafe_allow_html=True)
        wp = ddr.get("waterproofing_recommendations", "")
        sr = ddr.get("structural_recommendations", "")
        if wp:
            st.markdown(f'<div class="obs-label">💧 Waterproofing Systems</div><div class="note-card" style="margin-bottom:0.5rem">{wp}</div>', unsafe_allow_html=True)
        if sr:
            st.markdown(f'<div class="obs-label">🧱 Structural Repairs</div><div class="note-card" style="margin-bottom:0.5rem">{sr}</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="obs-label">📝 Additional Notes</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="note-card">{ddr.get("additional_notes","—")}</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="obs-label" style="color:#d32f2f">❓ Missing / Unclear Info</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="note-card" style="color:#f57f17; border-color:#5c1e1e; background-color: #240a0a;">{ddr.get("missing_or_unclear_info","None")}</div>', unsafe_allow_html=True)

        # ── Download buttons ──
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">⬇️ Download Report</div>', unsafe_allow_html=True)

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            if st.session_state.docx_bytes:
                st.download_button(
                    label="📄 Download DDR Report (.docx)",
                    data=st.session_state.docx_bytes,
                    file_name="UrbanRoof_DDR_Report.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
        with col_dl2:
            st.download_button(
                label="{ } Download Raw Data (.json)",
                data=json.dumps(ddr, indent=2),
                file_name="UrbanRoof_DDR_Data.json",
                mime="application/json",
                use_container_width=True,
            )

        st.markdown("""
        <div class="tip-box">
            💡 <b>To open as Google Doc:</b> Upload the <code>.docx</code> to
            <a href="https://drive.google.com" target="_blank">Google Drive</a>,
            right-click → <i>Open with Google Docs</i>. All sections, tables, and formatting will be preserved.
        </div>
        """, unsafe_allow_html=True)

