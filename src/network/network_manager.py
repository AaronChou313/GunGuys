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
        
        # Broadcast discovery
        self.broadcast_socket = None
        self.discovery_running = False
        
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
                # Handle client in a separate thread
                client_thread = threading.Thread(target=self._handle_client, args=(client_sock,))
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                if self.is_host:
                    print(f"Error accepting connections: {e}")
                break
    
    def _handle_client(self, client_socket):
        """Handle communication with a connected client"""
        # TODO: Implement client handling logic
        pass
    
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
        """Connect to a hosted game"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5)  # 5 second timeout
            self.client_socket.connect((host, port))
            self.client_socket.settimeout(None)  # Remove timeout after connection
            self.is_connected = True
            
            # Start listening for data in a separate thread
            listen_thread = threading.Thread(target=self._listen_for_data)
            listen_thread.daemon = True
            listen_thread.start()
            
            return True
        except Exception as e:
            print(f"Error connecting to game: {e}")
            return False
    
    def _listen_for_data(self):
        """Listen for data from the server"""
        while self.is_connected:
            try:
                # TODO: Implement data receiving logic
                pass
            except Exception as e:
                print(f"Error listening for data: {e}")
                break
    
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