import asyncio
from game_engine import GameEngine
from network import AsyncServer, AsyncClient
import json

async def async_input(prompt: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)

async def networked_bet_input(server, player_name):
    """Send a bet request to the client and wait for response."""
    writer = None
    for w, n in server.clients.items():
        if n == player_name:
            writer = w
            break
    if writer is None:
        raise RuntimeError(f"No connection for player {player_name}")
    await server.send_msg(writer, {"type": "bet_request"})
    while True:
        msg = await server.recv_msg(writer._transport._protocol._stream_reader)
        if msg and msg.get("type") == "bet_response":
            return msg.get("amount")

async def networked_action_input(server, player_name, prompt):
    """Send an action request to the client and wait for response."""
    writer = None
    for w, n in server.clients.items():
        if n == player_name:
            writer = w
            break
    if writer is None:
        raise RuntimeError(f"No connection for player {player_name}")
    await server.send_msg(writer, {"type": "action_request", "prompt": prompt})
    while True:
        msg = await server.recv_msg(writer._transport._protocol._stream_reader)
        if msg and msg.get("type") == "action_response":
            return msg.get("action")

async def start_multiplayer_game(host_name, server):
    """
    Start the multiplayer game as host. Build player list and run the multiplayer game loop.
    """
    from game_engine import GameEngine
    player_names = [host_name] + list(server.clients.values())
    print(f"[Host] Starting multiplayer game with players: {player_names}")
    engine = GameEngine()
    # Build input strategy
    async def host_bet_input(prompt):
        return await async_input(prompt)
    async def host_action_input(prompt):
        return await async_input(prompt)
    player_input_strategy = {}
    for name in player_names:
        if name == host_name:
            player_input_strategy[name] = host_bet_input
        else:
            # Use networked input for remote players
            player_input_strategy[name] = lambda prompt, n=name: networked_bet_input(server, n) if 'bet' in prompt else networked_action_input(server, n, prompt)
    # Start the game
    await engine.start_game(player_names, player_input_strategy)
    print("[Host] Multiplayer game finished.")

async def host_game():
    """
    Host game logic: prompt for name, start server, accept clients, collect names, allow host to type 'start' to begin.
    """
    host_name = await async_input("Enter your name (host): ")
    server = AsyncServer()
    player_names = [host_name.strip()]  # Host is always first
    print("[Host] Starting server... Waiting for players to join.")

    # Start server in background
    server_task = asyncio.create_task(server.start())

    # Simple lobby loop: print connected players, allow 'start' to begin
    try:
        while True:
            print(f"\nCurrent players: {player_names + list(server.clients.values())}")
            cmd = await async_input("Type 'start' to begin or press Enter to refresh: ")
            if cmd.strip().lower() == 'start':
                print("[Host] Starting game...")
                await start_multiplayer_game(host_name, server)
                break
    finally:
        if server.server is not None:
            server.server.close()
            await server.server.wait_closed()
        server_task.cancel()

async def join_game():
    """
    Client flow: prompt for IP/port and name, connect to server, send name, handle lobby and game state updates.
    """
    host = await async_input("Enter server IP (default 127.0.0.1): ") or "127.0.0.1"
    port_str = await async_input("Enter server port (default 8765): ") or "8765"
    try:
        port = int(port_str)
    except ValueError:
        print("Invalid port. Exiting.")
        return
    name = await async_input("Enter your name: ")
    client = AsyncClient(host, port)
    try:
        await client.connect()
        # Send join message
        await client.send_msg({"type": "join", "name": name.strip()})
        print("[Client] Waiting for host to start the game...")
        # Lobby/game message loop
        while True:
            msg = await client.recv_msg()
            if msg is None:
                print("[Client] Disconnected from server.")
                break
            msg_type = msg.get("type")
            if msg_type == "join_ack":
                players = msg.get("players", [])
                print(f"[Lobby] Current players: {players}")
            elif msg_type == "start":
                print("[Client] Game is starting!")
                # TODO: Enter game loop (betting, actions, etc.)
                # break  # Don't break; keep listening for requests
            elif msg_type == "bet_request":
                # Prompt user for bet and send response
                while True:
                    try:
                        bet = int(await async_input("Place your bet: "))
                        break
                    except ValueError:
                        print("Please enter a valid number.")
                await client.send_msg({"type": "bet_response", "amount": bet})
            elif msg_type == "action_request":
                prompt = msg.get("prompt", "Choose your action: ")
                action = await async_input(prompt)
                await client.send_msg({"type": "action_response", "action": action})
            elif msg_type == "error":
                print(f"[Error] {msg.get('message')}")
            else:
                print(f"[Client] Received: {msg}")
    except Exception as e:
        print(f"[Client] Error: {e}")

async def start_local_game():
    """
    Start the blackjack game in local (terminal) mode.
    """
    engine = GameEngine()
    player_names = (await async_input("Enter player names (comma separated): ")).split(',')
    player_names = [name.strip() for name in player_names if name.strip()]
    await engine.start_game(player_names)

async def main():
    print("Welcome to Blackjack!")
    print("Select mode:")
    print("1. Play locally in terminal")
    print("2. Host a game on local network")
    print("3. Join a game on local network")
    mode = await async_input("Enter 1, 2, or 3: ")
    if mode == '1':
        await start_local_game()
    elif mode == '2':
        await host_game()
    elif mode == '3':
        await join_game()
    else:
        print("Invalid selection. Exiting.")

if __name__ == "__main__":
    asyncio.run(main())
    
# Dealer needs to not have his cards shown in the deal cards functions
# When it is dealers turn, it should show the hidden card first