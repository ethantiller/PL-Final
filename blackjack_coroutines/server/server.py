import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from game_engine import GameEngine, GameIO

class NetworkGameIO(GameIO):
    def __init__(self, player_writers, player_names):
        self.player_writers = player_writers
        self.player_names = player_names
    async def input(self, prompt: str) -> str:
        print(f"[SERVER PROMPT] {prompt}")
        return await asyncio.to_thread(input, f"[SERVER SIMULATED INPUT] {prompt}")
    def output(self, message: str):
        print(f"[SERVER BROADCAST] {message}")
        for writer in self.player_writers:
            try:
                writer.write((message + '\n').encode())
            except Exception:
                pass

connected_players = []
player_names = []
player_writers = []
accepting_players = True

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

    writer.write(b"Enter your name:\n")
    await writer.drain()
    name = (await reader.readline()).decode().strip()
    player_names.append(name)
    player_writers.append(writer)
    connected_players.append((name, writer))
    print(f"Player '{name}' joined from {addr}")

    for w in player_writers:
        w.write(f"Player '{name}' has joined the game.\n".encode())
        await w.drain()
    try:
        while accepting_players:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    print(f"Closing connection to {addr}")
    writer.close()
    await writer.wait_closed()

async def wait_for_players():
    print("Waiting for players to join...")
    print("Type 'start' to begin the game.")
    while True:
        print(f"Connected players: {player_names}")
        cmd = (await asyncio.to_thread(input, "[HOST] > ")).strip().lower()
        if cmd == 'start' and player_names:
            print("Starting the game!")
            return list(player_names)
        elif cmd == 'start':
            print("At least one player must join before starting.")
        await asyncio.sleep(0.5)

async def main():
    global accepting_players
    server = await asyncio.start_server(handle_client, '0.0.0.0', 5555)
    addr = server.sockets[0].getsockname()
    print(f"Serving on {addr}")
  
    server_task = asyncio.create_task(server.serve_forever())

    player_names_list = await wait_for_players()

    accepting_players = False
    server.close()
    await server.wait_closed()

    game_io = NetworkGameIO(player_writers, player_names_list)
    engine = GameEngine(game_io=game_io)
    await engine.start_game(player_names_list)

if __name__ == "__main__":
    asyncio.run(main())