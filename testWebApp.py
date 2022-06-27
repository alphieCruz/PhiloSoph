import streamlit as st
import requests

st.write('hello web app here')

st.write(requests.get('http://localhost:5000').text)
