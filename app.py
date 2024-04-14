from flask import Flask, render_template, request,url_for
import requests
import pyperclip
from transformers import pipeline
from gen_mcq import display
import pandas as pd
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import pathlib
import textwrap
import google.generativeai as genai
from IPython.display import display
from IPython.display import Markdown


def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))




summarizer = pipeline("summarization", model="Falconsai/text_summarization")

API_URL1 = "https://api-inference.huggingface.co/models/rabiyulfahim/grammerchecking"
headers1= {"Authorization": "Bearer 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"}


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def text_to_json(input_text):
    # Split the input text into individual question-answer pairs
    print(input_text)
    pairs = input_text.split('#')

    # Initialize a list to store the question-answer pairs
    qa_list = []

    # Process each question-answer pair
    for pair in pairs:
        print(pair)
        # Split the pair into question and answer
        question, _, answer = pair.partition('\nANS => ')
        question = question.replace('\n', '')
        print("ques = ", str(question))
        print("\nans = ", str(answer))
        # Create a dictionary for the question-answer pair
        qa_dict = {
            "question": question.strip(),
            "answer": answer.strip()
        }
        # Add the dictionary to the list
        qa_list.append(qa_dict)

    # Write the list of dictionaries to a JSON file
    with open("questions_answers.json", "w") as json_file:
        json.dump(qa_list, json_file, indent=4)


@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/Summarization', methods = ['POST','GET'])
def summarization():
    summary_output = " "
    summary_text = " "
    if(request.method == 'POST'):
        summary_text = request.form['input']
        response = summarizer(summary_text, max_length=300, min_length=30, do_sample=False)
        summary_output = response[0]['summary_text']

    return render_template('summarization.html', response=summary_output, text=summary_text)


@app.route('/Summarization/copy', methods=['POST'])
def copy_to_clipboard():
    summary_output = request.form['output']
    button_clicked = request.form['submit']
    summary_text = request.form['input']

    if button_clicked == 'Copy':
        pyperclip.copy(summary_output)
    elif button_clicked == 'Download':
        output="downloaded"
    return render_template('summarization.html', response=summary_output, text=summary_text, copied = "Copied to Clipboard")


@app.route('/GrammerCheck',methods = ['POST',"GET"])
def GrammerCheck():
    grammer_output = " "
    grammer_text = " "
    if (request.method == 'POST'):
        grammer_text = request.form['input']
        response = requests.post(API_URL1, headers=headers1, json=grammer_text)
        grammer_output = response.json()
        grammer_output = grammer_output[0]['grammer_text']
    return render_template('GrammerCheck.html', response = grammer_output, text = grammer_text)

@app.route('/mcqGen', methods=['POST','GET'])
def mcqGen():
    return render_template('MCQ_Generator.html',data="")





@app.route('/mcqResult', methods=['POST', 'GET'])
def mcqRes():
    para = request.form['text']
    num = request.form['num']
    print(para, num)
    display(para, num)
    data = pd.read_json('response.json')
    json_data1 = data.to_json(orient='records')
    json_data = json.loads(json_data1)
    print("Finally returning Response...")
    # Format the MCQs
    formatted_output = ""

    for index, question_data in enumerate(json_data):
        question = question_data["question"]
        options = question_data["options"]
        answer = question_data["answer"]

        formatted_output += f"{index + 1}. {question}\n"
        for i, option in enumerate(options):
            formatted_output += f"   {chr(97 + i)}) {option}\n"
        formatted_output += f"   Answer: {chr(97 + options.index(answer))}) {answer}\n\n"
    return render_template('MCQ_Generator.html', data=formatted_output, text=para)

@app.route('/download', methods=['POST'])
def text_to_pdf():

    questions = pd.read_json('response.json')
    questions = questions.to_dict(orient='records')

    output_filename = "MCQs.pdf"
    doc = SimpleDocTemplate(output_filename, pagesize=letter)
    styles = getSampleStyleSheet()
    content = []

    # Add questions to the content
    for index, question in enumerate(questions, start=1):
        question_text = f"{index}. {question['question']}\n"
        options_text = "\n".join([f"   {chr(97 + i)}. {option}" for i, option in enumerate(question['options'])])
        answer_text = f"Answer: {question['answer']}\n\n"
        # Add line break after each option
        options_text = options_text.replace('\n\n\n', '\n\n')
        content.append(Paragraph(question_text, styles["Normal"]))
        content.append(Paragraph(options_text, styles["Normal"]))
        content.append(Paragraph(answer_text, styles["Normal"]))
        # Add line break after each question except the last one
        if index < len(questions):
            content.append(Paragraph("<br/><br/><br/>", styles["Normal"]))

    doc.build(content)
    return render_template('MCQ_Generator.html', data="Downloaded")

@app.route('/subjQues')
def subjQues():
    return render_template('SubjQuestion.html')

@app.route('/subjGen', methods=['POST','GET'])
def subjGen():
    text = request.form['text']
    num = request.form['num']
    marks = request.form['marks']
    print(text, num, marks)
    GOOGLE_API_KEY = 'AIzaSyCNXZibEPhVweJNK4mBRDVe793u5xpLaN0'
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    propmt = "paragraph:"+str(text)+"i want create"+str(num)+"question with there answer using Blooms Taxonomy the question is for "+str(marks)+"marks and i want only Question on one line and Answer on other line else not need any single sentence or word & add '#' at the end of the answer of each question."
    response = model.generate_content(contents=propmt)
    print(response.text)
    # remove all '*' from the response
    out = response.text
    out = out.replace("*", "")
    # Answer text is bold
    out = out.replace("Answer:","ANS =>")
    return render_template('SubjQuestion.html',data=out, text=text)

@app.route('/subjDownload', methods=['POST','GET'])
def text_to_pdfsubj():
    output_filename = 'output.pdf'
    input_text = request.form['output']
    print(input_text)
    # Create a PDF document
    # Create a PDF document
    doc = SimpleDocTemplate(output_filename, pagesize=letter)

    i=1;

    # Define styles for the paragraphs
    styles = getSampleStyleSheet()

    # Initialize a list to store the paragraphs
    content = []

    # Split the input text into question-answer pairs
    pairs = input_text.split('#')

    # Add each question-answer pair to the content
    for pair in pairs:
        # Split the pair into question and answer
        print(pair)
        # Split the pair into question and answer
        question, _, answer = pair.partition('\nANS => ')
        question = question.replace('\n', '')
        question = question.replace('Question', '')

        print("ques = ", str(question))
        print("\nans = ", str(answer))
        # Create Paragraph objects for question and answer with appropriate styles
        question_para = Paragraph(f'<b>Question:</b> {question}', styles["Normal"])
        answer_para = Paragraph(f'<b>Answer:</b> {answer.strip()}', styles["Normal"])
        # Add question and answer to the content
        content.extend([question_para, answer_para, Spacer(1, 12)])  # Adding space between each pair
        i = i + 1
        if (i == len(pairs)):
            break

    # Build the PDF document
    doc.build(content)

    return render_template('SubjQuestion.html', data="Downloaded")




app.run(debug=True)
