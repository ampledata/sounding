#!/usr/bin/python
"""
The script opens an ALSA pcm for sound capture. Set various attributes
of the capture, and reads in a loop, then prints the volume.

To test it out, run it and shout at your microphone.
"""


import alsaaudio
import audioop
import logging
import logging.handlers
import os
import sys
import time


CHANNELS = 1  # Mono
RATE = 8000  # 8 kHz
FORMAT = alsaaudio.PCM_FORMAT_S16_LE  # 16bit Little Endian

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


def setup_logger():
    my_logger = logging.getLogger('MyLogger')
    my_logger.setLevel(logging.DEBUG)

    # Syslog dest
    syslog_handler = logging.handlers.SysLogHandler(
            address=(LOGHOST, LOGPORT))
    if LOGHOST is not None and LOGPORT is not None:
        my_logger.addHandler(syslog_handler)

    console_logger = logging.StreamHandler()
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
    while True:
        data_len, data = audio.read()
        if data_len:
            logger.info(
                "%f rms=%s max=%s\n"
                % (time.time(), audioop.max(data, 2), audioop.rms(data, 2)))
        time.sleep(SLEEP)


if __name__ == '__main__':
    sys.exit(main())