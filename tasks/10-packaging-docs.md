# Task 10 – Packaging, Versioning & Documentation

## Description
Prepare the project for distribution and user onboarding.

Work items:
1. **Packaging**
   - `pyproject.toml` using PEP 621 metadata.
   - Build wheels for Linux, macOS, Windows; include pure-Python fallback distribution tag.
   - Include classifiers for supported Python versions.
2. **Semantic Versioning & Changelog**
   - Adopt `versioneer` or `hatch-version` for automatic version bumps.
   - Maintain `CHANGELOG.md` per *Keep A Changelog* guidelines.
3. **License**
   - Add MIT license file (or Apache-2.0 upon decision).
4. **Documentation**
   - Sphinx configuration under `docs/` with:
     - Usage guide with quickstart.
     - Locale matrix table.
     - Benchmarks page.
     - Migration notes (esp. breaking changes across major versions).
   - Publish to Read the Docs or GitHub Pages.

## Acceptance Criteria
- `pip install intl-number-parser` wheel works on target platforms.
- `make docs` builds HTML with no warnings.
- README lists installation, badges, quick example.

## References
- REQUIREMENTS.md – Operations & Deployment. 