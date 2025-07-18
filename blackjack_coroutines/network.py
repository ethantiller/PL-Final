"""
network.py

Message Protocol (JSON):
------------------------
All messages are JSON objects with at least a 'type' field. Example types:

- 'join': {"type": "join", "name": <player_name>}
- 'join_ack': {"type": "join_ack", "players": [<name>, ...]}
- 'start': {"type": "start"}
- 'state': {"type": "state", "data": <game_state_dict>}
- 'action': {"type": "action", "action": <action>, "amount": <optional>}
- 'error': {"type": "error", "message": <error_message>}
- 'disconnect': {"type": "disconnect", "reason": <reason>}

All communication is line-delimited JSON (one message per line).
"""
import asyncio
import json

class AsyncServer:
    def __init__(self, host='0.0.0.0', port=8765):
        self.host = host
        self.port = port
        self.server = None
        self.clients = {}  # {writer: name}
        self.responses = {}  # {writer: latest_response}

    async def start(self):
        self.server = await asyncio.start_server(self.handle_client, self.host, self.port)
        print(f"[Server] Listening on {self.host}:{self.port}")
        async with self.server:
            await self.server.serve_forever()

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"[Server] Connection from {addr}")
        try:
            while True:
                msg = await self.recv_msg(reader)
                if msg is None:
                    break
                await self.handle_message(msg, reader, writer)
        except Exception as e:
            print(f"[Server] Error: {e}")
        finally:
            print(f"[Server] Disconnecting {addr}")
            if writer in self.clients:
                name = self.clients[writer]
                del self.clients[writer]
                print(f"[Server] Player {name} removed from game.")
            if writer in self.responses:
                del self.responses[writer]
            writer.close()
            await writer.wait_closed()

    async def handle_message(self, msg, reader, writer):
        msg_type = msg.get("type")
        if msg_type == "join":
            name = msg.get("name", "")
            if not name:
                await self.send_msg(writer, {"type": "error", "message": "Name required."})
                return
            self.clients[writer] = name
            await self.broadcast_players()
        elif msg_type in ("bet_response", "action_response"):
            if writer in self.clients:
                self.responses[writer] = msg
        else:
            print(f"[Server] Received: {msg}")

    async def broadcast_players(self):
        players = list(self.clients.values())
        msg = {"type": "join_ack", "players": players}
        for w in list(self.clients.keys()):
            try:
                await self.send_msg(w, msg)
            except Exception as e:
                print(f"[Server] Failed to send to client: {e}")

    async def send_msg(self, writer, msg_dict):
        data = json.dumps(msg_dict) + '\n'
        writer.write(data.encode())
        await writer.drain()

    async def recv_msg(self, reader):
        line = await reader.readline()
        if not line:
            return None
        return json.loads(line.decode())

    def get_latest_response(self, writer):
        return self.responses.pop(writer, None)

class AsyncClient:
    def __init__(self, host: str = '127.0.0.1', port: int = 8765):
        self.host = host
        self.port = port
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        print(f"[Client] Connected to {self.host}:{self.port}")

    async def send_msg(self, msg_dict):
        if self.writer is None:
            raise RuntimeError("Not connected: writer is None")
        data = json.dumps(msg_dict) + '\n'
        self.writer.write(data.encode())
        await self.writer.drain()

    async def recv_msg(self):
        if self.reader is None:
            raise RuntimeError("Not connected: reader is None")
        line = await self.reader.readline()
        if not line:
            return None
        return json.loads(line.decode()) 