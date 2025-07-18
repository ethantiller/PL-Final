import asyncio
import sys

class ClientGameIO:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer

    async def input(self, prompt: str) -> str:
        user_input = input(prompt)
        self.writer.write(user_input.encode() + b'\n')
        await self.writer.drain()
        return user_input

    def output(self, message: str):
        print(message)

async def listen_server(reader):
    while True:
        data = await reader.readline()
        if not data:
            print("Server closed the connection.")
            break
        print(f"[SERVER] {data.decode().strip()}")

async def main():
    server_ip = input("Enter server IP (default 127.0.0.1): ") or "127.0.0.1"
    server_port = input("Enter server port (default 5555): ") or "5555"
    try:
        server_port = int(server_port)
    except ValueError:
        print("Invalid port number.")
        return
    reader, writer = await asyncio.open_connection(server_ip, server_port)
    print(f"Connected to server at {server_ip}:{server_port}")
    # Receive prompt for name from server
    name_prompt = await reader.readline()
    print(name_prompt.decode().strip())
    name = input("Your name: ")
    writer.write(name.encode() + b'\n')
    await writer.drain()
    # Start listening to server messages
    asyncio.create_task(listen_server(reader))
    # Main loop: send user input to server
    try:
        while True:
            msg = input("")
            if msg.lower() in ("quit", "exit"):
                print("Disconnecting...")
                break
            writer.write(msg.encode() + b'\n')
            await writer.drain()
    except KeyboardInterrupt:
        print("\nDisconnected.")
    writer.close()
    await writer.wait_closed()

if __name__ == "__main__":
    asyncio.run(main()) 