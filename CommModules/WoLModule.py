import subprocess
import re
from colors import *
import sys

#for finding whole words within a string, to match the word within the macs.txt for computer identification
def findWholeWord(w):
	return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

#main function for wake on lan
def spark(inputText):
	#clear variables
	mac = ''
	computer = ''
	#open the file macs.txt and read lines within it
	macfile = open('macs.txt','r')
	macs = macfile.readlines()
	#print the input text for debugging
	sys.stdout.write(RED)
	print inputText
	sys.stdout.write(RESET)
	#strip the word 'wake' out as it is no longer useful in this module
	inputText = inputText.strip('wake')
	#check through each item in the macs variable
	for item in macs:
		#split the words in the string
		for word in inputText.split():
			print word, item
			#if the word matches a word take from macs.txt then set the variables for the computer name and mac address
			if (findWholeWord(word)(item)):
				computer, mac = item.split(',')
	#if no computer is found and mac address is blank then say computer not found and return to main code
	if mac == '':
		sys.stdout.write(BLUE)
		print 'computer not found'
		sys.stdout.write(RESET)
		subprocess.call(["espeak 'computer not found'"], shell=True)
		return
	#if successful then run the wake command for the mac address of the computer using etherwake
	wakeCommand = ('wakeonlan ' + mac)
	#print the wakecommand for debugging
	sys.stdout.write(BLUE)
	print wakeCommand
	sys.stdout.write(RESET)
	#use tts to inform the user what computer has been woken
	wakeNotification = str("waking computer " + computer)
	subprocess.call([wakeCommand], shell=True)
	subprocess.call(['espeak', wakeNotification])
	#close the macs.txt file
	macfile.close()
	return

#the the function for the main code to see if there are any matching words from the input for this module
def isValid(text):
	return bool(re.search(r'\bwakeup|lan|wake\b', text, re.IGNORECASE))
