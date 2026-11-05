# Versions and tags

**Current consolidated release: [v1.5.13](https://github.com/cuchipandy/comelit-cuchicodex/releases/tag/v1.5.13).**

Versions 1.5.2–1.5.13 were developed in this fork. Their annotated tags were
published retrospectively on 2026-11-05. Dates below are development dates,
not claims of earlier public releases. Version details are in the [changelog](../CHANGELOG.md).

| Tag | Developed | Source | Main changes |
| --- | --- | --- | --- |
| [v1.5.2](https://github.com/cuchipandy/comelit-cuchicodex/tree/v1.5.2) | 2026-10-28 | `f84e741` | Requested video profiles and two-way audio lifecycle |
| [v1.5.3](https://github.com/cuchipandy/comelit-cuchicodex/tree/v1.5.3) | 2026-10-28 | `eb30be0` | Outbound ACKs and video renewal |
| [v1.5.4](https://github.com/cuchipandy/comelit-cuchicodex/tree/v1.5.4) | 2026-10-28 | `a627fff` | Manual entrance audio, UDP channels and cleanup |
| [v1.5.5](https://github.com/cuchipandy/comelit-cuchicodex/tree/v1.5.5) | 2026-10-28 | `a4c8798` | Serialize incoming setup and answer; report service failures |
| [v1.5.6](https://github.com/cuchipandy/comelit-cuchicodex/tree/v1.5.6) | 2026-10-29 | `7cb8560` | Share HA media sessions and recover listener health |
| [v1.5.7](https://github.com/cuchipandy/comelit-cuchicodex/tree/v1.5.7) | 2026-10-29 | `79f21a4` | Fail cleanly when a manual session is rejected |
| [v1.5.8](https://github.com/cuchipandy/comelit-cuchicodex/tree/v1.5.8) | 2026-10-29 | `97fac6a` | Incoming RTPC1 UDP audio reception |
| [v1.5.9](https://github.com/cuchipandy/comelit-cuchicodex/tree/v1.5.9) | 2026-10-29 | `120c28c` | Restore VIP registration after media sessions |
| [v1.5.10](https://github.com/cuchipandy/comelit-cuchicodex/tree/v1.5.10) | 2026-10-29 | `119d0eb` | Door-release resilience and microphone gain |
| [v1.5.11](https://github.com/cuchipandy/comelit-cuchicodex/tree/v1.5.11) | 2026-10-30 | `acf0682` | Live microphone gain control from Portero |
| [v1.5.12](https://github.com/cuchipandy/comelit-cuchicodex/tree/v1.5.12) | 2026-10-30 | `863d5df` | Consume incoming preview media earlier |
| [v1.5.13](https://github.com/cuchipandy/comelit-cuchicodex/releases/tag/v1.5.13) | 2026-11-01 | Consolidated `main` with repository documentation | Incoming negotiation, talk-back startup and native release |

Tags through **v1.5.1** are inherited upstream history and remain unchanged.
Earlier fork tags are checkpoints, not recommendations to downgrade. The
v1.5.13 tag includes the November 5 documentation cleanup; its runtime behavior
is the same 1.5.13 integration consolidated from the incoming-call work branch.

## Installation and validation

Use `comelit_man.zip` from the current release. Its root contains `manifest.json`
and the integration files; extract it into `config/custom_components/comelit_man/`
and restart HA. Do not install the full repository archive into that directory.

The consolidated 1.5.13 source passed **1126 Python tests** (9 hardware-dependent
skips), **8 Node tests**, source Ruff lint/format and strict mypy during the
November 5 cleanup. Those results do not mean every earlier tag was re-tested.
Native 1024x608 output is not established: observed video was 640x240.
See [device findings](MT6741W.md) for remaining limitations.

Android Portero has its own versions; they are not integration tags or APK releases here.
