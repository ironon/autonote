
import prompt
import asyncio
import os
import json
import math
import time

# def main():

#     useCache = input("Would you like to actually prompt GPT or use the latest cache?(1/2): ")
#     information = prompt.parse_files()
#     print("Parsed all slideshows...")
#     print("Amount of slideshows: " + str(len(information)))
#     for slideshow in information:
#         generate_questions_from_text(slideshow, "isfgifanyonenamestheirthingthistheywilldie", settings)

def generate_questions_from_pdf(pdf_path, cache_name, settings=None):
    if settings == None:
        return 400 ## bad request no settings
    text = prompt.get_text_from(pdf_path)
    result = {}
    print("Getting reformatted notes...this could take a bit.")
    if settings['inputType'] != "markdown":
        text = prompt.stich_slideshow(text, settings)
    result['markdown'] = text
    print(text)
    questions = generate_questions_from_text(text, cache_name, settings)
    result["questions"] = questions
    return result

def generate_questions_from_text(text, cache_name, settings):
    print("NEW REQUEST ===== " + str(int(time.time())))
    print("Cache name: " + cache_name)
    general_idea = None
    questions_json = None
    if not os.path.exists("./server/notes/"+cache_name+".json"):
        print("Getting questions from a slideshow from GPT...")
        # general_idea = prompt.get_general_idea(text, settings)
        # print("The general idea: " + general_idea)
        questions = prompt.prompt_GPT_for_questions(text, cache_name, settings)
        # print(questions)
        print("Got questions!")
        questions_json = prompt.formatResponse(questions)
        print("Formatted questions!")
        print("Checking for dumbness...")
        # questions_json = questions_json + prompt.get_connecting_questions(questions_json, general_idea)
        questions_json = prompt.removeDumbness(questions_json, general_idea, settings)
        with open("./server/notes/"+cache_name+".json", mode="w", encoding="utf-8") as f:
            json.dump(questions_json, f, indent=4)
    else:
        print("Using latest prompt from notes...")
        with open(file="./server/notes/"+cache_name+".json", mode="r") as f:
            questions_json = json.load(f)
    return questions_json

# if __name__ == '__main__':
    # main()