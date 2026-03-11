# Changelog

## [Unreleased]

### Changed

- Update `compute_best_second_guesses` to have more consistent printout

## [1.4.0] - 2026-03-10

### Added

- Add dark mode toggle

## [1.3.0] - 2026-03-03

### Changed

- Update best starting word to "SLATE"
- Move functions for displaying groups in Wordle UI to `ui.helpers`
- Improve printout when computing best second guess
- Add project script for computing best second guess

### Fixed

- Fix Wordle solver UI not properly displaying groups

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

[Unreleased]: https://github.com/gabrieljreed/octordle_solver/compare/1.4.0...HEAD
[1.4.0]: https://github.com/gabrieljreed/octordle_solver/releases/tag/1.4.0
[1.3.0]: https://github.com/gabrieljreed/octordle_solver/releases/tag/1.3.0
[1.2.0]: https://github.com/gabrieljreed/octordle_solver/releases/tag/1.2.0
[1.1.0]: https://github.com/gabrieljreed/octordle_solver/releases/tag/1.1.0
[1.0.0]: https://github.com/gabrieljreed/octordle_solver/releases/tag/1.0.0
