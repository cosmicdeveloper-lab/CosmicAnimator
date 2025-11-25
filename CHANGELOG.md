Here is your **ready-to-paste CHANGELOG entry** for **v0.3.0**, fully matching the structure and tone of the existing file .

---

## **[0.3.0] – 2025-11-25**

### Added

* `--disable-caching` flag in `render.py`
* Azure TTS integration with updated voice selection in `tts.py`

### Changed

* Refactored **actions** system (unified execution flow)
* Refactored **style** system (cleaner architecture + new flexibility)
* Fully reworked **transition** system
* Adjusted subtitle vertical position in `subtitle.py`
* Updated test suite to align with new systems

### Documentation

* Updated `README.md`, `scenario.md`, and `LICENSE`
* Refreshed `sample.gif` preview

### Breaking Changes

* Old TTS backend removed and replaced with Azure TTS
* Legacy transition logic deleted and replaced with new design
* Action system and style system contain structural/API changes that require updates in user scenarios
* Subtitle positioning changes may affect layouts in custom scenes
