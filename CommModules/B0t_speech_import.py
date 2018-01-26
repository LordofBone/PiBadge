#!/usr/bin/

import sys
import subprocess
import re
import time
import random
import pymongo
import datetime
import sys
import time
import numpy
from pymongo import MongoClient
from pprint import pprint
from difflib import SequenceMatcher
from wit import Wit

#main class where all the workings happen
class talkLoop(object):

	#initialise the class with all variables required
	def __init__(self, client, db, responses, allwords, inputwords, globalReply, botAccuracy, botAccuracyLower):
		self.client = client
		self.db = db
		self.responses = responses
		self.allwords = allwords
		self.inputwords = inputwords
		self.globalReply = globalReply
		self.botAccuracy = botAccuracy
		self.botAccuracyLower = botAccuracyLower

	#function for comparing string similarity
	def similar(self, a, b):
		return SequenceMatcher(None, a, b).ratio()

	#function for grabbing a random document from the database
	def get_random_doc(self):
		count = self.allwords.count()
		return self.allwords.find()[random.randrange(count)]

	#this function generates a random sentence at any length between 1 and 10 words long
	def sentenceGen(self):
		#set a clear string and set a random integer 1-10
		result = ""
		length = random.randint(1, 10)

		#for the range in the integer above find a random word from the db and append to the string
		for i in range(length):
			cursor = self.get_random_doc()
			for x, y in cursor.items():
				if x == "word":
					cWord = (y)
					result += cWord
					result += ' '
					#clear the cursor
					del cursor
		#return the constructed sentence
		return result

	#this function searches the database for the input string and returns all replies for that string, returning a random one
	def dbSearch(self, searchIn):
		#search the database for inputs the bot has said prior
		cursor = self.responses.find_one({"whatbotsaid": searchIn})
		#return list of human replies to this response and choose one at random
		for x, y in cursor.items():
			if x == 'humanReply':
				chosenReply = (random.choice(y))
		#erase the cursor and return the chosen string
		del cursor
		return chosenReply

	#the string comparison function
	def mongoFuzzyMatch(self, inputString, searchZone, termZone, setting):
		#create an empty list
		compareList = []
		#search the database passed in
		for cursor in searchZone.find():
			for x, y in cursor.items():
				#find the item in the cursor that matches the search term passed into the function, eg: 'whatbotsaid'	
				if x == termZone:
					#compare the input string to the current string in the cursor, which returns a decimal point of accuracy (0.0 > 1.0)
					compareNo = self.similar(inputString, y)
					#if accuracy is off then append the string and its accuracy to the dictionary no matter the accuracy
					if setting == 'off':
						compareList.append(y)
					#if accuracy is medium then append the string and its accuracy to the dictionary only if its over the medium setting
					elif setting == 'med':
						if compareNo > self.botAccuracyLower:
							compareList.append(y)
					#if accuracy is on/high then append the string and its accuracy to the dictionary only if its over the on/high setting
					elif setting == 'on':
						if compareNo > self.botAccuracy:
							compareList.append(y)
		#if nothing found then return a non match
		if compareList == []:
			compareChosen = 'none_match'
		#if found responses then choose one at random from the top selections
		else:
			compareChosen = random.choice(compareList)
		#delete cursor
		del cursor
		return compareChosen

	def replyTumbler(self):
		#find the search string using the high accuracy number - to find a decent match to what the bot has said prior
		#when this function is called it required four arguments: the human response, the database to search on, the response required from the database and the accuracy level
		searchSaid = self.mongoFuzzyMatch(self.wordsIn, self.responses, 'whatbotsaid', 'on')
		#if no matches then try with a lower accuracy to find a less similar sentence
		if searchSaid == 'none_match':
			searchSaid = self.mongoFuzzyMatch(self.wordsIn, self.responses, 'whatbotsaid', 'med')
			#if still no match then move onto generating a totally random reply either from words in the database (if there are over twenty stored)
			#and if under twenty words stored run the search function with zero minimum accuracy to essentially return a random sentence the bot has said prior
			if searchSaid == 'none_match':
				if int(self.allwords.count()) < 20:
					searchSaid = self.mongoFuzzyMatch(self.wordsIn, self.responses, 'whatbotsaid', 'off')
					#pass the response into the database to find prior human responses to the above sentence
					chosenReply = self.dbSearch(searchSaid)
				else:
					#pass the response into the database to find prior human responses to the above sentence
					chosenReply = self.sentenceGen()
			else:
				#pass the response into the database to find prior human responses to the above sentence
				chosenReply = self.dbSearch(searchSaid)
		else:
			chosenReply = self.dbSearch(searchSaid)
		#clear the search variable
		del searchSaid
		return (chosenReply)
	
	#this function passes in the information from the loop, the input reply and the bots last reply and appends them to the database	
	def updateDB(self, wordsIn, bResponse):
		self.wordsIn = wordsIn
		self.bResponse = bResponse
		
		#search the database for prior responses the bot has said
		cursor = self.responses.find_one({"whatbotsaid": self.bResponse})
		
		#if none then store a new bot response with the humans reply
		if cursor is None:
			postR = {"whatbotsaid": self.bResponse, "humanReply": [self.wordsIn]}
			self.responses.insert_one(postR).inserted_id
			del cursor
		#if already existing then update the database with a new reply
		else:
			self.responses.update({"whatbotsaid": self.bResponse}, {'$addToSet': {"humanReply": self.wordsIn}}, upsert=True)
			#clear the cursor
			del cursor
			
		#split the input sentence into individual words and store each in the database
		wordsInDB = self.wordsIn.split(' ')
		for word in wordsInDB:
			#search the database for the word
			cursor = self.allwords.find_one({"word": word})
			#if its not already in the database then insert into the database
			if cursor is None:
				postW = {"word": word}
				self.allwords.insert_one(postW).inserted_id
			#if the word is already in the database pass and clear the cursor
			else:
				pass
			del cursor

