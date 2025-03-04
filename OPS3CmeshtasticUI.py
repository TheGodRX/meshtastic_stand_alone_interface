#!/usr/bin/env python3

import sys
import time
import asyncio
import pygame
from pubsub import pub
from meshtastic.serial_interface import SerialInterface
import math

# Initialize Pygame
pygame.init()

# Screen dimensions for fullscreen
SCREEN_WIDTH, SCREEN_HEIGHT = pygame.display.Info().current_w, pygame.display.Info().current_h  # Full screen dimensions
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF)
pygame.display.set_caption("Meshtastic OLED Display Mirror")

# Font for displaying text on the screen (larger font for fullscreen)
font_size = int(SCREEN_HEIGHT * 0.03)  # Adjust font size based on screen height
large_font_size = int(SCREEN_HEIGHT * 0.04)
font = pygame.font.Font(None, font_size)
large_font = pygame.font.Font(None, large_font_size)

# Initialize variables
message_input = ""  # Input field for typing messages
messages_sent = []  # List of sent messages
messages_received = []  # List of received messages
channel = 0  # Default channel to send messages
channel_input_mode = False  # Whether the user is typing a channel number
channel_input = ""  # Input field for typing channel number
flash_visible = True  # Toggle for flashing effect
last_flash_time = time.time()  # Time tracking for flashing

# Function to get node info
def get_node_info(iface):
    node_info = {}
    my_node = iface.getMyNodeInfo()
    node_info['node_id'] = my_node['user']['id']
    node_info['node_name'] = my_node['user']['longName']
    node_info['role'] = my_node['user']['role']
    node_info['location'] = f"Lat: {my_node['position']['latitude']}, Long: {my_node['position']['longitude']}" if 'position' in my_node else "Location: Unknown"
    node_info['signal_strength'] = my_node.get('snr', 'Unknown')
    return node_info

