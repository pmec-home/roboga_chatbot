# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import requests
import json
import pandas as pd
import spacy
import os
import re
from datetime import datetime

logger = logging.getLogger(__name__)
directory = os.path.dirname(os.path.realpath(__file__))

import sys
current_module = sys.modules[__name__]

###########################################################
# List of Intens
# AWALYS CHANGE THIS LIST WHEN ,ADD A NEW INTENT, OR CHANGE AN INTENT NAME
##########################################################
from enum import Enum
class Intents(Enum):
	MOVE = 'move'
	GREET = 'greet'
	QUESTION = 'question'
	FOLLOW = 'follow'
	AFFIRM = "affirm"
	DENY = "deny"
	START = "start"
	STOP = "stop"
	PICK = "pick"
	BYE = "bye"
	NONE = None
	

###########################################################
# Initilize some global variables
# the list of questions and answer and its nlp abstraction
##########################################################
#Questions and Answer dataset
QandA = pd.read_csv(directory+'/rasa/questions_and_answers.csv')
nlp = spacy.load('en_core_web_sm')
def load_nlp(word_list):
    global nlp
    nlp_list = []
    for word in word_list:
        nlp_list.append(nlp(str(word), 'utf8'))
    return nlp_list

def compareToNlpList(phrase, nlp_list):
    global nlp
    nlp_phrase = nlp(phrase)
    ranks = []
    for element in nlp_list:
        ranks.append({})
        ranks[-1]['text'] = element.text
        ranks[-1]['similarity'] = nlp_phrase.similarity(element)
    return sorted(ranks, key=lambda x: x['similarity'], reverse=True)
nlp_list = load_nlp(QandA['QUESTION'])
#The database


class Planner():
	def __init__(self):
		# define the name of the action which can then be included in training stories
		x = "sup"

	def read(self, tracker):
		global nlp_list, QandA
		print(tracker)
		message = tracker['text']
		intent = Intents(tracker["intent"].get("name"))
		entities = Entities(tracker.get("entities"))
		print(message, intent)
		print(entities)
		if(intent == Intents.QUESTION):
			rank = compareToNlpList(message, nlp_list)
			if(float(rank[0]['similarity']) > 0.65):
				#Grab answer form the Q and A dataframe
				answer = QandA[QandA['QUESTION'] == rank[0]['text']]['ANSWER'].iloc[0]
				#If the answer is in the format ${code} grab the code inside and run ir
				if '$' in answer:
					code = re.search('\${(.*)}', answer).group(1)
					answer = eval(code)
				return answer
		if(intent == Intents.GREET):
			return "Hello there, how can I help you?"
		if(intent == Intents.MOVE):
			if(entities.size() > 0):
				if(entities.hasAllOfTypes(["location", "person"])):
					return "Ok, I will move to the " + entities.getFromTypes(["location", "direction"])[0]
	
			return "Where do you want me move?"
		if(intent == Intents.FOLLOW):
			msg = "I will start folowing"
			target = "you"
			location = ""
			if(entities.size() > 0):
				if(entities.hasType("pronoun")):
					pronoun = entities.getFromType("pronoun")[0]
					if(pronoun == "him" or pronoun == "her"):
						target = pronoun
				if(entities.hasType("gender")):
					gender = entities.getFromType("gender")[0]
					if(gender == "male"):
						target = "him"
					else:
						target = "her"
				if(entities.hasType("name")):
					target = entities.getFromType(["name"])[0]
				if(entities.hasType("location")):
					location = "to the " + entities.getFromType("location")[0]
			
			msg += " "+target
			msg += " "+location

			return msg
		return "Sorry I did not understand your question"

class Entities():
	def __init__(self, entities):
		self.entities = [{"entity": x.get("entity"), "value": x.get("value")} for x in entities]

	def hasType(self, type):
		for entity in self.entities:
			if(entity["entity"] == type):
				return True
		return False

	def hasAnyOfTypes(self, types):
		for type in types:
			if(self.hasType(type)):
				return True
		return False

	def hasAllOfTypes(self, types):
		for type in types:
			if(not self.hasType(type)):
				return False
		return True

	def countOfType(self, type):
		count = 0
		for entity in self.entities:
			if(entity["entity"] == type):
				count += 1
		return count

	def getFromType(self, type):
		typeList = []
		for entity in self.entities:
			if(entity["entity"] == type):
				typeList.append(entity["value"])
		return typeList

	def getFromTypes(self, types):
		typesList = []
		for type in types:
			typesList.extend(self.getFromType(type))
		return typesList

	def size(self):
		return len(self.entities)
