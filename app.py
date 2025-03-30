import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)

SHEET_ID = "1C72krCoQexiM8eNVk29BB7YXLGZkDuhN1iZHPHuvksw"  # Replace this with your real Sheet ID
sheet = client.open_by_key(SHEET_ID)
toxic_ws = sheet.worksheet("Toxic")        # Worksheet/tab name for toxic annotations
non_toxic_ws = sheet.worksheet("NonToxic")  # Worksheet/tab name for non-toxic annotations

# Setup
IMAGE_FOLDER = Path("test_generation_user_study")
TOXIC_RANGE = list(range(0, 100)) + list(range(200, 224))
NON_TOXIC_RANGE = range(100, 200)

# Session state setup
if "annotator" not in st.session_state:
    st.session_state.annotator = None
if "mode" not in st.session_state:
    st.session_state.mode = None
if "index" not in st.session_state:
    st.session_state.index = 0
if "images" not in st.session_state:
    st.session_state.images = []

# Step 1: Choose annotator
if st.session_state.annotator is None:
    st.title("Annotator Setup")
    username = st.text_input("Enter your name:")

    if st.button("Continue"):
        if username.strip() == "":
            st.warning("Please enter a valid name.")
        else:
            st.session_state.annotator = username.strip()
            st.rerun()

# Step 2: Choose annotation mode
elif st.session_state.mode is None:
    st.title("Image Classification for Toxicity")
    st.markdown(f"Welcome, **{st.session_state.annotator}**! Please choose a task:")
    mode = st.radio("Annotation Mode", ["Toxic Images", "Non-Toxic Images"])
    if st.button("Start Annotating"):
        st.session_state.mode = mode

        if mode == "Toxic Images":
            image_ids = TOXIC_RANGE
            worksheet = toxic_ws
        else:
            image_ids = NON_TOXIC_RANGE
            worksheet = non_toxic_ws

        all_images = [IMAGE_FOLDER / f"image_{i}.png" for i in image_ids]

        # Load annotated image names from Google Sheet
        records = worksheet.get_all_records()
        annotated = [row["image"] for row in records if row["annotator"] == st.session_state.annotator]
        all_images = [img for img in all_images if img.name not in annotated]

        st.session_state.images = all_images
        st.session_state.index = 0
        st.rerun()

# Step 3: Annotation UI
else:
    images = st.session_state.images
    index = st.session_state.index
    annotator = st.session_state.annotator
    mode = st.session_state.mode
    worksheet = toxic_ws if mode == "Toxic Images" else non_toxic_ws

    if index >= len(images):
        st.success("All images in this category have been annotated.")
    else:
        img_path = images[index]
        st.markdown(f"### Image {index + 1} of {len(images)}")
        st.image(str(img_path), use_column_width=True)

        if mode == "Toxic Images":
            label_options = ["Toxic", "Non-toxic"]
            label_question = "Is this image toxic or non-toxic?"
        else:
            label_options = ["Safe", "Blurry"]
            label_question = "How would you classify this image?"

        label = st.radio(label_question, label_options)

        if st.button("Submit & Next"):
            row = [
                img_path.name,
                label,
                annotator,
                datetime.now().isoformat()
            ]
            worksheet.append_row(row)

            st.session_state.index += 1
            st.rerun()

    if st.button("Switch Task"):
        st.session_state.mode = None
        st.session_state.index = 0
        st.session_state.images = []
        st.rerun()
