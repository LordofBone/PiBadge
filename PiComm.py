#!/usr/bin/

import sys
import os
import subprocess
import pkgutil
from wit import Wit
import CommModules
import time
import RPi.GPIO as GPIO

#setting up the gpio
GPIO.setmode(GPIO.BCM)

#words defined for exiting
exitWords = 'bye goodbye exit cancel'

#setup the pin for the touch button
padPin = 23
GPIO.setup(padPin, GPIO.IN)

#function that scans loaded modules and assigns their names to a variable
def scannload():
	modules = []
	for importer, modname, ispkg in pkgutil.walk_packages(path=['/home/pi/PiBadge/CommModules'], prefix=__name__+'.'):
		try:
			loader = importer.find_module(modname)
			mod = loader.load_module(modname)
		except:
			print 'couldnt load module'
		else:
			modules.append(mod)
	return modules

#function that parses the text from the input and analyses whether any words match any activation words in a module, if so runs that module
#credits to http://jasperproject.github.io/
def query(modules, texts):
	for module in modules:
		for text in texts.split():
			if module.isValid(text):
				try:
					print 'attempting to run module'
					module.spark(texts)
				except Exception:
					print 'no valid words'
					pass
				else:
					print 'ran module'
				finally:
					print 'nope'
					return
			else:
				print 'nope'

#function for converting the speech to text
def openComms():
	#define api key for https://wit.ai/
	client_wit = Wit('YOURKEYHERE')
	#clear input words variable
	inputWords = ''
	#call recording software, to start recording on noise detection and stop after a few seconds of silence
	subprocess.call(['rec test.wav rate 32k silence 1 0.1 1% 1 3.0 1%'], shell=True)
	resp = None
	#pass the wav file to wit.ai for processing
	with open('test.wav', 'rb') as f:
		resp = client_wit.speech(f, None, {'Content-Type': 'audio/wav'})
	#extract the return text from the stt at wit.ai
	inputWords = str(resp['_text'])
	#print input words for debugging
	print inputWords
	#if the input matches any of the exit words then return from the function back to main loop
	if any(x in inputWords.split() for x in exitWords.split()):
		return
	#send the modules and the input to the query module
	query(modules, inputWords)
	return

#assign modules to a variable with the scan function
modules = scannload()		

#loop for detecting button presses			
while True:
	#define true or false on gpio input from touch button
	padPressed =  GPIO.input(padPin)
	#if button has been pressed
	if padPressed:
		#call the aplay command to play the tng combadge chirp sound
		subprocess.call(['aplay tng_chirp2_clean.wav'], shell=True)
		#call the opencomms function
		openComms()
	time.sleep(0.1)
