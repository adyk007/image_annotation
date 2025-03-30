import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

# Setup
IMAGE_FOLDER = Path("test_generation_user_study")
TOXIC_RANGE = range(0, 100)
NON_TOXIC_RANGE = range(100, 200)
TOXIC_CSV = "toxic_annotations.csv"
NON_TOXIC_CSV = "non_toxic_annotations.csv"

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
    username = st.text_input("Enter your name or ID:")

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
    mode = st.radio("Annotation Mode", ["Toxic Prompts", "Non-Toxic Prompts"])
    if st.button("Start Annotating"):
        st.session_state.mode = mode

        if mode == "Toxic Prompts":
            image_ids = TOXIC_RANGE
            csv_path = TOXIC_CSV
        else:
            image_ids = NON_TOXIC_RANGE
            csv_path = NON_TOXIC_CSV

        # Generate filenames
        all_images = [IMAGE_FOLDER / f"image_{i}.png" for i in image_ids]

        # Skip already annotated for this user
        if Path(csv_path).exists():
            df = pd.read_csv(csv_path)
            annotated = df[df["annotator"] == st.session_state.annotator]["image"].tolist()
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
    csv_path = TOXIC_CSV if mode == "Toxic Prompts" else NON_TOXIC_CSV

    if index >= len(images):
        st.success("All images in this category have been annotated.")
    else:
        img_path = images[index]
        st.markdown(f"### Image {index + 1} of {len(images)}")
        st.image(str(img_path), use_column_width=True)

        label = st.radio("Is this image toxic or non-toxic?", ["toxic", "non-toxic"])

        if st.button("Submit & Next"):
            # Load or create annotation file
            if Path(csv_path).exists():
                df = pd.read_csv(csv_path)
            else:
                df = pd.DataFrame(columns=["image", "label", "annotator", "timestamp"])

            # Save annotation
            row = {
                "image": img_path.name,
                "label": label,
                "annotator": annotator,
                "timestamp": datetime.now().isoformat()
            }
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            df.to_csv(csv_path, index=False)

            st.session_state.index += 1
            st.rerun()

    if st.button("Switch Task"):
        st.session_state.mode = None
        st.session_state.index = 0
        st.session_state.images = []
        st.rerun()