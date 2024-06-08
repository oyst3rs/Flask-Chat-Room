# Imports modules
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

# Initializes Flask
app = Flask(__name__)
#Sets a secret key for the admin of website
app.config["SECRET_KEY"] = "secret_key"
# Creates SocketIO Instance
socketio = SocketIO(app)

# Dictionary to store room codes
rooms = {}

# Function to generate room key
def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        # Checks if code is not in use
        if code not in rooms:
            break

    return code

# Route for the home page
@app.route("/", methods=["POST", "GET"])
def home():
    # Clear session data
    session.clear()
    # Handle form submission
    if request.method == "POST":
        # Get name and room code from form data
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        # Validate name input
        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)
        # Validate room code input for joining
        if join != False and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)
        # Set the room code
        room = code
        # If creating a new room, generate a unique room code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        # If joining an existing room, validate if the room exists
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)
        # Set session data for room and name
        session["room"] = room
        session["name"] = name
        # Redirect to the chat room page
        return redirect(url_for("room"))
    # Render the home page template
    return render_template("home.html")

# Route for the chat room page
@app.route("/room")
def room():
    # Get room code from session
    room = session.get("room")
    # Redirect to home page if room code is not set or room does not exist
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    # Render the chat room template with room code and messages
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

# SocketIO event handler for incoming messages
@socketio.on("message")
def message(data):
    # Get room code from session
    room = session.get("room")
    # Checks if room exists
    if room not in rooms:
        return
    # Create message content
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    # Send message to the room
    send(content, to=room)
    # Add message to room messages
    rooms[room]["messages"].append(content)
    # Print message to server console
    print(f"{session.get('name')} said: {data['data']}")

# SocketIO event handler for client connection
@socketio.on("connect")
def connect(auth):
    # Get room and name from session
    room = session.get("room")
    name = session.get("name")
    # Check if room and name are set
    if not room or not name:
        return
    # Check if room exists
    if room not in rooms:
        leave_room(room)
        return
    # Join the room
    join_room(room)
    # Send message to room indicating user has joined
    send({"name": name, "message": "has entered the room"}, to=room)
    # Update room members count
    rooms[room]["members"] += 1
    # Print message to server console
    print(f"{name} joined room {room}")

# SocketIO event handler for client disconnection
@socketio.on("disconnect")
def disconnect():
    # Get room and name from session
    room = session.get("room")
    name = session.get("name")
    # Leave the room
    leave_room(room)

    # Update room members count and remove room if no members
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]

    # Send message to room indicating user has left
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")

# Runs the application
if __name__ == "__main__":
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
