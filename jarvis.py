#!/usr/bin/env python
# -*- coding: utf-8 -*-

# jarvis.py
# [cling]

import websocket
import pickle
import json
import urllib
import requests
import sqlite3
import sklearn
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.externals import joblib

import botsettings
TOKEN = botsettings.API_TOKEN
DEBUG = False
punctuation = set([',','.','?','!', ':'])


def debug_print(*args):
    if DEBUG:
        print(*args)

try:
    conn = sqlite3.connect("jarvis.db")
except:
    debug_print("Can't connect to sqlite3 database...")


def post_message(message_text, channel_id):
    requests.post("https://slack.com/api/chat.postMessage?token={}&channel={}&text={}&as_user=true".format(TOKEN,channel_id,message_text))


class Jarvis():
    def __init__(self): # initialize Jarvis
        self.JARVIS_MODE = None
        self.ACTION_NAME = None
        
        # SKLEARN STUFF HERE:
        # Building a pipeline, 
        # code is from http://scikit-learn.org/stable/tutorial/text_analytics/working_with_text_data.html#building-a-pipeline
        self.BRAIN = Pipeline([('vect', CountVectorizer()),('tfidf', TfidfTransformer()),('clf', MultinomialNB()),])
    
    def on_message(self, ws, message):
        m = json.loads(message)
        debug_print(m, self.JARVIS_MODE, self.ACTION_NAME)
        action_list = []
        index_list = []
        
        # only react to Slack "messages" not from bots (me):
        if m['type'] == 'message' and 'bot_id' not in m:
            # Get the channel name from the json file
            channel = m['channel']

            # Clean the text first, remove punctuations
            user_message = m['text'].strip().lower()
            user_message = ''.join(ch for ch in user_message if ch not in punctuation)
            
            if self.JARVIS_MODE == None:
                jarvis_mode = ""
            else:
                jarvis_mode = self.JARVIS_MODE.split()[1]
            
            # Detect user's input
            if user_message == 'training time':
                self.JARVIS_MODE = 'start training'
                jarvis_mode = 'training'  
            elif user_message == 'testing time':
                self.JARVIS_MODE = 'start testing'
                jarvis_mode = 'testing'     
            elif user_message == 'done' and jarvis_mode == "training":
                self.JARVIS_MODE = 'finish training'       
            elif user_message == 'done' and jarvis_mode == "testing":
                self.JARVIS_MODE = 'finish testing'
                
            # Training Jarvis
            if self.JARVIS_MODE == 'start training':
                post_message("OK, I'm ready for training. What NAME should this ACTION be?", channel)            
                self.JARVIS_MODE = 'action training'
            elif self.JARVIS_MODE == 'action training':
                self.ACTION_NAME = user_message.upper()
                post_message("Okay, let's call this action `{}`. Now give me some training text!".format(self.ACTION_NAME), channel)
                self.JARVIS_MODE = 'in_process training'
            elif self.JARVIS_MODE == 'in_process training':
                conn.cursor().execute("INSERT INTO training_data (txt,action) VALUES (?, ?)", (user_message, self.ACTION_NAME,))                
                conn.commit() # save (commit) the changes      
                post_message("OK, I've got it! What else?", channel)
            elif jarvis_mode == 'training' and self.JARVIS_MODE == 'finish training':
                post_message("OK, I'm finished training", channel)
                self.JARVIS_MODE = None

            # Testing data
            if self.JARVIS_MODE == 'start testing':
                post_message("I'm training my brain with the data you've already given me...",channel)
                for row in conn.cursor().execute("SELECT * from training_data"):
                    index_list.append(row[1])
                    action_list.append(row[2])
                # Print two lists as refernences here                   
                print(index_list)
                print(action_list)
                self.BRAIN = self.BRAIN.fit(index_list, action_list)    
                joblib.dump(self.BRAIN, 'jarvis_brain.pkl')
                post_message("OK, I am ready for testing. Write me something and I'll try to figure it out.", channel)
                self.JARVIS_MODE = 'inprocess testing'
            elif self.JARVIS_MODE == 'inprocess testing':
                prediction = self.BRAIN.predict([user_message])
                new = str(prediction[0])                
                post_message("OK, I think the action you mean is `{}` ...".format(new),channel)
                post_message("Write me something else, and I'll try to figure it out.", channel)
            elif jarvis_mode == 'testing' and self.JARVIS_MODE == 'finish testing':
                post_message("OK, I'm finished testing", channel)
                self.JARVIS_MODE = None
                
            
def start_rtm():
    """Connect to Slack and initiate websocket handshake"""
    r = requests.get("https://slack.com/api/rtm.start?token={}".format(TOKEN), verify=False)
    r = r.json()
    r = r["url"]
    return r


def on_error(ws, error):
    print("SOME ERROR HAS HAPPENED", error)


def on_close(ws):
    conn.close()
    print("Web and Database connections closed")


def on_open(ws):
    print("Connection Started - Ready to have fun on Slack!")



r = start_rtm()
jarvis = Jarvis()
ws = websocket.WebSocketApp(r, on_message=jarvis.on_message, on_error=on_error, on_close=on_close)
ws.run_forever()


