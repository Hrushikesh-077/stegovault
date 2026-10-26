"""Streamlit UI.  Run with:  streamlit run app.py"""
import io

import cv2
import numpy as np
import streamlit as st
from PIL import Image

import stego

st.set_page_config(page_title="StegoVault", page_icon="🔐", layout="centered")
st.title("🔐 StegoVault")
st.caption("Data Hiding in Image Using Steganography - LSB + AES password protection")

tab_hide, tab_extract, tab_about = st.tabs(["Hide data", "Extract data", "About"])

# ---------------------------------------------------------------- HIDE
with tab_hide:
    cover_file = st.file_uploader("Cover image", type=["png", "bmp", "jpg", "jpeg"], key="cover")
    txt_file = st.file_uploader("...or load the secret from a .txt file", type=["txt"], key="txt")
    message = st.text_area("Secret message", height=120)
    if txt_file is not None:
        message = txt_file.read().decode("utf-8", errors="replace")
        st.info(f"Using text from {txt_file.name} ({len(message)} characters).")
    password = st.text_input("Password / key (optional - enables AES-256 encryption)",
                             type="password", key="pw_hide")

    if cover_file:
        cover = stego.load_rgb(cover_file)
        st.caption(f"{cover.shape[1]}x{cover.shape[0]} px - capacity about "
                   f"{stego.capacity(cover):,} bytes")

    if st.button("Embed message", type="primary"):
        if not cover_file:
            st.error("Please upload a cover image.")
        elif not message:
            st.error("Please enter or load a secret message.")
        else:
            try:
                out = stego.embed(cover, message, password)
            except stego.StegoError as e:
                st.error(str(e))
            else:
                q = stego.quality(cover, out)
                # cross-check PSNR with OpenCV
                cv_psnr = cv2.PSNR(cover, out) if q["mse"] else float("inf")
                st.success("Message hidden successfully.")
                c1, c2, c3 = st.columns(3)
                c1.metric("MSE", f"{q['mse']:.5f}")
                c2.metric("PSNR (dB)", "inf" if cv_psnr == float("inf") else f"{cv_psnr:.2f}")
                c3.metric("Encrypted", "Yes" if password else "No")

                diff = cv2.absdiff(cover, out) * 255  # amplified: every changed value -> 255
                heat = cv2.applyColorMap(cv2.cvtColor(diff, cv2.COLOR_RGB2GRAY), cv2.COLORMAP_INFERNO)
                a, b, c = st.columns(3)
                a.image(cover, caption="Original", use_container_width=True)
                b.image(out, caption="Stego image", use_container_width=True)
                c.image(cv2.cvtColor(heat, cv2.COLOR_BGR2RGB),
                        caption="Changed pixels (amplified)", use_container_width=True)

                buf = io.BytesIO()
                Image.fromarray(out).save(buf, format="PNG")
                st.download_button("Download stego image (PNG)", buf.getvalue(),
                                   file_name="stego_image.png", mime="image/png")

# ------------------------------------------------------------- EXTRACT
with tab_extract:
    stego_file = st.file_uploader("Stego image (PNG/BMP)", type=["png", "bmp"], key="stego")
    pw2 = st.text_input("Password / key (if one was used)", type="password", key="pw_ext")
    if st.button("Extract message", type="primary"):
        if not stego_file:
            st.error("Please upload a stego image.")
        else:
            try:
                secret = stego.extract(stego.load_rgb(stego_file), pw2)
            except stego.StegoError as e:
                st.error(str(e))
            else:
                st.success("Hidden message extracted:")
                st.code(secret, language=None)

# --------------------------------------------------------------- ABOUT
with tab_about:
    st.markdown("""
**How it works** - every message bit replaces the *least significant bit* of a pixel's
R, G or B value, changing each colour by at most 1/255 (invisible to the eye).
A header (magic bytes, flag, length) lets the extractor find the data.
With a password, the text is AES-256-GCM encrypted first (key from PBKDF2-SHA256).

**Always keep the stego image as PNG or BMP.** JPEG compression destroys hidden bits.
""")
