# Secure Network Application Development Using TCP (Assignment 07)

## Student Information

- **Name:** Kaushal Kumar
- **Roll No:** CSB24069
- **Course:** B.Tech Computer Science & Engineering
- **Subject:** Advance Programming
- **Assignment:** 07
- **Title:** Secure Network Application Development Using TCP

---

# Objective

The objective of this assignment is to enhance the GUI-based multi-client TCP chat application developed in Assignment 06 by implementing practical application security mechanisms. The application provides secure user authentication, password hashing, duplicate login prevention, input validation, session management, and secure logging while maintaining reliable communication between multiple clients.

---

# Features Implemented

### User Authentication
- Username and password based login
- Authentication before entering the chat room

### Secure Password Storage
- Passwords stored using SHA-256 hashing
- No plaintext passwords stored

### Duplicate Login Prevention
- Prevents the same user from logging in from multiple devices simultaneously

### Failed Login Protection
- Blocks login temporarily after five consecutive failed attempts

### Input Validation
- Rejects empty usernames
- Rejects empty passwords
- Rejects oversized messages
- Rejects invalid commands

### Session Management
- User logout support
- Automatic session timeout after inactivity

### Secure Logging
- Login events
- Logout events
- Failed login attempts
- Session timeout events
- Invalid input attempts
- Passwords are never logged

### Chat Features
- Multi-client communication
- Broadcast messaging
- Private messaging
- Online users list
- Previous message history

---

# Software Requirements

- Ubuntu Linux
- Python 3.x
- Mininet
- Tkinter
- Wireshark

---

# Python Modules

```bash
socket
threading
tkinter
hashlib
json
csv
datetime
os
time
```

---

# Network Topology

```
          +-----------+
          | Switch s1 |
          +-----------+
        /      |      \
      h1      h2      h3
      |        |       |
   Server   Client1  Client2
```

The application was tested using Mininet.

```bash
sudo mn --topo single,5
```

---

# How to Run

## Step 1

Start Mininet

```bash
sudo mn --topo single,5
```

---

## Step 2

Open terminals

```bash
xterm h1
xterm h2
xterm h3
```

---

## Step 3

Run Server

Inside **h1**

```bash
python3 server_multi.py
```

---

## Step 4

Run Client

Inside **h2**

```bash
python3 client_gui.py
```

Repeat for additional clients.

---

# Login Credentials

Example users stored inside `users.json`

| Username | Password |
|----------|----------|
| admin | password123 |
| alice | alice123 |
| bob | bob123 |

Passwords are stored as SHA-256 hashes.

---

# Supported Commands

| Command | Description |
|----------|-------------|
| /list | Show online users |
| /msg username message | Send private message |
| /stats | Display server statistics |
| /quit | Logout and disconnect |

---

# Security Features

- SHA-256 Password Hashing
- Authentication
- Duplicate Login Prevention
- Failed Login Protection
- Session Timeout
- Secure Logging
- Input Validation
- Password Protection
- Thread-safe Client Management

---

# Wireshark Verification

Capture network traffic using

```
tcp.port == 5000
```

The following were verified:

- Successful Login
- Failed Login
- Authenticated Chat
- Private Messaging
- Logout

---

# Testing

The application was tested for:

- Multiple client connections
- Successful authentication
- Failed authentication
- Duplicate login
- Private messaging
- Broadcast messaging
- Session timeout
- Logout
- Invalid commands
- Oversized messages
- Secure logging

All tests were successfully completed.

---

# Screenshots

Include screenshots of:

- Login Window
- Successful Login
- Failed Login
- Duplicate Login
- Chat Window
- Online Users
- Broadcast Message
- Private Message
- Logout
- Wireshark Capture

---

# Learning Outcomes

Through this assignment, the following concepts were learned:

- TCP Socket Programming
- Multi-threaded Server Development
- Authentication and Authorization
- Password Hashing using SHA-256
- Session Management
- Secure Logging
- Input Validation
- Network Packet Analysis using Wireshark
- Client-Server Communication

---

# Conclusion

This project successfully enhanced the TCP-based multi-client chat application by integrating practical security mechanisms. Features such as secure user authentication, SHA-256 password hashing, duplicate login prevention, failed login protection, session timeout, input validation, and secure logging significantly improved the application's security and reliability. Testing in a Mininet environment and verification using Wireshark confirmed that the implemented security features functioned correctly while maintaining stable communication between multiple clients. The assignment provided valuable practical experience in developing secure client-server applications and demonstrated the importance of implementing authentication, secure password handling, session management, and network security best practices.

---


## Author

**Kaushal Kumar**

B.Tech Computer Science & Engineering

Assignment 07 – Secure Network Application Development Using TCP
