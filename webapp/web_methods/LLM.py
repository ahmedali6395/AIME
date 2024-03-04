from langchain_community.chat_models import ChatOpenAI
from langchain.chains.conversation.base import ConversationChain
from langchain.memory.buffer import ConversationBufferMemory
from docx import Document
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId)
import os
import datetime as date
import base64
import io
import streamlit as st
from audiorecorder import audiorecorder
from openai import OpenAI
import tempfile
from annotated_text import annotated_text
import json

from lookups import *
from web_classes.data_category import DataCategory
from web_classes.message import Message


def transcribe_voice(voice_input):
    temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    voice_input.export(temp_audio_file.name, format="wav")
    with open(temp_audio_file.name, "rb") as file:
        transcription = LLM.audio.transcriptions.create(model="whisper-1", 
                                                    file=file, 
                                                    response_format="text")
    
    return transcription


def classifier(category: DataCategory, messages: list[Message]) -> None:    
    # Get the base class prompt for the category
    prompt_system = category.class_prompt

    # Append applicable messages to prompt
    applicable_messages = []
    for message in messages:
        if message.type == category.type:
            applicable_messages.append(message)
    message_list = [message.content for message in applicable_messages]
    prompt_user = json.dumps(message_list)

    print("System prompt: \n" + prompt_system + "\n\nUser prompt: \n" + prompt_user + "\n\n")

    # Classify
    response = LLM.chat.completions.create(model = CLASS_MODEL, 
                                           temperature = CLASS_TEMP, 
                                           response_format = { "type": "json_object" }, 
                                           messages = [{"role": "system", "content": prompt_system}, 
                                                       {"role": "user", "content": prompt_user}])
    output = response.choices[0].message.content

    print("LLM output: " + output + "\n\n")

    raw_classifications = json.loads(output)
    classifications = raw_classifications["output"]
    classifications = [[label for label in classification if label != "Other"] for classification in classifications] # Remove "Other" labels
    
    # Assign labels to each message accordingly
    if len(applicable_messages) != len(classifications):
        print(applicable_messages)
        print(classifications)
        raise ValueError("Number of classifications must match number of applicable messages.")
    for i in range(len(applicable_messages)):
        if classifications[i]: # If not an empty list with no labels
            applicable_messages[i].labels[category.name] = classifications[i]


def summarizer(convo_memory: list[dict[str, str]]) -> str:
    messages = [{"role": "system", "content": SUM_PROMPT}]
    dialogue = ""
    for message in convo_memory[1:]:
        if message["role"] == "system":
            dialogue += message["content"] + " \n"
        elif message["role"] == "user":
            dialogue += "User: " + message["content"] + " \n"
        elif message["role"] == "assistant":
            dialogue += "AI: " + message["content"] + "\n"
    messages.append({"role": "user", "content": dialogue})
    raw_summary = LLM.chat.completions.create(model = SUM_MODEL, 
                                              temperature = SUM_TEMP, 
                                              messages = messages)
    summary = raw_summary.choices[0].message.content
    return summary


def get_chat_output(convo_memory: list[dict[str, str]], user_input: str) -> list[list[dict[str, str]], str]:
    convo_memory.append({"role": "user", "content": user_input})
    response = LLM.chat.completions.create(model = CONVO_MODEL, 
                                           temperature = CHAT_TEMP, 
                                           messages = convo_memory)
    output = response.choices[0].message.content
    convo_memory.append({"role": "assistant", "content": output})
    if len(convo_memory) >= 10:
        summary = summarizer(convo_memory)
        convo_memory = [convo_memory[0], {"role": "system", "content": ("Summary of conversation so far: \n" + summary)}]
    return convo_memory, output


def match_diagnosis(prompt: str, user_input: str) -> str:
    raw_output = LLM.chat.completions.create(model = DIAG_MODEL, 
                                                    temperature = DIAG_TEMP, 
                                                    messages = [{"role": "system", "content": prompt}, 
                                                                {"role": "user", "content": user_input}])
    matched_condition = raw_output.choices[0].message.content
    return matched_condition