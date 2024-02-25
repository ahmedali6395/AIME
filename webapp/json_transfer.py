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
from lookups import *
from website_methods import *
from website_classes import *
from audiorecorder import audiorecorder
from openai import OpenAI
import tempfile
from annotated_text import annotated_text
import json

role = {"Personal Details": [{"detail": "Sex", "line": "Male"}, 
                             {"detail": "Name", "line": "John Smith"}, 
                             {"detail": "Birthdate", "line": "December 5th 1959"}, 
                             {"detail": "Personality", "line": "Wise and approachable"}, 
                             {"detail": "Tone", "line": "Worried and nervous"}, 
                             {"detail": "Manner of Speech", "line": "Respectful"}], 
        "Chief Concern": "You came to the hospital because you are experiencing a heaviness in your chest. You are nervous about your symptoms because your father died suddenly of a heart attack when he was 50.", 
        "History of Present Illness": [{"lock": False, "dim": "Onset", "line": "heaviness came on gradually, seated at desk at home when symptoms appeared"}, 
                                       {"lock": False, "dim": "Quality", "line": "heaviness in chest"}, 
                                       {"lock": False, "dim": "Location", "line": "center of chest"}, 
                                       {"lock": False, "dim": "Timing", "line": "started around 2 hours ago"}, 
                                       {"lock": False, "dim": "Pattern", "line": "constant"}, 
                                       {"lock": False, "dim": "Severity", "line": "the pain was pretty severe when it first started; the pain has gradually improved and the pressure is much better but it is still there"}, 
                                       {"lock": True, "dim": "Prior History", "line": "You have never had chest pain or pressure like you are experiencing now. However, you have experienced a milder chest discomfort when walking (thought this was heart burn or you had a stomach problem). Discomfort would happen when walking up long hill near end of route, you would take an antacid and feel better. Walking program is 2 miles 3-4 times a week, started 3-4 months ago for weight loss."}, 
                                       {"lock": True, "dim": "Radiation", "line": "when the pressure sensation was at its worst, you also felt an aching pain in your jaw and both shoulders"}, 
                                       {"lock": True, "dim": "Exacerbating", "line": "you have not noticed anything that makes the heaviness worse"}, 
                                       {"lock": True, "dim": "Relieving", "line": "you took two or three tums but had no relief"}], 
        "Associated Symptoms": [{"lock": False, "line": "You were feeling slightly nauseated and sweaty prior to arriving in the Emergency Department, but you feel better now."}, 
                                {"lock": False, "line": "You occasionally get burning in your chest after eating too much, but your current symptoms feel different than this burning."}, 
                                {"lock": True, "line": "You have been stressed about your finances recently."}], 
        "Medical History": [{"lock": True, "line": "You've had high blood pressure since you were 50. You take a “water pill” for that and were recently started on another new medication."}, 
                            {"lock": True, "line": "You've had high cholesterol for many years and take a statin for this."}, 
                            {"lock": True, "line": "On your most recent visit to your doctor, she said you have “pre-diabetes” - you are not sure what this means, but she recommended you lose weight.  To lose weight, you started a walking program; this was about 6 months ago."}, 
                            {"lock": False, "line": "You have been fully boosted for COVID, but do not always get a flu vaccine."}], 
        "Surgical History": [{"lock": False, "line": "You had a hernia in your groin that was repaired when you were 26."}], 
        "Medications": [{"lock": False, "line": "If asked about medications, you will state that the medications are written on your phone. Then read the list: “Hydrochlorothiazide, Amlodipine, Atorvastatin”."}], 
        "Allergies": [{"lock": False, "line": "You do not have any allergies that you are aware of."}], 
        "Family History": [{"lock": False, "line": "Your father died suddenly of a heart attack when he was 50 years old."}, 
                           {"lock": False, "line": "Your mother passed away from breast cancer two years ago."}], 
        "Social History": [{"lock": True, "line": "You are a former smoker. You started smoking when you were in college at 19 years old and quit about 5 years ago. You smoked about one pack per day."}, 
                           {"lock": True, "line": "You drink about 2 glasses of wine or a cocktail during the week, more on the weekend."}], 
        "Other Symptoms": [{"lock": False, "line": "You have had difficulty maintaining an erection for the past 2 years and have considered speaking to your doctor about this."}, 
                           {"lock": False, "line": "You do get pain in your left leg when you walk, a cramp in the calf. It goes away when you stop walking."}]}


with open("./Patient_Info/JohnSmith_case.json", "w") as json_file:
    json.dump(role, json_file, indent=2)

patient = Patient("John Smith")
print(patient.convo_prompt)