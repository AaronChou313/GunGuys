import socket
import threading
import json
import time
import struct

class NetworkManager:
    def __init__(self):
        self.host = None
        self.port = 12345
        self.broadcast_port = 12346
        self.server_socket = None
        self.client_socket = None
        self.is_host = False
        self.is_connected = False
        self.game_data = {}
        self.discovered_games = {}  # {host: (name, last_seen)}
        
        # Connected players
        self.connected_players = {}
        
        # Broadcast discovery
        self.broadcast_socket = None
        self.discovery_running = False
        
        # Game state synchronization
        self.game_state = {
            "players": {},
            "monsters": {},
            "projectiles": {}
        }
        
        # Reconnection settings
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 2  # seconds
        
    def start_hosting(self, game_name="Player's Game"):
        """Start hosting a game session"""
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.host = socket.gethostbyname(socket.gethostname())
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.is_host = True
            
            # Start accepting connections in a separate thread
            accept_thread = threading.Thread(target=self._accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
            
            # Start broadcasting game availability
            broadcast_thread = threading.Thread(target=self._broadcast_game, args=(game_name,))
            broadcast_thread.daemon = True
            broadcast_thread.start()
            
            # Start listening for other broadcasts
            discovery_thread = threading.Thread(target=self._discover_games)
            discovery_thread.daemon = True
            discovery_thread.start()
            
            # Start game state synchronization
            sync_thread = threading.Thread(target=self._sync_game_state)
            sync_thread.daemon = True
            sync_thread.start()
            
            return True
        except Exception as e:
            print(f"Error starting host: {e}")
            return False
    
    def _accept_connections(self):
        """Accept incoming client connections"""
        while self.is_host:
            try:
                client_sock, address = self.server_socket.accept()
                print(f"Connection from {address}")
                # Assign player ID
                player_id = f"player_{len(self.connected_players) + 1}"
                self.connected_players[player_id] = {
                    "socket": client_sock,
                    "address": address,
                    "x": 400,
                    "y": 300
                }
                # Handle client in a separate thread
                client_thread = threading.Thread(target=self._handle_client, args=(client_sock, player_id))
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                if self.is_host:
                    print(f"Error accepting connections: {e}")
                break
    
    def _handle_client(self, client_socket, player_id):
        """Handle communication with a connected client"""
        try:
            while self.is_host and player_id in self.connected_players:
                # In a real implementation, you would receive data from the client
                # and update the game state accordingly
                time.sleep(0.016)  # ~60 FPS
        except Exception as e:
            print(f"Error handling client {player_id}: {e}")
        finally:
            if player_id in self.connected_players:
                del self.connected_players[player_id]
            client_socket.close()
    
    def _broadcast_game(self, game_name):
        """Broadcast game availability on the network"""
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        while self.is_host:
            try:
                # Broadcast game information
                message = json.dumps({
                    "type": "game_discovery",
                    "name": game_name,
                    "host": self.host,
                    "port": self.port,
                    "timestamp": time.time()
                }).encode('utf-8')
                
                self.broadcast_socket.sendto(message, ('<broadcast>', self.broadcast_port))
                time.sleep(2)  # Broadcast every 2 seconds
            except Exception as e:
                print(f"Error broadcasting game: {e}")
                break
    
    def _discover_games(self):
        """Listen for game broadcasts on the network"""
        self.discovery_running = True
        discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        discovery_socket.bind(('', self.broadcast_port))
        
        while self.discovery_running:
            try:
                data, addr = discovery_socket.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))
                
                if message["type"] == "game_discovery":
                    host = message["host"]
                    # Only keep games seen in the last 10 seconds
                    if time.time() - message["timestamp"] < 10:
                        self.discovered_games[host] = (message["name"], message["timestamp"])
                    # Remove old games
                    self.discovered_games = {
                        h: info for h, info in self.discovered_games.items()
                        if time.time() - info[1] < 10
                    }
            except Exception as e:
                if self.discovery_running:
                    print(f"Error discovering games: {e}")
                break
    
    def _sync_game_state(self):
        """Synchronize game state with connected clients using delta compression"""
        last_state = {}  # Store last sent state for delta compression
        
        while self.is_host:
            try:
                # Create delta state (only send changes)
                delta_state = {}
                for key, value in self.game_state.items():
                    if key not in last_state or last_state[key] != value:
                        delta_state[key] = value
                
                # Only send if there are changes
                if delta_state or time.time() % 1 < 0.033:  # Force send every second
                    # Send game state to all connected clients
                    game_state_msg = json.dumps({
                        "type": "game_state",
                        "data": self.game_state,
                        "timestamp": time.time()
                    }).encode('utf-8')
                    
                    # Prefix each message with a 4-byte length (network byte order)
                    game_state_msg = struct.pack('>I', len(game_state_msg)) + game_state_msg
                    
                    # Send to all connected players
                    for player_id, player_info in list(self.connected_players.items()):
                        try:
                            player_info["socket"].send(game_state_msg)
                        except Exception as e:
                            print(f"Error sending to player {player_id}: {e}")
                            # Remove disconnected player
                            if player_id in self.connected_players:
                                del self.connected_players[player_id]
                
                # Update last state
                last_state = self.game_state.copy()
                
                time.sleep(1/30)  # 30 FPS sync
            except Exception as e:
                print(f"Error syncing game state: {e}")
                time.sleep(1/30)
    
    def get_discovered_games(self):
        """Get list of discovered games"""
        games = []
        for host, (name, timestamp) in self.discovered_games.items():
            games.append({
                "name": name,
                "host": host,
                "port": self.port
            })
        return games
    
    def connect_to_game(self, host, port=12345):
        """Connect to a hosted game with reconnection support"""
        self.reconnect_attempts = 0
        
        while self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.settimeout(5)  # 5 second timeout
                self.client_socket.connect((host, port))
                self.client_socket.settimeout(None)  # Remove timeout after connection
                self.is_connected = True
                self.reconnect_attempts = 0  # Reset on successful connection
                
                # Start listening for data in a separate thread
                listen_thread = threading.Thread(target=self._listen_for_data)
                listen_thread.daemon = True
                listen_thread.start()
                
                return True
            except Exception as e:
                print(f"Error connecting to game (attempt {self.reconnect_attempts + 1}): {e}")
                self.reconnect_attempts += 1
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    print(f"Retrying in {self.reconnect_delay} seconds...")
                    time.sleep(self.reconnect_delay)
                else:
                    print("Max reconnection attempts reached.")
                    return False
    
    def _listen_for_data(self):
        """Listen for data from the server"""
        while self.is_connected:
            try:
                # Receive the message length (4 bytes)
                raw_msglen = self._recvall(4)
                if not raw_msglen:
                    break
                msglen = struct.unpack('>I', raw_msglen)[0]
                
                # Receive the message data
                data = self._recvall(msglen)
                if not data:
                    break
                    
                message = json.loads(data.decode('utf-8'))
                
                if message["type"] == "game_state":
                    self.game_state = message["data"]
            except Exception as e:
                print(f"Error listening for data: {e}")
                # Attempt to reconnect
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    print("Connection lost. Attempting to reconnect...")
                    self.is_connected = False
                    # Try to reconnect
                    time.sleep(self.reconnect_delay)
                    # In a real implementation, you would need the host and port to reconnect
                    # For now, we'll just break the loop
                break
    
    def _recvall(self, n):
        """Helper function to receive n bytes or return None if EOF"""
        data = b''
        while len(data) < n:
            packet = self.client_socket.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data
    
    def send_data(self, data):
        """Send data to connected clients or server"""
        try:
            if self.is_host and self.client_socket:
                # Send to specific client
                message = json.dumps(data).encode('utf-8')
                # Prefix each message with a 4-byte length (network byte order)
                message = struct.pack('>I', len(message)) + message
                self.client_socket.send(message)
            elif self.is_connected and self.client_socket:
                # Send to server
                message = json.dumps(data).encode('utf-8')
                # Prefix each message with a 4-byte length (network byte order)
                message = struct.pack('>I', len(message)) + message
                self.client_socket.send(message)
        except Exception as e:
            print(f"Error sending data: {e}")
            # Attempt to reconnect
            if self.is_connected and self.reconnect_attempts < self.max_reconnect_attempts:
                print("Connection error. Attempting to reconnect...")
                self.is_connected = False
    
    def stop_networking(self):
        """Stop all networking activities"""
        self.is_host = False
        self.is_connected = False
        self.discovery_running = False
        
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
            
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            
        if self.broadcast_socket:
            self.broadcast_socket.close()
            self.broadcast_socket = None