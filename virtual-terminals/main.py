"""
Entrypoint for the EzServe virtual terminals.
Used to emulate a physical terminal instance screen..
"""
import os
import subprocess
from multiprocessing import Process

# Specify the paths to the Python scripts you want to run
customer_path = "source/customer/customer_virtual_terminal.py"
vendor_path = "source/vendor/vendor_virtual_terminal.py"

def run_script(script_path):
    try:
        subprocess.run(["python3", script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Create two processes, one for each script
    customer_process = Process(target=run_script, args=(customer_path,))
    vendor_process = Process(target=run_script, args=(vendor_path,))

    # Start both processes concurrently
    customer_process.start()
    vendor_process.start()

    # Wait for both processes to finish
    customer_process.join()
    vendor_process.join()
