import network
import socket
import json
import time
from machine import Pin

# ==== Wi-Fi Credentials ====
SSID = "ENTER SSID HERE"
PASSWORD = "ENTER PASSWORD HERE"

# ==== Relay Pins ====
# Pico W GPIO pins - adjust as needed
relay_pins = [15, 14, 13, 12]  # GP15, GP14, GP13, GP12
relays = [Pin(pin, Pin.OUT, value=1) for pin in relay_pins]  # HIGH = OFF (active-low)
relay_state = [False, False, False, False]
relay_names = ["Antenna 1", "Antenna 2", "Antenna 3", "Antenna 4"]

# Simple persistent storage using a file
def load_config():
    global relay_names, relay_state
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            relay_names = config.get('names', relay_names)
            last_relay = config.get('last_relay', -1)
            if 0 <= last_relay < 4:
                relay_state[last_relay] = True
                relays[last_relay].value(0)  # Turn ON (active-low)
    except:
        pass

def save_config():
    config = {
        'names': relay_names,
        'last_relay': relay_state.index(True) if True in relay_state else -1
    }
    with open('config.json', 'w') as f:
        json.dump(config, f)

# Connect to WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # Disconnect if already connected to ensure clean connection
    if wlan.isconnected():
        wlan.disconnect()
        time.sleep(1)
    
    print('Connecting to WiFi...')
    wlan.connect(SSID, PASSWORD)
    
    # Wait for connection with timeout
    max_wait = 20
    while max_wait > 0:
        if wlan.isconnected():
            break
        max_wait -= 1
        print('.', end='')
        time.sleep(1)
    
    if wlan.isconnected():
        status = wlan.ifconfig()
        print('
WiFi connected!')
        print('IP:', status[0])
        print('Subnet:', status[1])
        print('Gateway:', status[2])
        print('DNS:', status[3])
        return status[0]
    else:
        print('
Failed to connect to WiFi')
        return None

# HTML Pages
INDEX_HTML = """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pico W Antenna Control</title>
<style>
  body {
    background-color: #121212;
    color: #e0e0e0;
    font-family: Arial, sans-serif;
    text-align: center;
    padding: 20px;
    margin: 0;
  }
  h2 {
    color: #00bcd4;
    margin-bottom: 30px;
  }
  #buttons {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 15px;
    margin-bottom: 30px;
  }
  button {
    padding: 15px 25px;
    font-size: 18px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    min-width: 160px;
    transition: background-color 0.3s, transform 0.1s;
  }
  .on {
    background-color: #4caf50;
    color: white;
  }
  .off {
    background-color: #f44336;
    color: white;
  }
  button:hover {
    opacity: 0.9;
    transform: scale(1.05);
  }
  #settingsCog {
    position: fixed;
    top: 10px;
    right: 10px;
    font-size: 28px;
    color: #00bcd4;
    cursor: pointer;
    user-select: none;
  }
  #settingsCog:hover {
    color: #80deea;
  }
</style>
</head>
<body>
<div id="settingsCog" title="Settings" onclick="location.href='/settings'">&#9881;</div>
<h2>Pico W Antenna Control</h2>
<div id="buttons"></div>
<script>
function updateButtons() {
  fetch('/api/status')
    .then(r => r.json())
    .then(data => {
      let html = "";
      for (let i = 0; i < data.states.length; i++) {
        let btnClass = data.states[i] ? "on" : "off";
        html += `<button class='${btnClass}' onclick='toggleRelay(${i})'>${data.names[i]}</button>`;
      }
      document.getElementById("buttons").innerHTML = html;
    });
}
function toggleRelay(id) {
  fetch('/api/toggle?id=' + id)
    .then(() => updateButtons());
}
updateButtons();
setInterval(updateButtons, 2000);
</script>
</body>
</html>"""

SETTINGS_HTML = """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Settings - Antenna Names</title>
<style>
  body {
    background-color: #121212;
    color: #e0e0e0;
    font-family: Arial, sans-serif;
    padding: 20px;
    margin: 0;
  }
  h2 {
    color: #00bcd4;
    margin-bottom: 20px;
    text-align: center;
  }
  form {
    max-width: 400px;
    margin: 0 auto;
  }
  label {
    display: block;
    margin: 15px 0 5px 0;
  }
  input[type=text] {
    width: 100%;
    padding: 8px;
    font-size: 16px;
    border-radius: 5px;
    border: none;
  }
  button {
    margin-top: 25px;
    width: 100%;
    padding: 12px;
    background-color: #00bcd4;
    border: none;
    border-radius: 6px;
    font-size: 18px;
    color: white;
    cursor: pointer;
    transition: background-color 0.3s;
  }
  button:hover {
    background-color: #008c9e;
  }
  a {
    color: #00bcd4;
    display: block;
    text-align: center;
    margin-top: 15px;
    text-decoration: none;
  }
  a:hover {
    text-decoration: underline;
  }
</style>
</head>
<body>
<h2>Settings - Rename Antennas</h2>
<form id="nameForm">
  <label for="name0">Antenna 1 Name:</label>
  <input type="text" id="name0" name="name0" required maxlength="30">
  
  <label for="name1">Antenna 2 Name:</label>
  <input type="text" id="name1" name="name1" required maxlength="30">
  
  <label for="name2">Antenna 3 Name:</label>
  <input type="text" id="name2" name="name2" required maxlength="30">
  
  <label for="name3">Antenna 4 Name:</label>
  <input type="text" id="name3" name="name3" required maxlength="30">
  
  <button type="submit">Save Names</button>
</form>
<a href="/">&#8592; Back to Control</a>
<script>
window.onload = function() {
  fetch('/api/names')
    .then(r => r.json())
    .then(data => {
      for (let i=0; i<4; i++) {
        document.getElementById('name'+i).value = data.names[i];
      }
    });
}
document.getElementById('nameForm').onsubmit = function(e) {
  e.preventDefault();
  let names = [];
  for (let i=0; i<4; i++) {
    names.push(document.getElementById('name'+i).value);
  }
  fetch('/api/save-names', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({names: names})
  }).then(() => {
    alert('Names saved!');
    location.href = '/';
  });
}
</script>
</body>
</html>"""

def parse_query_string(url):
    """Parse query parameters from URL"""
    if '?' not in url:
        return {}
    query = url.split('?')[1]
    params = {}
    for param in query.split('&'):
        if '=' in param:
            key, value = param.split('=', 1)
            params[key] = value
    return params

def handle_request(client):
    global relay_state, relay_names
    
    try:
        request = client.recv(1024).decode('utf-8')
        lines = request.split('\r
')
        if not lines:
            return
        
        request_line = lines[0]
        parts = request_line.split(' ')
        if len(parts) < 2:
            return
            
        method = parts[0]
        path = parts[1]
        
        # Route handling
        if path == '/' or path.startswith('/?'):
            response = 'HTTP/1.1 200 OK\r
Content-Type: text/html\r
\r
' + INDEX_HTML
            
        elif path == '/settings':
            response = 'HTTP/1.1 200 OK\r
Content-Type: text/html\r
\r
' + SETTINGS_HTML
            
        elif path == '/api/status':
            data = {
                'states': relay_state,
                'names': relay_names
            }
            response = 'HTTP/1.1 200 OK\r
Content-Type: application/json\r
\r
' + json.dumps(data)
            
        elif path == '/api/names':
            data = {'names': relay_names}
            response = 'HTTP/1.1 200 OK\r
Content-Type: application/json\r
\r
' + json.dumps(data)
            
        elif path.startswith('/api/toggle'):
            params = parse_query_string(path)
            relay_id = int(params.get('id', -1))
            if 0 <= relay_id < 4:
                # Turn off all relays
                for i in range(4):
                    relay_state[i] = False
                    relays[i].value(1)  # HIGH = OFF
                # Turn on selected relay
                relay_state[relay_id] = True
                relays[relay_id].value(0)  # LOW = ON
                save_config()
            response = 'HTTP/1.1 200 OK\r
Content-Type: application/json\r
\r
{"status":"ok"}'
            
        elif path == '/api/save-names' and method == 'POST':
            # Find the JSON body
            body_start = request.find('\r
\r
')
            if body_start != -1:
                body = request[body_start+4:]
                data = json.loads(body)
                new_names = data.get('names', [])
                for i in range(min(4, len(new_names))):
                    if new_names[i].strip():
                        relay_names[i] = new_names[i].strip()
                save_config()
            response = 'HTTP/1.1 200 OK\r
Content-Type: application/json\r
\r
{"status":"ok"}'
            
        else:
            response = 'HTTP/1.1 404 Not Found\r
\r
404 Not Found'
        
        client.send(response.encode('utf-8'))
    except Exception as e:
        print('Error handling request:', e)
    finally:
        client.close()

def main():
    # Initialize
    print('Raspberry Pi Pico W Antenna Controller')
    print('======================================')
    
    load_config()
    ip = connect_wifi()
    
    if ip is None:
        print('Cannot start server without WiFi connection')
        return
    
    # Create socket server
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    
    print('
======================================')
    print('Web server running!')
    print('Access at: http://' + ip)
    print('======================================
')
    
    # Main loop
    while True:
        try:
            client, addr = s.accept()
            handle_request(client)
        except Exception as e:
            print('Error:', e)

# Run the server
if __name__ == '__main__':
    main()
