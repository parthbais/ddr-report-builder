import streamlit as st
import json
import os
import shutil
from src.extractor import extract_pdf, get_full_text, get_all_images
from src.merger import generate_ddr_json, save_ddr_json

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="DDR Report Builder | UrbanRoof",
    page_icon="🏠",
    layout="wide"
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background-color: #0f0f0f;
        color: #f0f0f0;
    }

    /* Header */
    .ur-header {
        background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
        border-bottom: 3px solid #FFC107;
        padding: 1.5rem 2rem;
        margin: -1rem -1rem 2rem -1rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .ur-logo { font-size: 2rem; }
    .ur-title { font-size: 1.6rem; font-weight: 700; color: #FFC107; margin: 0; }
    .ur-subtitle { font-size: 0.85rem; color: #aaa; margin: 0; }

    /* Upload cards */
    .upload-card {
        background: #1a1a1a;
        border: 2px dashed #FFC107;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s;
    }
    .upload-card:hover { border-color: #FFD54F; background: #222; }

    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #FFC107, #FF8F00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #333;
    }

    /* Observation cards */
    .obs-card {
        background: #1a1a1a;
        border-left: 4px solid #FFC107;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
    }
    .obs-area { font-weight: 700; color: #FFC107; font-size: 1rem; margin-bottom: 0.5rem; }
    .obs-label { font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 0.05em; }
    .obs-value { font-size: 0.9rem; color: #e0e0e0; margin-bottom: 0.6rem; }

    /* Severity badges */
    .badge-critical { background: #c62828; color: white; padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .badge-high     { background: #e65100; color: white; padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .badge-moderate { background: #f57f17; color: black; padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .badge-low      { background: #2e7d32; color: white; padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }

    /* Info box */
    .info-box {
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .info-row { display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #2a2a2a; }
    .info-key { color: #888; font-size: 0.85rem; }
    .info-val { color: #FFC107; font-size: 0.85rem; font-weight: 600; }

    /* Action items */
    .action-item {
        background: #1a1a1a;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.6rem;
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
    }
    .action-dot { width: 8px; height: 8px; background: #FFC107; border-radius: 50%; margin-top: 6px; flex-shrink: 0; }

    /* Generate button */
    .stButton > button {
        background: linear-gradient(135deg, #FFC107, #FF8F00) !important;
        color: black !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 2rem !important;
        width: 100% !important;
        transition: all 0.3s !important;
    }
    .stButton > button:hover { opacity: 0.9 !important; transform: translateY(-1px) !important; }

    /* Download button */
    .stDownloadButton > button {
        background: #1a1a1a !important;
        color: #FFC107 !important;
        border: 2px solid #FFC107 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        width: 100% !important;
    }

    /* Progress / status */
    .status-step {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.6rem 0;
        color: #ccc;
        font-size: 0.9rem;
    }
    .step-done { color: #FFC107; }

    /* Divider */
    hr { border-color: #2a2a2a; }

    /* Streamlit overrides */
    .stFileUploader { background: transparent !important; }
    [data-testid="stFileUploader"] { background: #1a1a1a; border-radius: 10px; padding: 1rem; }
    .stSpinner > div { border-top-color: #FFC107 !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────
st.markdown("""
<div class="ur-header">
    <div class="ur-logo">🏗️</div>
    <div>
        <p class="ur-title">DDR Report Builder</p>
        <p class="ur-subtitle">Powered by AI · UrbanRoof Private Limited</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Layout ───────────────────────────────────────────────────
left, right = st.columns([1, 2], gap="large")

with left:
    st.markdown('<p class="section-header">📂 Upload Documents</p>', unsafe_allow_html=True)

    inspection_file = st.file_uploader(
        "Inspection Report (PDF)",
        type=["pdf"],
        key="inspection",
        help="Upload the site inspection form PDF"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    thermal_file = st.file_uploader(
        "Thermal Images Report (PDF)",
        type=["pdf"],
        key="thermal",
        help="Upload the thermal scan report PDF"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    ready = inspection_file and thermal_file
    generate_btn = st.button(
        "⚡ Generate DDR Report",
        disabled=not ready,
        use_container_width=True
    )

    if not ready:
        st.markdown("""
        <div style="color:#666; font-size:0.8rem; text-align:center; margin-top:0.5rem;">
            Upload both files to enable generation
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="color:#555; font-size:0.75rem; line-height:1.6;">
        <b style="color:#888;">How it works</b><br>
        1. Upload inspection + thermal PDFs<br>
        2. AI extracts & merges both reports<br>
        3. Download a structured DDR document
    </div>
    """, unsafe_allow_html=True)

# ── Main panel ───────────────────────────────────────────────
with right:
    if not generate_btn:
        st.markdown("""
        <div style="
            background:#1a1a1a;
            border-radius:16px;
            padding:3rem;
            text-align:center;
            border:2px dashed #2a2a2a;
            margin-top:1rem;
        ">
            <div style="font-size:3rem; margin-bottom:1rem;">📋</div>
            <p style="color:#FFC107; font-size:1.2rem; font-weight:600;">Ready to Generate</p>
            <p style="color:#666; font-size:0.9rem;">Upload both documents on the left and click Generate.<br>
            Your DDR report will appear here.</p>
        </div>
        """, unsafe_allow_html=True)

    if generate_btn and inspection_file and thermal_file:
        # Save uploaded files temporarily
        os.makedirs("uploads/temp", exist_ok=True)
        inspection_path = f"uploads/temp/{inspection_file.name}"
        thermal_path = f"uploads/temp/{thermal_file.name}"

        with open(inspection_path, "wb") as f:
            f.write(inspection_file.read())
        with open(thermal_path, "wb") as f:
            f.write(thermal_file.read())

        # Processing steps
        progress_placeholder = st.empty()

        def show_progress(steps):
            html = '<div style="background:#1a1a1a; border-radius:10px; padding:1.2rem; margin-bottom:1rem;">'
            for label, done in steps:
                icon = "✅" if done else "⏳"
                color = "#FFC107" if done else "#555"
                html += f'<div class="status-step"><span>{icon}</span><span style="color:{color}">{label}</span></div>'
            html += '</div>'
            progress_placeholder.markdown(html, unsafe_allow_html=True)

        steps = [
            ("Extracting Inspection Report...", False),
            ("Extracting Thermal Report...", False),
            ("AI Merging & Analyzing...", False),
            ("Building DDR...", False),
        ]
        show_progress(steps)

        try:
            # Step 1
            inspection_data = extract_pdf(inspection_path)
            inspection_text = get_full_text(inspection_data)
            inspection_images = get_all_images(inspection_data)
            steps[0] = (f"Inspection Report extracted ({len(inspection_images)} images)", True)
            show_progress(steps)

            # Step 2
            thermal_data = extract_pdf(thermal_path)
            thermal_text = get_full_text(thermal_data)
            thermal_images = get_all_images(thermal_data)
            steps[1] = (f"Thermal Report extracted ({len(thermal_images)} thermal images)", True)
            show_progress(steps)

            # Step 3
            with st.spinner("AI is analyzing and merging reports..."):
                ddr = generate_ddr_json(inspection_text, thermal_text)
            save_ddr_json(ddr)
            steps[2] = ("AI analysis complete", True)
            show_progress(steps)

            steps[3] = ("DDR built successfully!", True)
            show_progress(steps)

            # ── Render DDR ──
            st.success("✅ DDR Generated Successfully!")

            # Property Info
            st.markdown('<p class="section-header">🏠 Property Information</p>', unsafe_allow_html=True)
            pi = ddr.get("property_info", {})
            info_html = '<div class="info-box">'
            for k, v in pi.items():
                label = k.replace("_", " ").title()
                info_html += f'<div class="info-row"><span class="info-key">{label}</span><span class="info-val">{v or "N/A"}</span></div>'
            info_html += '</div>'
            st.markdown(info_html, unsafe_allow_html=True)

            # Issue Summary
            st.markdown('<p class="section-header">📝 Property Issue Summary</p>', unsafe_allow_html=True)
            st.markdown(f'<div class="obs-card"><p style="color:#e0e0e0; margin:0">{ddr.get("property_issue_summary","")}</p></div>', unsafe_allow_html=True)

            # Area-wise Observations
            st.markdown('<p class="section-header">🔍 Area-wise Observations</p>', unsafe_allow_html=True)
            for obs in ddr.get("area_wise_observations", []):
                st.markdown(f"""
                <div class="obs-card">
                    <div class="obs-area">📍 {obs.get('area','')}</div>
                    <div class="obs-label">Negative Observations</div>
                    <div class="obs-value">⚠️ {obs.get('negative_observations','')}</div>
                    <div class="obs-label">Positive / Source Side</div>
                    <div class="obs-value">🔎 {obs.get('positive_observations','')}</div>
                    <div class="obs-label">Thermal Reading</div>
                    <div class="obs-value">🌡️ {obs.get('thermal_reading','Not Available')}</div>
                </div>
                """, unsafe_allow_html=True)

            # Severity
            st.markdown('<p class="section-header">⚡ Severity Assessment</p>', unsafe_allow_html=True)
            for s in ddr.get("severity_assessment", []):
                sev = s.get("severity","").lower()
                badge = f'<span class="badge-{sev}">{sev.upper()}</span>'
                st.markdown(f"""
                <div class="obs-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                        <span style="color:#FFC107; font-weight:600">{s.get('area','')}</span>
                        {badge}
                    </div>
                    <div class="obs-value" style="margin:0">{s.get('reasoning','')}</div>
                </div>
                """, unsafe_allow_html=True)

            # Recommended Actions
            st.markdown('<p class="section-header">🔧 Recommended Actions</p>', unsafe_allow_html=True)
            for action in ddr.get("recommended_actions", []):
                priority = action.get("priority","").upper()
                color = "#c62828" if priority == "IMMEDIATE" else "#f57f17" if priority == "HIGH" else "#888"
                st.markdown(f"""
                <div class="action-item">
                    <div class="action-dot"></div>
                    <div>
                        <span style="color:#e0e0e0">{action.get('action','')}</span>
                        <span style="color:#666; font-size:0.8rem"> — {action.get('area','')}</span>
                        <span style="color:{color}; font-size:0.75rem; font-weight:600; margin-left:0.5rem">[{priority}]</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Additional Notes & Missing Info
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<p class="section-header">📌 Additional Notes</p>', unsafe_allow_html=True)
                st.markdown(f'<div class="obs-card"><p style="color:#e0e0e0;margin:0">{ddr.get("additional_notes","")}</p></div>', unsafe_allow_html=True)
            with col2:
                st.markdown('<p class="section-header">❓ Missing / Unclear Info</p>', unsafe_allow_html=True)
                st.markdown(f'<div class="obs-card"><p style="color:#e0e0e0;margin:0">{ddr.get("missing_or_unclear_info","")}</p></div>', unsafe_allow_html=True)

            # Download JSON
            st.markdown("---")
            st.download_button(
                label="⬇️ Download DDR (JSON)",
                data=json.dumps(ddr, indent=2),
                file_name="DDR_Report.json",
                mime="application/json",
                use_container_width=True
            )

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.code(str(e))

        finally:
            # Cleanup temp files
            if os.path.exists(inspection_path): os.remove(inspection_path)
            if os.path.exists(thermal_path): os.remove(thermal_path)