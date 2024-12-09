
import sys          # System manipulation
import time         # Used to pause execution in threads as needed
import keyboard     # Register keyboard events (keypresses)
import threading    # Threads for parallel execution
import pyaudio      # Audio streams
import numpy as np  # Matrix/list manipulation
import audioop      # Getting volume from sound data

# import struct       # Used for converting sound data to integer lists
# For recording the sound into playable .wav files
# from scipy.fftpack import fft 
# import wave

# GUI dependencies
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtGui import * 

# Constants for streams, modify with care!
CHUNK = 1024*4
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100


print("Available audio devices:")
# Check the input devices
p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            print ("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))
p.terminate()


# Modified from:
# https://people.csail.mit.edu/hubert/pyaudio/

# This is the method running on a thread, one initialized for each audio device
def log_sound(index, label):
    
    # This global buffer consists of several lists, this stream has a list available at the provided index
    # Store the volume data at: buffer[index]
    global buffer       
    # wave_buffer = []      # Store audiosignal here
    
    # Open stream
    stream = p.open(
        format = FORMAT,           # Format of stream data
        channels = CHANNELS,       # Number of input channels
        rate = RATE,               # Frequency of audio
        input = True,              # Stream reads data
        frames_per_buffer = CHUNK, # Number of inout frames for each buffer
        input_device_index = index # Input device
    )

    while True:
            
        # Read a chunk of data from the stream
        data = stream.read(CHUNK)
        
        # Store the data in buffer for .wav file convertion
        # wave_buffer.append(data)
        
        # Calculate the volume from the "chunk" of data
        volume = audioop.rms(data, 2)
        
        # Append the necessary data to the buffer
        buffer[index].append(volume)
        label.setText(str(index)+ " : IMPLEMENT ME!" )
        
        # Check for quit command
        if keyboard.is_pressed('q') or quit_flag:
            
            print("Closing stream", index)
            stream.stop_stream()
            stream.close()
            
            # Save the buffer as a .wav file, for testing purposes only
            #print("Storing f"+str(index)+".wav")
            #wf = wave.open("f"+str(index)+".wav", 'wb')
            #wf.setnchannels(CHANNELS)
            #wf.setsampwidth(p.get_sample_size(FORMAT))
            #wf.setframerate(RATE)
            #wf.writeframes(b''.join(wave_buffer))
            #wf.close()
            break

            
# Close threads when window is closed
def exitMethod():
    global quit_flag
    quit_flag = True
    
# This is the main thread, the code should be implemented here
def mainThread(mean_label, var_label):
    
    # This is the buffer which includes data from all audio sources
    global buffer
    
    # the buffers sould only include the latest entries, this is the length of them
    # try finding a suitable value for it
    buffer_width = 10
    
    while True:
        
            # Check the exit condition and join the threads if it is met
            if keyboard.is_pressed('q') or quit_flag:
                for x in threads:
                    x.join()
                p.terminate()
                break
                
            #time.sleep(0.01) # Pause the updates
            
            # Limit buffers to the buffer_width
            for i in range(len(buffer)):
                buffer[i] = buffer[i][-buffer_width:]  

#########################################################################
#################### TODO: Implement your code there ####################
            
            # The method has been given a set of labels where you may put the desired text
            # Use 'label.setText(string)' to display text

            

    print("Execution finished")



# Store threads and labels
threads = []
labels = []
buffer = []
quit_flag = False

# GUI
app = QApplication(sys.argv)
app.aboutToQuit.connect(exitMethod)

# Initializing window
window = QWidget()
window.setWindowTitle('Soundwave log')
window.setGeometry(50, 50, 500, 500)
window.move(500, 500)

# Initialize pyaudio
p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

# Run the threads
for i in range(0, numdevices):
    
        # Check if the device takes input
    if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            
            # Initialize labels
        labels.append(QLabel("____________", parent = window))
        labels[-1].move(60, (15 * (i+1)) + (10*i))
        labels[-1].setFont(QFont('Arial', 10))
        
            # Append a new buffer to the global list
        buffer.append([])
        
            # Start threads
        threads.append(threading.Thread(target=log_sound, args=(i, labels[i])))
        threads[i].start()

# Init. labels for combined data        
mean = QLabel("Mean: IMPLEMENT ME!", parent = window)
mean.move(60, (15 * numdevices + (10 * numdevices)))
mean.setFont(QFont('Arial', 12))

variance = QLabel("Variance: IMPLEMENT ME!", parent = window)
variance.move(60, (15 * numdevices + (13 * (numdevices + 2))))
variance.setFont(QFont('Arial', 12))

# Start the main thread
main_thread = threading.Thread(target = mainThread, args=[mean, variance])
main_thread.start()

# Show window
window.show()
# Run GUI-application loop
app.exec_()

# Implementation without threads
