"""Constants for the Comelit Local integration."""

DOMAIN = "comelit_man"
MANUFACTURER = "Comelit"
MODEL = "6701W"

CONF_HTTP_PORT = "http_port"
CONF_ENABLE_NOTIFICATIONS = "enable_notifications"
CONF_VIDEO_QUALITY = "video_quality"
DEFAULT_VIDEO_QUALITY = "compatible"
CONF_MICROPHONE_GAIN = "microphone_gain"
DEFAULT_MICROPHONE_GAIN = "1"
MICROPHONE_GAIN_PROFILES = {
    "1": "Original (0 dB)",
    "1.2589254117941673": "+2 dB",
    "1.5": "+3.5 dB",
    "1.5848931924611136": "+4 dB",
    "2": "+6 dB",
    "2.51188643150958": "+8 dB",
    "3": "+9.5 dB",
}
# Requested device resolutions; actual output depends on the panel/firmware.
# Compatible preserves the captured 800x480 outbound / 320x240 inbound flow.
VIDEO_QUALITY_PROFILES = {
    "compatible": "Compatible (800x480 / inbound 320x240)",
    "480p": "800x480 (all calls)",
    "high": "Maximum (1024x608, 25 fps)",
}
# Opt-in: create a dedicated device user instead of reusing an existing token.
CONF_CREATE_USER = "create_dedicated_user"

DEFAULT_PORT = 64100
DEFAULT_HTTP_PORT = 8080

# Increment applied to our CTPP init timestamp to derive registration-renewal
# ACK timestamps.  PCAP-verified on the 6701W (firmware 2.x).  Community notes
# for other Comelit models report the same value for the 6742W, and one source
# claims 0x01000000 for the 6701W — not what this device does.  Parameterised
# here so a differing firmware can be accommodated without hunting literals.
# Distinct from video_call.py's _CTR_INCR_* call-counter arithmetic, which
# happens to share this value but means something else.
RENEWAL_ACK_INCREMENT = 0x01010000

# Video config sent to the device via encode_video_config().
VIDEO_WIDTH = 800
VIDEO_HEIGHT = 480
VIDEO_FPS = 16
