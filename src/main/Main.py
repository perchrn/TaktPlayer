'''
Created on 28. nov. 2011

@author: pcn
'''

#Kivy imports
import os
from configuration.EffectSettings import EffectTemplates, FadeTemplates
from configuration.GuiServer import GuiServer
os.environ['KIVY_CAMERA'] = 'opencv'
import kivy
kivy.require('1.0.9') # replace with your current kivy version !
from kivy.app import App
from kivy.clock import Clock

from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
#from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty
from kivy.graphics import RenderContext, Fbo, Color, Rectangle

#pcn stuff
from pcnKivy.pcnVideoWidget import PcnVideo

from configuration.ConfigurationHolder import ConfigurationHolder

from video.media.MediaMixer import MediaMixer
from video.media.MediaPool import MediaPool

from midi.MidiTiming import MidiTiming
from midi.TcpMidiListner import TcpMidiListner
from midi.MidiStateHolder import MidiStateHolder

from utilities import MultiprocessLogger

#Python standard
import time
import signal
#Log system
import logging
logging.root.setLevel(logging.ERROR)


header = '''
#ifdef GL_ES
precision highp float;
#endif

/* Outputs from the vertex shader */
varying vec4 frag_color;
varying vec2 tex_coord0;

/* uniform texture samplers */
uniform sampler2D texture0;

uniform vec2 resolution;
uniform float time;
'''

# pulse (Danguafer/Silexars, 2010)
shader_pulse = header + '''
void main(void)
{
    vec2 halfres = resolution.xy/2.0;
    vec2 cPos = gl_FragCoord.xy;

    cPos.x -= 0.5*halfres.x*sin(time/2.0)+0.3*halfres.x*cos(time)+halfres.x;
    cPos.y -= 0.4*halfres.y*sin(time/5.0)+0.3*halfres.y*cos(time)+halfres.y;
    float cLength = length(cPos);

    vec2 uv = tex_coord0+(cPos/cLength)*sin(cLength/30.0-time*10.0)/25.0;
    vec3 col = texture2D(texture0,uv).xyz*50.0/cLength;

    gl_FragColor = vec4(col,1.0);
}
'''

# post processing (by iq, 2009)
shader_postprocessing = header + '''
uniform vec2 uvsize;
uniform vec2 uvpos;
void main(void)
{
    vec2 q = tex_coord0 * vec2(1, -1);
    vec2 uv = 0.5 + (q-0.5);//*(0.9);// + 0.1*sin(0.2*time));

    vec3 oricol = texture2D(texture0,vec2(q.x,1.0-q.y)).xyz;
    vec3 col;

    col.r = texture2D(texture0,vec2(uv.x+0.003,-uv.y)).x;
    col.g = texture2D(texture0,vec2(uv.x+0.000,-uv.y)).y;
    col.b = texture2D(texture0,vec2(uv.x-0.003,-uv.y)).z;

    col = clamp(col*0.5+0.5*col*col*1.2,0.0,1.0);

    //col *= 0.5 + 0.5*16.0*uv.x*uv.y*(1.0-uv.x)*(1.0-uv.y);

    col *= vec3(0.8,1.0,0.7);

    col *= 0.9+0.1*sin(10.0*time+uv.y*1000.0);

    col *= 0.97+0.03*sin(110.0*time);

    float comp = smoothstep( 0.2, 0.7, sin(time) );
    //col = mix( col, oricol, clamp(-2.0+2.0*q.x+3.0*comp,0.0,1.0) );

    gl_FragColor = vec4(col,1.0);
}
'''

shader_monochrome = header + '''
void main() {
    vec4 rgb = texture2D(texture0, tex_coord0);
    float c = (rgb.x + rgb.y + rgb.z) * 0.3333;
    gl_FragColor = vec4(c, c, c, 1.0);
}
'''

class ShaderWidget(FloatLayout):

    # property to set the source code for fragment shader
    fs = StringProperty(None)

    # texture of the framebuffer
    texture = ObjectProperty(None)

    def __init__(self, **kwargs):
        # Instead of using canvas, we will use a RenderContext,
        # and change the default shader used.
        self.canvas = RenderContext()

        # We create a framebuffer at the size of the window
        # FIXME: this should be created at the size of the widget
        with self.canvas:
            self.fbo = Fbo(size=kivy.core.window.Window.size)

        # Set the fbo background to black.
        with self.fbo:
            Color(0, 0, 0)
            Rectangle(size=kivy.core.window.Window.size)

        # call the constructor of parent
        # if they are any graphics object, they will be added on our new canvas
        super(ShaderWidget, self).__init__(**kwargs)

        # We'll update our glsl variables in a clock
        Clock.schedule_interval(self.update_glsl, 0)

        # Don't forget to set the texture property to the texture of framebuffer
        self.texture = self.fbo.texture

    def update_glsl(self, *largs):
        self.canvas['time'] = Clock.get_boottime()
        self.canvas['resolution'] = map(float, self.size)
        # This is needed for the default vertex shader.
        self.fbo['projection_mat'] = kivy.core.window.Window.render_context['projection_mat']
        self.canvas['projection_mat'] = kivy.core.window.Window.render_context['projection_mat']

    def on_fs(self, instance, value):
        # set the fragment shader to our source code
        shader = self.canvas.shader
        old_value = shader.fs
        shader.fs = value
        if not shader.success:
            shader.fs = old_value
            raise Exception('failed')

    #
    # now, if we have new widget to add,
    # add their graphics canvas to our Framebuffer, not the usual canvas.
    #

    def add_widget(self, widget):
        c = self.canvas
        self.canvas = self.fbo
        super(ShaderWidget, self).add_widget(widget)
        self.canvas = c

    def remove_widget(self, widget):
        c = self.canvas
        self.canvas = self.fbo
        super(ShaderWidget, self).remove_widget(widget)
        self.canvas = c

