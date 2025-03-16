#!/usr/bin/env python
"""
Script to start the API server and perform a basic check
"""
import subprocess
import time
import sys
import os
import requests
import signal

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import settings

def main():
    print("Starting API server...")
    
    # Start server in a subprocess
    server_process = subprocess.Popen(
        ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("Server is running!")
            print(f"Response: {response.json()}")
        else:
            print(f"Server returned unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error connecting to server: {e}")
    
    # Print any server output so far
    stdout_data, stderr_data = server_process.communicate(timeout=0.1)
    
    if stdout_data:
        print("\nServer stdout:")
        print("-" * 60)
        print(stdout_data)
    
    if stderr_data:
        print("\nServer stderr:")
        print("-" * 60)
        print(stderr_data)
    
    print("\nTerminating server...")
    server_process.terminate()
    
    print("Done!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript interrupted by user.")
        sys.exit(0) 