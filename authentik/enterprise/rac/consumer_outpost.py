"""RAC consumer"""
from channels.exceptions import ChannelFull
from channels.generic.websocket import AsyncWebsocketConsumer

from authentik.enterprise.rac.consumer_client import RAC_CLIENT_GROUP


class RACOutpostConsumer(AsyncWebsocketConsumer):
    """Consumer the outpost connects to, to send specific data back to a client connection"""

    dest_channel_id: str

    async def connect(self):
        self.dest_channel_id = self.scope["url_route"]["kwargs"]["channel"]
        await self.accept()
        await self.channel_layer.group_send(
            RAC_CLIENT_GROUP,
            {
                "type": "event.outpost.connected",
                "outpost_channel": self.channel_name,
                "client_channel": self.dest_channel_id,
            },
        )

    async def receive(self, text_data=None, bytes_data=None):
        """Mirror data received from guacd running in the outpost
        to the dest_channel_id which is the channel talking to the browser"""
        # print(f"outpost - receive - {text_data[:50]}")
        try:
            await self.channel_layer.send(
                self.dest_channel_id,
                {
                    "type": "event.send",
                    "text_data": text_data,
                    "bytes_data": bytes_data,
                },
            )
        except ChannelFull:
            pass

    async def event_send(self, event: dict):
        """Handler called by client websocket that sends data to this specific
        outpost connection"""
        # print(f"outpost - send - {event['text_data'][:50]}")
        await self.send(text_data=event.get("text_data"), bytes_data=event.get("bytes_data"))