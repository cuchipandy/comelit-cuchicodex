"""Regressions from the MT-6741W app's manual listen/talk capture.

Only protocol bytes are reproduced; no PCAP, authentication or audio is stored.
"""

import asyncio
import struct
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.comelit_man.channels import Channel, ChannelType
from custom_components.comelit_man.client import IconaBridgeClient
from custom_components.comelit_man.protocol import encode_answer_peer, encode_call_end, encode_media_end
from custom_components.comelit_man.rtp_receiver import RtpReceiver, _build_control_packet
from custom_components.comelit_man.video_call import VideoCallSession


def test_manual_audio_peer_matches_captured_48_byte_wire_format():
    expected = bytes.fromhex(
        "40 18 06 ae fe db 00 0e 00 70 "
        "53 42 30 30 30 30 30 36 31 00 01 00 00 00 ff ff ff ff "
        "53 42 30 30 30 30 30 36 31 00 53 42 31 30 30 30 30 31 00 00"
    )
    assert encode_answer_peer("SB0000061", "SB100001", 0xDBFEAE06, extended=True) == expected


def test_udp_discovery_switches_to_media_ready_after_two_probes():
    assert _build_control_packet(0x1234, 0x5678, 0)[12] == 0
    assert _build_control_packet(0x1234, 0x5678, 1)[12] == 0
    assert _build_control_packet(0x1234, 0x5678, 2)[12] == 1
    # Sequence byte wraps, while the media-ready state remains asserted.
    assert _build_control_packet(0x1234, 0x5678, 256)[11:13] == b"\x00\x01"


def test_media_end_and_ack_match_captured_control_channel_packets():
    assert encode_media_end(0x1234) == bytes.fromhex("00 06 0a 00 00 00 00 00 ef 01 03 00 02 00 00 00 34 12")
    assert encode_media_end(0x1234, response=True) == bytes.fromhex(
        "00 06 0c 00 00 00 00 00 ef 01 04 00 04 00 00 00 34 12 00 00"
    )


async def test_media_close_releases_the_device_udp_mapping_and_registry_entry():
    client = IconaBridgeClient("127.0.0.1")
    client._channels["UDPM"] = Channel("UDPM", ChannelType.UAUT, 1, server_channel_id=0x1234, is_open=True)
    client._send = AsyncMock()
    await client.close_media_channel("UDPM")
    client._send.assert_awaited_once_with(encode_media_end(0x1234))
    assert "UDPM" not in client._channels
    await client.close_media_channel("missing")
    client._channels["pending"] = Channel("pending", ChannelType.UAUT, 0)
    await client.close_media_channel("pending")
    assert client._send.await_count == 1


def test_device_microphone_channel_close_is_acknowledged():
    client = IconaBridgeClient("127.0.0.1")
    client._writer = MagicMock()
    channel = Channel("RTPC_DEVICE", ChannelType.UAUT, 0, server_channel_id=0x1234, is_open=True)
    client._channels["RTPC_DEVICE"] = channel
    client._dispatch_command_response(encode_media_end(0x1234)[8:])
    client._writer.write.assert_called_once_with(encode_media_end(0x1234, response=True))
    assert not channel.is_open


def test_startup_grace_does_not_restart_a_panel_still_opening_video():
    session = VideoCallSession(MagicMock(), MagicMock())
    session._rtp_receiver = RtpReceiver("127.0.0.1")
    with patch("custom_components.comelit_man.video_call.time.monotonic", return_value=110):
        assert not session._recover_stalled_video(100)


def test_only_outbound_audio_requests_a_panel_release_interval():
    session = VideoCallSession(MagicMock(), MagicMock())
    assert not session.manual_audio_used
    session._device_rtpc_req_id = 0x1234
    assert session.manual_audio_used
    session._inbound = True
    assert not session.manual_audio_used


