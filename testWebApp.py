import streamlit as st
import requests
import traceback

st.write('hello web app here')

try:
  st.write(requests.get('http://179.50.15.34:5000').text)
except:
  st.write(traceback.format_exc())
