from langchain_community.chat_models import ChatOpenAI
from langchain.chains.conversation.base import ConversationChain
from langchain.memory.buffer import ConversationBufferMemory
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
from openai import OpenAI
import tempfile
from annotated_text import annotated_text
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from lookups import *
from web_classes import *
from web_methods import *


# from dotenv import load_dotenv

# load_dotenv()


############## DATABASE

# Establish connection to server

client = MongoClient(DB_URI,server_api=ServerApi('1'))

# Ping server on startup

try:
    client.admin.command('ping')
    print("Connection Successful")
except Exception as e:
    print(e)

# Method to get data of server

@st.cache_data(ttl=1200)
def get_data():
    db=client["AIME"]
    items=db["Conversation"].find()
    items = list(items)
    return items

# MongoDB Collection to add to

collection=client["AIME"]["Conversation"]

######### WEBSITE 

st.set_page_config(page_title = "AIME", page_icon = "🧑‍⚕️", layout = "wide")

if "stage" not in st.session_state:
    st.session_state["stage"] = LOGIN_PAGE

def set_stage(stage):
    st.session_state["stage"] = stage


if st.session_state["stage"] == LOGIN_PAGE:
    layout1 = st.columns([2, 3, 2])
    with layout1[1]:
        st.title("Virtual Patient (BETA)")
        st.write("For beta testing use only.")

        username = st.text_input("Enter any username (does not have to be your real name):")
        password = st.text_input("Enter the password you were provided:", type = "password")

        layout12b = layout1[1].columns(5)
        if layout12b[2].button("Log in"):
            if username and password == LOGIN_PASS:
                st.session_state["username"] = username
                st.write("Authentication successful!")
                time.sleep(1)
                set_stage(SETTINGS)
                st.rerun()
            if username == DATABASE_USERNAME and password == DATABASE_PASSWORD:
                st.write("Authentication successful!")
                time.sleep(1)
                set_stage(VIEW_INTERVIEWS)
                st.rerun()
            else:
                st.write("Password incorect.")


if st.session_state["stage"]==VIEW_INTERVIEWS:
    st.title("View Interviews")
    if "interview_display_index" not in st.session_state:
        st.session_state["interview_display_index"]=0
        st.session_state["all_interviews"] = get_data() 



    list_of_interviews = {}
    for i in range(len(st.session_state["all_interviews"])):
        str_to_append = st.session_state["all_interviews"][i]["username"]+": "
        if "date_time" in st.session_state["all_interviews"][i].keys():
            str_to_append+=st.session_state["all_interviews"][i]["date_time"]
        list_of_interviews[str_to_append] = i
    

    interview_selection=st.selectbox("Select an interview", 
                                     options = list_of_interviews, 
                                     placeholder = "Select Interview")
    st.session_state["interview_display_index"] = list_of_interviews[interview_selection]

    st.subheader("Interview " + str(st.session_state["interview_display_index"] + 1) + "/" + str(len(st.session_state["all_interviews"])))
    display_Interview(st.session_state["all_interviews"][st.session_state["interview_display_index"]])


    button_columns=st.columns(5)

    # if button_columns[1].button("Previous"):
    #     if st.session_state["interview_display_index"] == 0:
    #         st.write("No more interviews available.")
    #     else: 
    #         st.session_state["interview_display_index"] -= 1
    #         st.rerun()
    # if button_columns[3].button("Next"):
    #     if st.session_state["interview_display_index"] >= len(st.session_state["all_interviews"])-1:
    #         st.write("No more interviews available")
    #     else: 
    #         st.session_state["interview_display_index"] += 1
    #         st.rerun()

    button_columns[2].button("Back to Login", on_click=set_stage, args=[LOGIN_PAGE])


