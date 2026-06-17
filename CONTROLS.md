# Sony STR-DN1080 — Controls Catalog

What the unit can do over the **Audio Control API** (TCP/UDP **33336**, enable via
*Setup → Network Settings → External Control*). This is the browsable surface —
inputs we can drive, state we can read — so use-cases can be designed against it.

Transport: JSON-RPC style calls grouped by service (`system`, `audio`, `avContent`).
Two-way: the unit also **pushes notifications** on state change, so the fabric can
react to the remote/front panel, not just command the box.

## Power

| Capability | Notes |
| ---------- | ----- |
| Power on / off (standby) | `system.setPowerStatus` |
| Read power state | + notification on change |

## Volume & mute

| Capability | Notes |
| ---------- | ----- |
| Set absolute volume | `audio.setAudioVolume`, numeric |
| Volume up / down (relative) | step value |
| Mute on / off / toggle | `audio.setAudioMute` |
| Read volume + mute | + notifications |
| Per-zone volume | main + Zone 2 (see Multi-zone) |

## Input switching

`avContent.setPlayContent` / `getCurrentExternalTerminalsStatus`. DN1080 sources:

| Source | Typical use |
| ------ | ----------- |
| BD/DVD | Blu-ray / disc |
| Game | Console |
| SAT/CATV | Set-top box |
| TV | ARC return from telly |
| Video / AUX | Aux video |
| SA-CD/CD | Disc audio |
| FM / AM | Tuner |
| Bluetooth | BT audio in |
| USB | Front USB |
| Home / Screen mirroring / Chromecast built-in | Network/cast sources |

Read which input is live; switch to any of the above.

## Sound field / surround

`audio.setSoundField`. Modes on the DN1080:

- Dolby Surround
- Neural:X / DTS modes
- Multi Stereo
- 2ch Stereo / Direct / Pure Direct
- Auto Format Direct (AFD)
- Front Surround / Sports / Music modes

Read current sound field; set any mode. (Object-audio formats — Dolby Atmos /
DTS:X — pass through when source provides them.)

## Multi-zone (Zone 2)

| Capability | Notes |
| ---------- | ----- |
| Zone 2 power on / off | independent of main |
| Zone 2 input select | different source to another room |
| Zone 2 volume / mute | independent |

This is the interesting one for whole-house: main zone for the lounge, Zone 2
feeding speakers elsewhere, each switchable independently from the fabric.

## State we can read (for `edge-net/sony/state`)

- Power status
- Current input / external terminal status
- Volume + mute (per zone)
- Current sound field
- Playing content metadata (network/cast sources)

## Not controllable here

- HDMI video switching is tied to input selection (no independent video matrix)
- Speaker calibration / DCAC setup is front-panel/OSD only
- Firmware updates — leave to Sony

## Open questions

- Exact source-name strings the API expects (capture from a live unit)
- Does External Control survive standby, or only respond when powered? (test)
- Worth modelling Zone 2 as its own capability vs. nested under this node?
- Auth/pairing: does the DN1080 require a pairing handshake or open on the LAN?
