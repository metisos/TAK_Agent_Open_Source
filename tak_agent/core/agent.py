"""Main TAK AI Agent class"""

import asyncio
import logging
import re
from typing import Optional
import xml.etree.ElementTree as ET

from .config import AgentConfig
from .tak_client import TakClient
from .cot_builder import CotBuilder

logger = logging.getLogger(__name__)


class TakAgent:
    """TAK AI Agent - connects to TAK server and handles messages"""

    def __init__(self, config: AgentConfig, llm_provider=None):
        self.config = config
        self.llm = llm_provider

        self.cot = CotBuilder(
            agent_uid=config.uid,
            agent_callsign=config.callsign,
        )

        self.client = TakClient(
            host=config.tak_server_host,
            port=config.tak_server_port,
            cert_file=config.cert_file,
            key_file=config.key_file,
            ca_file=config.ca_file,
            on_message=self._on_message,
        )

        self._running = False
        self._position_task: Optional[asyncio.Task] = None
        self._tracked_units: dict = {}  # uid -> position/info
        self._created_items: dict = {}  # uid -> item info (markers, routes we created)

    async def start(self) -> None:
        """Start the agent"""
        logger.info(f"Starting agent: {self.config.callsign} ({self.config.uid})")

        # Connect to TAK server
        if not await self.client.connect():
            raise ConnectionError("Failed to connect to TAK server")

        self._running = True

        # Send initial position
        await self._send_position()

        # Start position reporting loop
        self._position_task = asyncio.create_task(self._position_loop())

        # Announce presence
        await self._announce_online()

        logger.info(f"Agent {self.config.callsign} is online")

    async def stop(self) -> None:
        """Stop the agent"""
        self._running = False

        if self._position_task:
            self._position_task.cancel()
            try:
                await self._position_task
            except asyncio.CancelledError:
                pass

        await self.client.disconnect()
        logger.info(f"Agent {self.config.callsign} stopped")

    async def run(self) -> None:
        """Run the agent (blocking)"""
        await self.start()

        try:
            while self._running:
                if not self.client.is_connected:
                    logger.warning("Connection lost, attempting reconnect...")
                    if await self.client.reconnect():
                        await self._send_position()
                        await self._announce_online()
                    else:
                        await asyncio.sleep(10)
                else:
                    await asyncio.sleep(1)

        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()

    async def _position_loop(self) -> None:
        """Periodically send position updates"""
        interval = self.config.position_report_interval
        while self._running:
            try:
                await asyncio.sleep(interval)
                await self._send_position()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Position report error: {e}")

    async def _send_position(self) -> None:
        """Send agent position to TAK server"""
        pos = self.config.position
        cot_xml = self.cot.build_position_report(
            lat=pos["lat"],
            lon=pos["lon"],
            team=self.config.team,
            role=self.config.role,
            stale_minutes=self.config.stale_minutes,
        )
        await self.client.send(cot_xml)

    async def _announce_online(self) -> None:
        """Announce agent is online via chat"""
        message = f"{self.config.callsign} online. GEOINT support ready. Type my callsign to interact."
        await self.send_chat(message)

    async def send_chat(self, message: str, chat_room: str = "All Chat Rooms") -> bool:
        """Send a chat message"""
        pos = self.config.position
        cot_xml = self.cot.build_chat_message(
            message=message,
            chat_room=chat_room,
            lat=pos["lat"],
            lon=pos["lon"],
        )
        return await self.client.send(cot_xml)

    async def send_waypoint(
        self, name: str, lat: float, lon: float, remarks: str = ""
    ) -> bool:
        """Send a waypoint marker"""
        cot_xml = self.cot.build_waypoint(
            name=name,
            lat=lat,
            lon=lon,
            remarks=remarks,
        )
        return await self.client.send(cot_xml)

    async def send_route(self, route_name: str, waypoints: list) -> bool:
        """Send a route with waypoints"""
        cot_messages, uids = self.cot.build_route(
            route_name=route_name,
            waypoints=waypoints,
        )
        success = True
        for cot_xml in cot_messages:
            if not await self.client.send(cot_xml):
                success = False
            await asyncio.sleep(0.1)  # Small delay between messages
        if success:
            for uid in uids:
                self._track_created_item(uid, "route", route_name)
        return success

    async def send_marker(
        self,
        name: str,
        lat: float,
        lon: float,
        marker_type: str = "neutral",
        remarks: str = "",
    ) -> bool:
        """Send a map marker"""
        cot_xml, uid = self.cot.build_marker(
            name=name,
            lat=lat,
            lon=lon,
            marker_type=marker_type,
            remarks=remarks,
        )
        success = await self.client.send(cot_xml)
        if success:
            self._track_created_item(uid, "marker", name)
        return success

    async def send_polyline(
        self,
        name: str,
        points: list,
        color: str = "white",
        closed: bool = False,
    ) -> bool:
        """Send a polyline/shape to the map"""
        cot_xml = self.cot.build_polyline(
            name=name,
            points=points,
            color=color,
            closed=closed,
        )
        if cot_xml:
            return await self.client.send(cot_xml)
        return False

    async def send_circle(
        self,
        name: str,
        center_lat: float,
        center_lon: float,
        radius_meters: float,
        color: str = "yellow",
    ) -> bool:
        """Send a circle/area to the map"""
        cot_xml = self.cot.build_circle(
            name=name,
            center_lat=center_lat,
            center_lon=center_lon,
            radius_meters=radius_meters,
            color=color,
        )
        return await self.client.send(cot_xml)

    async def send_delete(self, uid: str) -> bool:
        """Delete an item from the TAK map by UID"""
        cot_xml = self.cot.build_delete(uid)
        success = await self.client.send(cot_xml)
        if success and uid in self._created_items:
            del self._created_items[uid]
        return success

    async def delete_all_created(self) -> int:
        """Delete all items created by this agent"""
        count = 0
        items_to_delete = list(self._created_items.keys())
        for uid in items_to_delete:
            if await self.send_delete(uid):
                count += 1
            await asyncio.sleep(0.1)
        return count

    def _track_created_item(self, uid: str, item_type: str, name: str) -> None:
        """Track an item we created so we can delete it later"""
        self._created_items[uid] = {
            "uid": uid,
            "type": item_type,
            "name": name,
        }

    async def _on_message(self, xml_str: str, root: ET.Element) -> None:
        """Handle incoming CoT message"""
        event_type = root.get("type", "")
        uid = root.get("uid", "")

        # Track unit positions
        if event_type.startswith("a-"):
            await self._track_unit(root)

        # Handle chat messages
        if event_type == "b-t-f":
            await self._handle_chat(root)

    async def _track_unit(self, root: ET.Element) -> None:
        """Track unit position from CoT event"""
        uid = root.get("uid", "")
        if uid == self.config.uid:
            return  # Ignore our own position

        point = root.find("point")
        detail = root.find("detail")

        if point is None:
            return

        callsign = uid
        if detail is not None:
            contact = detail.find("contact")
            if contact is not None:
                callsign = contact.get("callsign", uid)

        self._tracked_units[uid] = {
            "uid": uid,
            "callsign": callsign,
            "lat": float(point.get("lat", 0)),
            "lon": float(point.get("lon", 0)),
            "type": root.get("type", ""),
        }

    async def _handle_chat(self, root: ET.Element) -> None:
        """Handle incoming chat message"""
        detail = root.find("detail")
        if detail is None:
            return

        remarks = detail.find("remarks")
        chat = detail.find("__chat")

        if remarks is None or remarks.text is None:
            return

        message_text = remarks.text.strip()
        sender_callsign = "Unknown"

        if chat is not None:
            sender_callsign = chat.get("senderCallsign", "Unknown")

        # Ignore our own messages
        if sender_callsign == self.config.callsign:
            return

        logger.info(f"Chat from {sender_callsign}: {message_text}")

        # Let LLM analyze intent and decide whether/how to respond
        if self.llm:
            response = await self._generate_response(sender_callsign, message_text)
            if response and response.strip() and response.strip().upper() != "[NO_RESPONSE]":
                await self.send_chat(response)

    async def _generate_response(self, sender: str, message: str) -> Optional[str]:
        """Generate AI response to chat message"""
        if not self.llm:
            return f"Received your message, {sender}. LLM not configured."

        try:
            # Build context with tracked units
            context = self._build_context()

            response = await self.llm.generate(
                system_prompt=self.config.system_prompt,
                user_message=f"[From {sender}]: {message}",
                context=context,
            )

            # Process any route/waypoint commands (errors handled internally)
            try:
                await self._process_ai_actions(response)
            except Exception as e:
                logger.warning(f"Action processing error: {e}")

            # Clean up response - remove action markers before sending
            clean_response = response
            clean_response = re.sub(r'\[WAYPOINT:[^\]]+\]', '', clean_response)
            clean_response = re.sub(r'\[ROUTE:[^\]]+\]', '', clean_response)
            clean_response = re.sub(r'\[MARKER:[^\]]+\]', '', clean_response)
            clean_response = re.sub(r'\[POLYLINE:[^\]]+\]', '', clean_response)
            clean_response = re.sub(r'\[CIRCLE:[^\]]+\]', '', clean_response)
            clean_response = re.sub(r'\[DELETE_ALL\]', '', clean_response)
            clean_response = re.sub(r'\[NO_RESPONSE\]', '', clean_response)
            clean_response = clean_response.strip()

            return clean_response if clean_response else None

        except Exception as e:
            logger.error(f"LLM error: {e}")
            return f"Error processing request. Please try again."

    def _build_context(self) -> dict:
        """Build context dictionary for LLM"""
        units = []
        for uid, info in self._tracked_units.items():
            units.append({
                "callsign": info["callsign"],
                "lat": info["lat"],
                "lon": info["lon"],
                "type": "friendly" if info["type"].startswith("a-f") else "other",
            })

        return {
            "agent_callsign": self.config.callsign,
            "agent_position": self.config.position,
            "tracked_units": units,
            "unit_count": len(units),
        }

    async def _process_ai_actions(self, response: str) -> None:
        """Process any actions embedded in AI response"""

        # Check for DELETE_ALL command first
        if "[DELETE_ALL]" in response:
            count = await self.delete_all_created()
            logger.info(f"Deleted {count} items created by this agent")
            return  # Don't process other actions after delete all

        # Look for marker definitions
        # Format: [MARKER: name, lat, lon, type, remarks]
        marker_pattern = r'\[MARKER:\s*([^,]+),\s*([-\d.]+),\s*([-\d.]+),\s*([^,]+),\s*([^\]]*)\]'
        for match in re.finditer(marker_pattern, response):
            try:
                name = match.group(1).strip()
                lat = float(match.group(2))
                lon = float(match.group(3))
                marker_type = match.group(4).strip().lower()
                remarks = match.group(5).strip()
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    await self.send_marker(name, lat, lon, marker_type, remarks)
                    logger.info(f"Placed marker: {name} ({marker_type}) at {lat}, {lon}")
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse marker: {e}")

        # Look for route definitions
        # Format: [ROUTE: name | wp1_name,lat,lon | wp2_name,lat,lon | ...]
        route_pattern = r'\[ROUTE:\s*([^|]+)\|(.+?)\]'
        for match in re.finditer(route_pattern, response):
            try:
                route_name = match.group(1).strip()
                waypoints_str = match.group(2)
                waypoints = []

                for wp_str in waypoints_str.split("|"):
                    parts = wp_str.strip().split(",")
                    if len(parts) >= 3:
                        try:
                            lat = float(parts[1].strip())
                            lon = float(parts[2].strip())
                            if -90 <= lat <= 90 and -180 <= lon <= 180:
                                waypoints.append({
                                    "name": parts[0].strip(),
                                    "lat": lat,
                                    "lon": lon,
                                })
                        except ValueError:
                            continue

                if waypoints:
                    await self.send_route(route_name, waypoints)
                    logger.info(f"Created route: {route_name} with {len(waypoints)} waypoints")
            except Exception as e:
                logger.warning(f"Failed to parse route: {e}")

        # Look for waypoint coordinates in response (legacy support)
        # Format: [WAYPOINT: name, lat, lon]
        waypoint_pattern = r'\[WAYPOINT:\s*([^,]+),\s*([-\d.]+),\s*([-\d.]+)\]'
        for match in re.finditer(waypoint_pattern, response):
            try:
                name = match.group(1).strip()
                lat = float(match.group(2))
                lon = float(match.group(3))
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    await self.send_waypoint(name, lat, lon)
                    logger.info(f"Placed waypoint: {name} at {lat}, {lon}")
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse waypoint: {e}")

    def get_tracked_units(self) -> dict:
        """Get currently tracked units"""
        return self._tracked_units.copy()
