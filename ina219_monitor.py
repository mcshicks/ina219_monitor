#!/usr/bin/env python
import time
import logging
import os
from ina219 import INA219
import urwid

UPDATE_INTERVAL = 0.1
LOGGING_INTERVAL = 60
SHUNT_OHMS = 0.1
LOGFILE = "logfile.log"
MAX_EXPECTED_AMPS = .5

filesize = 0
percentused = 0
mah = 0.0
before = time.time()
start = before

palette = [('titlebar', 'black', 'white'),
           ('refresh button', 'dark green,bold', 'black'),
           ('quit button', 'dark red,bold', 'black'),
           ('monitor', 'dark green', 'black')]


def create_header():
    text = urwid.Text(u'INA219 Current Monitor')
    return urwid.AttrMap(text, 'titlebar')


def create_footer():
    return urwid.Text([u'Press (',
                       ('quit button', u'Q'),
                       u') to quit'])


def create_Monitorbox():
    text = urwid.Text(u"Press (R) for a new quote!")
    filler = urwid.Filler(text, valign='top', top=1, bottom=1)
    v_padding = urwid.Padding(filler, left=1, right=1)
    return urwid.LineBox(v_padding)


def create_gui(body):
    return urwid.Frame(header=create_header(), body=body, footer=create_footer())


def append_text(l, s, tabsize=10, color='white'):
    l.append((color, s.expandtabs(tabsize)))


maxc = 0.0
minc = 0.0
maxv = 0.0
minv = 0.0


def read(ina):
    global maxc
    global minc
    global maxv
    global minv
    current = ina.current()
    voltage = ina.voltage()
    now = time.time()
    if(current < minc):
        minc = current
    if(current > maxc):
        maxc = current
    if(voltage < minv):
        minv = voltage
    if(voltage > maxv):
        maxv = voltage
        
    # elapsed = now - start
    # bmah = mah
    # mah = bmah + current*((now - before)/3600.0)
    # before = now
    return(current, voltage, now, minc, maxc, minv, maxv )


def updates(ina):
    global mah
    global before
    global start
    global filesize
    current, voltage, now, minc, maxc, minv, maxv = read(ina)
    elapsed = now - start
    bmah = mah
    mah = bmah + current*((now - before)/3600.0)
    before = now
    averagecurrent = mah*3600/elapsed
    main_loop.draw_screen()
    #
    # TODO Elasped Time currently wraps at 24 need to fix 
    #
    updates = [(u'start: \t'.expandtabs(5)),
               (time.strftime('%Y-%m-%d %H:%M:%S \n',
                              time.localtime(start)).expandtabs(5)),
               (u'elapsed: \t'.expandtabs(5)),
               (time.strftime("%H:%M:%S\n",
                              time.gmtime(elapsed)).expandtabs(5))]
    updates.append(('{:<10}{:<10.2f}{:<10}{:<10.2f}{:<10}{:10.2f}\n'.
                    format('current', current, 'max', maxc, 'min', minc)))
    updates.append(('{:<10}{:<10.2f}{:<10}{:<10.2f}{:<10}{:10.2f}\n'.
                    format('volts', voltage, 'max', maxv, 'min', minv)))
    updates.append(('{:<10}{:<10.2f}{:<20}{:<10.2f}\n'.
                    format('mAH', mah, 'avg current', averagecurrent)))
    updates.append(('{:<10}{:<15}{:<10}{:<10}\n'.
                    format('logfile', LOGFILE, 'size', filesize)))

    return(updates)


def handle_input(key):
    if key == 'Q' or key == 'q':
        file.close()
        raise urwid.ExitMainLoop()


ina = INA219(SHUNT_OHMS, MAX_EXPECTED_AMPS, log_level=logging.INFO)
monitor_box = create_Monitorbox()
main_loop = urwid.MainLoop(create_gui(monitor_box), palette,
                           unhandled_input=handle_input)
# Open log file and write header
file = open(LOGFILE, 'a')
file.write("time , current, voltage , milliamp hours\n")


def refresh(_loop, _data):
    main_loop.draw_screen()
    monitor_box.base_widget.set_text(updates(ina))
    main_loop.set_alarm_in(UPDATE_INTERVAL, refresh)

    
def logging(_loop, _data):
    global filesize
    global mah
    current, voltage, now, minc, maxc, minv, maxv = read(ina)
    file.write("%6F, %.3f, %.3f, %.3f\n" % (now, current, voltage, mah))
    file.flush()
    fileinfo = os.stat(LOGFILE)
    filesize = fileinfo.st_size
    main_loop.set_alarm_in(LOGGING_INTERVAL, logging)


def run():
    global maxc
    global minc
    global maxv
    global minv
    ina.configure(ina.RANGE_16V, ina.GAIN_AUTO)
    ina_alarm = main_loop.set_alarm_in(0, refresh)
    ina_log_alarm = main_loop.set_alarm_in(LOGGING_INTERVAL, logging)
    current = ina.current()
    voltage = ina.voltage()
    maxc = current
    minc = current
    maxv = voltage
    minv = voltage
    main_loop.run()


if __name__ == '__main__':
    run()
