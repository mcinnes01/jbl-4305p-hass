# Changelog

All notable changes to this project will be documented in this file.

## [0.1.4] - 2026-01-06
### Fixed
- Make versions/network fetch non-blocking to prevent setup failures
- Add explicit error logging during coordinator first refresh
- Improved error visibility for setup debugging

## [0.1.3] - 2026-01-06
### Fixed
- Set minimum Home Assistant version to 2025.12.0 in hacs.json

## [0.1.2] - 2026-01-06
### Fixed
- Bluetooth device path parsing (use parts[-1] instead of parts[-2])
- MAC address now consistently lowercase in all methods
- Manifest key order for hassfest validation
- HACS validation with brands check ignored (standard for custom integrations)
- Code formatting with ruff
- Test suite mock response structures
- Added homeassistant dependency to test workflow

## [0.1.1] - 2026-01-06
- Initial public release
- Input Source select entity
- Device name get/set via config flow
- Rediscover Inputs service and button
- Diagnostics sensors (versions, network, MAC/serial/uptime)
- Buttons to switch to Google Cast and last Bluetooth device
- Input factory: add current Bluetooth device as selectable input
- Branding: icon/logo
