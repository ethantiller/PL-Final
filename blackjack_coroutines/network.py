import asyncio
import json

class AsyncServer:
    def __init__(self, host='0.0.0.0', port=8765):
        """
        Initializes the AsyncServer with a host and port.
        """
        self.host = host
        self.port = port
        self.server = None
        self.clients = {}
        self.queues = {}
        
    async def start(self):
        """
        Starts the async server and starts listening for incoming connections.
        """
        
        self.server = await asyncio.start_server(self.handle_client, self.host, self.port)
        print(f"[Server] Listening on {self.host}:{self.port}")
        async with self.server:
            await self.server.serve_forever()
            
    async def handle_client(self, reader, writer):
        """
        Handle a new client connection.
        Args:
            reader (asyncio.StreamReader): The stream reader for the client.
            writer (asyncio.StreamWriter): The stream writer for the client.
        Returns:
            None
        """
        addr = writer.get_extra_info('peername')
        print(f"[Server] Connection from {addr}")
        try:
            while True:
                message = await self.recv_message(reader)
                if message is None:
                    break
                await self.handle_message(message, reader, writer)
        except Exception as e:
            print(f"[Server] Error: {e}")
        finally:
            print(f"[Server] Disconnecting {addr}")
            if writer in self.clients:
                name = self.clients[writer]
                del self.clients[writer]
                print(f"[Server] Player {name} removed from game.")
                if name in self.queues:
                    del self.queues[name]
            writer.close()
            await writer.wait_closed()

    async def handle_message(self, message, reader, writer):
        """
        Process an incoming message from a client.
        Args:
            message (dict): The received message as a dictionary.
            reader (asyncio.StreamReader): The stream reader for the client.
            writer (asyncio.StreamWriter): The stream writer for the client.
        Returns:
            None
        """
        message_type = message.get("type")
        
        if message_type == "join":
            name = message.get("name", "")
            
            if not name:
                await self.send_message(writer, {"type": "error", "message": "Name required."})
                return
            
            self.clients[writer] = name
            if name not in self.queues:
                self.queues[name] = asyncio.Queue()
                
            await self.broadcast_players()
            
        elif message_type in ("bet_response", "action_response"):
            # Find player name for this writer
            name = self.clients.get(writer)
            if name and name in self.queues:
                await self.queues[name].put(message)
                
        else:
            print(f"[Server] Received: {message}")

    async def broadcast_players(self):
        """
        Broadcast the list of players to all of the clients.
        """
        players = list(self.clients.values())
        message = {"type": "join_ack", "players": players}
        for writer in list(self.clients.keys()):
            try:
                await self.send_message(writer, message)
            except Exception as error:
                print(f"[Server] Error sending message to client: {error}")
                
    async def send_message(self, writer, message_dict):
        """
        Send a JSON message to a client.
        """
        data = json.dumps(message_dict) + '\n'
        writer.write(data.encode())
        await writer.drain()

    async def recv_message(self, reader):
        """
        Receive a JSON message from a client.
        """
        line = await reader.readline()
        if not line:
            return None
        return json.loads(line.decode())

    def get_latest_response(self, writer):
        """
        Retrieve and remove the latest response for a given writer.
        """
        return self.responses.pop(writer, None)

    def get_response_queue(self, name):
        """
        Get the response queue for a player by name, creating it if it doesn't exist.
        """
        return self.queues.setdefault(name, asyncio.Queue())


    
class AsyncClient:
    def __init__(self, host: str = '127.0.0.1', port: int = 8765):
        """
        Initialize the AsyncClient instance.
        """
        self.host = host
        self.port = port
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

    async def connect(self):
        """
        Connect to the server.
        """
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        print(f"[Client] Connected to {self.host}:{self.port}")
        
    async def send_message(self, message_dict):
        """
        Send a JSON message to the server.
        """
        if self.writer is None:
            raise RuntimeError("Not connected: writer is None")
        data = json.dumps(message_dict) + '\n'
        self.writer.write(data.encode())
        await self.writer.drain()

    async def recv_message(self):
        """
        Receive a JSON message from the server.
        """
        if self.reader is None:
            raise RuntimeError("Not connected: reader is None")
        line = await self.reader.readline()
        if not line:
            return None
        return json.loads(line.decode())