#the function called from the main code that will run the main class with all the necessary parameters and start the loop
def spark(inputWords):

	#the wit.ai API key (this is a fake one you will need to sign up for your own at wit.ai)
	client_wit = Wit('YOURKEYHERE')

	#setting up variables for mongodb
	client = MongoClient('localhost', 27017)
	db = client.words_database
	responses = db.responses
	allwords = db.allwords

	#variables for first input and the 2 levels of search accuracy
	globalReply = "hello"
	botAccuracy = 0.725
	botAccuracyLower = 0.45
	
	#exit words for exiting the bot
	exitWords = 'bye goodbye exit cancel'
	
	#initialise the main class and get a basic first response from the bot	
	talkClass = talkLoop(client, db, responses, allwords, inputWords, globalReply, botAccuracy, botAccuracyLower)
	#pass the starting inputs to the database for storage
	talkClass.updateDB(inputWords, globalReply)
	#the below three lines push the input words into the reply tumbler in order to find another greeting other than just human responses to 'hello'
	#for instance: 'hello' can return 'greeting' which will return human responses to that such as 'good day' instead of just returning 'greeting'
	inputWords = (talkClass.replyTumbler())
	#combine the greeting with the humans name from the face identification code
	talkClass.updateDB(inputWords, globalReply)
	globalReply = (talkClass.replyTumbler())
	#use subprocess again to initialise espeak (the TTS) and say the bots response
	subprocess.call(['espeak', globalReply])
	#print the output words to the screen (debug/testing purposes)
	print (globalReply)
	
	#the main loop wrapped in a try to capture any errors and hopefully exit cleanly
	try:
		while True:
			#using subprocess to call the sox recording software with a configuration to trim silence from the recording and stop recording when the speaker has finished
			subprocess.call(['rec /home/pi/PiBadge/test.wav rate 32k silence 1 0.1 1% 1 3.0 1%'], shell=True)
			resp = None
			#use the wit.ai class to interface with the API and send off the wav file from above for STT functions
			with open('/home/pi/PiBadge/test.wav', 'rb') as f:
				resp = client_wit.speech(f, None, {'Content-Type': 'audio/wav'})
			#parse the response given to get the text sent back which will then become the words the bot uses	
			inputWords = str(resp['_text'])
			#print input for debugging
			print inputWords
			#if any exit works detected break from the loop which will return back to the main code
			if any(x in inputWords.split() for x in exitWords.split()):
				break
			#update the database with the humans response and the bots last response
			talkClass.updateDB(inputWords, globalReply)
			#call the reply tumbler function for the bots reply
			globalReply = (talkClass.replyTumbler())
			#use subprocess again to initialise espeak (the TTS) and say the bots response
			subprocess.call(['espeak', globalReply])
			#print the output words to the screen (debug/testing purposes)
			print(globalReply)
	except: 
		pass
	  
def isValid(text):
    return bool(re.search(r'\bchat|talk\b', text, re.IGNORECASE))
