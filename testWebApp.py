import streamlit as st
import requests
import sys

st.write('hello web app here')

try:
  st.write(requests.get('http://179.50.15.34:5000').text)
except:
  print(sys.exc_info()[2])
