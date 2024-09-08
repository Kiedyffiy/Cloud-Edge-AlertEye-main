# -*- coding: utf-8 -*-
"""
Created on Tue Aug 29 19:55:50 2023

@author: 19509
"""

import sys
import pyttsx3

def init_engine():
    engine = pyttsx3.init()
    return engine
def say(s):
    engine.say(s)
    engine.runAndWait()
    
engine = init_engine()
say(str(sys.argv[1]))
#pyttsx3.speak("How are you?")