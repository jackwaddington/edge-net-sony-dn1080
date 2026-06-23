# edge-net-sony

A network-native AV receiver node on [Edge-NET](https://github.com/jackwaddington/edge-net).

## Hardware

- **Sony STR-DN1080** — 7.2ch AV receiver with built-in WiFi + Ethernet
- **No bridge hardware** — unlike the [HK AVR365](https://github.com/jackwaddington/edge-net-hk-avr365)
  (which needs a Pico W + MAX3232 to reach RS-232), the Sony is already on the
  network. Nothing of ours runs *on* it.

## Role

An **audio output capability** on the fabric — power, input routing, volume,
surround mode. Same capability the HK AVR365 provides, different transport. Above
the bus they speak the same vocabulary; the edge fires `power on` without caring
which amp answers.

The Sony exposes Sony's **Audio Control API** over IP (enable
*Setup → Network Settings → External Control*; responds on **TCP/UDP 33336**,
JSON-RPC style). So this node is **adapter + catalog**, not firmware:

- an **adapter service** (lives on a Linux node / VM, not on the Sony) that
  bridges the `edge-net/sony/*` MQTT contract ↔ the Audio Control API
- this repo's **controls catalog** ([CONTROLS.md](CONTROLS.md)) — the browsable
  surface of everything the unit can do, so use-cases can be imagined against it

## Why a repo if no firmware runs here?

A node is **a controllable surface worth documenting**, not just a thing that
runs our code. The point of this repo is to list what the Sony *can do* so the
capability is visible when browsing the fabric — then we design use-cases against
it. The adapter code lands here too once written, so it's a real repo regardless.

## MQTT topics

Addressed by **capability**, not box name — `edge-net/avr/*`, shared with
[edge-net-hk-avr365](https://github.com/jackwaddington/edge-net-hk-avr365). See
[mqtt-contract D7](https://github.com/jackwaddington/edge-net/blob/main/docs/mqtt-contract.md).
If both amps run at once, this unit's instance id is `sony` (`edge-net/avr/sony/*`).

| Topic | Direction | Payload |
| ----- | --------- | ------- |
| `edge-net/avr/power` | subscribe | `{"state":"on"}` / `off` |
| `edge-net/avr/input` | subscribe | `{"source":"bd-dvd"}` (`game`, `tv`, …) |
| `edge-net/avr/volume` | subscribe | `{"level":42}` or `up` / `down` |
| `edge-net/avr/mute` | subscribe | `on` / `off` / `toggle` |
| `edge-net/avr/sound` | subscribe | sound field (`dolby-surround`, `multi-stereo`) |
| `edge-net/avr/state` | publish | sensed power/input/volume/mute (API notifications), retained |

This unit **earns `/state`**: the Audio Control API pushes real state changes
(front panel, remote), so the feedback is honest — see D7.

## Status

API confirmed live at `192.168.0.6:10000` — no auth required, source URIs captured
from live unit. Adapter written (`adapter/adapter.py`); deployed as LXC CT 210 on
pve1 (192.168.0.60) via Terraform. Catalog in [CONTROLS.md](CONTROLS.md).
