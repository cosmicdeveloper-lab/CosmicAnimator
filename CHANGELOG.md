## [0.2.0] - 2025-09-24
### Added
- Configurable label position option
- New defaults for TTS model and speaker moved into constants

### Changed
- Restructured subtitle handling and TTS narration flow
- Updated CLI flags (see README for usage)
- Updated Mermaid structure diagram in README

### Removed
- Obsolete `narration_actions` module (now handled by redesigned subtitle/tts flow)

### Documentation
- Updated Quick Start with `work/` directory setup
- Clarified CLI usage in README
- Added/improved docstrings in constants module

### Breaking Changes
- `narration_actions` removed — any references should be migrated to new subtitle/tts system
- CLI flag changes
