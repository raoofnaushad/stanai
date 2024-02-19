from flask import Flask
from deepgram import Deepgram
from dotenv import load_dotenv
import os
import json
import asyncio
from aiohttp import web
from aiohttp_wsgi import WSGIHandler

load_dotenv()

app = Flask('aioflask')
dg_client = Deepgram(os.getenv('DEEPGRAM_API_KEY'))

def get_transcription_data(data):
    channel_data = data.get("channel", {}).get("alternatives", [])[0]
    transcription = {
        "start": data.get("start", 0.0),
        "duration": data.get("duration", 0.0),
        "transcript": channel_data.get("transcript", ""),
        "confidence": channel_data.get("confidence", 0.0),
        "speaker": channel_data.get("words", [])[0].get("speaker", 0) if channel_data.get("words") else 0,
        "channel": -1,
    }
    return transcription

async def process_audio(websocket: web.WebSocketResponse):
    async def get_transcript(data: dict) -> None:
        if 'channel' in data:
            transcription_data = get_transcription_data(data)
            print(transcription_data["transcript"])
            if len(transcription_data["transcript"]) > 1:                
                await websocket.send_str(json.dumps(transcription_data))

    deepgram_socket = await connect_to_deepgram(get_transcript)
    return deepgram_socket

async def connect_to_deepgram(transcript_received_handler) -> str:
    try:
        socket = await dg_client.transcription.live({ "smart_format": True,
                                                      "model": "base-general",
                                                      "language": "en-IN" ,
                                                      'diarize' : True,
                                                      'filler_words' : False,
                                                      'interim_results': False})
        socket.registerHandler(socket.event.CLOSE, lambda c: print(f'Connection closed with code {c}.'))
        socket.registerHandler(socket.event.TRANSCRIPT_RECEIVED, transcript_received_handler)
        return socket
    except Exception as e:
        raise Exception(f'Could not open socket: {e}')


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request) 

    deepgram_socket = await process_audio(ws)

    async for msg in ws:
        if msg.type == web.WSMsgType.BINARY:
            deepgram_socket.send(msg.data)

    return ws


if __name__ == "__main__":

    print("Starting Transcription Module updated....")

    loop = asyncio.get_event_loop()
    aio_app = web.Application()
    wsgi = WSGIHandler(app)
    aio_app.router.add_route('*', '/{path_info: *}', wsgi.handle_request)
    aio_app.router.add_route('GET', '/dgram/listen', websocket_handler)  # Ensure this matches your Nginx configuration
    web.run_app(aio_app, host='0.0.0.0', port=5555)
