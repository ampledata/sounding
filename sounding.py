#!/usr/bin/python
"""
The script opens an ALSA pcm for sound capture. Set various attributes
of the capture, and reads in a loop, then prints the volume.

To test it out, run it and shout at your microphone.

Required: libasound2-dev
RPi:
# Keep snd-usb-audio from beeing loaded as first soundcard
#options snd-usb-audio index=-2

See the associated article:
    http://ampledata.org/blue_angels_flyover_detection_using_splunk.html

Source: https://github.com/ampledata/sounding
"""

__author__ = 'Greg Albrecht <gba@gregalbrecht.com>'
__copyright__ = 'Copyright 2015 Greg Albrecht'
__license__ = 'Apache License, Version 2.0'


import alsaaudio

import audioop
import math
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

COLLECTD_HOST = os.environ.get('COLLECTD_HOST')
COLLECTD_PORT = os.environ.get('COLLECTD_PORT', 2003)


def collect_metric(name, value, timestamp, prefix='sounding'):
    metric_name = '.'.join([prefix, name])
    sock = socket.socket()
    sock.connect((COLLECTD_HOST, COLLECTD_PORT) )
    sock.send("%s %d %d\n" % (metric_name, value, timestamp))
    sock.close()


def setup_audio():
    inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK)
    inp.setchannels(CHANNELS)
    inp.setrate(RATE)
    inp.setformat(FORMAT)
    inp.setperiodsize(PERIODSIZE)
    return inp


def main():
    audio = setup_audio()

    while 1:
        data_len, data = audio.read()
        if data_len:
            try:
                audio_max = audioop.max(data, 2)
                audio_rms = audioop.rms(data, 2)
                amplitude = float(audio_max) / float(MAX_AMPLITUDE)
                dBg = 20 * math.log10(amplitude)
                timestamp = time.time()
                collect_metric('audio_rms', audio_rms, timestamp)
                collect_metric('audio_max', audio_max, timestamp)
                collect_metric('amplitude', amplitude, timestamp)
                collect_metric('dBg', dBg, timestamp)
                time.sleep(SLEEP)
            except audioop.error:
                pass

if __name__ == '__main__':
    sys.exit(main())
