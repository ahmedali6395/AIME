import os
from openai import OpenAI
from anthropic import Anthropic


# SECRETS
LOGIN_PASS = os.getenv("LOGIN_PASS")
DB_URI=os.getenv("DB_URI")
DATABASE_USERNAME=os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD=os.getenv("DATABASE_PASSWORD")


# Email API
EMAIL_TO_SEND = [('rutgers.aime@gmail.com')]


# Streamlit stages
LOGIN_PAGE = 0
SETTINGS = 1
CHAT_SETUP = 2
CHAT_INTERFACE_TEXT = 3
CHAT_INTERFACE_VOICE = 4
POST_INTERVIEW = 5
PHYSICAL_SCREEN = 6
ECG_SCREEN = 7
DIAGNOSIS = 8
FEEDBACK_SETUP = 9
FEEDBACK_SCREEN = 10
FINAL_SCREEN = 11
VIEW_INTERVIEWS=12


# Audio related
AUDIO_IN = OpenAI()
# AUDIO_OUT = ElevenLabs()


# LLM related
HOST = "anthropic"
if HOST == "openai":
    CLIENT = OpenAI()
    CONVO_MODEL = "gpt-4"
    CHAT_TEMP = 0.7
    CLASS_MODEL = "gpt-4-0125-preview"
    CLASS_TEMP = 0.0
    SUM_MODEL = "gpt-4-0125-preview"
    SUM_TEMP = 0.0
    DIAG_MODEL = "gpt-4-0125-preview"
    DIAG_TEMP = 0.0
elif HOST == "anthropic":
    CLIENT = Anthropic()
    CONVO_MODEL = "claude-3-sonnet-20240229"
    CHAT_TEMP = 0.5
    CLASS_MODEL = "claude-3-opus-20240229"
    CLASS_TEMP = 0.0
    SUM_MODEL = "claude-3-sonnet-20240229"
    SUM_TEMP = 0.0
    DIAG_MODEL = "claude-3-sonnet-20240229"
    DIAG_TEMP = 0.0

BATCH_MAX = 99 # no limit rn
BATCH_DELAY = 30

with open("./Prompts/Summarizer_2-25.txt", "r", encoding="utf8") as summarizer_file:
    SUM_PROMPT = summarizer_file.read()
MAX_MESSAGES = 99 # no limit rn

with open("./Prompts/Diagnosis_Grader_2-25.txt", "r", encoding="utf8") as grader_file:
    DIAG_PROMPT = grader_file.read()

BASE_PATH = "./Prompts/Base_3-14_anth.txt"
with open(BASE_PATH, "r", encoding="utf8") as base_file:
    BASE_PROMPT = base_file.read()

PATIENTS = {
    "John Smith": {"case": "./Patient_Info/JohnSmith_case.json", 
                   "grading": "./Patient_Info/JohnSmith_grading.json", 
                   "physical": "./Patient_Info/JohnSmith_physical.docx", 
                   "ECG": "./Patient_Info/JohnSmith_ECG.png"}, 
    "Jackie Smith": {"case": "./Patient_Info/JackieSmith_case.json", 
                     "grading": "./Patient_Info/JackieSmith_grading.json", 
                     "physical": "./Patient_Info/JackieSmith_physical.docx", 
                     "ECG": "./Patient_Info/JackieSmith_ECG.png"}
}


# Classification base prompts
CLASS_INPUT = "./Prompts/Class_Input_3-3.txt"
CLASS_OUTPUT = "./Prompts/Class_Output_3-3.txt"

DATACATEGORIES = {
    "gen": {"type": "input", 
            "header": "General Questions", 
            "color": "blue", 
            "highlight": "#bae1ff", # light blue
            "desc": "./Prompts/desc_gen.json"}, 
    "dims": {"type": "output", 
             "header": "Dimensions of Chief Concern", 
             "color": "red", 
             "highlight": "#ffb3ba", # light red
             "desc": "./Prompts/desc_dims.json"}, 
    "asoc": {"type": "input", 
             "header": "Associated Symptoms Questions", 
             "color": "orange", 
             "highlight": "#ffdfba", # light orange
             "desc": "./Prompts/desc_asoc.json"}, 
    "risk": {"type": "input", 
             "header": "Risk Factor Questions", 
             "color": "violet", 
             "highlight": "#f1cbff", # light violet
             "desc": "./Prompts/desc_risk.json"}
}

WEBSITE_TEXT = {
        "intro" : "./webapp/website_text/intro.txt",
        "selection" : "./webapp/website_text/selection.txt",
        "interview" : "./webapp/website_text/interview.txt",
        "post" : "./webapp/website_text/post.txt",
        "feedback" : "./webapp/website_text/feedback.txt",
        "final": "./webapp/website_text/final.txt"
}