import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from game_engine import GameEngine, GameIO

# Global variables for managing connections
connected_players = []  # List of (name, writer, reader)
player_names = []
player_writers = []
player_readers = []
player_connections = {}  # name -> (reader, writer)
accepting_players = True

class NetworkGameIO(GameIO):
    """Network-based game I/O handler for multiplayer blackjack."""
    
    def __init__(self, player_connections, player_names, host_name):
        """
        Initialize NetworkGameIO with player connections.
        Args:
            player_connections: Dict of player name to (reader, writer)
            player_names: List of player names
            host_name: Name of the host (for terminal input)
        """
        self.player_connections = player_connections
        self.player_names = player_names
        self.host_name = host_name
    
    async def input(self, prompt: str, player_name: str = None) -> str:
        """Get input from the correct player (host or client)."""
        if player_name is None:
            player_name = ""
        if player_name == self.host_name or player_name not in self.player_connections:
            print(f"[SERVER PROMPT] {prompt}")
            return await asyncio.to_thread(input, f"[SERVER SIMULATED INPUT] {prompt}")
        else:
            # Send prompt to the correct client
            reader, writer = self.player_connections[player_name]
            try:
                writer.write(("__PROMPT__" + prompt + '\n').encode())
                await writer.drain()
                response = await reader.readline()
                return response.decode().strip()
            except Exception as e:
                print(f"Error getting input from {player_name}: {e}")
                return ""
    
    def output(self, message: str):
        """Send output message to all connected players."""
        print(f"[SERVER BROADCAST] {message}")
        for name, (reader, writer) in self.player_connections.items():
            try:
                writer.write((message + '\n').encode())
            except Exception:
                pass

async def handle_client(reader, writer):
    global accepting_players
    addr = writer.get_extra_info('peername')
    print(f"Connection from {addr}")
    
    if not accepting_players:
        writer.write(b"Game is already starting. Try again later.\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    # Ask for player name
    writer.write(b"Enter your name:\n")
    await writer.drain()
    name = (await reader.readline()).decode().strip()
    
    # Add player to game
    player_names.append(name)
    player_writers.append(writer)
    player_readers.append(reader)
    connected_players.append((name, writer, reader))
    player_connections[name] = (reader, writer)
    print(f"Player '{name}' joined from {addr}")

    # Notify all players
    for w in player_writers:
        w.write(f"Player '{name}' has joined the game.\n".encode())
        await w.drain()
    
    # Keep connection open until game starts
    try:
        while accepting_players:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    # Do not close the connection here; keep it open for the game
    # print(f"Closing connection to {addr}")
    # writer.close()
    # await writer.wait_closed()

async def wait_for_players():
    print("Waiting for players to join...")
    host_name = str(input("Type in your name to start hosting the game: "))
    player_names.append(host_name)
    print("Type 'start' to begin the game.")
    while True:
        print(f"Connected players: {player_names}")
        cmd = (await asyncio.to_thread(input, "[HOST] > ")).strip().lower()
        if cmd == 'start' and player_names:
            print("Starting the game!")
            return list(player_names), host_name
        elif cmd == 'start':
            print("At least one player must join before starting.")
        await asyncio.sleep(0.5)

async def main():
    global accepting_players
    server = await asyncio.start_server(handle_client, '0.0.0.0', 5555)
    addr = server.sockets[0].getsockname()
    print(f"Serving on {addr}")
    server_task = asyncio.create_task(server.serve_forever())
    player_names_list, host_name = await wait_for_players()
    accepting_players = False
    server.close()
    await server.wait_closed()
    game_io = NetworkGameIO(player_connections, player_names_list, host_name)
    engine = GameEngine(game_io=game_io)
    await engine.start_game(player_names_list)

if __name__ == "__main__":
    asyncio.run(main())