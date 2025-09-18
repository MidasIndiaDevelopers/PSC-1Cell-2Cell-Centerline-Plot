import streamlit as st
from urllib.parse import urlparse
import backend.midasfn_npg as fn  
import matplotlib.pyplot as plt
from io import BytesIO

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
            st.session_state.mapi_key = mapi_key_input.strip()
            st.session_state.base_url = base_url_input.strip()
            st.session_state.submitted = True
            st.rerun()

# Main plugin UI after form submission
if st.session_state.submitted:
    fn.MAPI_KEY(st.session_state.mapi_key)
    fn.base_url = st.session_state.base_url  # Ensure backend uses this variable dynamically

    st.title("Frame Section to Plate")

    sections = fn.get_Section()
    if not sections:
        st.error("No PSC sections found.")
    else:
        sections_dict = {name: sid for sid, name in sections}
        selected_section_name = st.selectbox("Choose a section", list(sections_dict.keys()))
        selected_section_id = sections_dict[selected_section_name]

        st.markdown("### CENTERLINE PLOT VIEWER")

        if selected_section_name:
            with st.spinner("Please wait while generating the plot..."):
                fig = fn.PSC_1CEL_XY(selected_section_id)

            st.pyplot(fig)

            # --- Add download button ---
            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
            buf.seek(0)

            st.download_button(
                label="📥 Download Plot as PNG",
                data=buf,
                file_name=f"PSC_Section_{selected_section_id}.png",
                mime="image/png"
            )
