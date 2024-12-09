import sys
import threading
import pyaudio
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Constants for audio processing
CHUNK = 1024 * 4
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
FAULT_THRESHOLD = 10  # Volume below this value indicates a potential fault

# Some Global variables
threads = []
labels = []
buffer = []
plots = []
quit_flag = False

def list_audio_devices():
    """
    List of all available input audio devices.
    """
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    print("Available audio devices:")
    for i in range(numdevices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        if device_info.get('maxInputChannels') > 0:
            print(f"Input Device id {i} - {device_info.get('name')}")
    p.terminate()

def calculate_combined_stats():
    """
    Calculate the combined mean and variance over all sound sources.
    """
    if any(len(b) > 0 for b in buffer):  # Ensure there is data in the buffer
        combined_buffer = np.concatenate([np.array(b) for b in buffer if len(b) > 0])
        mean = np.mean(combined_buffer)
        variance = np.var(combined_buffer)
        print(f"Combined Mean: {mean:.2f}, Combined Variance: {variance:.2f}")
    else:
        print("No data to calculate combined statistics.")

def calculate_device_stats(index):
    """
    Calculate the mean and variance for a specific sound source.
    """
    if len(buffer[index]) > 0:
        mean = np.mean(buffer[index])
        variance = np.var(buffer[index])
        print(f"Device {index}: Mean: {mean:.2f}, Variance: {variance:.2f}")
    else:
        print(f"Device {index}: No data to calculate statistics.")

def detect_faulty_sources():
    """
    Detect if one or more sources are faulty based on the buffer data.
    """
    for i, b in enumerate(buffer):
        if len(b) > 0 and np.mean(b) < FAULT_THRESHOLD:
            print(f"Device {i} might be faulty: Low mean volume {np.mean(b):.2f}")
        elif len(b) == 0:
            print(f"Device {i} has no data. Check if it's connected properly.")

def log_sound(index, label, plot):
    """
    Thread function to log sound volume and update the plot for a specific audio device.
    """
    global buffer
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
        input_device_index=index
    )

    while True:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            signal = np.frombuffer(data, dtype=np.int16)
            volume = np.sqrt(np.mean(signal ** 2))
            label.setText(f"Device {index}: Volume: {volume:.2f}")

            # Update the waveform plot
            plot.update_plot(signal)

            # Update the buffer
            buffer[index].append(volume)
            if len(buffer[index]) > 100:
                buffer[index] = buffer[index][-100:]  # Keep buffer limited to 100 values

            # Calculate and log device-specific statistics
            calculate_device_stats(index)

            if quit_flag:
                stream.stop_stream()
                stream.close()
                p.terminate()
                break
        except Exception as e:
            print(f"Error with Device {index}: {e}")
            break

def exit_method():
    """
    Exit method to handle app quit signal.
    """
    global quit_flag
    quit_flag = True

class AudioPlot(FigureCanvas):
    """
    Class to handle audio waveform plotting.
    """
    def __init__(self, parent=None):
        fig = Figure()
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

        self.ax.set_xlim(0, CHUNK)
        self.ax.set_ylim(-32768, 32768)
        self.line, = self.ax.plot(np.zeros(CHUNK))

    def update_plot(self, data):
        self.line.set_ydata(data)
        self.draw()

# GUI setup
app = QApplication(sys.argv)
app.aboutToQuit.connect(exit_method)

window = QWidget()
window.setWindowTitle('Soundwave Log with Plots')
window.setGeometry(50, 50, 800, 600)

layout = QVBoxLayout()
window.setLayout(layout)

# Initialize PyAudio and list devices
list_audio_devices()

p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

# Threading concept
for i in range(numdevices):
    device_info = p.get_device_info_by_host_api_device_index(0, i)
    if device_info.get('maxInputChannels') > 0:
        label = QLabel(f"Device {i}: ______________")
        label.setFont(QFont('Arial', 10))
        layout.addWidget(label)

        plot = AudioPlot(parent=window)
        layout.addWidget(plot)

        labels.append(label)
        buffer.append([])  
        plots.append(plot)

        threads.append(threading.Thread(target=log_sound, args=(i, labels[i], plots[i])))
        threads[i].start()

# Combined tasks

def periodic_tasks():
    calculate_combined_stats()
    detect_faulty_sources()
    threading.Timer(5, periodic_tasks).start()

periodic_tasks()

# Show GUI window
window.show()
app.exec_()

# Cleanup
for t in threads:
    t.join()
p.terminate()
