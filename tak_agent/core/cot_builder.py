"""CoT (Cursor on Target) XML message builder for TAK"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import xml.etree.ElementTree as ET


class CotBuilder:
    """Builds CoT XML messages for TAK server communication"""

    # CoT type codes - Units
    TYPE_FRIENDLY_GROUND = "a-f-G-U-C-I"  # Friendly ground unit
    TYPE_FRIENDLY_HQ = "a-f-G-U-C"  # Friendly HQ/command
    TYPE_HOSTILE_GROUND = "a-h-G"  # Hostile ground
    TYPE_NEUTRAL = "a-n-G"  # Neutral point
    TYPE_UNKNOWN = "a-u-G"  # Unknown ground

    # CoT type codes - Points/Markers
    TYPE_WAYPOINT = "b-m-p-w"  # Waypoint
    TYPE_POINT = "b-m-p-s-p-i"  # Point of interest
    TYPE_CHECKPOINT = "b-m-p-c"  # Checkpoint

    # CoT type codes - Lines/Areas
    TYPE_ROUTE = "b-m-r"  # Route
    TYPE_DRAWING = "u-d-f"  # Freeform drawing/shape
    TYPE_POLYLINE = "u-d-f"  # Polyline (same as drawing)
    TYPE_CIRCLE = "u-d-c-c"  # Circle

    # CoT type codes - Other
    TYPE_GEOCHAT = "b-t-f"  # GeoChat message

    # Color mapping (ARGB format)
    COLORS = {
        "red": "-65536",      # 0xFFFF0000
        "green": "-16711936", # 0xFF00FF00
        "blue": "-16776961",  # 0xFF0000FF
        "yellow": "-256",     # 0xFFFFFF00
        "cyan": "-16711681",  # 0xFF00FFFF
        "white": "-1",        # 0xFFFFFFFF
        "orange": "-32768",   # 0xFFFF8000
        "black": "-16777216", # 0xFF000000
        "magenta": "-65281",  # 0xFFFF00FF
    }

    def __init__(self, agent_uid: str, agent_callsign: str):
        self.agent_uid = agent_uid
        self.agent_callsign = agent_callsign

    def _get_time_strings(self, stale_minutes: int = 10) -> tuple:
        """Generate time, start, and stale timestamps"""
        now = datetime.now(timezone.utc)
        stale = now + timedelta(minutes=stale_minutes)
        time_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        return (
            now.strftime(time_format),
            now.strftime(time_format),
            stale.strftime(time_format),
        )

    def _create_base_event(
        self,
        uid: str,
        event_type: str,
        lat: float,
        lon: float,
        hae: float = 0.0,
        stale_minutes: int = 10,
        how: str = "h-e",
    ) -> ET.Element:
        """Create base CoT event element"""
        time_str, start_str, stale_str = self._get_time_strings(stale_minutes)

        event = ET.Element("event")
        event.set("version", "2.0")
        event.set("uid", uid)
        event.set("type", event_type)
        event.set("time", time_str)
        event.set("start", start_str)
        event.set("stale", stale_str)
        event.set("how", how)

        point = ET.SubElement(event, "point")
        point.set("lat", str(lat))
        point.set("lon", str(lon))
        point.set("hae", str(hae))
        point.set("ce", "10.0")
        point.set("le", "10.0")

        return event

    def build_position_report(
        self,
        lat: float,
        lon: float,
        team: str = "Cyan",
        role: str = "HQ",
        stale_minutes: int = 10,
    ) -> str:
        """Build agent position report CoT message"""
        event = self._create_base_event(
            uid=self.agent_uid,
            event_type=self.TYPE_FRIENDLY_HQ,
            lat=lat,
            lon=lon,
            stale_minutes=stale_minutes,
            how="h-e",
        )

        detail = ET.SubElement(event, "detail")

        contact = ET.SubElement(detail, "contact")
        contact.set("callsign", self.agent_callsign)
        contact.set("endpoint", "*:-1:stcp")

        group = ET.SubElement(detail, "__group")
        group.set("name", team)
        group.set("role", role)

        takv = ET.SubElement(detail, "takv")
        takv.set("device", "Server")
        takv.set("platform", "TAK-AI-Agent")
        takv.set("os", "Linux")
        takv.set("version", "1.0.0")

        status = ET.SubElement(detail, "status")
        status.set("battery", "100")

        precisionlocation = ET.SubElement(detail, "precisionlocation")
        precisionlocation.set("altsrc", "DTED0")

        remarks = ET.SubElement(detail, "remarks")
        remarks.text = f"AI GEOINT Support Agent - Online"

        return self._to_xml_string(event)

    def build_chat_message(
        self,
        message: str,
        chat_room: str = "All Chat Rooms",
        destination_uid: Optional[str] = None,
        lat: float = 0.0,
        lon: float = 0.0,
    ) -> str:
        """Build GeoChat message CoT"""
        msg_uid = f"GeoChat.{self.agent_uid}.{chat_room}.{uuid.uuid4()}"

        event = self._create_base_event(
            uid=msg_uid,
            event_type=self.TYPE_GEOCHAT,
            lat=lat,
            lon=lon,
            stale_minutes=60 * 24,  # Chat messages stay for 24 hours
            how="h-g-i-g-o",
        )

        # Override point for chat (high CE/LE values)
        point = event.find("point")
        point.set("ce", "9999999.0")
        point.set("le", "9999999.0")

        detail = ET.SubElement(event, "detail")

        # Chat metadata
        chat = ET.SubElement(detail, "__chat")
        chat.set("parent", "RootContactGroup")
        chat.set("groupOwner", "false")
        chat.set("chatroom", chat_room)
        chat.set("id", chat_room)
        chat.set("senderCallsign", self.agent_callsign)

        chatgrp = ET.SubElement(chat, "chatgrp")
        chatgrp.set("uid0", self.agent_uid)
        chatgrp.set("uid1", destination_uid or chat_room)
        chatgrp.set("id", chat_room)

        # Link to sender
        link = ET.SubElement(detail, "link")
        link.set("uid", self.agent_uid)
        link.set("type", self.TYPE_FRIENDLY_HQ)
        link.set("relation", "p-p")

        # Message content
        time_str, _, _ = self._get_time_strings()
        remarks = ET.SubElement(detail, "remarks")
        remarks.set("source", self.agent_uid)
        remarks.set("sourceID", self.agent_uid)
        remarks.set("time", time_str)
        remarks.text = message

        return self._to_xml_string(event)

    def build_waypoint(
        self,
        name: str,
        lat: float,
        lon: float,
        remarks: str = "",
        waypoint_type: str = "waypoint",
        uid: Optional[str] = None,
    ) -> str:
        """Build a waypoint/marker CoT message"""
        wp_uid = uid or f"{self.agent_uid}-WP-{uuid.uuid4().hex[:8]}"

        event = self._create_base_event(
            uid=wp_uid,
            event_type=self.TYPE_WAYPOINT,
            lat=lat,
            lon=lon,
            stale_minutes=60 * 24,  # 24 hours
            how="h-g-i-g-o",
        )

        detail = ET.SubElement(event, "detail")

        contact = ET.SubElement(detail, "contact")
        contact.set("callsign", name)

        remarks_elem = ET.SubElement(detail, "remarks")
        remarks_elem.text = remarks or f"Waypoint placed by {self.agent_callsign}"

        link = ET.SubElement(detail, "link")
        link.set("uid", self.agent_uid)
        link.set("type", self.TYPE_FRIENDLY_HQ)
        link.set("relation", "p-p")
        link.set("production_time", self._get_time_strings()[0])

        color = ET.SubElement(detail, "color")
        color.set("argb", "-1")  # White

        precisionlocation = ET.SubElement(detail, "precisionlocation")
        precisionlocation.set("altsrc", "DTED0")

        return self._to_xml_string(event)

    def build_route(
        self,
        route_name: str,
        waypoints: list,
        route_uid: Optional[str] = None,
        color: str = "white",
    ) -> tuple:
        """
        Build a route with connected waypoints for ATAK.

        Args:
            route_name: Name of the route
            waypoints: List of dicts with keys: name, lat, lon, remarks (optional)
            route_uid: Optional UID for the route
            color: Route line color

        Returns:
            Tuple of (list of CoT XML strings, list of all UIDs created)
        """
        route_uid = route_uid or f"{self.agent_uid}-RTE-{uuid.uuid4().hex[:8]}"
        color_argb = self.COLORS.get(color.lower(), "-1")
        cot_messages = []
        all_uids = []
        waypoint_uids = []

        # Create individual checkpoint waypoints
        for i, wp in enumerate(waypoints):
            wp_uid = f"{route_uid}.{i}"
            waypoint_uids.append(wp_uid)
            all_uids.append(wp_uid)

            wp_name = wp.get("name", f"WP{i}")

            # Use checkpoint type for route waypoints
            event = self._create_base_event(
                uid=wp_uid,
                event_type="b-m-p-c",  # Checkpoint type
                lat=wp["lat"],
                lon=wp["lon"],
                stale_minutes=60 * 24,
                how="h-g-i-g-o",
            )

            detail = ET.SubElement(event, "detail")

            contact = ET.SubElement(detail, "contact")
            contact.set("callsign", wp_name)

            remarks_elem = ET.SubElement(detail, "remarks")
            remarks_elem.text = wp.get("remarks", f"{route_name} - Point {i+1}")

            link = ET.SubElement(detail, "link")
            link.set("uid", route_uid)
            link.set("type", "b-m-r")
            link.set("relation", "c")

            color_elem = ET.SubElement(detail, "color")
            color_elem.set("argb", color_argb)

            cot_messages.append(self._to_xml_string(event))

        # Create route object linking all waypoints
        if len(waypoints) >= 2:
            first_wp = waypoints[0]
            event = self._create_base_event(
                uid=route_uid,
                event_type="b-m-r",  # Route type
                lat=first_wp["lat"],
                lon=first_wp["lon"],
                stale_minutes=60 * 24,
                how="h-g-i-g-o",
            )

            detail = ET.SubElement(event, "detail")

            contact = ET.SubElement(detail, "contact")
            contact.set("callsign", route_name)

            remarks = ET.SubElement(detail, "remarks")
            remarks.text = f"Route created by {self.agent_callsign}"

            # Stroke color for route line
            strokeColor = ET.SubElement(detail, "strokeColor")
            strokeColor.set("value", color_argb)

            strokeWeight = ET.SubElement(detail, "strokeWeight")
            strokeWeight.set("value", "3.0")

            # Route info
            routeinfo = ET.SubElement(detail, "__routeinfo")
            routeinfo.set("type", "Ground")

            # Link each waypoint with point coordinates
            for i, (wp_uid, wp) in enumerate(zip(waypoint_uids, waypoints)):
                link = ET.SubElement(detail, "link")
                link.set("uid", wp_uid)
                link.set("callsign", wp.get("name", f"WP{i}"))
                link.set("type", "b-m-p-c")
                link.set("point", f"{wp['lat']},{wp['lon']},0.0")
                link.set("relation", "c")

            # Archive to persist
            archive = ET.SubElement(detail, "archive")

            cot_messages.append(self._to_xml_string(event))
            all_uids.append(route_uid)

        return (cot_messages, all_uids)

    def build_marker(
        self,
        name: str,
        lat: float,
        lon: float,
        marker_type: str = "neutral",
        remarks: str = "",
        color: str = "-1",
        uid: Optional[str] = None,
    ) -> tuple:
        """Build a point marker on the map. Returns (xml_string, uid)"""
        marker_uid = uid or f"{self.agent_uid}-MRK-{uuid.uuid4().hex[:8]}"

        type_map = {
            "friendly": self.TYPE_FRIENDLY_GROUND,
            "hostile": self.TYPE_HOSTILE_GROUND,
            "neutral": self.TYPE_NEUTRAL,
            "unknown": self.TYPE_UNKNOWN,
        }
        cot_type = type_map.get(marker_type, self.TYPE_NEUTRAL)

        event = self._create_base_event(
            uid=marker_uid,
            event_type=cot_type,
            lat=lat,
            lon=lon,
            stale_minutes=60 * 24,
            how="h-g-i-g-o",
        )

        detail = ET.SubElement(event, "detail")

        contact = ET.SubElement(detail, "contact")
        contact.set("callsign", name)

        remarks_elem = ET.SubElement(detail, "remarks")
        remarks_elem.text = remarks or f"Marker placed by {self.agent_callsign}"

        color_elem = ET.SubElement(detail, "color")
        color_elem.set("argb", color)

        link = ET.SubElement(detail, "link")
        link.set("uid", self.agent_uid)
        link.set("type", self.TYPE_FRIENDLY_HQ)
        link.set("relation", "p-p")

        return (self._to_xml_string(event), marker_uid)

    def build_polyline(
        self,
        name: str,
        points: List[dict],
        color: str = "white",
        closed: bool = False,
    ) -> str:
        """
        Build a polyline/shape on the map.

        Args:
            name: Name of the polyline
            points: List of dicts with lat, lon keys
            color: Color name (red, green, blue, yellow, cyan, white, orange)
            closed: If True, connects last point to first (polygon)

        Returns:
            CoT XML string
        """
        if len(points) < 2:
            return ""

        line_uid = f"{self.agent_uid}-LINE-{uuid.uuid4().hex[:8]}"
        color_argb = self.COLORS.get(color.lower(), "-1")

        # Use first point as the event location
        first_point = points[0]

        event = self._create_base_event(
            uid=line_uid,
            event_type=self.TYPE_POLYLINE,
            lat=first_point["lat"],
            lon=first_point["lon"],
            stale_minutes=60 * 24,
            how="h-g-i-g-o",
        )

        detail = ET.SubElement(event, "detail")

        contact = ET.SubElement(detail, "contact")
        contact.set("callsign", name)

        remarks = ET.SubElement(detail, "remarks")
        remarks.text = f"Created by {self.agent_callsign}"

        # Stroke style
        strokeColor = ET.SubElement(detail, "strokeColor")
        strokeColor.set("value", color_argb)

        strokeWeight = ET.SubElement(detail, "strokeWeight")
        strokeWeight.set("value", "3.0")

        # Fill for closed shapes
        if closed:
            fillColor = ET.SubElement(detail, "fillColor")
            fillColor.set("value", color_argb)

        # Link element with points
        link = ET.SubElement(detail, "link")
        link.set("uid", self.agent_uid)
        link.set("type", self.TYPE_FRIENDLY_HQ)
        link.set("relation", "p-p")

        # Add all points as link elements with point attribute
        for i, pt in enumerate(points):
            pt_link = ET.SubElement(detail, "link")
            pt_link.set("point", f"{pt['lat']},{pt['lon']}")

        # Close the shape if requested
        if closed and len(points) > 2:
            pt_link = ET.SubElement(detail, "link")
            pt_link.set("point", f"{points[0]['lat']},{points[0]['lon']}")

        # Labels element
        labels = ET.SubElement(detail, "labels_on")
        labels.set("value", "true")

        return self._to_xml_string(event)

    def build_circle(
        self,
        name: str,
        center_lat: float,
        center_lon: float,
        radius_meters: float,
        color: str = "yellow",
    ) -> str:
        """
        Build a circle/area on the map using ATAK-compatible format.

        Args:
            name: Name of the circle
            center_lat: Center latitude
            center_lon: Center longitude
            radius_meters: Radius in meters
            color: Color name

        Returns:
            CoT XML string
        """
        circle_uid = f"{self.agent_uid}-CIR-{uuid.uuid4().hex[:8]}"
        color_argb = self.COLORS.get(color.lower(), "-256")

        # Use drawing type for shapes
        event = self._create_base_event(
            uid=circle_uid,
            event_type="u-d-f",  # Freeform drawing type works better for shapes
            lat=center_lat,
            lon=center_lon,
            stale_minutes=60 * 24,
            how="h-g-i-g-o",
        )

        detail = ET.SubElement(event, "detail")

        contact = ET.SubElement(detail, "contact")
        contact.set("callsign", name)

        remarks = ET.SubElement(detail, "remarks")
        remarks.text = f"Created by {self.agent_callsign}"

        # Stroke style - must come before shape
        strokeColor = ET.SubElement(detail, "strokeColor")
        strokeColor.set("value", color_argb)

        strokeWeight = ET.SubElement(detail, "strokeWeight")
        strokeWeight.set("value", "4.0")

        # Semi-transparent fill
        base_color = int(color_argb)
        if base_color < 0:
            base_color = base_color & 0xFFFFFFFF
        semi_transparent = (0x40 << 24) | (base_color & 0x00FFFFFF)
        if semi_transparent > 0x7FFFFFFF:
            semi_transparent = semi_transparent - 0x100000000

        fillColor = ET.SubElement(detail, "fillColor")
        fillColor.set("value", str(semi_transparent))

        # Shape element for circle - ATAK format
        shape = ET.SubElement(detail, "shape")

        ellipse = ET.SubElement(shape, "ellipse")
        ellipse.set("major", str(radius_meters))
        ellipse.set("minor", str(radius_meters))
        ellipse.set("angle", "0")

        # Labels
        labels = ET.SubElement(detail, "labels_on")
        labels.set("value", "true")

        link = ET.SubElement(detail, "link")
        link.set("uid", self.agent_uid)
        link.set("type", self.TYPE_FRIENDLY_HQ)
        link.set("relation", "p-p")

        # Archive flag to persist the shape
        archive = ET.SubElement(detail, "archive")

        return self._to_xml_string(event)

    def build_delete(self, uid: str) -> str:
        """
        Build a delete message for removing an item from TAK.

        Args:
            uid: The UID of the item to delete

        Returns:
            CoT XML string that will remove the item
        """
        # Use past time to mark as expired/deleted
        now = datetime.now(timezone.utc)
        past = now - timedelta(minutes=5)
        time_format = "%Y-%m-%dT%H:%M:%S.%fZ"

        event = ET.Element("event")
        event.set("version", "2.0")
        event.set("uid", uid)
        event.set("type", "t-x-d-d")  # Delete type
        event.set("time", now.strftime(time_format))
        event.set("start", past.strftime(time_format))
        event.set("stale", past.strftime(time_format))  # Already stale = delete
        event.set("how", "h-g-i-g-o")

        point = ET.SubElement(event, "point")
        point.set("lat", "0.0")
        point.set("lon", "0.0")
        point.set("hae", "0.0")
        point.set("ce", "9999999.0")
        point.set("le", "9999999.0")

        detail = ET.SubElement(event, "detail")

        return self._to_xml_string(event)

    def _to_xml_string(self, element: ET.Element) -> str:
        """Convert ElementTree element to XML string"""
        return '<?xml version="1.0" encoding="UTF-8"?>' + ET.tostring(
            element, encoding="unicode"
        )
