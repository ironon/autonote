
import os.path
import os
import json
import random
import logging
import shutil
from functools import wraps
import io
import gpt
import genanki
from helpers import get_time
from flask import Flask, request, Response, send_file, send_from_directory
from flask_sock import Sock

notes_logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
notes_logger.debug("Prompt library loaded!")

with open("./server/admin_api_key.json", "r") as f:
    global api_key
    api_key = json.load(f)['key']
app = Flask(__name__)
sock = Sock(app)

def delete_downloads_folder():
    for file in os.scandir("./server/downloads"):
        os.remove(file.path)

def fire_all_functions(arr, **kwargs):
    for func in arr:
        func(**kwargs)

def admin_only(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "Authorization" in request.headers:
            if request.headers['Authorization'] == api_key:
                return f(*args, **kwargs)
            else: 
                notes_logger.warning("Got key: " + request.headers['Authorization'])
        else:
            notes_logger.warning("Wrong admin authorization header!")
            notes_logger.warning("No key provided!")
            return Response(response="Unauthorized, get outta here loser.", status=401)
    return wrap

@app.route('/')
def index():
    return send_from_directory('../frontend/dist/', 'index.html')

@app.route("/assets/<path:path>")
def assets(path):
    return send_from_directory('../frontend/dist/assets', path)


def getMarkdownPDF(name, text:str):
    id = random.randint(1, 100000)
    with open(f"./server/notes/{name}_{id}.md", "w", encoding='utf-8') as f:
        f.write(text)
    os.system(f"mdpdf -o ./server/notes/{name}_{id}.pdf ./server/notes/{name}_{id}.md")
    return (f"/notes/{name}_{id}.md", f"/notes/{name}_{id}.pdf")

def getCSVFile(name, questions:str):
    id = random.randint(1, 100000)
    with open(f"./server/notes/{name}_{id}.csv", "w", encoding="utf-8") as f:
        for question in questions:
            f.write(f'"{question["question"]}","{question["answer"]}"\n')
    return f"/notes/{name}_{id}.csv"
def create_anki_deck(name, questions):
    deck = genanki.Deck(
        random.randint(0, 9999999999),
        name
    )
    id = random.randint(0, 10000000)
    best_model = genanki.Model(
        2098481978,
        'DavidsAmazingNote',
        fields=[
            {'name': 'Question'},
            {'name': 'Answer'},
        ],
        templates=[
            {
            'name': 'Card 1',
            'qfmt': '{{Question}}',
            'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
            },
    ])
    print(questions)
    for question in questions:
        note = genanki.Note(
            model=best_model,
            fields=[question['question'], question['answer']]
        )
        deck.add_note(note)
    genanki.Package(deck).write_to_file(f'./server/notes/{name}_{id}.apkg')
    return f"/notes/{name}_{id}.apkg"
    
@app.route("/sendnotes", methods=["POST"])
@admin_only
def send_notes():
    delete_downloads_folder()
    if len(request.files) == 0:
        return "Please actually send files you bozo", 400
    questions = None
    settings = {
        "gpt4": request.args.get('gptfour'),
        "inputType": request.args.get('inputType'),
        "wantsStudyGuide": request.args.get("wantsStudyGuide"),
        "wantsAnkiCSV": request.args.get("wantsAnkiCSV"),
        "wantsMarkdownNotes": request.args.get("wantsMarkdownNotes"),
        # "wantsAIStitching": request.args.get("wantsAIStitching")
    }
    name = ""
    for file in request.files:
        a_file = request.files[file]
        name = a_file.name
        filename = "./server/downloads/"+a_file.name+".pdf"
        with open(filename, "wb") as fb:
            shutil.copyfileobj(a_file, fb)
            result = gpt.generate_questions_from_pdf(filename, a_file.name, settings=settings)
    (markdown, markdown_pdf) = getMarkdownPDF("notes", result['markdown'])
    result['csv'] = getCSVFile("csv_questions", result['questions'])
    deck_file = create_anki_deck(name, result['questions'])
    result['anki'] = deck_file
    result['markdown_pdf'] = markdown_pdf
    result['markdown'] = markdown
    return result

@app.route("/getnotes")
def get_notes():
    notes = os.listdir("./server/notes")
    return notes, 200

@app.route("/notes/<path:path>")
def notes(path):
    print(path)
    return send_from_directory("./notes/", path)

def main():
    app.run(port=2001)
if __name__ == '__main__':
    main()