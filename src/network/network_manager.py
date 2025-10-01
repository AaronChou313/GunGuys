import socket
import threading
import json
import time

class NetworkManager:
    def __init__(self):
        self.host = None
        self.port = 12345
        self.server_socket = None
        self.client_socket = None
        self.is_host = False
        self.is_connected = False
        self.game_data = {}
        
    def start_hosting(self):
        """Start hosting a game session"""
        try:
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
    
    def discover_games(self):
        """Discover games on the local network"""
        # TODO: Implement game discovery using UDP broadcast or similar
        discovered_games = []
        return discovered_games
    
    def connect_to_game(self, host, port=12345):
        """Connect to a hosted game"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))
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
                self.client_socket.send(json.dumps(data).encode('utf-8'))
            elif self.is_connected and self.client_socket:
                # Send to server
                self.client_socket.send(json.dumps(data).encode('utf-8'))
        except Exception as e:
            print(f"Error sending data: {e}")
    
    def stop_networking(self):
        """Stop all networking activities"""
        self.is_host = False
        self.is_connected = False
        
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
            
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None