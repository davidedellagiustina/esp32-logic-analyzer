import pickle, serial, time
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

# Set some settings about the recording device
def settings():
    global port, baudrate
    new_baudrate = None
    new_port = input('Enter the serial port where the ESP32 is connected: ')
    try:
        new_baudrate = int(input('Enter the serial baudrate: '))
        port, baudrate = new_port, new_baudrate
    except:
        print('ERROR: insert a valid number as a baudrate - last valid settings will be restored')

# Check if the recording device is connected
# Returns true on success, false otherwise
def check_device():
    global s, port, baudrate
    try:
        s = serial.Serial(port, baudrate)
        s.close()
        return True
    except:
        return False

# Read a chunk of data from the serial port
def read_data_from_serial():
    global s, bufserial
    try:
        raw = s.read(s.in_waiting).decode(errors='replace') # Read data in chunks whenever it's available
        bufserial += raw
        if 'INFO::FREEBUF=0' in raw: # Check reported buffer state in ~real-time
            print('WARNING: ESP32 is reporting a full buffer - sampling frequency will dramatically drop')
    except KeyboardInterrupt: raise
    except:
        print('ERROR: device was disconnected')
        raise

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
        raise
    print('Recording started')
    try:
        while True: read_data_from_serial()
    except KeyboardInterrupt:
        print('Recording stopped')
        print('Waiting for the device to send any late and buffered data...')
        # If the sensor produces data at a high frequency (e.g. an IR sensor), it takes a lot of time to send them over the serial port since it runs at ~13kHz and RLE doesn't really suit this case
        time.sleep(2)
        read_data_from_serial()
        s.close()

# Decode the raw recorded data
# Generates a RLE list that will be plotted
def decode_datastream():
    global bufserial, bufrle
    print('Decoding data...')
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
                tmp1 = record[6:].split('x')
                tmp2 = tmp1[1].split('-')
                bufrle.append((int(tmp1[0]), int(tmp2[0]), int(tmp2[1])))
    except:
        print('ERROR: Unknown format encountered in recorded data')
    # Shift RLE buffer to make it start from 0
    m = bufrle[0][1]
    for i in range(len(bufrle)):
        v = bufrle[i][0]
        s = bufrle[i][1] - m
        e = bufrle[i][2] - m
        bufrle[i] = (v, s, e)

# Plot the decoded data
# Instead of drawing all points, draw a line for each run in order to be faster
def plot_data():
    global bufrle
    global fig, ax, plotx, ploty
    print('Building plot...')
    fig = plt.figure(figsize=(13,7))
    plt.subplots_adjust(left=0.07, right=0.95, top=0.93, bottom=0.1)
    ax = fig.add_subplot(111)
    ax.set_title('Oscilloscope')
    ax.set_xlabel('time [$\mu s$]')
    ax.set_ylabel('logical value')
    ax.set_ylim([-0.05,1.05])
    ax.grid(True)
    plotx, ploty = [], []
    for v,s,e in bufrle:
        plotx.append(s)
        ploty.append(v)
        if s != e:
            plotx.append(e)
            ploty.append(v)
    ax.plot(plotx, ploty, 'c-') # Cyan line
    fig.show()

# Save a serialized representation of the recorded data
# Saves all the buffers (so we can always recover old captures even if this software gets updated)
# It seems that is not possible to pickle the final plot, but we can just recompute it on-the-fly
def save_recording():
    global bufserial, bufrle
    filename = input('Enter the filename: ')
    print('Saving recording...')
    with open(filename, 'wb') as f:
        pickle.dump((bufserial, bufrle), f)
    print('Done')

# Load a previously saved recording
# Loads all buffers, then regenerates and shows plot
def load_recording():
    global bufserial, bufrle
    filename = input('Enter the filename: ')
    print('Loading recording...')
    with open(filename, 'rb') as f:
        bufserial, bufrle = pickle.load(f)
    print('Done')
    plot_data()

# [ ===== MAIN ===== ]

if __name__ == '__main__':

    # Welcome and settings, check if device attached and ready
    print('Welcome to the ESP32 Oscilloscope interface')
    settings()
    if (check_device()): print('Your device was correctly detected')
    else: print('WARNING: you do not have a recording device connected')
    print()

    # Main menu
    print('Press:\n - \'r\' to start recording data\n - \'s\' to save the previous recording\n - \'l\' to load a previously saved one\n - \'t\' to edit settings\n - \'q\' to quit')
    print('While recording, press \'Ctrl-C\' to stop, analyze the recorded data, and plot it')
    while True:
        print()
        choice = input('Your choice [r|s|l|t|q]: ')
        if choice == 'q': # Quit
            print('Bye!')
            break
        elif choice == 'r': # Start recording
            if (check_device()):
                try:
                    start_recording()
                    decode_datastream()
                    plot_data()
                except: pass
            else: print('ERROR: you do not have a recording device connected')
        elif choice == 's': # Save previous recording
            save_recording()
        elif choice == 'l': # Load saved recording
            load_recording()
        elif choice == 't': # Edit settings
            settings()
            if (check_device()): print('Your device was correctly detected')
            else: print('WARNING: you do not have a recording device connected')
        else: # Unrecognized option
            print('Unrecognized option')
    exit(0)