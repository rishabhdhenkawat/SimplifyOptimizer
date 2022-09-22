import pandas as pd
import numpy as np

from collections import Counter


import fitz
import spacy
from spacy.matcher import Matcher
nlp = spacy.load('en_core_web_sm')

df = pd.read_csv("New simplyfi dataset.csv")
df.columns = df.iloc[0]
df = df.iloc[1:]


df = df.dropna()
df = df.applymap(str.lower)

labels_principals = dict(zip(df["LABELS"],df["PRINCIPLES"]))
keywords_labels = {}
all_keywords = []
for i in range(1,df.shape[0]):
  for j in list(df["KEYWORDS"][i]):
    keywords_labels[j.strip()] = df["LABELS"][i]
    all_keywords.append(j.strip())
    
    
labels_keywords_count = {}

for i in range(1,df.shape[0]):
    labels_keywords_count[df["LABELS"][i]] = len(list(df["KEYWORDS"][i]))

def wordslist_to_Matcher(words_list):
    """It will take list of words and Make a Matcher of it"""
    global nlp
    global matcher

    matcher = Matcher(nlp.vocab)
    words_included = []
    

    for word in words_list:
        if word not in words_included:
            pattern = [{'LOWER': str(word)}]
            # print(str(word), len(str(word)))
            matcher.add(str(word),[pattern])
            words_included.append(word)

    return matcher, words_included

def Match(matcher, doc):
    """It will give all matches in the file w.r.t to the keywords in Matcher\nArguments: Matcher, spacy.tokens.Docs\nReturns: Matched Words, Freq of matches"""
    global nlp
    key_freq = {}
    matches = matcher(doc)

    x = [match[0] for match in matches]
    y = set(x)

    for id_ in y:
        value = x.count(id_)
        # print(value, id_)
        string_id = nlp.vocab.strings[id_]
        key_freq[string_id] = value

    keys_list = list(key_freq.keys())
    return keys_list, key_freq
    
    
 def get_keywords_match_2(pdf_name, words_list):
      ### READ IN PDF
      dict={}
      doc = fitz.open(pdf_name)
      k=pdf_name

      print("fitz working")
      s=''
      for i in range(0,doc.pageCount):
          page = doc[i]
          s=s+page.get_text().replace('\n','')
      text=s
      from spacy.matcher import Matcher
      global nlp
      skills_matcher, all_skill = wordslist_to_Matcher(words_list)
#             print('Keywords for matching:', len(all_skill))
      doc = nlp(text)
      skills, freq = Match(skills_matcher, doc)
      return freq
  
  def get_score(result):
  found_lables = []
  for i in result.keys():
    found_lables.append(keywords_labels[i])

  lables_counts = Counter(found_lables)
  lables_counts = dict(lables_counts)

  percent_matched = {}

  for i in lables_counts.keys():
    percent_matched[i] = lables_counts[i]/labels_keywords_count[i] 

  final_principals = []
  for label in percent_matched.keys():
    if percent_matched[label] > 0.05:
      final_principals.append(labels_principals[label])

  principal_counts = Counter(final_principals)
  principal_counts = dict(principal_counts)

  final_score = 0
  for key in principal_counts:
    per_score = 0
    if 5 > principal_counts[key] and 1< principal_counts[key]:
      final_score = final_score + 0.5
      per_score = per_score + 0.5
    if 11 > principal_counts[key] and 5< principal_counts[key]:
      final_score = final_score + 1
      per_score = per_score + 1
    # print(key,per_score)

  final_principals  = list(principal_counts.keys())
  return final_score,final_principals



suggestionsDF = pd.read_excel("Suggestions.xlsx")
suggestions_list = list(zip(suggestionsDF["Suggestions"],suggestionsDF["Suggestions.1"]))

suggestions_dict = {}
for i in range(len(list(suggestionsDF['Labels']))):
  suggestions_dict[suggestionsDF['Labels'][i]] = suggestions_list[i]
  
def get_suggestions():

  result = []
  final_score,final_principals = get_score(result1)
  final_principals = list(set(final_principals))
  suggestions = {}
  for i in list(suggestions_dict.keys()): 
    k = i.lower()
    if k in final_principals:
      suggestions[i] = suggestions_dict[i]

  
  result.append({"suggestions":suggestions})

  result.append({"score":final_score})

  return result
  
# get_suggestions()
# import PyPDF2
from flask import Flask
from flask import Flask, render_template, Response,request, jsonify
from flask import Flask, flash, request, redirect, render_template
from flask import Flask, flash, request, redirect, url_for, render_template
import os
#from flask_ngrok import run_with_ngrok

import requests
import json
from bson.json_util import dumps

from flask_restful import Resource, Api, reqparse
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage

app = Flask(__name__)
run_with_ngrok(app)

UPLOAD_FOLDER = './'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
 
ALLOWED_EXTENSIONS = set(['pdf'])
 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
 
@app.route('/')
def main():
    return 'Homepage'
 
@app.route('/upload', methods=['POST'])
def upload_file():
    # check if the post request has the file part
    print(request.files)
    if 'files[]' not in request.files:
        resp = jsonify({'message' : 'No file part in the request'})
        resp.status_code = 400
        return resp
 
    files = request.files.getlist('files[]')
     
    errors = {}
    success = False
    final_filename = ""
    for file in files:      
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            final_filename = filename
            success = True
        else:
            errors[file.filename] = 'File type is not allowed'

    pdf_name = final_filename
    if success and errors:
        errors['message'] = 'File(s) successfully uploaded'
        resp = jsonify(errors)
        resp.status_code = 500
        return resp
    if success:
        result = get_keywords_match_2(pdf_name, words_list)
        output = get_suggestions()
        
        response = app.response_class(response=dumps(output),mimetype='application/json')
        response.status_code = 201
        
        return response
        # resp = jsonify({'message' : 'Files successfully uploaded'})
        # resp.status_code = 201
        # return resp
    else:
        resp = jsonify(errors)
        resp.status_code = 500
        return resp

if __name__ == "__main__":

    app.run(host="0.0.0.0",port="6000",debug=True)

