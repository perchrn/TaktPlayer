'''
Created on 18. des. 2011

@author: pcn
'''
import logging
import multiprocessing

class QueueHandler(logging.Handler):
    """
    This is a logging handler which sends events to a multiprocessing queue.
    
    The plan is to add it to Python 3.2, but this can be copy pasted into
    user code for use with earlier Python versions.
    """

    def __init__(self, queue):
        """
        Initialise an instance, using the passed queue.
        """
        logging.Handler.__init__(self)
        self.queue = queue

    def emit(self, record):
        """
        Emit a record.

        Writes the LogRecord to the queue.
        """
        try:
            ei = record.exc_info
            if ei:
                dummy = self.format(record) # just to get traceback text into record.exc_text
                record.exc_info = None  # not needed any more
            self.queue.put_nowait(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

class MultiprocessLogger(object):
    def __init__(self, mainLogger):
        self._queue = multiprocessing.Queue(-1)
        self._multiprocessLogger = mainLogger.getChild("SubProcesses")
#        logFormater = logging.Formatter('%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s')
#        self._multiprocessLogger.setFormatter(logFormater)

#    def __del__(self):
#        self._queue.put(None)
#        self._listener.join(10.0)

    def handleQueuedLoggs(self):
        try:
            record = self._queue.get_nowait()
            logger = logging.getLogger(record.name)
            logger.handle(record) # No level or filter logic applied - just do it!
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            pass
#            import sys, traceback
#            print >> sys.stderr, 'Whoops! Problem:'
#            traceback.print_exc(file=sys.stderr)

    def getLogQueue(self):
        return self._queue

def configureProcessLogger(processLogger, logQueue):
    h = QueueHandler(logQueue)
    processLogger.addHandler(h)
