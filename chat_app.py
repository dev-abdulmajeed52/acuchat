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
reMarkApi = "http://localhost:3000/api/remarks"
INTERVIEW_DURATION = 3 * 60  # 15 minutes in seconds
REDIRECT_URL = "http://localhost:5173/"

interview_data = {}
query_params = st.query_params

# Parse interview data from query params
if "data" in query_params:
    try:
        interview_json = urllib.parse.unquote(query_params["data"])
        interview_data = json.loads(interview_json)
    except Exception as e:
        st.error(f"Failed to parse interview data: {e}")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    if interview_data.get("applicantName"):
        greeting = f"Hello {interview_data['applicantName']}! I'll be interviewing you for the {interview_data.get('jobTitle', 'position')} role."
        st.session_state.messages.append({"role": "assistant", "content": greeting})

if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()

# Calculate elapsed and remaining time
current_time = time.time()
elapsed_time = current_time - st.session_state.start_time
remaining_time = max(0, INTERVIEW_DURATION - elapsed_time)

# Navbar with logo and timer
logo_url = "https://acuvision.netlify.app/svg/logo.svg"
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
    # Display interview information
    if interview_data:
        st.subheader("Interview Information")
        st.markdown(f"**Applicant:** {interview_data.get('applicantName', 'N/A')}")
        st.markdown(f"**Job Title:** {interview_data.get('jobTitle', 'N/A')}")
        st.markdown(f"**Job Type:** {interview_data.get('JobType', 'N/A')}")

        with st.expander("View Job Description"):
            st.write(interview_data.get('JobDes', 'N/A'))

        with st.expander("View Job Requirements"):
            st.write(interview_data.get('JobReq', 'N/A'))

    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle chat input if interview is ongoing
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

        # Generate and send dynamic remark
        try:
            # Call Groq API to generate AI remark
            headers = {
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json",
            }

            system_prompt = {
                "role": "system",
                "content": f"You are evaluating a candidate's interview for the {interview_data.get('jobTitle', 'position')} role. "
                          f"Job description: {interview_data.get('JobDes', '')}. "
                          f"Job requirements: {interview_data.get('JobReq', '')}. "
                          "Based on the conversation history, provide a concise remark (1-2 sentences) on the candidate's suitability for the role."
            }

            messages = [system_prompt] + st.session_state.messages

            data = {
                "model": "llama3-8b-8192",
                "messages": messages,
                "max_tokens": 100,  # Limit response length
            }

            response = requests.post(GROK_API_URL, headers=headers, json=data)
            response.raise_for_status()
            ai_remark = response.json()["choices"][0]["message"]["content"]

            # Construct remark data
            remark_data = {
                "name": interview_data.get("applicantName", "Unknown Applicant"),
                "title": interview_data.get("jobTitle", "Unknown Position"),
                "description": f"Applied for the {interview_data.get('jobTitle', 'position')} role. Engaged actively during the interview.",
                "airemark": ai_remark
            }

            # Send remark to reMarkApi
            response = requests.post(reMarkApi, headers=headers, json=remark_data)
            response.raise_for_status()
            st.success("Remark sent successfully!")
        except Exception as e:
            st.error(f"Failed to send remark: {e}")

        # Redirect to evaluation page
        st_javascript(f"window.location.href = '{REDIRECT_URL}';")

# Rerun to update timer
time.sleep(1)
st.rerun()