from lookups import *
import json
from openai import OpenAI
from patient import *
from message import *

class DataCategory:

    def __init__(self, name: str, patient: Patient):
        # Attributes
        self.name = name                                    # str
        self.type = DATACATEGORIES[name]["type"]            # str
        self.header = DATACATEGORIES[name]["header"]        # str
        self.color = DATACATEGORIES[name]["color"]          # str
        self.highlight = DATACATEGORIES[name]["highlight"]  # str
        self.all_label_descs                                # dict{str, str}
        self.example                                        # str
        self.used_label_descs                               # dict{str, str}
        self.class_prompt                                   # str

        # Create classification prompt (patient dependent)
        class_base = CLASS_INPUT if self.type == "input" else CLASS_OUTPUT
        with open(class_base, "r", encoding="utf8") as class_base_file:
            base_raw = class_base_file.read()
            base_split = base_raw.split("|PATIENT DEPENDENT|")
            if len(base_split) != 3:
                raise ValueError("Base classification prompt should have 3 parts.")

        with open(DATACATEGORIES[name]["desc"], "r") as desc_json:
            full_desc = json.load(desc_json)
        self.all_label_descs = full_desc["labels"]
        self.example = full_desc["example"]

        self.used_label_descs = {}
        for label in patient.grading["DataAcquisition"][name]:
            self.used_label_descs[label] = self.all_label_descs[label]
        
        self.class_prompt = base_split[0]
        for label in self.used_label_descs:
            self.class_prompt += "[" + label.replace(" ", "_") + "] " + self.used_label_descs[label] + "\n"
        self.class_prompt += base_split[1] + self.example + base_split[2]
    
    def get_dict(self):
        to_return = {"name": self.name, 
                     "type": self.type, 
                     "header": self.header, 
                     "color": self.color, 
                     "highlight": self.highlight}
        return to_return
    

class DataAcquisition:

    def __init__(self, patient: Patient, messages: list[Message]):
        # Attributes
        self.datacategories  # list[DataCategory]
        self.weights     # dict{str, dict{str, int}}
        self.checklists  # dict{str, dict{str, bool}}
        self.scores      # dict{str, int}
        self.maxscores   # dict{str, int}

        # Only data categories for patient
        self.datacategories = []
        for category in patient.grading["DataAcquisition"]:
            self.datacategories.append(DataCategory(category, patient))
        self.weights = patient.grading["DataAcquisition"]
        
        # Initialize all grades for each category to label: False
        self.checklists = {}
        for category in self.datacategories:
            self.checklists[category.name] = {label: False for label in self.weights[category.name]}

        # Iterate through messages and grade checklists
        for message in messages:
            for category in self.datacategories:
                if category.name in message.labels:
                    labels = message.labels[category.name]
                    for label in labels:
                        self.checklists[category.name][label] = True

        # Calculate scoring for each category
        self.scores = {}
        self.maxscores = {}
        for category in self.datacategories:
            self.scores[category.name] = self.get_score(category)
            self.maxscores[category.name] = self.get_maxscore(category)
        
    def get_score(self, category: DataCategory) -> int:
        # Get weights from patient and grades from self
        weights = self.weights[category.name]
        label_checklist = self.checklists[category.name]
        # Calculate score from weights and grades
        score = 0
        for label in weights:
            if label_checklist[label]: 
                score += weights[label]
        return score
    
    def get_maxscore(self, category: DataCategory) -> int:
        # Get weights from patient
        weights = self.weights[category.name]
        # Calculate max score from weights
        max = 0
        for label in weights:
            max += weights[label]
        return max
    
    def get_dict(self):
        to_return = {"datacategories": [category.get_dict() for category in self.datacategories], 
                     "weights": self.weights, 
                     "checklists": self.checklists, 
                     "scores": self.scores, 
                     "maxscores": self.maxscores}
        return to_return