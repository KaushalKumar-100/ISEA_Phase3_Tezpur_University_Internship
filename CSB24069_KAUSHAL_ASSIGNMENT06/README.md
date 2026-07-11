# GUI-Based Multi-Client Chat Application Using TCP

A GUI-based Multi-Client Chat Application developed using **Python**, **Tkinter**, and **TCP Socket Programming**. This project is an extension of Assignment 5, where the terminal-based client has been replaced with a graphical user interface while reusing the existing server implementation. The application supports multiple clients communicating simultaneously through a central server using reliable TCP connections.

---

# Objective

The objective of this project is to develop a graphical desktop chat application by integrating **socket programming**, **GUI development**, and **multithreading**. The application provides an intuitive user interface for communication while maintaining the networking logic developed in the previous assignment.

The application supports:

- Multi-client communication
- Broadcast messaging
- Private messaging
- Online user management
- Join and leave notifications
- Chat history logging
- Background message receiving
- Responsive graphical interface

---

# Software Requirements

## Operating System

- Ubuntu 22.04 or later
- Linux with Mininet installed

## Programming Language

- Python 3.x

## Python Modules

- socket
- threading
- tkinter
- tkinter.scrolledtext
- csv
- datetime
- os

## Networking Tools

- Mininet
- Wireshark

## IDE (Optional)

- Visual Studio Code
- PyCharm
- Any Python IDE

---

# Network Topology

The application was tested using **Mininet** with one server and four clients.

```
                 +----------------------+
                 |      Chat Server     |
                 |      (Host h1)       |
                 +----------+-----------+
                            |
        ---------------------------------------------
        |             |             |               |
      Host h2       Host h3       Host h4       Host h5
      Client A      Client B      Client C      Client D
```

### Mininet Command

```bash
sudo mn --topo single,5
```

Verify topology

```bash
nodes
net
pingall
```

---

# Project Structure

```
Assignment6/
│
├── server.py
├── client_gui.py
├── chat_history.csv
├── screenshots/
│
├── report.pdf
└── README.md
```

---

# Features

- Graphical Login Window
- TCP Socket Communication
- Multi-threaded Server
- Multi-client Support
- Broadcast Messaging
- Private Messaging
- Dynamic Online User List
- Join Notifications
- Leave Notifications
- Background Message Receiving
- Connection Status Indicator
- Automatic Chat Scrolling
- Safe Client Disconnect

---

# Implementation Overview

The project follows a **Client-Server Architecture** using TCP sockets.

## Server

The server is responsible for:

- Accepting client connections
- Managing connected users
- Broadcasting messages
- Delivering private messages
- Maintaining online user list
- Sending join/leave notifications
- Logging chat history

The server uses **multiple threads** to handle multiple clients simultaneously.

---

## Client GUI

The client is implemented using **Tkinter**.

The GUI contains:

- Login Window
- Chat Window
- Scrollable Chat Area
- Message Input Box
- Send Button
- Online User List
- Disconnect Button
- Connection Status Label

A background thread continuously receives incoming messages without blocking the GUI.

---

# Execution Steps

## Step 1

Start the server

```bash
python3 server.py
```

---

## Step 2

Start Mininet

```bash
sudo mn --topo single,5
```

---

## Step 3

Verify connectivity

```bash
pingall
```

---

## Step 4

Open terminals

```bash
xterm h1 h2 h3 h4 h5
```

---

## Step 5

Run the server

```bash
python3 server.py
```

---

## Step 6

Run each client

```bash
python3 client_gui.py
```

---

## Step 7

Enter usernames

Example

```
Alice
Bob
Charlie
David
```

---

## Step 8

Start chatting

Broadcast

```
Hello Everyone
```

Private Message

```
/msg Bob Hello Bob
```

---

## Step 9

Disconnect

Click

```
Disconnect
```

---

# Sample Screenshots

## Login Window

> Insert Screenshot Here

---

## Successful Connection

> Insert Screenshot Here

---

## Main Chat Window

> Insert Screenshot Here

---

## Broadcast Messaging

> Insert Screenshot Here

---

## Private Messaging

> Insert Screenshot Here

---

## Online Users List

> Insert Screenshot Here

---

## User Join Notification

> Insert Screenshot Here

---

## User Leave Notification

> Insert Screenshot Here

---

## Client Disconnect

> Insert Screenshot Here

---

## Wireshark Verification

Display Filter

```
tcp.port == 5000
```

> Insert Screenshot Here

---

# Testing Summary

The application was tested using one server and four clients in Mininet.

The following functionalities were successfully verified:

- Server startup
- Client connection
- Username validation
- Broadcast messaging
- Private messaging
- Online user updates
- Join notifications
- Leave notifications
- Background message receiving
- Client disconnection
- TCP packet verification using Wireshark

---

# Technologies Used

- Python
- Tkinter
- Socket Programming
- TCP Protocol
- Multithreading
- Mininet
- Wireshark

---

# Future Enhancements

- End-to-end encryption
- User authentication
- Group chat support
- File sharing
- Voice messaging
- Emoji support
- Message notifications
- Database storage
- User profiles
- Dark mode interface

---

# Conclusion

This project successfully converts a terminal-based TCP chat application into a graphical desktop application using Python Tkinter. The networking logic from Assignment 5 was reused with minimal modifications, while the client interface was redesigned to improve usability. The application supports multiple simultaneous users, broadcast and private messaging, online user management, and real-time communication using TCP sockets. Background threading ensures that the graphical interface remains responsive during message reception, and testing with Mininet and Wireshark verified the correctness and reliability of the implementation.

---

# Author

**Name:** Kaushal Kumar

**Roll Number:** CSB24069

**Course:** B.Tech Computer Science and Engineering

**Assignment:** GUI-Based Multi-Client Chat Application Using TCP (Assignment 6)

**Internship:** ISEA Phase III – Tezpur University

---
