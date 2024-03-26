from lookups import *
import json
import pydantic
from typing import Optional, List
from openai import OpenAI

from .patient import Patient

class DataCategory(pydantic.BaseModel):

    name: str
    type: str
    header : str
    color : str
    highlight: str
    class_prompt : Optional[str]    

    def __init__(self, name: str, patient: Patient):
        # Attributes
        name = name                                    # str
        type = DATACATEGORIES[name]["type"]            # str
        header = DATACATEGORIES[name]["header"]        # str
        color = DATACATEGORIES[name]["color"]          # str
        highlight = DATACATEGORIES[name]["highlight"]  # str
        # example = None                                 # str
        class_prompt = None                            # str

        # Create classification prompt (patient dependent)
        class_base = CLASS_INPUT if type == "input" else CLASS_OUTPUT
        with open(class_base, "r", encoding="utf8") as class_base_file:
            base_raw = class_base_file.read()
            base_split = base_raw.split("|PATIENT DEPENDENT|")
            if len(base_split) != 2:
                raise ValueError("Base classification prompt should have 2 parts.")

        # example = LABEL_EXAMPLES[name]
        
        class_prompt = base_split[0]
        for label in patient.grading["Data Acquisition"][name]:
            class_prompt += "[" + label + "] " + LABEL_DESCS[label] + "\n"
        class_prompt += base_split[1]
        
        print(f"\n\n{class_prompt}\n\n") # debugging

        super().__init__(name=name,type=type,header=header,color=color,highlight=highlight,class_prompt=class_prompt)
    
    def get_dict(self):
        to_return = {"name": self.name, 
                     "type": self.type, 
                     "header": self.header, 
                     "color": self.color, 
                     "highlight": self.highlight}
        return to_return