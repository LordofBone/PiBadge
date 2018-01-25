import subprocess
import re
import sys

#use tts to inform the user of shutdown then execute the command
def spark(inputText):
	subprocess.call(["espeak 'shutting down'"], shell=True)
	subprocess.call('sudo shutdown now', shell=True)
	return

#the the function for the main code to see if there are any matching words from the input for this module
def isValid(text):
	return bool(re.search(r'\bshutdown|off|power\b', text, re.IGNORECASE))
