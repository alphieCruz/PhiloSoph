import streamlit as st
import requests

st.write('hello web app here')

st.write(requests.get('http://179.50.15.34:5000').text)
