#!/usr/bin/python
"""
The script opens an ALSA pcm for sound capture. Set various attributes
of the capture, and reads in a loop, then prints the volume.

To test it out, run it and shout at your microphone.

See the associated article:
    http://ampledata.org/blue_angels_flyover_detection_using_splunk.html

Source: https://github.com/ampledata/sounding
"""

__author__ = 'Greg Albrecht <gba@gregalbrecht.com>'
__copyright__ = 'Copyright 2012 Greg Albrecht'
__license__ = 'Creative Commons Attribution 3.0 Unported License.'


import alsaaudio

import audioop
import math
import logging
import logging.handlers
import os
import socket
import sys
import time


CHANNELS = 1  # Mono
RATE = 8000  # 8 kHz
FORMAT = alsaaudio.PCM_FORMAT_S16_LE  # 16bit Little Endian

# http://stackoverflow.com/questions/2445756/how-can-i-calculate-audio-db-level
MAX_AMPLITUDE = 32767

# The period size controls the internal number of frames per period.
# The significance of this parameter is documented in the ALSA api.
# For our purposes, it is suficcient to know that reads from the device
# will return this many frames. Each frame being 2 bytes long.
# This means that the reads below will return either 320 bytes of data
# or 0 bytes of data. The latter is possible because we are in nonblocking
# mode.
PERIODSIZE = 160

# Seconds to sleep between samples
SLEEP = .01

# Syslog destination
LOGHOST = os.environ.get('LOGHOST')
LOGPORT = os.environ.get('LOGPORT')
LOG_FORMAT = '%(asctime)s log_src=%(name)s %(message)s'


def setup_logger():
    my_logger = logging.getLogger(socket.gethostname())
    my_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(LOG_FORMAT)

    # Syslog dest
    syslog_handler = logging.handlers.SysLogHandler(
        address=(LOGHOST, int(LOGPORT)))
    syslog_handler.setFormatter(formatter)
    if LOGHOST is not None and LOGPORT is not None:
        my_logger.addHandler(syslog_handler)

    console_logger = logging.StreamHandler()
    console_logger.setFormatter(formatter)
    my_logger.addHandler(console_logger)

    return my_logger


def setup_audio():
    inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK)
    inp.setchannels(CHANNELS)
    inp.setrate(RATE)
    inp.setformat(FORMAT)
    inp.setperiodsize(PERIODSIZE)
    return inp


def main():
    audio = setup_audio()
    logger = setup_logger()
    
    while 1:
        data_len, data = audio.read()
        if data_len:
            audio_max = audioop.max(data, 2)
            audio_rms = audioop.rms(data, 2)
            amplitude = float(audio_max) / float(MAX_AMPLITUDE)
            dBg = 20 * math.log10(amplitude)
            logger.info(
                "CHANNELS=%s RATE=%s MAX_AMPLITUDE=%s "
                "rms=%s max=%s amplitude=%f dBg=%f\n",
                CHANNELS,
                RATE,
                MAX_AMPLITUDE,
                audio_rms,
                audio_max,
                amplitude,
                dBg
            )
        time.sleep(SLEEP)


if __name__ == '__main__':
    sys.exit(main())
