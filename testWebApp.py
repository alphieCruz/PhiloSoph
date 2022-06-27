import streamlit as st
import requests
import traceback

st.write('hello web app here')

try:
  st.write(requests.get('https://749b-179-50-15-34.ngrok.io').text)
except:
  st.write(traceback.format_exc())
