import serial
import numpy as np
import matplotlib.pyplot as plt

# [ ===== INIT ===== ]

s = None # Serial communication handle
port = '' # Port for serial communication
baudrate = 0 # Baudrate for serial communication
bufserial = '' # Very big bytestring for bufferizing data received on serial
                # We cannot analyze it on-the-fly for performance reasons
bufrle = [] # Preprocessed buffer
fig, ax = None, None # Plot
plotx, ploty = None, None # Plot values
plt.style.use(['ggplot'])

# [ ===== FUNC ===== ]

# Record data from the serial port in the fastest way possible
# Don't perform any processing nor decoding on the data
def start_recording():
    global s, port, baudrate
    global bufserial, bufrle
    global fig, ax, plotx, ploty
    bufserial, bufrle = '', []
    fig, ax, plotx, ploty = None, None, None, None
    try:
        s = serial.Serial(port, baudrate)
    except:
        print('ERROR: device was disconnected')
        exit(1)
    print('Recording started')
    try:
        while True:
            raw = s.read(s.in_waiting).decode(errors='replace') # Read data in chunks whenever it's available
            bufserial += raw
            if 'INFO::FREEBUF=0' in raw: # Check reported buffer state in ~real-time
                print('WARNING: ESP32 is reporting a full buffer - sampling frequency will dramatically drop')
    except KeyboardInterrupt:
        print('Recording stopped')
        s.close()

# Decode the raw recorded data
# Generates a RLE list that will be plotted
def decode_datastream():
    global bufserial, bufrle
    # Drop any truncated message that was read on the serial
    start = bufserial.find('DATA::')
    if start == -1:
        print('WARNING: Empty recording, nothing to do')
        return
    bufserial = bufserial[start:]
    end = bufserial.rfind('\n')
    if end == -1:
        print('WARNING: Empty recording, nothing to do')
        return
    bufserial = bufserial[:end]
    # Build the RLE buffer
    spl = bufserial.split('\n')
    try:
        for record in spl:
            if 'DATA::' in record:
                bufrle.append((int(record[6:7]), int(record[8:])))
    except:
        print('ERROR: Unknown format encountered in recorded data')

# Plot the decoded data
# Instead of drawing all points, draw a line for each run in order to be faster
def plot_data():
    global bufrle
    global fig, ax, plotx, ploty
    fig, ax = plt.subplots()
    ax.set_title('Oscilloscope')
    ax.set_xlabel('time [$\mu s$]')
    ax.set_ylabel('logical value')
    ax.set_ylim([-0.05,1.05])
    ax.grid(True)
    plotx, ploty = [], []
    dt = 0
    for v,t in bufrle:
        plotx.append(dt)
        ploty.append(v)
        dt += t - 1
        plotx.append(dt)
        ploty.append(v)
        dt += 1
    ax.plot(plotx, ploty, 'c-')
    fig.show()

# [ ===== MAIN ===== ]

if __name__ == '__main__':

    # Welcome and settings
    print('Welcome to the ESP32 Oscilloscope interface')
    port = input('Enter the serial port where the ESP32 is connected: ')
    baudrate = None
    try:
        baudrate = int(input('Enter the serial baudrate: '))
    except:
        print('ERROR: insert a valid number as a baudrate')
        exit(1)

    # Chck if device attached and ready
    try:
        s = serial.Serial(port, baudrate)
        s.close()
        print('Your device was correctly detected')
        print()
    except:
        print('ERROR: there is no such device')
        exit(1)

    # Main menu
    print('Press:\n - \'r\' to start recording data\n - \'s\' to save the previous recording\n - \'l\' to load a previously saved one\n - \'q\' to quit')
    print('While recording, press \'Ctrl-C\' to stop, analyze the recorded data, and plot it')
    while True:
        print()
        choice = input('Your choice [r|s|l|q]: ')
        if choice == 'q': # Quit
            print('Bye!')
            break
        elif choice == 'r': # Start recording
            start_recording()
            decode_datastream()
            plot_data()
        elif choice == 's': # Save previous recording
            # save_recording()
            print('TODO')
        elif choice == 'l': # Load saved recording
            # load_recording()
            print('TODO')
        else: # Unrecognized option
            print('Unrecognized option')
    exit(0)