class MyKivyApp(App):
#    icon = 'custom-kivy-icon.png'
    title = 'Musical Video Player'

    def build(self):
        #Multithreaded logging utility and regular logging:
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
#        self._log.setLevel(logging.WARNING)
        self._multiprocessLogger = MultiprocessLogger.MultiprocessLogger(self._log)

        self._configurationTree = ConfigurationHolder("MusicalVideoPlayer")
#        self._configurationTree.loadConfig("DefaultConfig.cfg")
#        self._configurationTree.loadConfig("NerverIEnBunt_1.cfg")
#        self._configurationTree.loadConfig("HongKong_1.cfg")
#        self._configurationTree.loadConfig("Baertur_1.cfg")
        self._configurationTree.loadConfig("PovRay_1.cfg")
        self._globalConfig = self._configurationTree.addChildUnique("Global")
        self._globalConfig.addIntParameter("ResolutionX", 800)
        self._globalConfig.addIntParameter("ResolutionY", 600)

        self._internalResolutionX =  self._configurationTree.getValueFromPath("Global.ResolutionX")
        self._internalResolutionY =  self._configurationTree.getValueFromPath("Global.ResolutionY")


        available_shaders = (
            shader_pulse, shader_postprocessing, shader_monochrome)
        self.shader_index = 0
        root = FloatLayout(size_hint=(None,None), size=(self._internalResolutionX+340, self._internalResolutionY+140))
        self._pcnVideoWidget = PcnVideo(resolution=(self._internalResolutionX, self._internalResolutionY), internalResolution=(self._internalResolutionX, self._internalResolutionY))
        root.add_widget(self._pcnVideoWidget)
        btn = Button(text='Change fragment shader', size_hint=(1, None),
                     height=50)
        def change(*largs):
            self._pcnVideoWidget.updateShader(available_shaders[self.shader_index])
            self.shader_index = (self.shader_index + 1) % len(available_shaders)
        btn.bind(on_release=change)
        root.add_widget(btn)


        self._midiTiming = MidiTiming()
        self._midiStateHolder = MidiStateHolder()
        self._midiStateHolder.noteOn(0, 0x18, 0x40, (True, 0.0))

        self._effectsConfiguration = EffectTemplates(self._globalConfig, self._midiTiming, self._internalResolutionX, self._internalResolutionY)
        self._mediaFadeConfiguration = FadeTemplates(self._globalConfig, self._midiTiming)

        confChild = self._configurationTree.addChildUnique("MediaMixer")
        self._mediaMixer = MediaMixer(confChild, self._midiStateHolder, self._effectsConfiguration)
        confChild = self._configurationTree.addChildUnique("MediaPool")
        self._mediaPool = MediaPool(self._midiTiming, self._midiStateHolder, self._mediaMixer, self._effectsConfiguration, self._mediaFadeConfiguration, confChild, self._multiprocessLogger)

        self._pcnVideoWidget.setFrameProviderClass(self._mediaMixer)
        self._midiListner = TcpMidiListner(self._midiTiming, self._midiStateHolder, self._multiprocessLogger)
        self._timingThreshold = 2.0/60
        self._lastDelta = -1.0

        self._configCheckEveryNRound = 60 * 5 #Every 5th second
        self._configCheckCounter = 0

        self._guiServer = GuiServer(self._configurationTree, self._mediaPool)
        self._guiServer.startGuiServerProcess("0.0.0.0", 2021)
        print self._configurationTree.getConfigurationXMLString()

        return root

    def _getConfiguration(self):
        self._internalResolutionX =  self._configurationTree.getValueFromPath("Global.ResolutionX")
        self._internalResolutionY =  self._configurationTree.getValueFromPath("Global.ResolutionY")

    def checkAndUpdateFromConfiguration(self):
        if(self._configCheckCounter >= self._configCheckEveryNRound):
            if(self._configurationTree.isConfigurationUpdated()):
#                print "config is updated..."
                self._getConfiguration()
                self._mediaPool.checkAndUpdateFromConfiguration()
                self._configurationTree.resetConfigurationUpdated()
                self._globalConfig.resetConfigurationUpdated()
                #TODO: autosave...
            self._configCheckCounter = 0
        else:
            self._configCheckCounter += 1

    def stopProcess(self):
        self._log.info("Caught signal INT")
        self.stop()

    def on_stop(self):
        self._log.info("Close applicaton")
        self._midiListner.stopDaemon()
        self._guiServer.stopGuiServerProcess()

    def frameReady(self, dt):
        pass

    def getNextFrame(self, dt):
        try:
#            if (dt > self._timingThreshold):
#                self._log.info("Too slow main schedule " + str(dt))
            timeStamp = time.time()
            self._midiListner.getData()
            self._mediaPool.updateVideo(timeStamp)
            self._multiprocessLogger.handleQueuedLoggs()
            self.checkAndUpdateFromConfiguration()
            self._guiServer.processGuiRequests()
#            timeUsed = time.time() - timeStamp
#            if((timeUsed / self._lastDelta) > 0.9):
#                print "PCN time: " + str(timeUsed) + " last delta: " + str(self._lastDelta)
            self._lastDelta = dt
        except:
            self.stopProcess()
            raise

if __name__ in ('__android__', '__main__'):
    try:
        mainApp = MyKivyApp()
        Clock.schedule_interval(mainApp.getNextFrame, 0)
#        Clock.schedule_interval(mainApp.frameReady, -1)
        signal.signal(signal.SIGINT, mainApp.stopProcess)
        mainApp.run()
    except:
        mainApp.stopProcess()
        raise
    print "Exiting MAIN XoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoX"
    mainApp.stopProcess()
