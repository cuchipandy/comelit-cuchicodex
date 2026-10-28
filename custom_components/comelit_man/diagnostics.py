"""Diagnostics support for Comelit Man."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_VIDEO_QUALITY, DEFAULT_VIDEO_QUALITY
from .coordinator import ComelitLocalConfigEntry

REDACT_KEYS = {"token", "password"}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ComelitLocalConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    video = coordinator.video_session
    receiver = video.rtp_receiver if video else None
    rtsp = coordinator.rtsp_server
    return {
        "config": async_redact_data(dict(entry.data), REDACT_KEYS),
        "device_config": (
            {
                "apt_address": coordinator.device_config.apt_address,
                "apt_subaddress": coordinator.device_config.apt_subaddress,
                "caller_address": coordinator.device_config.caller_address,
                "door_count": len(coordinator.device_config.doors),
                "camera_count": len(coordinator.device_config.cameras),
            }
            if coordinator.device_config
            else None
        ),
        "connection": {
            "connected": bool(coordinator._client and coordinator._client.connected),
            "connection_lost": coordinator._connection_lost,
            "vip_listener_active": coordinator._vip_listener is not None,
        },
        "video": {
            "requested_quality": entry.options.get(CONF_VIDEO_QUALITY, DEFAULT_VIDEO_QUALITY),
            "received_dimensions": receiver.video_dimensions if receiver else None,
            "audio_rx_packets": receiver._audio_packet_count if receiver else 0,
            "mic_rx_packets": rtsp.backchannel_rx_count if rtsp else 0,
            "mic_tx_frames": receiver.audio_tx_real_count if receiver else 0,
            "silence_tx_frames": receiver.audio_tx_silence_count if receiver else 0,
            "session_active": bool(coordinator.video_session and coordinator.video_session.active),
            "rtsp_url": coordinator.rtsp_url,
            "rtsp_server_running": coordinator.rtsp_server is not None,
        },
    }
