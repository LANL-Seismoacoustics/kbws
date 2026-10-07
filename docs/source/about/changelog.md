# Changelog

All notable changes to KBWS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial Sphinx documentation
- Installation guide
- Deployment guide
- Contributing guide

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

[Unreleased]: https://github.com/LANL-seismoacoustics/kbws/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/LANL-seismoacoustics/kbws/releases/tag/v0.1.0
