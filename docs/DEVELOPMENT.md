# Development

## Repository layout

| Path | Purpose |
| --- | --- |
| `custom_components/comelit_man/` | Installable integration and bundled HA cards |
| `tests/` | Protocol, lifecycle, media and frontend regressions |
| `docs/PROTOCOL.md` | Protocol reference |
| `docs/MT6741W.md` | Device findings, limitations and diagnostics |
| `CHANGELOG.md` | Integration version history |
| `memory/` | Historical upstream audit and backlog, not current validation claims |

## Branches

| Branch | Purpose |
| --- | --- |
| `main` | Consolidated integration, currently 1.5.13 |
| `codex/hd-video-two-way-audio` | Earlier MT-6741W checkpoint through 1.5.11 |
| `codex/video-framing-diagnostics` | Preview and resolution checkpoint through 1.5.12 |
| `codex/inbound-call-release` | Incoming-call handling, 1.5.13 and repository maintenance |

The three work branches are successive development stages, not separate products.
Their useful changes are consolidated into `main`. Keep them as comparison points.
Create future changes on `codex/` branches and merge via PR.

Inherited feature branches have been removed from GitHub. A local Git bundle
was retained before deletion. Existing tags and commit history remain intact.

## Checks

Use Python 3.13 or later and the dependencies in the validation workflow.
Run from the repository root:

```sh
python -m pytest tests/ --tb=short
node --test tests/test_doorbell_card.cjs
python -m ruff check custom_components/
python -m ruff format --check custom_components/ tests/
python -m mypy custom_components/comelit_man/
```

Device-dependent tests require an explicitly configured test device and may
skip locally. Never commit credentials, packet captures or captured audio.
Packet counters establish transport, not intelligibility; report hardware
checks separately from simulated regressions.

Repository housekeeping does not include deploying to a live HA instance.
Changing GitHub files does not update a running installation.

[Back to README](../README.md)
