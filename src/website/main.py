from flask import *
from json import load, dump



# send this schema to ai to fill out
dataSchema = {
    "Weight":  "", # Options: “obese”, “overweight”, “healthy”, “underweight”, “emaciated”, “can’t see lizard”
    "Shed": "", # Options: “soon”, “now”, “not shedding”, “can’t see lizard” 
    "Food in bowl": "", # Options: "true", "false", "no bowl visible"
    "Current activity": "", # Options: “basking”, “exploring”, “hiding”
    "Temperature cool side": None, # Degrees F
    "Temperature warm side": None, # degrees F
    "Humidity cool side": None, # percent
    "Humidity warm side": None, # percent
    "Hazardous conditions": 
        {
            "Improper substrate" : False,
            "Unsafe lighting" : False,
            "Temperature too high" : False,
            "Temperature too low" : False,
            "Humidity too high" : False,
            "Signs of disease" : "none", # describe illness if present
            "Other" : "none" # describe hazard if present
        }

}


def SendPrompt(lizardName, pathToSpeciesResearch, pathToPDF): 
    JSONdata = None
    return JSONdata
    # this function will send the prompt data from the prompt.json, the most recent images parsed into a pdf, and the research gathered from the ideal conditions of a leopard gecko.
    # it will parse the text into json data

def ParsePDF(pathToImageFolder):
    # parses the photos into a pdf, wipes the original images after its done.
    pass





