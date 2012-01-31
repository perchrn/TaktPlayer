'''
OpenCV Camera: Implement CameraBase with OpenCV
'''

#
# TODO: make usage of thread or multiprocess
#

__all__ = ('PcnVideo')

import kivy
from kivy.graphics.texture import Texture
from kivy.core.camera import CameraBase
from kivy.clock import Clock

from kivy.properties import StringProperty, ObjectProperty
from kivy.graphics import RenderContext, Fbo, Color, Rectangle

import logging
log = logging.getLogger('pcnKivy.PcnVideo')

class PcnVideo(CameraBase):
    '''Implementation of CameraBase using OpenCV
    '''
    # property to set the source code for fragment shader
    fs = StringProperty(None)

    # texture of the framebuffer
    texture = ObjectProperty(None)


    def __init__(self, **kwargs):
        self._device = None
        self._frameProvider = None
        kwargs.setdefault('internalResolution', (800, 600))
        self._internalResolution = kwargs.get('internalResolution')

        # Instead of using canvas, we will use a RenderContext,
        # and change the default shader used.
        self.canvas = RenderContext()

        # We create a framebuffer at the size of the window
        # FIXME: this should be created at the size of the widget
        with self.canvas:
            self.fbo = Fbo(size=self._internalResolution)

        # Set the fbo background to black.
        with self.fbo:
            Color(0, 0, 0)
            Rectangle(size=self._internalResolution)

        super(PcnVideo, self).__init__(**kwargs)

        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._log.setLevel(logging.WARNING)

        # We'll update our glsl variables in a clock
        Clock.schedule_interval(self.update_glsl, 0)

        # Don't forget to set the texture property to the texture of framebuffer
        self.texture = self.fbo.texture

    def update_glsl(self, *largs):
        self.canvas['time'] = Clock.get_boottime()
        self.canvas['resolution'] = map(float, self._internalResolution)
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

    def updateShader(self, shader):
        self.fs = shader

    def init_camera(self):
        # create the device
        # Just set the resolution to the frame we just got, but don't use
        # self.resolution for that as that would cause an infinite recursion
        # with self.init_camera (but slowly as we'd have to always get a frame).
        self._resolution = self._internalResolution

        if not self.stopped:
            self.start()

    def setFrameProviderClass(self, providerClass):
        self._frameProvider = providerClass

    def start(self):
        '''Start the camera acquire'''
        self.stopped = False
        Clock.unschedule(self._update)
        Clock.schedule_interval(self._update, 0)

    def _update(self, dt):
        if (dt > 0.02):
            self._log.info("Too slow pcnVideoWidget._update " + str(dt))
        if self.stopped:
            return
        if self._texture is None:
            # Create the texture
            self._texture = Texture.create(self._resolution)
            self._texture.flip_vertical()
            self.dispatch('on_load')
        if self._frameProvider is None:
            return
        frame = self._frameProvider.getImage()
        self._format = 'bgr'
        if frame is not None:
            try:
                self._buffer = frame.imageData
            except AttributeError:
                # On OSX there is no imageData attribute but a tostring()
                # method.
                self._buffer = frame.tostring()
            self._copy_to_gpu()

