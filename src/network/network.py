import socket
import threading
import json
import time
from typing import Dict, Any, Callable

class NetworkManager:
    """网络管理器，处理客户端和服务器通信"""
    
    def __init__(self, host: str = "localhost", port: int = 12345):
        self.host = host
        self.port = port
        self.socket = None
        self.is_server = False
        self.is_connected = False
        self.clients = {}  # 用于服务器端存储客户端信息
        self.player_data = {}  # 存储其他玩家的数据
        self.on_data_received: Callable[[Dict[str, Any]], None] = None
        self.running = False
        self.game_name = "GunGuys Game"
        
    def start_server(self, game_name: str = "GunGuys Game"):
        """启动服务器"""
        self.game_name = game_name
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.is_server = True
            self.is_connected = True
            self.running = True
            
            print(f"Server started on {self.host}:{self.port}")
            
            # 启动接收连接的线程
            accept_thread = threading.Thread(target=self._accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
            
            # 启动发现服务
            discovery_thread = threading.Thread(target=self._discovery_service)
            discovery_thread.daemon = True
            discovery_thread.start()
            
            return True
        except Exception as e:
            print(f"Failed to start server: {e}")
            return False
    
    def connect_to_server(self, host: str = None, port: int = None):
        """连接到服务器"""
        if host:
            self.host = host
        if port:
            self.port = port
            
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.is_connected = True
            self.running = True
            
            # 启动接收数据的线程
            receive_thread = threading.Thread(target=self._receive_data)
            receive_thread.daemon = True
            receive_thread.start()
            
            print(f"Connected to server {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            return False
    
    def _accept_connections(self):
        """服务器接受客户端连接"""
        while self.running:
            try:
                client_socket, address = self.socket.accept()
                client_id = f"{address[0]}:{address[1]}"
                self.clients[client_id] = client_socket
                
                # 为每个客户端启动一个接收数据的线程
                client_thread = threading.Thread(target=self._handle_client, args=(client_socket, client_id))
                client_thread.daemon = True
                client_thread.start()
                
                print(f"Client {client_id} connected")
            except Exception as e:
                if self.running:
                    print(f"Error accepting connections: {e}")
    
    def _handle_client(self, client_socket: socket.socket, client_id: str):
        """处理客户端数据"""
        while self.running:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                message = json.loads(data.decode('utf-8'))
                # 将客户端数据广播给所有其他客户端
                self._broadcast_message(message, exclude_client=client_id)
                
            except Exception as e:
                print(f"Error handling client {client_id}: {e}")
                break
        
        # 客户端断开连接
        if client_id in self.clients:
            del self.clients[client_id]
        print(f"Client {client_id} disconnected")
    
    def _receive_data(self):
        """接收来自服务器的数据"""
        while self.running:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                
                message = json.loads(data.decode('utf-8'))
                if self.on_data_received:
                    self.on_data_received(message)
                    
            except Exception as e:
                if self.running:
                    print(f"Error receiving data: {e}")
                break
    
    def _broadcast_message(self, message: Dict[str, Any], exclude_client: str = None):
        """服务器广播消息给所有客户端"""
        for client_id, client_socket in self.clients.items():
            if client_id != exclude_client:
                try:
                    client_socket.send(json.dumps(message).encode('utf-8'))
                except Exception as e:
                    print(f"Error broadcasting to {client_id}: {e}")
    
    def _discovery_service(self):
        """发现服务，允许局域网内的其他玩家发现游戏"""
        discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        discovery_socket.bind(("", 12346))  # 使用不同的端口进行发现
        
        while self.running and self.is_server:
            try:
                # 广播游戏信息
                game_info = {
                    "type": "game_discovery",
                    "name": self.game_name,
                    "host": self.host,
                    "port": self.port,
                    "players": len(self.clients) + 1  # 包括主机
                }
                
                discovery_socket.sendto(
                    json.dumps(game_info).encode('utf-8'),
                    ('<broadcast>', 12347)
                )
                
                time.sleep(5)  # 每5秒广播一次
            except Exception as e:
                print(f"Discovery service error: {e}")
    
    @staticmethod
    def discover_games():
        """发现局域网内的游戏"""
        discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        discovery_socket.bind(("", 12347))
        discovery_socket.settimeout(10)  # 10秒超时
        
        games = []
        start_time = time.time()
        
        while time.time() - start_time < 10:  # 监听10秒
            try:
                data, addr = discovery_socket.recvfrom(1024)
                game_info = json.loads(data.decode('utf-8'))
                
                if game_info["type"] == "game_discovery":
                    # 检查是否已经存在这个游戏
                    existing_game = next((g for g in games if g["host"] == game_info["host"] and g["port"] == game_info["port"]), None)
                    if not existing_game:
                        games.append(game_info)
            except socket.timeout:
                break
            except Exception as e:
                print(f"Error discovering games: {e}")
                break
                
        return games
    
    def send_data(self, data: Dict[str, Any]):
        """发送数据"""
        if not self.is_connected:
            return
        
        try:
            message = json.dumps(data)
            if self.is_server:
                # 服务器广播给所有客户端
                self._broadcast_message(data)
            else:
                # 客户端发送给服务器
                self.socket.send(message.encode('utf-8'))
        except Exception as e:
            print(f"Error sending data: {e}")
    
    def disconnect(self):
        """断开连接"""
        self.running = False
        if self.socket:
            self.socket.close()
        self.is_connected = False
        print("Disconnected from network")