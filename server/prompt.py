import os
import json
import openai
import math
import re
import time
import logging
import wikipedia
from PyPDF2 import PdfReader
from helpers import printProgressBar


# p_logging = logging.getLogger("PyPDF2")
# p_logging.setLevel("INFO")
notes_logger = logging.getLogger(__name__)


global api_key


split_interval = 16000
questions_regex = r"(?P<question>Q: .*?)\n(?P<answer>A: .+?(?=\nQ:|$))"
general_idea_prompt = '''

You are now an educational tutor. Tell me which subject this text has most to do with: "history", "math", "science", "english", "arts", or "life"

"{text}"

'''




dumbness_prompt = '''

Below is a question and an answer that has something to do with "{general_idea}". Your job is to mark it as "vague" or "good". You should only say one of those 2 quotes, nothing else. Mark it as "vague" if the
question is impossible to answer, even for an expert, without more context. Mark it as "good" if the answer is clearly related to the question, and the question is answerable without further context.

Question: {question}
Answer: {answer}

'''

connecting_questions_prompt = '''

{wikipedia_summary}

Based on that description, make 1 question and answer using the above text that elaborates on the question below. Remove any citations, refrences, or anything in parentheses. Follow the following format when making the questions:

Q: <insert question here>
A: <insert answer here>

Here is the question:

{question}

'''
with open("./server/api_key.json", "r") as f:
    obj = json.load(f)
    api_key = obj['key']
    openai.api_key = api_key
def parse_files():
    '''
    Functions goes through all the stuff in the /downloads folder and returns an array of strings, each entry 
    representing an entire slideshow
    '''
    files = os.scandir("./server/downloads")
    information = []
    for file in files:
        text = get_text_from(file.path)
        information.append(text)
    return information

def getModel(settings):
    # print(settings)
    if settings['gpt4'] == 'true':
        return 'gpt-4-32k-0613'
    return 'gpt-3.5-turbo-16k'

def getTokenAmount(settings):
    if settings['gpt4'] == 'true':
        return 32600
    return 16385
        
def stich_slideshow(text, settings):
    """
    Takes in the text read from a slideshow and uses GPT to turn it into a Markdown document. 
    Args:
        text (string): Text to stitch together.
    """
    stitch_prompt = """
    You are helping a student organize their notes. This is very important to them, so be careful. The following is text that was ripped from a PDF document. The text is unorganized, jumbled, and doesn't make a lot of sense structurally.
    Your job is to format the notes using Markdown in a way that makes structural sense. Your job is to organize the information, not the course's buraucracy, so leave out any class objectives or note numbers. Think of the notes like a JSON tree, where information can be nested under whatever makes the most sense. Make sure it is organized and consistent.
    Your response needs to be in Markdown, do not say anything else.
    NOTES:
    {notes}
    
    """
    prompt = stitch_prompt.format(notes = text)
    response = openai.ChatCompletion.create(
        model=getModel(settings),
        messages=[
            {"role": "system", "content": prompt},
        ]
    )
    markdown_notes = response['choices'][0]['message']['content']
    return markdown_notes
    
    
def get_text_from(path):
    reader = PdfReader(path)

    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def get_general_idea(slideshow, settings):
    xerpt = ""
    if len(slideshow) > split_interval:
        xerpt = slideshow[0:split_interval]
    else:
        xerpt = slideshow
    xerpt = xerpt.replace("⦿", "")
   
    prompt = general_idea_prompt.format(text=xerpt)
    # response = openai.ChatCompletion.create(
    #     model="text-davinci-003",
    #     prompt=prompt,
    #     temperature=0,
    #     max_tokens=1000,
    #     top_p=1.0,
    #     frequency_penalty=0.0,
    #     presence_penalty=0.0,
    #     stop=["###"]
    # )
    response = openai.ChatCompletion.create(
        model=getModel(settings),
        messages=[
            {"role": "system", "content": prompt},
        ]
    )
    general_idea = response['choices'][0]['message']['content']
    return general_idea

def prompt_GPT_for_questions(slideshow, cache_name:str, settings):
    questions = []
    iteration_amount = math.floor(len(slideshow) / split_interval)
    print("Iteration Amount: " + str(iteration_amount))
    if iteration_amount == 0:
        questions.append(getCompletion(slideshow, 0, -1, settings))
    else:
        for i in range(1, iteration_amount):
            print(i)
            printProgressBar(i, iteration_amount, "Scanning through slideshow: ", "", 1, 50)
            questions.append(getCompletion(slideshow, (i-1)*split_interval,i*split_interval, settings))
        questions.append(getCompletion(slideshow, i*split_interval, len(slideshow), settings))
    with open("./server/cache/"+cache_name+".json", "w+") as f:
        json.dump(questions, f)
    return questions

