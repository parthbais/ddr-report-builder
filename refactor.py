import sys

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add session state init
state_init = """
if "ddr_data" not in st.session_state:
    st.session_state.ddr_data = None
if "docx_bytes" not in st.session_state:
    st.session_state.docx_bytes = None
if "show_success" not in st.session_state:
    st.session_state.show_success = False
"""
content = content.replace(
    'initial_sidebar_state="collapsed"\n)',
    'initial_sidebar_state="collapsed"\n)\n' + state_init
)

# 2. Update Empty State condition
content = content.replace(
    'if not generate_btn:\n        upload_count',
    'if not generate_btn and st.session_state.ddr_data is None:\n        upload_count'
)

# 3. Restructure try-except-finally and extract UI
ui_start = content.find('            # ── Success banner ──')
ui_end = content.find('        except Exception as e:')

if ui_start != -1 and ui_end != -1:
    old_ui_block = content[ui_start:ui_end]
    
    # Replacement for inside the try block
    new_try_end = """            st.session_state.ddr_data = ddr
            with open(docx_path, "rb") as f:
                st.session_state.docx_bytes = f.read()
            st.session_state.show_success = True\n\n"""
            
    # Modify the old UI block to use st.session_state and unindent if needed? 
    # Actually wait, it should stay indented at 4 spaces because it goes inside `with right:` (which is 4 spaces).
    # Wait, the `try` block was inside `if generate_btn and inspection_file and thermal_file:` (which is 4 spaces indentation, so inside it is 8 spaces).
    # We want it to be inside `if st.session_state.ddr_data is not None:` (which is at 4 spaces indentation, so inside it is 8 spaces!)
    # That means the indentation of the old UI block (12 spaces) should be unindented by 4 spaces.
    
    lines = old_ui_block.split('\n')
    unindented_lines = []
    for line in lines:
        if line.startswith('    '):
            unindented_lines.append(line[4:])
        else:
            unindented_lines.append(line)
            
    # We only want to keep the UI parts. 
    # But wait, we need to modify the success banner to be conditional on st.session_state.show_success
    new_ui_code = """    # ════════════════════════════
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
            st.session_state.show_success = False\n\n"""
            
    # Find where the Property Info starts so we skip the old success banner
    prop_info_start = old_ui_block.find('            # Property Info')
    
    prop_info_block = old_ui_block[prop_info_start:]
    # Unindent this
    prop_lines = prop_info_block.split('\n')
    unindented_prop = []
    for line in prop_lines:
        if line.startswith('    '):
            unindented_prop.append(line[4:])
        else:
            unindented_prop.append(line)
    
    unindented_prop_text = '\n'.join(unindented_prop)
    
    # Fix the docx download button to use st.session_state.docx_bytes
    unindented_prop_text = unindented_prop_text.replace(
        \'\'\'            with open(docx_path, "rb") as f:
                st.download_button(
                    label="📄 Download DDR Report (.docx)",
                    data=f.read(),\'\'\',
        \'\'\'            if st.session_state.docx_bytes:
                st.download_button(
                    label="📄 Download DDR Report (.docx)",
                    data=st.session_state.docx_bytes,\'\'\'
    )
    
    new_ui_code += unindented_prop_text
    
    # We also need to fix the finally block
    finally_start = content.find('        finally:')
    finally_end = content.find('\n', finally_start + 150) # find the end roughly
    
    old_full_try = content[content.find('        try:'):]
    # We'll just replace the original old_ui_block with new_try_end
    content = content.replace(old_ui_block, new_try_end)
    
    # And then we append the new_ui_code AFTER the finally block
    # We will search for the end of the finally block
    finally_part = """        finally:
            if os.path.exists(inspection_path): os.remove(inspection_path)
            if os.path.exists(thermal_path):    os.remove(thermal_path)"""
            
    safe_finally = """        finally:
            if 'inspection_path' in locals() and os.path.exists(inspection_path): os.remove(inspection_path)
            if 'thermal_path' in locals() and os.path.exists(thermal_path):    os.remove(thermal_path)"""
            
    content = content.replace(finally_part, safe_finally + '\n\n' + new_ui_code)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)
print("done")
