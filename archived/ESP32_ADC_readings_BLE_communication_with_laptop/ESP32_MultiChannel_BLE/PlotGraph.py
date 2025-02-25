# References:
# https://numpy.org/doc/stable/reference/generated/numpy.savez.html
# https://numpy.org/doc/stable/reference/generated/numpy.load.html
# https://docs.python.org/3/library/tkinter.html
# https://matplotlib.org/

import asyncio
import numpy as np
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import threading

# Create the main window 
root = tk.Tk()
root.title("Data Visualization from .npz File")

# Create a frame for the Matplotlib figure
frame = ttk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True)

# Create lists to store data for all three channels
channel_1_data = []
channel_2_data = []
channel_3_data = []

# Define the Matplotlib figure and axis for the graph
fig, ax = plt.subplots(figsize=(10, 6))

# Plot three lines, one for each channel
line_1, = ax.plot([], [], lw=2, label="Channel 1")
line_2, = ax.plot([], [], lw=2, label="Channel 2")
line_3, = ax.plot([], [], lw=2, label="Channel 3")

# Set the axis labels
ax.set_title("Data from .npz File")
ax.set_xlabel("Time")
ax.set_ylabel("Voltage (V)")

# Initialize the plot limits
ax.set_xlim(0, 20)
ax.set_ylim(0, 3.5)

# Add a legend for the channels
ax.legend()

# Set up the animation function
def update_graph(i):
    # Update the plot with new data for all channels
    line_1.set_data(range(len(channel_1_data)), channel_1_data)
    line_2.set_data(range(len(channel_2_data)), channel_2_data)
    line_3.set_data(range(len(channel_3_data)), channel_3_data)
    return line_1, line_2, line_3

# Set up the animation
ani = animation.FuncAnimation(fig, update_graph, blit=True)

# Read data from .npz file and process
def read_npz_data():
    global channel_1_data, channel_2_data, channel_3_data  # Update global data lists

    # Load the .npz file
    npz_data = np.load('input_data.npz')
    
    if 'data' in npz_data:
        data_array = npz_data['data']
        print(f"Loaded data from .npz file: {data_array}")
        
        # Process the data for three channels
        for item in data_array:
            try:
                # Split the string by commas and convert to float for each channel
                channel_values = [float(x) for x in item.split(',')]
                
                # Make sure the data has exactly 3 channels (3 values per item)
                if len(channel_values) == 3:
                    channel_1_data.append(channel_values[0])
                    channel_2_data.append(channel_values[1])
                    channel_3_data.append(channel_values[2])
                else:
                    print(f"Skipping invalid data (not 3 values): {item}")
            except ValueError:
                print(f"Error processing data: {item}")
    else:
        print("No 'data' array found in .npz file.")

    # Update the graph with the loaded data
    print("Data loaded. Updating graph...")
    root.after(100, update_graph, 0)

# Run the read_npz_data function in a separate thread
def start_reading_npz():
    threading.Thread(target=read_npz_data, daemon=True).start()

# Start reading data from the .npz file
start_reading_npz()

# Create a Matplotlib canvas and attach it to Tkinter window
canvas = FigureCanvasTkAgg(fig, master=frame)
canvas.draw()
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Run the Tkinter main loop
root.mainloop()