# Function to display device info including node location, signal, and messages
def display_device_info(iface):
    global message_input, channel, channel_input_mode, channel_input, flash_visible, last_flash_time

    try:
        # Clear the screen
        screen.fill((0, 0, 0))  # Fill screen with black

        # Calculate the size of the circle and arrow based on screen size
        circle_radius = int(SCREEN_HEIGHT * 0.15)  # Larger circle taking up most of the upper-right area
        arrow_length = int(SCREEN_HEIGHT * 0.2)  # Larger arrow proportional to the circle size

        # Position the circle and arrow on the upper-right corner
        node_x = SCREEN_WIDTH - circle_radius - 60  # Padding from the right edge (reduced to move it left)
        node_y = circle_radius + 40  # Padding from the top edge (reduced to move it down slightly)

        # Flash the circle and arrow at an imperceptible speed (100 times faster)
        current_time = time.time()
        if current_time - last_flash_time >= 0.0001:  # 0.1ms interval (100 times faster)
            flash_visible = not flash_visible
            last_flash_time = current_time

        if flash_visible:
            pygame.draw.circle(screen, (0, 255, 255), (node_x, node_y), circle_radius, 2)  # Cyan circle
            # Draw the arrow inside the circle (direction)
            arrow_angle = math.radians(45)  # Example arrow direction
            arrow_x = node_x + arrow_length * math.cos(arrow_angle)
            arrow_y = node_y - arrow_length * math.sin(arrow_angle)
            pygame.draw.line(screen, (0, 255, 255), (node_x, node_y), (arrow_x, arrow_y), 4)  # Cyan arrow

        # Get node information
        node_info = get_node_info(iface)

        # Display node information (Location, Signal Strength, Node ID)
        node_info_text = [
            f"Node: {node_info['node_name']}",
            f"Location: {node_info['location']}",
            f"Signal: {node_info['signal_strength']} dBm",
            f"Role: {node_info['role']}",
            f"Channel: {channel}"  # Display the current channel
        ]

        y_offset = int(SCREEN_HEIGHT * 0.05)  # Start drawing node info at the top
        for line in node_info_text:
            msg_surface = font.render(line, True, (0, 255, 255))  # Neon blue text
            screen.blit(msg_surface, (int(SCREEN_WIDTH * 0.05), y_offset))
            y_offset += int(SCREEN_HEIGHT * 0.03)  # Increase offset for the next line

        # Display received messages (clearing old message)
        if messages_received:
            received_msg = messages_received[-1]  # Only show the latest received message
            wrapped_text = wrap_text(received_msg, SCREEN_WIDTH - int(SCREEN_WIDTH * 0.06))
            y_offset += int(SCREEN_HEIGHT * 0.02)  # Add spacing before the received message
            for line in wrapped_text:
                msg_surface = font.render(f"Recv: {line}", True, (255, 165, 0))  # Retro cyberpunk neon orange
                screen.blit(msg_surface, (int(SCREEN_WIDTH * 0.05), y_offset))  # Draw it
                y_offset += int(SCREEN_HEIGHT * 0.03)  # Increase offset for the next line

        # Display sent messages (clearing old message)
        if messages_sent:
            sent_msg = messages_sent[-1]  # Only show the latest sent message
            wrapped_text = wrap_text(sent_msg, SCREEN_WIDTH - int(SCREEN_WIDTH * 0.06))
            y_offset += int(SCREEN_HEIGHT * 0.02)  # Add spacing before the sent message
            for line in wrapped_text:
                msg_surface = font.render(f"Sent: {line}", True, (255, 165, 0))  # Retro cyberpunk neon orange
                screen.blit(msg_surface, (int(SCREEN_WIDTH * 0.05), y_offset))  # Draw it
                y_offset += int(SCREEN_HEIGHT * 0.03)  # Increase offset for the next line

        # Display connected nodes on the left side, below the messages
        try:
            nodes = iface.nodes
            node_text = [f"Connected Nodes: {len(nodes)}"]
            for node in nodes.values():
                node_text.append(f"Node {node['user']['id']}: {node['user']['longName']}")

            y_offset += int(SCREEN_HEIGHT * 0.05)  # Add extra spacing below the messages
            for line in node_text:
                msg_surface = font.render(line, True, (0, 255, 255))  # Neon blue text
                screen.blit(msg_surface, (int(SCREEN_WIDTH * 0.05), y_offset))
                y_offset += int(SCREEN_HEIGHT * 0.03)
        except Exception as e:
            print(f"Error displaying connected nodes: {e}")

        # Display the message input field at the bottom
        if channel_input_mode:
            msg_surface = large_font.render(f"Set Channel: {channel_input}", True, (0, 255, 255))  # Neon blue text
        else:
            msg_surface = large_font.render(f"Send: {message_input}", True, (0, 255, 255))  # Neon blue text
        screen.blit(msg_surface, ((SCREEN_WIDTH - msg_surface.get_width()) // 2, SCREEN_HEIGHT - int(SCREEN_HEIGHT * 0.1)))

        # Update the display
        pygame.display.flip()

    except Exception as e:
        print(f"Error displaying device info: {e}")

# Function to send a message
def send_message(message, iface):
    global channel
    try:
        iface.sendText(message, channelIndex=channel)  # Send message on the selected channel
        messages_sent.append(f"Channel {channel}: {message}")
    except Exception as e:
        print(f"Error sending message: {e}")

# Callback function to process incoming text messages
def onReceive(packet=None, interface=None):
    if not packet:
        return  # No packet data, do nothing
    decoded = packet.get("decoded", {})
    if "text" in decoded:
        sender = packet.get("fromId", "unknown")
        message = decoded["text"]
        messages_received.append(f"{sender}: {message}")
        display_device_info(interface)

# Function to wrap text to fit within the screen width
def wrap_text(text, max_width):
    lines = []
    words = text.split(" ")
    current_line = ""
    for word in words:
        # Check if the word fits within the remaining space on the line
        if font.size(current_line + word)[0] <= max_width:
            current_line += word + " "
        else:
            if current_line:
                lines.append(current_line.strip())  # Add the current line to the list
            current_line = word + " "  # Start a new line with the current word
    if current_line:
        lines.append(current_line.strip())  # Add the last line
    return lines

# Main function
async def main():
    global message_input, channel, channel_input_mode, channel_input

    if len(sys.argv) < 2:
        print("Usage: python simcc.py <SERIAL_PORT>")
        sys.exit(1)

    port = sys.argv[1].strip()
    print(f"Attempting to connect to Meshtastic device at serial port: {port}")

    try:
        iface = SerialInterface(devPath=port)
        print("Connected to Meshtastic device over serial!")
        time.sleep(2)
    except Exception as e:
        print("Error initializing SerialInterface:", e)
        sys.exit(1)

    print("Serial Interactive Meshtastic Chat Client 0.1.0")
    print("-----------------------------------------------")
    print("Type your message and press Enter to send.")
    print("Type '/channel' to change the channel.")
    print("Press Ctrl+C to exit...\n")

    # Subscribe to receive messages
    pub.subscribe(onReceive, "meshtastic.receive.text")

    loop = asyncio.get_event_loop()
    while True:
        try:
            display_device_info(iface)  # Update display with node and message info

            # Wait for user input to send message or change channel
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if message_input.strip() == "/channel":  # Activate channel input mode
                            channel_input_mode = True
                            message_input = ""
                        elif channel_input_mode:
                            # Set the new channel
                            try:
                                new_channel = int(message_input)
                                if 0 <= new_channel <= 9:
                                    channel = new_channel
                                    print(f"Channel changed to {channel}")
                                else:
                                    print("Invalid channel. Must be between 0 and 9.")
                            except ValueError:
                                print("Invalid input. Please enter a number.")
                            channel_input_mode = False
                            message_input = ""
                        else:
                            # Send the message
                            if message_input:
                                send_message(message_input, iface)
                                message_input = ""  # Clear input field after sending
                    elif event.key == pygame.K_BACKSPACE:
                        message_input = message_input[:-1]  # Remove last character
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit(0)
                    else:
                        message_input += event.unicode  # Append character to message input

            await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            pygame.quit()
            sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
