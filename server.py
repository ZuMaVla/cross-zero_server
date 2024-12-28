import paho.mqtt.client as mqtt
import re
import subprocess

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
    global boardX, boardO, turn_count
    i, j = int(turn[0]), int(turn[1])
    board = globals()[f"board{player}"]
    if not (boardX[i][j] or boardO[i][j]):
        board[i][j] = 1
        turn_count += 1    
    return "turn" + turn 



def connect_displayRPi():
    remote_host = "zumavla@displayRPi"
    script_path = "/home/zumavla/cross-zero/connectRPi.py"
    ssh_command = f"ssh {remote_host} 'python3 {script_path}"
    result = subprocess.run(ssh_command, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Message displayed successfully: {result.stdout}")
    else:
        print(f"Error displaying message: {result.stderr}")


# Callback when connected to the broker
def on_connect(server, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # Subscribe to a topic
    server.subscribe("XO/server")
    connect_displayRPi()
    

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
    global active_game, players, turn_count, boardX, boardO
    active_game = False
    players = 0
    turn_count = 0
    boardX = [ [0, 0, 0], [0, 0, 0], [0, 0, 0] ]
    boardO = [ [0, 0, 0], [0, 0, 0], [0, 0, 0] ]


active_game = False
players = 0
turn_count = 0
boardX = [ [0, 0, 0], [0, 0, 0], [0, 0, 0] ]
boardO = [ [0, 0, 0], [0, 0, 0], [0, 0, 0] ]

XOserver = mqtt.Client()              # Create an MQTT client instance

# Assign callback functions
XOserver.on_connect = on_connect
XOserver.on_message = on_message

# Connect to the MQTT broker (replace with your broker address)
XOserver.connect("xoserver.duckdns.org", 1883, 60)

# Start the loop to listen for incoming messages
XOserver.loop_forever()
