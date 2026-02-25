# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Update best starting word to "SLATE"

## [1.2.0] - 2026-02-25

### Changed

- Fix filtering to better handle duplicate letters
    - Instead of storing and using constraints, use direct simulation of Wordle feedback
- Update Wordle Solver UI, `Game`, and `compute_best_second_guesses` script to use the `Puzzle` class
- Improve type hinting
- Rename `compute_wordle_feedback` to `score_guess`

## [1.1.0] - 2026-02-24

### Changed

- Use `Puzzle` class within Wordle solver UI

## [1.0.0] - 2026-02-24

### Added

- Initial release!

[Unreleased]: https://github.com/gabrieljreed/octordle_solver/compare/1.2.0...HEAD
[1.2.0]: https://github.com/gabrieljreed/octordle_solver/releases/tag/1.2.0
[1.1.0]: https://github.com/gabrieljreed/octordle_solver/releases/tag/1.1.0
[1.0.0]: https://github.com/gabrieljreed/octordle_solver/releases/tag/1.0.0
