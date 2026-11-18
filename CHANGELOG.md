# Changelog

All notable changes to KBWS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.5.0] - 2026-11-18

### Added
- FDSN Availability Web Service endpoints for querying waveform coverage and extents.
- FDSN Event Web Service text output, including CSV and JSON serialization.
- FDSN Station Web Service text output and WADL documentation.
- Dataselect POST request support for standard FDSN request files.
- Dataselect `queryauth` compatibility aliases.
- SQL and CSS output formats for event and waveform queries.
- Configurable database table mappings, including guards and clear service responses when required tables are unavailable.
- Optional Oracle `oracledb` support and Oracle Instant Client configuration.
- Container workflows for Docker and rootless Podman development.
- OpenAPI, Sphinx, and autodoc documentation improvements.

### Changed
- Unified no-data and service error responses across endpoints.
- SAC ZIP filenames use `XX` for traces without a network code, avoiding hidden extracted files.

## [0.1.0] - 2025

### Added
- Initial release of KBWS
- FDSN Event Web Service implementation
  - QuakeML, JSON, and CSV output formats
  - Geographic and temporal filtering
  - Magnitude filtering
  - Catalog parameter support
- FDSN Station Web Service implementation
  - StationXML output
  - Channel-level metadata
- FDSN Dataselect Web Service implementation
  - MiniSEED output format
  - SAC output format
  - Direct waveform file access
- FDSN Availability Web Service implementation
  - Query waveform data availability
- FastAPI-based web service framework
- Pisces integration for database access
- Docker/Podman container support
- Flexible schema configuration via environment variables
- Support for Oracle databases (cx_Oracle and oracledb)
- Comprehensive test suite with mocked database connections
- OpenAPI/Swagger documentation
- CORS middleware support

[Unreleased]: https://github.com/LANL-seismoacoustics/kbws/compare/v0.5.0...HEAD
[v0.5.0]: https://github.com/LANL-seismoacoustics/kbws/releases/tag/v0.5.0
[0.1.0]: https://github.com/LANL-seismoacoustics/kbws/releases/tag/v0.1.0
