from lookups import *
import json
from openai import OpenAI

from .patient import *
from .message import *
import web_methods

class Diagnosis:

    def __init__(self, patient: Patient, userdiagnosis: dict[str, str]):
        # Attributes
        self.weights = patient.grading["Diagnosis"]  # dict{str, dict{str, int}}
        self.classified = None                       # dict{str, dict{str, str}}
        self.checklists = None                       # dict{str, dict{str, bool}}
        self.score = None                            # int
        self.maxscore = None                         # int

        # Dict to see user input and corresponding matched conditions
        self.classified = {"Main": {}, 
                           "Secondary": {}}
        
        # Intialize the checklists
        self.checklists = {"Main": {}, 
                           "Secondary": {}}
        for condition in self.weights["Main"]:
            self.checklists["Main"][condition] = False
        for condition in self.weights["Secondary"]:
            self.checklists["Secondary"][condition] = False
        
        # Grade the checklists
        main_prompt = DIAG_PROMPT
        for condition in self.checklists["Main"]:
            main_prompt += condition + "\n"
        matched_condition = web_methods.match_diagnosis(main_prompt, userdiagnosis["main_diagnosis"])
        self.classified["Main"][userdiagnosis["main_diagnosis"]] = matched_condition
        if matched_condition in self.checklists["Main"]:
            self.checklists["Main"][matched_condition] = True
        
        secondary_prompt = DIAG_PROMPT
        for condition in self.checklists["Secondary"]:
            secondary_prompt += condition + "\n"
        for diagnosis in userdiagnosis["secondary_diagnoses"]:
            matched_condition = web_methods.match_diagnosis(secondary_prompt, diagnosis)
            self.classified["Secondary"][diagnosis] = matched_condition
            if matched_condition in self.checklists["Secondary"]:
                self.checklists["Secondary"][matched_condition] = True
        
        # Calculate scoring
        self.score = 0
        self.maxscore = 10 # Just 10 static for now
        for condition in self.checklists["Main"]:
            if self.checklists["Main"][condition]:
                self.score += self.weights["Main"][condition]
        for condition in self.checklists["Secondary"]:
            if self.checklists["Secondary"][condition]:
                self.score += self.weights["Secondary"][condition]
    
    def get_dict(self):
        to_return = {"weights": self.weights, 
                     "classified": self.classified, 
                     "checklists": self.checklists, 
                     "score": self.score, 
                     "maxscore": self.maxscore}
        return to_return