if st.session_state["stage"] == SETTINGS:
    st.session_state["interview"] = None
    st.session_state["convo_memory"] = None
    st.session_state["convo_file"] = None
    st.session_state["sent"] = False

    layout1 = st.columns([1, 3, 1])
    with layout1[1]:
        st.title("Patient Settings")

        chat_mode = st.selectbox("Would you like to use text or voice input for the interview?",
                                ["Text", "Voice"],
                                index = None,
                                placeholder = "Select interview mode...")
        if chat_mode == "Text": st.session_state["chat_mode"] = CHAT_INTERFACE_TEXT
        elif chat_mode == "Voice": st.session_state["chat_mode"] = CHAT_INTERFACE_VOICE
        else: st.session_state["chat_mode"] = None

        patient_name = st.selectbox("Which patient would you like to interview?", 
                                                ["John Smith", "Jackie Smith"],
                                                index = None,
                                                placeholder = "Select patient...")
        if patient_name: st.session_state["interview"] = Interview.build(username=st.session_state["username"], patient=Patient.build(patient_name))
        print(st.session_state["interview"])
        if st.session_state["chat_mode"]:
            print("chat mode active")
        if st.session_state["interview"]:
            print("interview active")

        if st.session_state["chat_mode"] and st.session_state["interview"]: 
            st.button("Start Interview", on_click=set_stage, args=[CHAT_SETUP])
            print("Reached here!")   


if st.session_state["stage"] == CHAT_SETUP:
    st.session_state["convo_memory"] = [{"role": "system", "content": st.session_state["interview"].get_patient().convo_prompt}]
                                        # {"role": "system", "content": "Summary of conversation so far: None"}
        
    set_stage(st.session_state["chat_mode"])


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
        st.session_state["interview"].add_message(Message(type="input", role="User", content=user_input))
        st.session_state["convo_memory"].append({"role": "user", "content": user_input})
        response = generate_response(model = CONVO_MODEL, 
                                   temperature = CONVO_TEMP, 
                                   system = st.session_state["convo_memory"][0]["content"], 
                                   messages = st.session_state["convo_memory"][1:])
        speech = generate_voice(st.session_state["interview"].get_patient(), response)
        st.session_state["convo_memory"].append({"role": "assistant", "content": response})
        with container:
            with st.chat_message("AI"): #TODO Needs avatar eventually
                st.markdown(response)
                play_voice(speech)
        st.session_state["interview"].add_message(Message(type="output", role="AI", content=response))

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
        st.session_state["interview"].add_message(Message(type="input", role="User", content=user_input))
        st.session_state["convo_memory"].append({"role": "user", "content": user_input})
        response = generate_response(model = CONVO_MODEL, 
                                   temperature = CONVO_TEMP, 
                                   system = st.session_state["convo_memory"][0]["content"], 
                                   messages = st.session_state["convo_memory"][1:])
        speech = generate_voice(st.session_state["interview"].get_patient(), response)
        st.session_state["convo_memory"].append({"role": "assistant", "content": response})
        with container:
            with st.chat_message("AI"): # Needs avatar eventually
                st.markdown(response)
                play_voice(speech)
        st.session_state["interview"].add_message(Message(type="output", role="AI", content=response))

    columns = st.columns(4)
    columns[1].button("Restart", on_click=set_stage, args=[SETTINGS])
    columns[2].button("End Interview", on_click=set_stage, args=[DIAGNOSIS])


