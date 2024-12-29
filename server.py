import paho.mqtt.client as mqtt
import re
from pymongo import MongoClient
from datetime import datetime


def win_condition(board):
    factor = board[0][0]*board[0][1]*board[0][2] + \
             board[1][0]*board[1][1]*board[1][2] + \
             board[2][0]*board[2][1]*board[2][2] + \
             board[0][0]*board[1][0]*board[2][0] + \
             board[0][1]*board[1][1]*board[2][1] + \
             board[0][2]*board[1][2]*board[2][2] + \
             board[0][0]*board[1][1]*board[2][2] + \
             board[0][2]*board[1][1]*board[2][0]
    if factor:
        return True
    else:
        return False
                 
def winning_combination(board):
    if board[0][0]*board[0][1]*board[0][2] == 1:
        print("000102") 
        return "000102"
    elif board[1][0]*board[1][1]*board[1][2] == 1:
        print("101112") 
        return "101112"
    elif board[2][0]*board[2][1]*board[2][2] == 1:
        print("202122") 
        return "202122"
    elif board[0][0]*board[1][0]*board[2][0] == 1:
        print("001020") 
        return "001020"
    elif board[0][1]*board[1][1]*board[2][1] == 1:
        print("011121") 
        return "011121"
    elif board[0][2]*board[1][2]*board[2][2] == 1:
        print("021222") 
        return "021222"
    elif board[0][0]*board[1][1]*board[2][2] == 1:
        print("001122") 
        return "001122"
    elif board[0][2]*board[1][1]*board[2][0] == 1:
        print("021120") 
        return "021120"

def response(player, turn):
    global boardX, boardO, turn_count, script  # to access global variables
    i, j = int(turn[0]), int(turn[1])
    target_board = boardX if player == "X" else boardO  # Select appropriate board

    # Check if the spot is already taken
    if not (boardX[i][j] or boardO[i][j]):  
        target_board[i][j] = 1  # Mark the move on the player's board
        turn_count += 1  # Increment turn counter
        
        # Create the script for updating the Sense HAT display
        color = "playerX" if player == "X" else "playerO"
        script += f"""
set_turn({i}, {j}, {color})
"""
        # Send the script to RPi #2
        display_on_RPi()  

    # Always return "turn" + turn, regardless of move validity
    return "turn" + turn



import subprocess

def display_on_RPi():
    global script
    remote_host = "zumavla@displayRPi.local"
    
    # Define the path for the script on the remote Raspberry Pi
    remote_script_path = "~/display.py"
    
    # Create the command to save the script to RPi #2
    write_script_command = f"echo \"{script}\" > {remote_script_path}"
    
    # Execute the command to save the script on RPi #2
    result = subprocess.run(f"ssh {remote_host} '{write_script_command}'", shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"Script saved successfully to {remote_script_path} on RPi #2.")
        # Now, execute the script on RPi #2
        run_command = f"ssh {remote_host} 'python3 {remote_script_path}'"
        result = subprocess.run(run_command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Message displayed successfully: {result.stdout}")
        else:
            print(f"Error displaying message: {result.stderr}")
        
        # Optionally, remove the script after execution
        cleanup_command = f"ssh {remote_host} 'rm {remote_script_path}'"
        subprocess.run(cleanup_command, shell=True, capture_output=True, text=True)
    else:
        print(f"Error saving script to {remote_script_path}: {result.stderr}")




# Callback when connected to the broker
def on_connect(server, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # Subscribe to a topic
    server.subscribe("XO/server")
    
    

# Callback when a message is received
def on_message(server, userdata, msg):
    global active_game, players, turn_count
    _response = ""
    _response2 = ""
    received_message = msg.payload.decode()
    print(f"Received message: {received_message} on topic {msg.topic}")
    # Handle the received message here (e.g., update the game state)
    if msg.topic == "XO/server":
        if not active_game:
            if received_message.startswith("ready"):
                if players == 0:
                    server.publish("XO", "O0" + received_message[5:])
                    players += 1 
                elif players == 1:
                    server.publish("XO", "X1" + received_message[5:])
                    server.publish("playerO", "opponent_found")
                    players += 1
                    active_game = True
                    display_on_RPi()
                elif players > 1:
                    server.publish("XO", "full")
        else:
            if len(received_message) == 4:
                turn = received_message[2] + received_message[3]
                _response = response(received_message[0], turn)
                _response2 = ""
            elif re.match(".*resign", received_message):
                _response = "victory"
                _response2 = "_defeat"
                reset_game()

            if received_message[0] == "X":
                server.publish("playerO", _response)
                if _response2:
                    server.publish("playerX", _response2)
                if win_condition(boardX):
                    w_c = winning_combination(boardX)
                    server.publish("playerO", "_defeat" + w_c)
                    server.publish("playerX", "victory" + w_c)
                    reset_game()

            elif received_message[0] == "O":
                server.publish("playerX", _response)
                if _response2:
                    server.publish("playerO", _response2)
                if win_condition(boardO):
                    w_c = winning_combination(boardO)
                    server.publish("playerX", "_defeat" + w_c)
                    server.publish("playerO", "victory" + w_c)
                    reset_game()

            if turn_count == 9:
                server.publish("playerX", "___draw")
                server.publish("playerO", "___draw")
                reset_game()
        

def reset_game():
    global active_game, players, turn_count, boardX, boardO, script, script0
    active_game = False
    players = 0
    turn_count = 0
    boardX = [ [0, 0, 0], [0, 0, 0], [0, 0, 0] ]
    boardO = [ [0, 0, 0], [0, 0, 0], [0, 0, 0] ]
    script = script0


active_game = False
players = 0
turn_count = 0
boardX = [ [0, 0, 0], [0, 0, 0], [0, 0, 0] ]
boardO = [ [0, 0, 0], [0, 0, 0], [0, 0, 0] ]

script0 = """
from sense_hat import SenseHat
sense = SenseHat()

def set_turn(x, y, colour):
    global virtual_display, flat_pixels
    _x = 3*x 
    _y = 3*y
    virtual_display[_y][_x] = colour
    virtual_display[_y + 1][_x] = colour
    virtual_display[_y][_x + 1] = colour
    virtual_display[_y + 1][_x + 1] = colour
    flat_pixels = [pixel for row in virtual_display for pixel in row]
    sense.set_pixels(flat_pixels)

playerX = (0, 63, 191)
playerO = (191, 63, 0)
grid = (48, 48, 48)
black = (0, 0, 0)
flat_pixels = [black]*64   

virtual_display = [[black for _ in range(8)] for _ in range(8)]

# Draw horizontal lines on rows 2 and 5 (which are 3rd and 6th rows in zero-indexing)
virtual_display[2] = [grid] * 8  # Set all pixels in row 2 to white
virtual_display[5] = [grid] * 8  # Set all pixels in row 5 to white

# Draw vertical lines on columns 2 and 5 (which are 3rd and 6th columns in zero-indexing)
for row in virtual_display:
    row[2] = grid  # Set pixels in column 2 to white
    row[5] = grid  # Set pixels in column 5 to white
    
flat_pixels = [pixel for row in virtual_display for pixel in row] 

set_turn(1, 1, black)       # depicting no colour  
"""
script = script0


XOserver = mqtt.Client()              # Create an MQTT client instance

# Assign callback functions
XOserver.on_connect = on_connect
XOserver.on_message = on_message

# Connect to the MQTT broker (replace with your broker address)
XOserver.connect("xoserver.duckdns.org", 1883, 60)

# Start the loop to listen for incoming messages
XOserver.loop_forever()
