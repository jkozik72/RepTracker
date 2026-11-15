from json import load, dump
from pathlib import Path

import ai


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


# allowed values for the fields above
dataOptions = {
    "Weight": ["obese", "overweight", "healthy", "underweight", "emaciated", "can't see lizard"],
    "Shed": ["soon", "now", "not shedding", "can't see lizard"],
    "Food in bowl": ["true", "false", "no bowl visible"],
    "Current activity": ["basking", "exploring", "hiding"],
}

WEBSITE_DIR = Path(__file__).parent


def SendPrompt(lizardName, pathToSpeciesResearch, pathToPDF):
    # sends the prompt from Prompt.txt, the most recent images, and the research on the
    # species' ideal conditions to Gemini in one call. Returns dataSchema filled out.
    # pathToPDF may be a PDF, a single image, or a folder of images (newest ones are used).
    # lizardName is not sent to the model; it is here so callers can log who the report is for.
    media = ai.CollectMedia(pathToPDF)
    if not media:
        raise FileNotFoundError(f"No images or PDF found at {pathToPDF} for {lizardName}")

    researchPath = Path(pathToSpeciesResearch)
    research = researchPath.read_text(encoding="utf-8") if researchPath.is_file() else ""
    promptTemplate = (WEBSITE_DIR / "Prompt.txt").read_text(encoding="utf-8")

    JSONdata = ai.AnalyzeEnclosure(
        media, researchPath.stem, research, dataSchema, dataOptions, promptTemplate
    )
    return JSONdata


def ParsePDF(pathToImageFolder):
    # parses the photos into a pdf, wipes the original images after its done.
    pass


def TakeAPicture(camera, pathToLizardFolder):
    # runs every 5 minutes
    pass


def CreateNewLizard(formData):
    # recieves form data from the website, creates the new file structure
    pass



