'''
Created on 09. dec. 2011

@author: pcn
'''
#Kivy imports
import os
os.environ['KIVY_CAMERA'] = 'opencv'
import kivy
kivy.require('1.0.9') # replace with your current kivy version !
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

#Python standard
import time
#Log system
import logging
logging.root.setLevel(logging.ERROR)

class EncoderKivyApp(App):
    def addToWidgetBox(self, widgets):
        if (hasattr(self, '_encLayout') == False):
            self._encLayout = BoxLayout(padding=10)
            self._encLayout.add_widget(widgets)

    def build(self):
        if (hasattr(self, '_encLayout') == False):
            self._encLayout = BoxLayout(padding=10)
            self._encLayout.add_widget(Button(text='No GUI made!'))
        return self._encLayout

