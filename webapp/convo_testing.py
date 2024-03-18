from openai import OpenAI
import time
import datetime as date
from docx import Document
import io
import os
import streamlit as st
import streamlit.components.v1 as components
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId)
from audiorecorder import audiorecorder
import tempfile
from annotated_text import annotated_text
import json

from lookups import *
from web_classes import *
from web_methods import *
# from dotenv import load_dotenv

# load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
st.session_state["username"] = "TESTING"
st.title("Medical Interview Simulation (CONVO ONLY)")

if "stage" not in st.session_state:
    st.session_state["stage"] = SETTINGS

def set_stage(stage):
    st.session_state["stage"] = stage

if st.session_state["stage"] == SETTINGS:
    st.session_state["interview"] = None
    st.session_state["convo_memory"] = None
    st.session_state["convo_file"] = None
    patient_name = st.selectbox("Which patient would you like to interview?", 
                                                ["John Smith", "Jackie Smith"],
                                                index = None,
                                                placeholder = "Select patient...")
    if patient_name: st.session_state["interview"] = Interview(st.session_state["username"], Patient(patient_name))

    st.button("Start Interview", on_click=set_stage, args=[CHAT_SETUP])


if st.session_state["stage"] == CHAT_SETUP:
    st.session_state["convo_memory"] = [{"role": "system", "content": st.session_state["interview"].get_patient().convo_prompt}]
                                        # {"role": "system", "content": "Summary of conversation so far: None"}
    
    set_stage(CHAT_INTERFACE_TEXT)


if st.session_state["stage"] == CHAT_INTERFACE_TEXT:
    st.write("You may now begin your interview with " + st.session_state["interview"].get_patient().name + ". Start by introducing yourself.")
    st.write("Click the Restart button to restart the interview. Click the End Interview button to go to the download screen.")
    # st.session_state["start_time"] = date.datetime.now()

    container = st.container(height=300)

    for message in st.session_state["interview"].get_messages():
        with container:
            with st.chat_message(message.role):
                st.markdown(message.content)

    if user_input := st.chat_input("Type here..."):
        with container:
            with st.chat_message("User"):
                st.markdown(user_input)
        st.session_state["interview"].add_message(Message("input", "User", user_input))
        st.session_state["convo_memory"].append({"role": "user", "content": user_input})
        response = generate_response(model = CONVO_MODEL, 
                                   temperature = CHAT_TEMP, 
                                   system = st.session_state["convo_memory"][0]["content"], 
                                   messages = st.session_state["convo_memory"][1:])
        speech = generate_voice(response)
        st.session_state["convo_memory"].append({"role": "assistant", "content": response})
        with container:
            with st.chat_message("AI"): #TODO Needs avatar eventually
                st.markdown(response)
                play_voice(speech)
        st.session_state["interview"].add_message(Message("output", "AI", response))

    columns = st.columns(4)
    columns[1].button("Restart", on_click=set_stage, args=[SETTINGS])
    columns[2].button("End Interview", on_click=set_stage, args=[DIAGNOSIS])


if st.session_state["stage"] == CHAT_INTERFACE_VOICE:
    st.write("You may now begin your interview with " + st.session_state["interview"].get_patient().name + ". Start by introducing yourself.")
    st.write("""Click the Start Recording button to start recording your voice input to the virtual patient.
             The button will then turn into a Stop button, which you can click when you are done talking.
             Click the Restart button to restart the interview, and the End Interview button to go to the download screen.""")

    audio = audiorecorder("Start Recording", "Stop")
    
    container = st.container(height=300)

    for message in st.session_state["interview"].get_messages():
        with container:
            with st.chat_message(message.role):
                st.markdown(message.content)

    if len(audio) > 0:
        user_input = transcribe_voice(audio)
        with container:
            with st.chat_message("User"):
                st.markdown(user_input)
        st.session_state["interview"].add_message(Message("input", "User", user_input))
        st.session_state["convo_memory"].append({"role": "user", "content": user_input})
        response = generate_response(model = CONVO_MODEL, 
                                   temperature = CHAT_TEMP, 
                                   system = st.session_state["convo_memory"][0]["content"], 
                                   messages = st.session_state["convo_memory"][1:])
        st.session_state["convo_memory"].append({"role": "assistant", "content": response})
        with container:
            with st.chat_message("AI"): # Needs avatar eventually
                st.markdown(response)
        st.session_state["interview"].add_message(Message("output", "AI", response))

    columns = st.columns(4)
    columns[1].button("Restart", on_click=set_stage, args=[SETTINGS])
    columns[2].button("End Interview", on_click=set_stage, args=[DIAGNOSIS])


if st.session_state["stage"] == DIAGNOSIS:
    currentDateAndTime = date.datetime.now()
    date_time = currentDateAndTime.strftime("%d-%m-%y__%H-%M")
    bio = io.BytesIO()
    st.session_state["convo_file"] = create_convo_file(st.session_state["interview"].get_username(), 
                                                       st.session_state["interview"].get_patient().name, 
                                                       [message.get_dict() for message in st.session_state["interview"].get_messages()])
    st.session_state["convo_file"].save(bio)
    
    button_columns = st.columns(6)
    button_columns[1].button("New Interview", on_click=set_stage, args=[SETTINGS])
    button_columns[2].download_button("Download interview", 
                    data = bio.getvalue(),
                    file_name = st.session_state["interview"].get_username() + "_"+date_time + ".docx",
                    mime = "docx")

