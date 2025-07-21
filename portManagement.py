import os
import socket
import subprocess
import streamlit as st
from threading import Thread, Timer
import time

# Base port for allocation
BASE_PORT = 8501
PORT_RANGE = 3
allocated_ports = {}  # Track user-to-port mappings (user_id -> port)
active_sessions = {}  # Track session activity (user_id -> last active timestamp)
session_timeout = 1800 
cleanup_running = True  # Flag to manage cleanup thread

# Function to check if a port is available
def is_port_available(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('10.1.220.95', port)) != 0

# Function to get the next available port
def get_next_available_port():
    for port in range(BASE_PORT, BASE_PORT + PORT_RANGE):
        if is_port_available(port):
            return port
    return None

# Function to start Streamlit app on a specific port
def start_streamlit_app(port):
    command = f"streamlit run timetable.py --server.port {port} --server.address 10.1.220.95"
    subprocess.Popen(command, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

import subprocess

def stop_streamlit_app(port):
    try:
        # Find the PID of the process using the specified port
        pid_output = subprocess.check_output(
            [
                "lsof",
                "-t",
                f"-i:{port}"
            ],
            text=True
        ).strip()
        
        # Ensure we only take the first PID and clean it
        pid = pid_output.splitlines()[0].strip()

        if pid.isdigit():  # Check if the PID is a valid number
            # Kill the process with the found PID
            subprocess.run(
                [
                    "kill",
                    "-9",
                    pid
                ],
                check=True
            )
            print(f"Streamlit app on port {port} has been stopped.")
        else:
            print(f"No valid process found using port {port}. Output was: {pid_output}")
    except subprocess.CalledProcessError as e:
        print(f"Error stopping the app on port {port}: {e}")


# Function to clean up inactive sessions
def cleanup_sessions():
    global cleanup_running
    while cleanup_running:
        current_time = time.time()
        to_remove = []
        for user_id, last_active in active_sessions.items():
            if current_time - last_active > session_timeout:
                port = allocated_ports.get(user_id)
                if port:
                    stop_streamlit_app(port)
                    to_remove.append(user_id)

        # Remove inactive sessions
        for user_id in to_remove:
            del active_sessions[user_id]
            del allocated_ports[user_id]

        time.sleep(60)  # Run every 60 seconds

# Start session cleanup loop
Thread(target=cleanup_sessions, daemon=True).start()

# Main app logic
st.title("Timetable Generator")

user_id = st.text_input("Enter your User ID:", "")
if st.button("Start Session"):
    if user_id in allocated_ports:
        port = allocated_ports[user_id]
        network_url = f"http://10.1.220.95:{port}"
        st.write(f"Welcome back! Access your session here: [Network URL]({network_url})")
        active_sessions[user_id] = time.time()  # Update activity timestamp
    else:
        port = get_next_available_port()
        if port is None:
            st.error("No available ports. Please try again later.")
        else:
            allocated_ports[user_id] = port
            active_sessions[user_id] = time.time()  # Record activity timestamp
            Thread(target=start_streamlit_app, args=(port,), daemon=True).start()

            # Generate the network URL
            network_url = f"http://10.1.220.95:{port}"
            
            # Display and let user open the URL manually
            st.info(f"A new tab will be opened shortly. If not use the URL below.")
            st.write(f"Network URL : http://10.1.220.95:{port}")

st.info("Download the sample CSV files below.")
st.info("Follow the same format while uploading.")
st.info("Leave the CSV empty if the corresponding feature not needed.")
st.write("CSV for Theory and Labs")
file1 = 'sub_List.csv'
with open(file1, 'r') as file:
    file_data1 = file.read()
st.download_button(
    label="Download CSV",
    data=file_data1,
    file_name="TheoryLab.csv",
    mime="text/csv"
)
st.write("CSV for Electives")
file2 = 'electives.csv'
with open(file2, 'r') as file:
    file_data2 = file.read()
st.download_button(
    label="Download CSV",
    data=file_data2,
    file_name="Electives.csv",
    mime="text/csv"
)
st.write("CSV for Visiting Faculties")
file3 = 'visiting.csv'
with open(file3, 'r') as file:
    file_data3 = file.read()
st.download_button(
    label="Download CSV",
    data=file_data3,
    file_name="Visiting.csv",
    mime="text/csv"
)
st.write("CSV for Blocking Teachers")
file4 = 'teacherBlock.csv'
with open(file4, 'r') as file:
    file_data4 = file.read()
st.download_button(
    label="Download CSV",
    data=file_data4,
    file_name="teacherBlock.csv",
    mime="text/csv"
)

# Stop cleanup thread on shutdown
def stop_cleanup():
    global cleanup_running
    cleanup_running = False

import atexit
atexit.register(stop_cleanup)
