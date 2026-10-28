const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

function deferred() {
  let resolve;
  const promise = new Promise((r) => { resolve = r; });
  return { promise, resolve };
}

function setup(getUserMedia) {
  let Card;
  const audio = [];
  const track = { enabled: true, stopped: false, stop() { this.stopped = true; } };
  const stream = { getAudioTracks: () => [track], getTracks: () => [track] };
  const context = vm.createContext({
    console: { info() {}, warn() {} },
    HTMLElement: class { attachShadow() { this.shadowRoot = { getElementById: () => null }; } },
    customElements: { get() {}, define(name, value) { Card = value; } },
    window: { customCards: [] },
    navigator: { mediaDevices: getUserMedia === null ? undefined : { getUserMedia: getUserMedia || (async () => stream) } },
    RTCRtpSender: { getCapabilities: () => ({ codecs: [
      { mimeType: "audio/opus" }, { mimeType: "audio/PCMU" }, { mimeType: "audio/PCMA" },
    ] }) },
    RTCPeerConnection: class {
      addTransceiver(kind, options) {
        const result = { kind, options, setCodecPreferences(codecs) { this.codecs = codecs; } };
        if (kind !== "video") audio.push(result);
        return result;
      }
      async createOffer() { return { sdp: "v=0\r\n" }; }
      async setLocalDescription(offer) { this.localDescription = offer; }
      close() {}
    },
    MediaStream: class {},
    setTimeout: (fn) => { fn(); return 1; },
    clearTimeout() {},
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, "../custom_components/comelit_man/www/comelit-doorbell-card.js"), "utf8"), context);
  const card = new Card();
  card._config = { camera_entity: "camera.intercom" };
  card._hass = { connection: {
    sendMessagePromise: async () => ({}),
    subscribeMessage: async () => () => {},
  } };
  card._state = "ringing";
  return { card, track, stream, audio };
}

test("ringing keeps the mic muted and negotiates only G.711, preferring PCMA", async () => {
  const { card, track, audio } = setup();
  await card._startWebrtc();
  assert.equal(track.enabled, false);
  assert.equal(audio[0].options.direction, "sendrecv");
  assert.deepEqual(Array.from(audio[0].codecs, (c) => c.mimeType), ["audio/PCMA", "audio/PCMU"]);
});

test("answer while permission is pending enables the track when capture completes", async () => {
  const pending = deferred();
  const capturing = deferred();
  const { card, track, stream } = setup(() => { capturing.resolve(); return pending.promise; });
  const starting = card._startWebrtc();
  await capturing.promise;
  await card._answer();
  pending.resolve(stream);
  await starting;
  assert.equal(track.enabled, true);
});

test("reconnecting an answered call restores microphone transmission", async () => {
  const { card, track } = setup();
  card._state = "answered";
  card._setMicEnabled(true);
  await card._startWebrtc();
  assert.equal(track.enabled, true);
});

test("reconnecting preserves an intentionally muted microphone", async () => {
  const { card, track } = setup();
  card._state = "answered";
  card._setMicEnabled(false);
  await card._startWebrtc();
  assert.equal(track.enabled, false);
});

test("dismiss during capture stops late tracks and prevents stale signaling", async () => {
  const pending = deferred();
  const capturing = deferred();
  const { card, track, stream } = setup(() => { capturing.resolve(); return pending.promise; });
  const starting = card._startWebrtc();
  await capturing.promise;
  card._teardownWebrtc();
  pending.resolve(stream);
  await starting;
  assert.equal(track.stopped, true);
  assert.equal(card._pc, null);
  assert.equal(card._unsub, null);
});

test("permission denial gives an accurate error while keeping receive audio", async () => {
  const { card, audio } = setup(async () => { throw { name: "NotAllowedError" }; });
  await card._startWebrtc();
  assert.match(card._micError, /permission denied/);
  assert.equal(audio[0].options.direction, "recvonly");
});

test("HTTP remains receive-only and explains the HTTPS requirement", async () => {
  const { card, audio } = setup(null);
  await card._startWebrtc();
  assert.match(card._micError, /HTTPS/);
  assert.equal(audio[0].options.direction, "recvonly");
});

test("a rejected device answer mutes the mic and presents the service error", async () => {
  const { card, track } = setup();
  await card._startWebrtc();
  card._config.answer_entity = "button.answer";
  card._hass.callService = async () => { throw new Error("Audio channel timed out"); };
  let status;
  card._setStatus = (value) => { status = value; };
  await card._answer();
  assert.equal(card._state, "ringing");
  assert.equal(track.enabled, false);
  assert.match(status, /Audio channel timed out/);
});