def test_udp_audio_arrives_on_rtpc1_independently_of_video_rtpc2():
    receiver = RtpReceiver("127.0.0.1", media_req_id=0x1235)
    receiver.set_audio_req_id(0x1234)
    audio_queue = asyncio.Queue()
    receiver.attach_rtsp_queues(asyncio.Queue(), audio_queue)
    audio = bytes([0xD5] * 160)
    rtp = struct.pack("!BBHII", 0x80, 8, 1, 0, 1) + audio
    packet = struct.pack("<2sHHH", b"\x00\x06", len(rtp), 0x1234, 0) + rtp
    receiver._on_udp_packet(packet)
    assert receiver._audio_packet_count == 1
    assert receiver.video_packet_count == 0
    assert audio_queue.get_nowait() == audio


@pytest.mark.parametrize("tcp", [False, True])
async def test_manual_audio_uses_current_device_channel_and_rtsp_backchannel(tcp):
    client = MagicMock()
    client.send_binary = AsyncMock()
    session = VideoCallSession(client, MagicMock(), rtsp_server=MagicMock())
    receiver = MagicMock()
    receiver.tcp_media_packet_count = int(tcp)
    session._rtp_receiver = receiver
    device_channel = MagicMock(server_channel_id=0x2468, is_open=True)
    session._outbound_device_rtpc = device_channel
    session._start_outbound_audio()
    receiver.attach_backchannel_queue.assert_called_once_with(session._rtsp_server.backchannel_queue)
    args, kwargs = receiver.start_audio_sender.call_args
    assert args == (0x2468,)
    assert kwargs["restart"] is True
    if tcp:
        await kwargs["tcp_send"](b"microphone")
        client.send_binary.assert_awaited_once_with(device_channel, b"microphone")
    else:
        assert kwargs["tcp_send"] is None


async def test_renewal_replaces_sender_bound_to_retired_rtpc_channel():
    receiver = RtpReceiver("127.0.0.1")
    with patch.object(receiver, "_audio_send_loop", new=AsyncMock()) as send:
        receiver.start_audio_sender(0x1234)
        old = receiver._audio_sender_task
        receiver.start_audio_sender(0x5678, restart=True)
        new = receiver._audio_sender_task
        await asyncio.sleep(0)
        assert old.cancelled()
        assert new is not old
        send.assert_awaited_once_with(0x5678, None)


@pytest.mark.parametrize("failure", [None, "send", "missing_channel"])
async def test_closing_manual_view_hangs_up_without_blocking_cleanup(failure):
    client = MagicMock()
    client.send_binary = AsyncMock(side_effect=OSError if failure == "send" else None)
    client.close_media_channel = AsyncMock()
    client.read_response = AsyncMock(side_effect=[b"\x00\x18" + bytes(6)] * 4 + [b"\x20\x18" + bytes(6)])
    if failure == "missing_channel":
        client.get_channel.return_value = None
    config = MagicMock(apt_address="SB000006", apt_subaddress=1)
    session = VideoCallSession(client, config)
    session._active = True
    session._outbound_device_rtpc = MagicMock()
    session._outbound_entrance = "SB100001"
    session._call_counter = 0xDAFFAE06
    session._ctpp_task = asyncio.create_task(asyncio.sleep(30))
    session._answer_task = asyncio.create_task(asyncio.sleep(30))
    session._cleanup = AsyncMock()
    await session.stop()
    session._cleanup.assert_awaited_once()
    if failure != "missing_channel":
        packet = client.send_binary.call_args_list[0].args[1]
        assert packet == encode_call_end("SB0000061", "SB100001", 0xDB00AE06)
        assert packet[6:12] == b"\x00\x03\x00\x0e\x00\x00"
        if failure is None:
            sent = [call.args[1] for call in client.send_binary.call_args_list]
            assert len(sent) == 4
            assert sent[1][10:12] == b"\x98\x02"
            assert sent[2][10:16] == b"\x94\x02\x00\x00\x00\x00"
            assert sent[2][18:36] == bytes(18)
            assert sent[3][:2] == b"\x60\x18"
            assert sent[3][20:24] == bytes(4)
