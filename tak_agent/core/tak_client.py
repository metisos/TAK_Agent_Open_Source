"""TAK Server client using asyncio and SSL"""

import asyncio
import logging
import ssl
from pathlib import Path
from typing import Callable, Optional
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class TakClient:
    """Async TAK server client with TLS support"""

    def __init__(
        self,
        host: str,
        port: int,
        cert_file: str,
        key_file: str,
        ca_file: str,
        on_message: Optional[Callable] = None,
    ):
        self.host = host
        self.port = port
        self.cert_file = Path(cert_file)
        self.key_file = Path(key_file)
        self.ca_file = Path(ca_file)
        self.on_message = on_message

        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._running = False
        self._receive_task: Optional[asyncio.Task] = None
        self._buffer = b""

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context with client certificate"""
        if not self.cert_file.exists():
            raise FileNotFoundError(f"Certificate file not found: {self.cert_file}")
        if not self.key_file.exists():
            raise FileNotFoundError(f"Key file not found: {self.key_file}")
        if not self.ca_file.exists():
            raise FileNotFoundError(f"CA file not found: {self.ca_file}")

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_cert_chain(
            certfile=str(self.cert_file),
            keyfile=str(self.key_file),
        )
        context.load_verify_locations(cafile=str(self.ca_file))
        context.check_hostname = False
        context.verify_mode = ssl.CERT_REQUIRED

        return context

    async def connect(self) -> bool:
        """Connect to TAK server"""
        try:
            ssl_context = self._create_ssl_context()
            logger.info(f"Connecting to {self.host}:{self.port}")

            self._reader, self._writer = await asyncio.open_connection(
                self.host,
                self.port,
                ssl=ssl_context,
            )

            self._connected = True
            self._running = True
            logger.info(f"Connected to TAK server at {self.host}:{self.port}")

            # Start receive loop
            self._receive_task = asyncio.create_task(self._receive_loop())

            return True

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from TAK server"""
        self._running = False

        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass

        self._connected = False
        logger.info("Disconnected from TAK server")

    async def send(self, cot_xml: str) -> bool:
        """Send CoT XML message to TAK server"""
        if not self._connected or not self._writer:
            logger.warning("Cannot send: not connected")
            return False

        try:
            # TAK uses newline-delimited XML
            message = cot_xml.strip() + "\n"
            self._writer.write(message.encode("utf-8"))
            await self._writer.drain()
            logger.debug(f"Sent: {cot_xml[:100]}...")
            return True

        except Exception as e:
            logger.error(f"Send failed: {e}")
            self._connected = False
            return False

    async def _receive_loop(self) -> None:
        """Receive and parse incoming CoT messages"""
        while self._running and self._reader:
            try:
                data = await self._reader.read(8192)
                if not data:
                    logger.warning("Connection closed by server")
                    self._connected = False
                    break

                self._buffer += data
                await self._process_buffer()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Receive error: {e}")
                self._connected = False
                break

    async def _process_buffer(self) -> None:
        """Process buffered data and extract complete CoT messages"""
        while b"</event>" in self._buffer:
            end_idx = self._buffer.find(b"</event>") + len(b"</event>")
            message = self._buffer[:end_idx]
            self._buffer = self._buffer[end_idx:]

            # Find start of XML
            start_idx = message.find(b"<?xml")
            if start_idx == -1:
                start_idx = message.find(b"<event")
            if start_idx == -1:
                continue

            message = message[start_idx:]

            try:
                xml_str = message.decode("utf-8")
                await self._handle_message(xml_str)
            except Exception as e:
                logger.error(f"Failed to process message: {e}")

    async def _handle_message(self, xml_str: str) -> None:
        """Handle a received CoT message"""
        try:
            root = ET.fromstring(xml_str)
            event_type = root.get("type", "")
            uid = root.get("uid", "")

            logger.debug(f"Received: type={event_type}, uid={uid}")

            if self.on_message:
                await self.on_message(xml_str, root)

        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def reconnect(self, delay: float = 5.0) -> bool:
        """Attempt to reconnect with delay"""
        await self.disconnect()
        logger.info(f"Reconnecting in {delay} seconds...")
        await asyncio.sleep(delay)
        return await self.connect()
