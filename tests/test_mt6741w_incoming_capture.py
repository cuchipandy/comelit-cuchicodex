"""Control-message regressions from the official app's two real incoming calls.

The 2026-11-01 PCAP remains private. Only signaling bytes are reproduced here;
no credentials, audio, video or cloud tunnel identifiers are included.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.comelit_man.channels import Channel, ChannelType
from custom_components.comelit_man.protocol import (
    encode_answer_peer,
    encode_call_accepted,
    encode_call_ack,
    encode_door_open_during_video,
)
from custom_components.comelit_man.video_call import VideoCallSession

# Second call: X pressed at 14:53:27.776, final peer at 14:53:29.156.
RELEASE = [
    "4018822c23020003000e0000ffffffff5342303030303034310053423030303030340000",
    "4018822c2402000a001198020000000073080000ffffffff5342303030303034310053423030303030340000",
    "4018822c2502001a00119402000000007608000000000000000000000000000000000000ffffffff5342303030303034310053423030303030340000",
    "6018822c2602000e00705342303030303034310000000000ffffffff5342303030303034310053423030303030340000",
]
ACKS = [
    "0018022c02240000ffffffff5342303030303034000053423030303030343100",
    "2018022c02240000ffffffff5342303030303034000053423030303030343100",
    "0018022c02250000ffffffff5342303030303034000053423030303030343100",
    "0018022c02250000ffffffff5342303030303034000053423030303030343100",
    "0018022c02260000ffffffff5342303030303034000053423030303030343100",
    "0018022c02270000ffffffff5342303030303034000053423030303030343100",
]


def test_incoming_accept_and_door_match_the_new_real_call_capture():
    assert encode_call_ack("SB0000041", "SB000004", 0x75950B95, codec_param=0x27) == bytes.fromhex(
        "4018950b957500080003490027000000ffffffff5342303030303034310053423030303030340000"
    )
    assert encode_answer_peer("SB0000041", "SB000004", 0x001F2C82, inbound=True) == bytes.fromhex(
        "4018822c1f00000e00705342303030303034310001000000ffffffff5342303030303034310053423030303030340000"
    )
    assert encode_call_accepted("SB0000041", "SB000004", 0x00202C82) == bytes.fromhex(
        "4018822c20000002000c0000ffffffff5342303030303034310053423030303030340000"
    )
    assert encode_door_open_during_video("SB0000041", "SB100001", 0x02222C82, 1, callee="SB000004") == bytes.fromhex(
        "4018822c2202000d002d5342313030303031000001000000ffffffff5342303030303034310053423030303030340000"
    )


def session_with_capture():
    client = MagicMock()
    ctpp = Channel("CTPP", ChannelType.UAUT, 1, server_channel_id=0x086F, is_open=True)
    channels = {
        "CTPP": ctpp,
        "RTPC": Channel("RTPC", ChannelType.UAUT, 2, server_channel_id=0x0873, is_open=True),
        "RTPC2": Channel("RTPC2", ChannelType.UAUT, 3, server_channel_id=0x0876, is_open=True),
    }
    client.get_channel.side_effect = channels.get
    client.close_media_channel = AsyncMock()
    client.send_binary = AsyncMock()
    client.read_response = AsyncMock(side_effect=[bytes.fromhex(body) for body in ACKS])
    session = VideoCallSession(client, MagicMock(apt_address="SB000004", apt_subaddress=1))
    session._inbound = True
    session._active = True
    session._device_rtpc_req_id = 0xCDDE
    session._call_counter = 0x02222C82
    session._rtp_receiver = MagicMock(stop=AsyncMock())
    session._cleanup = AsyncMock()
    return session, client


async def test_answered_incoming_release_matches_x_and_accepts_early_completion():
    session, client = session_with_capture()
    session._ctpp_task = asyncio.create_task(asyncio.sleep(30))
    await session.stop()
    session._rtp_receiver.stop.assert_awaited_once()
    assert [call.args[0] for call in client.close_media_channel.await_args_list] == ["RTPC", "RTPC2", "UDPM"]
    assert [call.args[1] for call in client.send_binary.await_args_list] == [bytes.fromhex(body) for body in RELEASE]
    # Ignore the early 0x1820 and duplicate RTPC-link ACK, rather than allowing
    # them to acknowledge the next transition or waiting for a second 0x1820.
    assert client.read_response.await_count == len(ACKS)
    session._cleanup.assert_awaited_once()


@pytest.mark.parametrize("failure", ["send", "read"])
async def test_incoming_release_failure_still_cleans_up(failure):
    session, client = session_with_capture()
    getattr(client, "send_binary" if failure == "send" else "read_response").side_effect = OSError
    await session.stop()
    session._cleanup.assert_awaited_once()


async def test_unanswered_preview_does_not_send_an_answered_call_release():
    session, client = session_with_capture()
    session._device_rtpc_req_id = 0
    await session.stop()
    client.send_binary.assert_not_awaited()
    session._cleanup.assert_awaited_once()


async def test_mic_starts_after_device_link_without_waiting_for_late_peer():
    session, client = session_with_capture()
    session._device_rtpc_req_id = 0
    session._inbound_device_rtpc = Channel("RTPC_DEVICE", ChannelType.UAUT, 0, server_channel_id=0xCDDE)
    session._inbound_device_rtpc.open_event.set()
    session._rtp_receiver.start_audio_sender = MagicMock()
    link = bytes.fromhex("4018022c0021000a0011180200000000decd0000ffffffff5342303030303034000053423030303030343100")

    async def send(_channel, body):
        if body[6:10] == b"\x00\x02\x00\x0c":
            await session._answer_handoff.put(link)

    client.send_binary.side_effect = send
    # The peer is deliberately absent: it comes much later in the real PCAP.
    await asyncio.wait_for(session.answer_inbound(), timeout=0.25)
    assert session._answer_handoff is None
    assert session._rtp_receiver.start_audio_sender.call_args.args[0] == 0xCDDE
    peer = bytes.fromhex(
        "4018022c0122000e00705342313030303031000001000000ffffffff5342303030303034000053423030303030343100"
    )
    await session._ack_active_message(client, client.get_channel("CTPP"), "SB0000041", "SB000004", peer)
    ack = client.send_binary.await_args.args[1]
    assert ack == bytes.fromhex("0018822c22020000ffffffff5342303030303034310053423030303030340000")


async def test_incoming_session_door_uses_entrance_relay_and_apartment_callee():
    session, client = session_with_capture()
    session._call_counter = 0x02212C82
    await session.async_open_door_on_ctpp("SB0000041", "SB100001", 1)
    assert client.send_binary.await_args.args[1] == bytes.fromhex(
        "4018822c2202000d002d5342313030303031000001000000ffffffff5342303030303034310053423030303030340000"
    )
