# FlashForge Guider 2s for Home Assistant

A Home Assistant integration for the FlashForge Guider 2s printer.

## Features
- Printer state sensor (online/printing/offline) with attributes for temperatures and job details.
- Progress sensor (percentage).
- Online binary sensor.
- MJPEG camera entity for the built-in stream.
- Service `flashforge_guider2s.refresh` to force an immediate poll.

## Installation
1. Install via [HACS](https://hacs.xyz/) as a custom repository (`https://github.com/tjuuljensen/FlashForgeGuider2s`), or copy this repository to `custom_components/flashforge_guider2s` in your Home Assistant config directory.
2. Restart Home Assistant.
3. Go to Settings → Integrations → Add integration → search for “FlashForge Guider 2s”.
4. Enter the printer IP (and port if different from default 8899). Assign a static IP in your network for reliability.

## Compatibility
Developed and tested with FlashForge Guider 2s. Other models may work but are unverified. Please open an issue if you test another model successfully (or encounter problems).

## Credits
Based on the original [FlashForge Adventurer 3 integration](https://github.com/modrzew/hass-flashforge-adventurer-3) by modrzew.
