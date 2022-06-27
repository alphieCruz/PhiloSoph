import streamlit as st
import requests
import traceback

st.write('hello web app here')

try:
  st.write(requests.get('http://localhost:5000').text)
except:
  st.write(traceback.format_exc())
