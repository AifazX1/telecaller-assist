import streamlit as st
import pandas as pd
import re
import io

def extract_leads(df):
    """
    Extract leads with phone and name from DataFrame.
    Preserves first-seen order, associatees name with first phone found in row.
    """
    phone_pattern = r'\b\d{10}\b'
    leads = []
    seen_phones = set()
    # Row-major order
    for idx, row in df.iterrows():
        row_strs = {}
        for col in df.columns:
            value = row[col]
            if pd.isna(value):
                continue
            row_strs[col] = str(value)
        # Find name-candidate: first non-numeric column value
        name = "Unknown"
        for col, val in row_strs.items():
            if not re.match(r'^\d+$', val.strip()):
                name = val.strip()
                break
        
        for col in df.columns:
            value = row[col]
            if pd.isna(value):
                continue
            str_value = str(value)
            found_numbers = re.findall(phone_pattern, str_value)
            for num in found_numbers:
                if num not in seen_phones:
                    seen_phones.add(num)
                    leads.append({"phone": num, "name": name})
    return leads

def main():
    st.title("📱 10-Digit Phone Number Extractor")
    st.markdown("Upload an Excel file (.xlsx) to extract unique 10-digit phone numbers.")

    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

    if uploaded_file is not None:
        try:
            # Read Excel file
            df = pd.read_excel(uploaded_file)
            st.success(f"✅ File uploaded successfully! Shape: {df.shape}")
            df_display = df.head().copy()
            df_display.index += 1
            st.dataframe(df_display, use_container_width=True)

            # Extract leads
            leads = extract_leads(df)
            
            if leads:
                st.success(f"✅ Found {len(leads)} unique leads!")
                
                # Initialize session state first to avoid access before init
                if 'current_index' not in st.session_state:
                    st.session_state.current_index = 0
                if 'statuses' not in st.session_state:
                    st.session_state.statuses = {}
                if 'notes' not in st.session_state:
                    st.session_state.notes = {}
                
                st.divider()
                
                # Progress Dashboard (top section)
                st.header("📈 Progress")
                total_leads = len(leads)
                called = len(st.session_state.statuses)
                remaining_leads = total_leads - called
                statuses_list = list(st.session_state.statuses.values())
                interested_count = statuses_list.count("Interested")
                not_interested_count = statuses_list.count("Not Interested")
                call_later_count = statuses_list.count("Call Later")
                not_reachable_count = statuses_list.count("Not Reachable")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Leads", total_leads)
                with col2:
                    st.metric("Called", called)
                with col3:
                    st.metric("Remaining", remaining_leads)
                
                col4, col5, col6, col7 = st.columns(4)
                with col4:
                    st.metric("Interested", interested_count)
                with col5:
                    st.metric("Not Interested", not_interested_count)
                with col6:
                    st.metric("Call Later", call_later_count)
                with col7:
                    st.metric("Not Reachable", not_reachable_count)
                
                st.divider()
                
                # Main Current Lead Display (prominent)
                st.header("👤 Current Lead")
                current_lead = leads[st.session_state.current_index]
                current_num = current_lead["phone"]
                current_name = current_lead["name"]
                total = len(leads)
                st.markdown(f"### **{current_name}**")
                st.markdown(f"**### {current_num}**")
                st.caption(f"Position: {st.session_state.current_index + 1} of {total}")
                
                # CALL NOW button - direct tel link
                call_html = f"""
                <div style="text-align: center; margin: 20px 0;">
                    <a href="tel:{current_num}" style="
                        background-color: #10B981; 
                        color: white; 
                        padding: 15px 30px; 
                        font-size: 24px; 
                        font-weight: bold; 
                        border-radius: 50px; 
                        text-decoration: none; 
                        display: inline-block; 
                        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
                        transition: all 0.3s ease;
                    " onmouseover="this.style.transform='scale(1.05)';" onmouseout="this.style.transform='scale(1)';">
                        📞 CALL NOW
                    </a>
                </div>
                """
                st.markdown(call_html, unsafe_allow_html=True)
                
                # Navigation buttons
                col_nav1, col_nav2 = st.columns(2)
                with col_nav1:
                    if st.session_state.current_index > 0:
                        if st.button("⬅️ Previous", use_container_width=True):
                            st.session_state.current_index -= 1
                            st.rerun()
                    else:
                        st.button("⬅️ Previous", disabled=True, use_container_width=True)
                with col_nav2:
                    if st.session_state.current_index < total - 1:
                        if st.button("Next ➡️", use_container_width=True):
                            st.session_state.current_index += 1
                            st.rerun()
                    else:
                        st.button("Next ➡️", disabled=True, use_container_width=True)
                
                st.divider()
                
                # Status Buttons (horizontal)
                st.header("📞 Call Status")
                current_status = st.session_state.statuses.get(current_num, "Not Marked")
                st.info(f"Current Status: **{current_status}**")
                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                with col_s1:
                    if st.button("👍 Interested", use_container_width=True):
                        st.session_state.statuses[current_num] = "Interested"
                        st.rerun()
                with col_s2:
                    if st.button("❌ Not Interested", use_container_width=True):
                        st.session_state.statuses[current_num] = "Not Interested"
                        st.rerun()
                with col_s3:
                    if st.button("⏳ Call Later", use_container_width=True):
                        st.session_state.statuses[current_num] = "Call Later"
                        st.rerun()
                with col_s4:
                    if st.button("📴 Not Reachable", use_container_width=True):
                        st.session_state.statuses[current_num] = "Not Reachable"
                        st.rerun()
                
                st.divider()
                
                # Notes Section
                st.header("📝 Call Notes")
                current_note = st.session_state.notes.get(current_num, "")
                new_note = st.text_area("Add your call notes here...", value=current_note, height=150, key=f"note_input_{current_num}")
                if st.button("💾 Save Note", use_container_width=True):
                    st.session_state.notes[current_num] = new_note
                    st.success("✅ Note saved!")
                    st.rerun()
                if current_note:
                    st.caption(f"Saved note: {current_note}")
                
                st.divider()
                
                # Export Report
                st.header("📤 Export")
                def create_report_df(leads, statuses, notes):
                    data = []
                    for lead in leads:
                        phone = lead['phone']
                        name = lead['name']
                        status = statuses.get(phone, "")
                        note = notes.get(phone, "")
                        data.append({"Phone Number": phone, "Name": name, "Status": status, "Notes": note})
                    return pd.DataFrame(data)
                
                report_df = create_report_df(leads, st.session_state.statuses, st.session_state.notes)
                csv = report_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download call_report.csv",
                    data=csv,
                    file_name="call_report.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                st.divider()
                
                # Show all leads expander
                with st.expander("📋 View All Leads"):
                    for i, lead in enumerate(leads):
                        st.write(f"**{i+1}.** Phone: `{lead['phone']}` | Name: {lead['name']}")
            else:
                st.warning("❌ No 10-digit phone numbers found in the file.")
                
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
    else:
        st.info("👆 Please upload an Excel file to get started.")

if __name__ == "__main__":
    main()

