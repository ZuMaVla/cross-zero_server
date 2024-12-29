import paho.mqtt.client as mqtt
import re
from pymongo import MongoClient
from datetime import datetime
import subprocess


def win_condition(board):           # calculating if the current board results in a win
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
                 
def winning_combination(board):     # finding the winning combination on a board
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

def response(player, turn):         # checking if turn is valid and composing the response
    global boardX, boardO, turn_count, script           # to access global variables
    i, j = int(turn[0]), int(turn[1])
    target_board = boardX if player == "X" else boardO  # Selecting board according to whose turn
    if not (boardX[i][j] or boardO[i][j]):              # Check if the spot is already taken (redundant)
        target_board[i][j] = 1                          # Mark the move on the player's board
        turn_count += 1                                 # Increment turn counter (for draw condition)
        # Preparations for the script for updating the Sense HAT display
        color = "playerX" if player == "X" else "playerO"
        script += f"""
set_turn({i}, {j}, {color})
"""
        display_on_RPi()            # Send the script to RPi #2
    return "turn" + turn            # returning what Android app "expects" to receive

def display_on_RPi():               # updates Sense HAT display according to the current board
    global script
    remote_host = "zumavla@displayRPi.local"    # uses local hostname as connection is over LAN (ethernet) 
    remote_script_path = "~/display.py"         # Defines the path for the Py script on the second RPi
    # Creates the shell command to silently save the script to RPi #2 (to be run by Python there)
    write_script_command = f"echo \"{script}\" > {remote_script_path}"
    # Executes the above shell command over SSH connection (requires sss-agent with private key loaded)
    result = subprocess.run(f"ssh {remote_host} '{write_script_command}'", shell=True, capture_output=True, text=True)
    if result.returncode == 0:                  # checking if no errors
        print(f"Script saved successfully to {remote_script_path} on RPi #2.")
        # Now, it is safe to execute the script on RPi #2's Python
        run_command = f"ssh {remote_host} 'python3 {remote_script_path}'"
        result = subprocess.run(run_command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:              # checking if no errors
            print(f"Message displayed successfully.")
        else:
            print(f"Error displaying message occured.")
    else:
        print(f"Error saving script to {remote_script_path}: {result.stderr}")

def on_connect(server, userdata, flags, rc):    # Subroutine to run when server connects to the Mosquitto broker
    print(f"Connected with result code {rc}")
    server.subscribe("XO/server")       # Server subscribes to the topic to which Android apps publish

def on_message(server, userdata, msg):          # Subroutine to run upon receiving a message
    global active_game, players, turn_count
    _response = ""                              # clearing responses before analysing the message
    _response2 = ""
    received_message = msg.payload.decode()     # decoding message to a string
    print(f"Received message: {received_message} on topic {msg.topic}")     # for development purposes
    # Handle the received message here (an analogue of message interpretator in Android app)
    if msg.topic == "XO/server":                # redundand as only one topic is listened
        if not active_game:
            if received_message.startswith("ready"):    
                if players == 0:
                    server.publish("XO", "O0" + received_message[5:])   # admitting the first player
                    players += 1 
                elif players == 1:
                    server.publish("XO", "X1" + received_message[5:])   # admitting the second player
                    server.publish("playerO", "opponent_found")         # notifying the first player
                    players += 1
                    active_game = True
                    display_on_RPi()                                    # resetting Sense HAT display
                elif players > 1:
                    server.publish("XO", "full")
        else:
            if len(received_message) == 4:                              # a turn received
                turn = received_message[2] + received_message[3]
                _response = response(received_message[0], turn)
                _response2 = ""
            elif re.match(".*resign", received_message):                # a resign request received
                _response = "victory"
                _response2 = "_defeat"
                reset_game()                # no documenting of game outcome if player resigned

            if received_message[0] == "X":
                server.publish("playerO", _response)        # informing the opponent of the current turn
                if _response2:
                    server.publish("playerX", _response2)   # sending a defeat notice (only triggers in a "resign" case)
                if win_condition(boardX):
                    w_c = winning_combination(boardX)
                    server.publish("playerO", "_defeat" + w_c)
                    server.publish("playerX", "victory" + w_c)
                    push_outcome("X won")
                    reset_game()

            elif received_message[0] == "O":
                server.publish("playerX", _response)        # informing the opponent of the current turn
                if _response2:
                    server.publish("playerO", _response2)   # sending a defeat notice (only triggers in a "resign" case)
                if win_condition(boardO):
                    w_c = winning_combination(boardO)
                    server.publish("playerX", "_defeat" + w_c)
                    server.publish("playerO", "victory" + w_c)
                    push_outcome("O won")
                    reset_game()
            if turn_count == 9:                             # detecting a "draw" case
                server.publish("playerX", "___draw")
                server.publish("playerO", "___draw")
                push_outcome("draw")
                reset_game()

def push_outcome(outcome):          # pushes the game outcome to the cloud database
    new_outcome = {
                    "value": outcome,  
                    "date": datetime.now()                  # Current date and time
                }
    result = collection.insert_one(new_outcome)
    print("Inserted document ID:", result.inserted_id)      # Print the ID of the new DB entry

def reset_game():                   # subroutine to reset global variables upon game ending
    global active_game, players, turn_count, boardX, boardO, script, script0
    active_game = False
    players = 0
    turn_count = 0
    boardX = [ [0, 0, 0], [0, 0, 0], [0, 0, 0] ]
    boardO = [ [0, 0, 0], [0, 0, 0], [0, 0, 0] ]
    script = script0                            # resetting of display script to display just the grid


active_game = False
players = 0
turn_count = 0
boardX = [ [0, 0, 0], [0, 0, 0], [0, 0, 0] ]
boardO = [ [0, 0, 0], [0, 0, 0], [0, 0, 0] ]

# keeping grid picture script for new games in a separate variable
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
script = script0                        # initialising script variable for a new game at the server start

XOserver = mqtt.Client()                # Create an MQTT client instance
# Assigning predefined subproutines to trigger on certain events on XOserver
XOserver.on_connect = on_connect
XOserver.on_message = on_message

DBclient = MongoClient("mongodb+srv://zumavla:Tgje8lv8CErF6m0K@cluster0.qaiqs.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = DBclient["XO"]                     # set push destination to the database "XO"
collection = db["outcomes"]             # set push destination to the collection "outcomes" within "XO"

# Connect to the MQTT broker
XOserver.connect("xoserver.duckdns.org", 1883, 60)

# Start the loop to listen for incoming messages
XOserver.loop_forever()