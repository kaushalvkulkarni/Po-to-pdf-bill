import streamlit as st 
import google.generativeai as genai
from fpdf import FPDF
from PIL import Image
st.set_page_config(page_title="Automated pdf Billing", layout="centered")
st.title("Purchase order to PDF bill")
st.write("Upload Purchase Order")
uploded_file= st.file_uploader("upload po here (PDF or IMG)" , type=["jpg", "jpeg", "png", "pdf"])
if uploaded_file  is not none:
  st.success("File succefully uploaded! processing......")
  

