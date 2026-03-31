with open("app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = False

for i, line in enumerate(lines):
    if line.startswith('    initial_sidebar_state="collapsed"'):
        new_lines.append(line)
        new_lines.append('\nif "ddr_data" not in st.session_state:\n    st.session_state.ddr_data = None\nif "docx_bytes" not in st.session_state:\n    st.session_state.docx_bytes = None\nif "show_success" not in st.session_state:\n    st.session_state.show_success = False\n')
        continue
        
    if line.startswith('    if not generate_btn:') and 'st.session_state' not in line:
        new_lines.append('    if not generate_btn and st.session_state.ddr_data is None:\n')
        continue
        
    if line.startswith('            # ── Success banner ──'):
        skip = True
        # Insert session state setup
        new_lines.append('            st.session_state.ddr_data = ddr\n')
        new_lines.append('            with open(docx_path, "rb") as f:\n')
        new_lines.append('                st.session_state.docx_bytes = f.read()\n')
        new_lines.append('            st.session_state.show_success = True\n\n')
        continue
        
    if skip and line.startswith('        except Exception as e:'):
        skip = False
        new_lines.append(line)
        continue
        
    if not skip:
        # replace the finally block with safe vars
        if line.startswith('            if os.path.exists(inspection_path):'):
            new_lines.append("            if 'inspection_path' in locals() and os.path.exists(inspection_path): os.remove(inspection_path)\n")
            continue
        if line.startswith('            if os.path.exists(thermal_path):'):
            new_lines.append("            if 'thermal_path' in locals() and os.path.exists(thermal_path):    os.remove(thermal_path)\n")
            continue
            
        new_lines.append(line)

start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if line.startswith('            # ── Success banner ──'):
        start_idx = i
    if line.startswith('        except Exception as e:'):
        end_idx = i
        break

ui_lines = lines[start_idx:end_idx]

ui_code = """
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
"""

prop_start = -1
for i, line in enumerate(ui_lines):
    if line.startswith('            # Property Info'):
        prop_start = i
        break

unindented_prop_lines = []
for line in ui_lines[prop_start:]:
    nl = line[4:] if line.startswith("    ") else line
        
    if 'with open(docx_path, "rb") as f:' in nl:
        nl = nl.replace('with open(docx_path, "rb") as f:', 'if st.session_state.docx_bytes:')
    elif 'data=f.read()' in nl:
        nl = nl.replace('data=f.read()', 'data=st.session_state.docx_bytes')
        
    unindented_prop_lines.append(nl)

new_lines.extend(["\n"])
new_lines.append(ui_code)
new_lines.extend(unindented_prop_lines)

with open("app.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)
print("done successfully")
