'''
OpenCV Camera: Implement CameraBase with OpenCV
'''

#
# TODO: make usage of thread or multiprocess
#

__all__ = ('PcnVideo')

from kivy.graphics.texture import Texture #@UnresolvedImport
from kivy.core.camera import CameraBase
from kivy.clock import Clock

import logging
log = logging.getLogger('pcnKivy.PcnVideo')

class PcnVideo(CameraBase):
    '''Implementation of CameraBase using OpenCV
    '''

    def __init__(self, **kwargs):
        self._device = None
        self._frameProvider = None
        kwargs.setdefault('internalResolution', (800, 600))
        self._internalResolution = kwargs.get('internalResolution')

        super(PcnVideo, self).__init__(**kwargs)

        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._log.setLevel(logging.WARNING)


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

