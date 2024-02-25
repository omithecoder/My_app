from flask import Flask, render_template, request,url_for

import requests

import pyperclip

API_URL = "https://api-inference.huggingface.co/models/Falconsai/text_summarization"
headers = {"Authorization": "Bearer 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"}
summary_output = " "
summary_text = " "
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/Summarization', methods = ['POST','GET'])

def summarization():


    if(request.method == 'POST'):
        summary_text = request.form['input']
        response = requests.post(API_URL, headers=headers, json=summary_text)
        summary_output = response.json()

    else:
        response = "[{'summary_text': Error in Summarization'}]"

    summary_output = summary_output[0]['summary_text']

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





app.run(debug=True)