def getCompletion(text, start, end, settings):
    xerpt = text[start:end]
    questions_prompt = '''
    You are helping a student make flashcards. This is very important to them, so be thorough and careful. I will give you some of the student's notes, which are about a school subject. Make as many questions as possible, although make sure you're questions make sense and aren't vague. ONLY use information from the excerpt, and every question should be answerable with no other context, so avoid vague language in the questions, be as specific as possible. Don't make questions on any trivia/useless facts.
    Your response should be in JSON format, i.e, so it can be parsed by something like "json.loads". Example response:
    
    [
        {
            "question": "question goes here"
            "answer": "answer goes here"
        }
        {
            "question": "question goes here"
            "answer": "answer goes here"
        }
    ]
    

    Here is the notes:
    <EXCERPT>
    '''

    aprompt = questions_prompt.replace("<EXCERPT>", xerpt)
    response = openai.ChatCompletion.create(
            model=getModel(settings),
            messages=[
                {"role": "system", "content": aprompt},
            ]
        )
    return response['choices'][0]['message']['content']

def removeEmptyQuotes(arr):
    newArr = []
    for i, v in enumerate(arr):
        if v != "":
           newArr.append(v)
    return newArr

def removeDumbness(questions, general_idea, settings):
    undumbed_questions = []
    for q in questions:
            time.sleep(0.5)
        
            response = openai.ChatCompletion.create(
                model=getModel(settings),
                messages=[
                    {"role": "system", "content": dumbness_prompt.format(general_idea=general_idea, question=q['question'], answer=q['answer'])},
                ]
            )
            notes_logger.info("Checking for dumbness -> Question:")
            notes_logger.info("\t"+q['question'])
            notes_logger.info("\t"+q['answer'])
            unformatted_response = response['choices'][0]['message']['content'].replace(".", "").lower()
            if unformatted_response != "vague":
                undumbed_questions.append(q)
                continue
            notes_logger.info("QUESTION IS VAGUE - REMOVING")
    return undumbed_questions

def get_connecting_questions(questions, general_idea):
    connecting_questions = []
    
    for q in questions:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt="What would you search in Wikipedia to research this question? \n" + q[0],
            temperature=0,
            max_tokens=1000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=["###"]
        )
        wiki_search_term = response['choices'][0]['text'].replace("\n", "")
        notes_logger.info("Wikipedia Search Term: " + wiki_search_term)
        try:
            wikisum = wikipedia.summary(wiki_search_term)
            notes_logger.info("Wikipedia Summary: " + wikisum)
            time.sleep(0.7)
            prompt = connecting_questions_prompt.format(wikipedia_summary=wikisum, question=q[0]+"\n"+q[1])
            notes_logger.info("Prompt for connecting questions: " + prompt)
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0,
                max_tokens=1000,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stop=["###"]
            )
            unformatted_question = response['choices'][0]['text']
            notes_logger.info("Unformatted question: " + unformatted_question)
            formatted_question = formatResponseText(unformatted_question)
            notes_logger.info("Adding connecting questions -> Question:")
            notes_logger.info("\t"+q[0])
            notes_logger.info("\t"+q[1])
            if len(formatted_question) != 0:
                notes_logger.info("Connecting question generated:")
                notes_logger.info(formatted_question)
            else:
                notes_logger.info("No connecting questions generated!")
            connecting_questions = connecting_questions + formatted_question
        except wikipedia.PageError as e:
            logging.warning("No wikipedia page for " + wiki_search_term)
      
    return connecting_questions

def removeMarkers(question):
    question[0] = question[0].replace("Q: ", "") 
    question[1] = question[1].replace("A: ", "") 
    return question

def formatResponse(questions):
    # formattedQuestions = []
    # for q in questions:
    #     matches = re.findall(questions_regex, q)
    #     print(matches)
    #     # for i, _ in enumerate(matches):
    #     #     matches[i] = removeMarkers(matches[i])
    #     formattedQuestions = formattedQuestions + matches
    formattedQuestions = []
    for q in questions:
        try:
            formattedQuestions.append(json.loads(q))
        except:
            print("ERROR IN PARSING ---- ITS TIME TO PANIC!! AHHHHH 😭😭")
            return []
    
    merged_questions = []
    for q in formattedQuestions:
        merged_questions = merged_questions + q

    return merged_questions

def formatResponseText(text_questions:str):
    
    matches = re.findall(questions_regex, text_questions)
    if len(matches) == 0:
        notes_logger.warning("No matches found!")
    return [] + matches