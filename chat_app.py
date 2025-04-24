import streamlit as st
from streamlit_javascript import st_javascript
import requests
import json
import urllib.parse
import time
from datetime import datetime, timedelta
import math

st.set_page_config(page_title="Acu Chat", page_icon="🧠", layout="wide")

GROK_API_KEY = "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"
GROK_API_URL = "https://api.groq.com/openai/v1/chat/completions"
INTERVIEW_DURATION = 15 * 60  # 15 minutes in seconds
REDIRECT_URL = "https://acuvision.netlify.app/"

interview_cookie = st_javascript("document.cookie")
interview_data = {}

# Top Navbar with Logo and Timer
logo_url = "https://acuvision.netlify.app/svg/logo.svg"  # Change to your logo URL
current_time = time.time()

if interview_cookie:
    try:
        cookie_parts = interview_cookie.split("; ")
        interview_raw = next((c for c in cookie_parts if c.startswith("interviewData=")), None)
        if interview_raw:
            interview_json = interview_raw.split("=", 1)[1]
            interview_data = json.loads(urllib.parse.unquote(interview_json))
    except Exception as e:
        st.error(f"Failed to parse interview data: {e}")

if "messages" not in st.session_state:
    st.session_state.messages = []
    if interview_data.get("applicantName"):
        greeting = f"Hello {interview_data['applicantName']}! I'll be interviewing you for the {interview_data.get('jobTitle', 'position')} role."
        st.session_state.messages.append({"role": "assistant", "content": greeting})

if "start_time" not in st.session_state:
    st.session_state.start_time = current_time

elapsed_time = current_time - st.session_state.start_time
remaining_time = max(0, INTERVIEW_DURATION - elapsed_time)

# Navbar layout
navbar_html = f"""
<div style="background-color:#0e1117; padding:10px 30px; display:flex; justify-content:space-between; align-items:center;">
    <div style="display:flex; align-items:center;">
        <img src="{logo_url}" style="height:40px; margin-right:10px;" />
        <span style="color:white; font-size:24px; font-weight:bold;">Acu Chat</span>
    </div>
    <div style="color:white; font-size:20px;">
        ⏰ {int(remaining_time // 60):02d}:{int(remaining_time % 60):02d}
    </div>
</div>
"""
st.markdown(navbar_html, unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    if interview_data:
        st.subheader("Interview Information")
        st.markdown(f"**Applicant:** {interview_data.get('applicantName', 'N/A')}")
        st.markdown(f"**Job Title:** {interview_data.get('jobTitle', 'N/A')}")
        st.markdown(f"**Job Type:** {interview_data.get('JobType', 'N/A')}")

        with st.expander("View Job Description"):
            st.write(interview_data.get('JobDes', 'N/A'))

        with st.expander("View Job Requirements"):
            st.write(interview_data.get('JobReq', 'N/A'))

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if remaining_time > 0:
        prompt = st.chat_input("Type your message...")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                headers = {
                    "Authorization": f"Bearer {GROK_API_KEY}",
                    "Content-Type": "application/json",
                }

                system_prompt = {
                    "role": "system",
                    "content": f"You are conducting an interview for {interview_data.get('jobTitle', 'a position')}. "
                              f"Job description: {interview_data.get('JobDes', '')}. "
                              f"Job requirements: {interview_data.get('JobReq', '')}. "
                              "Ask relevant questions and evaluate the candidate's responses."
                }

                messages = [system_prompt] + st.session_state.messages

                data = {
                    "model": "llama3-8b-8192",
                    "messages": messages,
                }

                response = requests.post(GROK_API_URL, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                reply = result["choices"][0]["message"]["content"]

            except Exception as e:
                reply = f"Error: {e}"

            st.session_state.messages.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)
    else:
        st.warning("Interview time has ended!")

with col2:

    if remaining_time <= 0:
        st.warning("Interview time has ended!")
        st.markdown(f"Redirecting to evaluation...")
        st_javascript(f"window.location.href = '{REDIRECT_URL}';")

time.sleep(1)
st.rerun()
