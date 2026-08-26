"""NetSage AI Streamlit entry point.

Milestone M0: prove the application environment starts.
No networking logic or AI diagnosis is implemented here.
"""

import streamlit as st

from config.settings import is_openai_configured

st.set_page_config(page_title="NetSage AI")
st.title("NetSage AI")
st.write("System initialized.")

# Configuration may be absent during M0. Never display secret values.
if is_openai_configured():
    st.caption("OpenAI API key is configured.")
else:
    st.caption("OpenAI API key is not configured.")
