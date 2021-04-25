import streamlit as st
from multiapp import MultiApp
import v1_app, v2_app

app = MultiApp()

st.markdown("""
# Multi-Page App
""")

# Add all your application here
app.add_app("Version 1", v1_app.app)
#app.add_app("Version 2", v2_app.app)
app.run()
#app.add_app("Model", model.app)
# The main app
