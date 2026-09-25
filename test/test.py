import asyncio
import json
import sys

import websockets


async def main(token: str, conversation_id: str) -> None:
    url = f"ws://127.0.0.1:8000/ws?token={token}"

    async with websockets.connect(url) as ws:
        # 1. Expect "ready"
        ready = json.loads(await ws.recv())
        print("ready:", ready)
        assert ready["type"] == "ready"

        # 2. Ping / pong
        await ws.send(json.dumps({"type": "ping"}))
        pong = json.loads(await ws.recv())
        print("pong:", pong)
        assert pong["type"] == "pong"

        # 3. Send a message
        await ws.send(json.dumps({
            "type": "message:send",
            "conversation_id": conversation_id,
            "content": "test from python",
            "temp_id": "py-1",
        }))
        ack = json.loads(await ws.recv())
        print("ack:", ack)
        assert ack["type"] == "message:ack"
        assert ack["temp_id"] == "py-1"

        print("all tests passed")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python test_ws.py <token> <conversation_id>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