if st.session_state["stage"] == DIAGNOSIS:
    st.title("Diagnosis")
    st.write("Use the interview transcription and additional patient information to provide an interpretative summary and differential diagnosis.")

    # 2 column full width layout
    layout1 = st.columns([1, 1])

    # User inputs
    summary = layout1[0].text_area(label = "Interpretive Summary:", placeholder = "Interpretive summary for patient", height = 200)
    layout11 = layout1[0].columns([1, 1, 1])
    potential1 = layout11[0].text_input(label = "Potential Diagnoses:", placeholder = "First condition name")
    potential2 = layout11[1].text_input(label = "None", placeholder = "Second condition name", label_visibility = "hidden")
    potential3 = layout11[2].text_input(label = "None", placeholder = "Third condition name", label_visibility = "hidden")
    rationale = layout1[0].text_area(label = "Rationale:", placeholder = "Rationale for diagnosis")
    final = layout1[0].text_input(label = "Final Diagnosis:", placeholder = "Condition name")

    # 3 buttons at bottom
    layout12 = layout1[0].columns([1, 1, 1])
    # New Interview
    layout12[0].button("New Interview", on_click=set_stage, args=[SETTINGS])
    # Download Interview
    currentDateAndTime = date.datetime.now()
    date_time = currentDateAndTime.strftime("%d-%m-%y__%H-%M")
    bio = io.BytesIO()
    st.session_state["convo_file"] = create_convo_file(st.session_state["interview"].get_username(), 
                                                       st.session_state["interview"].get_patient().name, 
                                                       [message.get_dict() for message in st.session_state["interview"].get_messages()])
    st.session_state["convo_file"].save(bio)
    layout12[1].download_button("Download interview", 
                                data = bio.getvalue(), 
                                file_name = st.session_state["interview"].get_username() + "_"+date_time + ".docx", 
                                mime = "docx")
    # Get Feedback
    if layout12[2].button("Get Feedback"): 
        st.session_state["interview"].add_diagnosis_inputs(summary, [potential1, potential2, potential3], rationale, final)
        set_stage(FEEDBACK_SETUP)
        st.rerun()
    
    # Interview transcription
    chat_container = layout1[1].container(height=400)
    for message in st.session_state["interview"].get_messages():
        with chat_container:
            with st.chat_message(message.role):
                st.markdown(message.content)
    # Physical Examination
    with layout1[1].expander("Physical Examination"):
        physical_exam_doc = Document(st.session_state["interview"].get_patient().physical)
        for paragraph in physical_exam_doc.paragraphs:
            st.write(paragraph.text)
    # ECG
    with layout1[1].expander("ECG"):
        st.image(st.session_state["interview"].get_patient().ECG)

    
if st.session_state["stage"] == FEEDBACK_SETUP:
    st.title("Processing feedback...")
    st.write("This might take a few minutes.")
    st.session_state["interview"].add_feedback()
    st.json(st.session_state["interview"].model_dump_json())
    st.session_state["interview_dict"] = st.session_state["interview"].get_dict()
    
    set_stage(FEEDBACK_SCREEN)
    st.rerun()


if st.session_state["stage"] == FEEDBACK_SCREEN:
    st.title("Feedback")
    layout1 = st.columns([7, 1])
    layout1[0].write("blah blah blah")
    layout1[1].button("Go to End Screen", on_click=set_stage, args=[FINAL_SCREEN])
    
    # Let the display methods cook
    display_Interview(st.session_state["interview_dict"])


if st.session_state["stage"] == FINAL_SCREEN: 
    st.write("Click the download button to download your most recent interview as a word file. Click the New Interview button to go back to the chat interface and keep testing.")
    
    currentDateAndTime = date.datetime.now()
    date_time = currentDateAndTime.strftime("%d-%m-%y__%H-%M")
    bio = io.BytesIO()
    st.session_state["convo_file"] = create_convo_file(st.session_state["interview"].get_username(), 
                                                       st.session_state["interview"].get_patient().name, 
                                                       [message.get_dict() for message in st.session_state["interview"].get_messages()])
    st.session_state["convo_file"].save(bio)
    
    button_columns = st.columns(5)
    button_columns[1].download_button("Download interview", 
                    data = bio.getvalue(),
                    file_name = st.session_state["interview"].get_username() + "_"+date_time + ".docx",
                    mime = "docx")
    
    # Store interview in database and send email as backup
    if st.session_state["sent"] == False:
        collection.insert_one(st.session_state["interview"].get_dict())
        send_email(bio, EMAIL_TO_SEND, st.session_state["interview"].get_username(), date_time, None)
        st.session_state["sent"] = True
        
    # st.download_button("Download JSON",
    #             data=st.session_state["interview"].get_json(),
    #             file_name = st.session_state ["interview"].get_username() + "_"+date_time + ".json",
    #             mime="json")

    button_columns[2].button("New Interview", on_click=set_stage, args=[SETTINGS])
    button_columns[3].button("Back to Login", on_click=set_stage, args=[LOGIN_PAGE])