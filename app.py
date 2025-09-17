import streamlit as st
from urllib.parse import urlparse

import backend.midasfn_npg as fn  

# Initialize session state if not already
if "mapi_key" not in st.session_state:
    st.session_state.mapi_key = ""
if "base_url" not in st.session_state:
    st.session_state.base_url = ""
if "submitted" not in st.session_state:
    st.session_state.submitted = False

def is_valid_url(url):
    """Check if the URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

# Show form only if not submitted
if not st.session_state.submitted:
    with st.form("config_form"):
        # st.title("Enter Configuration")

        base_url_input = st.text_input("Enter Base URL", placeholder="https://moa-engineers.midasit.com:443/civil")
        mapi_key_input = st.text_input("Enter MAPI Key", type="password", placeholder="Your MAPI Key here")

        submit_button = st.form_submit_button("Submit")

    if submit_button:
        errors = []

        if not base_url_input.strip():
            errors.append("Base URL cannot be empty.")
        elif not is_valid_url(base_url_input.strip()):
            errors.append("Please enter a valid URL.")

        if not mapi_key_input.strip():
            errors.append("MAPI Key cannot be empty.")

        if errors:
            for error in errors:
                st.error(error)
        else:
            # Save and rerun
            st.session_state.mapi_key = mapi_key_input.strip()
            st.session_state.base_url = base_url_input.strip()
            st.session_state.submitted = True
            st.rerun()  # Forces reload so form disappears

# Main plugin UI after form submission
if st.session_state.submitted:
    fn.MAPI_KEY(st.session_state.mapi_key)
    fn.base_url = st.session_state.base_url  # Ensure your backend uses this variable dynamically

    # Plugin content starts here
    st.title("Frame Section to Plate")

    sections = fn.get_Section()
    sections_dict = {name: sid for sid, name in sections}
    selected_section_name = st.selectbox("Choose a section",list(sections_dict.keys()))
    selected_section_id = sections_dict[selected_section_name]

    st.markdown("### CENTERLINE PLOT VIEWER")
    # plot_placeholder = st.empty()

    if selected_section_name:
      with st.spinner("Please wait while generating the plot..."):
        fig = fn.PSC_1CEL_XY(selected_section_id)
        # plot_placeholder.write(f"Plot for PSC section will be displayed here.")
      st.pyplot(fig)
