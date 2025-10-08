import streamlit as st
from urllib.parse import urlparse
import matplotlib.pyplot as plt
from io import BytesIO

from backend.finalUIfunc import SS_create
from midas_civil import *
import backend.midasfn_npg as fn  

def custom_header(text, size=24, color="white", align="left"):
    st.markdown(
        f"<h3 style='font-size:{size}px; color:{color}; text-align:{align};'>{text}</h3>",
        unsafe_allow_html=True
    )
    
# --- Session state setup ---
if "mapi_key" not in st.session_state:
    st.session_state.mapi_key = ""
if "base_url" not in st.session_state:
    st.session_state.base_url = ""
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "plot_generated" not in st.session_state:
    st.session_state.plot_generated = False


def is_valid_url(url):
    """Check if the URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


# --- Config Form ---
if not st.session_state.submitted:
    with st.form("config_form"):
        st.subheader("Enter Configuration")

        base_url_input = st.text_input(
            "Enter Base URL",
            placeholder="https://moa-engineers.midasit.com:443/civil"
        )
        mapi_key_input = st.text_input(
            "Enter MAPI Key",
            type="password",
            placeholder="Your MAPI Key here"
        )

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


# --- Main UI after config ---
if st.session_state.submitted:
    # Init Midas session
    fn.MAPI_KEY(st.session_state.mapi_key)
    fn.MAPI_BASEURL(st.session_state.base_url)
    MAPI_KEY(st.session_state.mapi_key)
    MAPI_BASEURL(st.session_state.base_url)

    # Two-column layout
    col1, col2 = st.columns(2)

    # --- Left panel: Frame Section to Plate ---
    with col1:
        custom_header("Frame Section to Plate", size=26, align="left")

        sections = fn.get_Section()
        if not sections:
            st.error("No PSC sections found.")
        else:
            sections_dict = {name: sid for sid, name in sections}
            selected_section_name = st.selectbox(
                "Choose a section",
                list(sections_dict.keys())
            )
            selected_section_id = sections_dict[selected_section_name]

            st.markdown("### Centerline Plot Viewer")

            if selected_section_name:
                with st.spinner("Please wait while generating the plot..."):
                    fig = fn.PSC_1CEL_XY(selected_section_id)

                st.pyplot(fig)
                st.session_state.plot_generated = True

                # --- Download button ---
                buf = BytesIO()
                fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
                buf.seek(0)

                st.download_button(
                    label="Download Image",
                    data=buf,
                    file_name=f"PSC_Section_{selected_section_id}.png",
                    mime="image/png"
                )

    # --- Right panel: Line to Plate Converter ---
    with col2:
        custom_header("Line to Plate Converter", size = 26)

        col_mesh, col_rigid = st.columns([2,1])

        with col_mesh:
            switch_chngMesh = st.checkbox("Meshing option (Size or division)", value=True)
            # Mesh label depends on checkbox
            mesh_label = "No. of division" if switch_chngMesh else "Mesh Size (length)"

        with col_rigid:
            chk_RigdLnk = st.checkbox("Rigid Link", value=True)
        txt_mesh = st.number_input(mesh_label, min_value=0, value=20, step=1)

           

            # Run button
        if st.button("Create Mesh"):
            # fn.PSC_1CEL_XY(selected_section_id)
                fn.plotsegment()
                fn.build_global_arrays()
                try:
                    nSeg = txt_mesh
                    mSize = 0
                    if not switch_chngMesh:
                        mSize = txt_mesh
                        nSeg = 0

                    # Run mesh generation
                    SS_create(int(nSeg), float(mSize), bool(chk_RigdLnk))

                    Thickness.create()
                    Node.create()
                    Element.create()
                    if chk_RigdLnk:
                        Boundary.RigidLink.create()

                    st.success("Plates created successfully!")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")