# edge-net-sony

A network-native AV receiver node on [Edge-NET](https://github.com/jackwaddington/edge-net).

## Hardware

- **Sony STR-DN1080** — 7.2ch AV receiver with built-in WiFi + Ethernet
- **No bridge hardware** — unlike the [HK AVR365](https://github.com/jackwaddington/edge-net-avr)
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

## MQTT topics (proposed)

Shared vocabulary with [edge-net-avr](https://github.com/jackwaddington/edge-net-avr) —
both amps honour the same topic shapes.

| Topic | Direction | Payload |
| ----- | --------- | ------- |
| `edge-net/sony/power`   | subscribe | `on` / `off` |
| `edge-net/sony/input`   | subscribe | source name (e.g. `bd-dvd`, `game`, `tv`) |
| `edge-net/sony/volume`  | subscribe | `up` / `down` / `0–100` |
| `edge-net/sony/mute`    | subscribe | `on` / `off` / `toggle` |
| `edge-net/sony/sound`   | subscribe | sound field (e.g. `dolby-surround`, `multi-stereo`) |
| `edge-net/sony/state`   | publish   | current power/input/volume/mute (from notifications) |

## Status

Scaffold — unit on the network, External Control to be enabled, adapter not yet
written. Catalog in [CONTROLS.md](CONTROLS.md).
