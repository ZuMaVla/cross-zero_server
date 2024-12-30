# Server for cross-zero (Tic-Tac-Toe Game)

This Python project realises a server designed to facilitate MQTT-based communication for a cross-platform cross-zero (Tic-Tac-Toe) game (Mobile App: https://github.com/ZuMaVla/XO). It manages game state synchronization, player moves, and statistical data collection (for example, to study cognitive functions across different age groups in future).

## Features

- Manages game sessions.
- Handles MQTT message processing and routing between players.
- Collects and stores gameplay statistics for analysis.
- Ensures secure and efficient communication over the MQTT protocol.
- Supports only 2 players in the current version (but scalable in future releases).

## Prerequisites
- **Hardware**:
  - RPi4 #1
  - RPi4 #2 (with SenseHAT)
- **Software**:
  - **dnsmasq**: DHCP&DNS (running on RPi #1)  
  - **MQTT Broker**: Mosquitto (running on RPi #1).
  - **Python**: Version 3.8 or later.
  - **Libraries**:
    - **sense-hat** - Library to interact with the Sense HAT for displaying the game progress with color coding.
    - **paho-mqtt** - MQTT library for communication between the Android client and Raspberry Pi server.
    - **pymongo** - MongoDB client for storing game statistics and player data.

## Usage

1. Ensure the Mosquitto broker is running on your Raspberry Pi.
   ```bash
   sudo systemctl start mosquitto
   ```

2. Start the server using:
   ```bash
   python server.py
   ```

3. Connect the Android client app to the same MQTT broker.

4. Begin playing the game and the server will handle synchronization and statistics collection.

## Configuration

- **MQTT Broker Address**: in the published version - xoserver.duckdns.org (use your hostname but then ammend the following code in the main Python file accordingly: XOserver.connect("xoserver.duckdns.org", 1883, 60)  ).
- **DHCP**: Configure dnsmasq to act as a DHCP server for the ethernet connection bwtween PRi #1 and #2
- **DNS**: Configure dnsmasq to act as DNS to resolve public hostname of MQTT broker into the local IP address of RPi #1 for devices in the same LAN (only if client(s) i.e. mobile device(s) is/are joining the game from the same LAN).

## Acknowledgments

- Sincere thanks to SETU teachers: Frank Walsh and Mujahid Tabassum (computer systems, networking), Caroline Cahill (Linux, Bash scripting), and Mary Lyng and Rossanne Birney (Databases) for their guidance and support in teaching programming fundamentals, which greatly contributed to the creation of this project.
- Inspired by the assignments and concepts from the Computer Systems course at SETU.
- Special thanks to OpenAI (company) for providing the free AI service (ChatGPT) explanations and examples from which as well as suggestions on existing libraries and servises helped me in realisation of this project.## License

This project is licensed under the MIT License.

---

Feel free to contribute to this project by submitting issues or pull requests.
