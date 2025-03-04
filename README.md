# meshtastic_stand_alone_interface
A custom clone of the oled screen to interface with as a standalone offgrid system

# Navigate to your project directory
cd path/to/your/project

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install the dependencies (including pyserial)
pip install -r requirements.txt

# Run the script
python3 OPS3CmeshtasticUI.py /dev/ttyUSB0                        # Replace with your actual serial port  -- (use ls /dev/tty* to find out your port)
