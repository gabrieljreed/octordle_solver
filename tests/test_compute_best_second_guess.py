from pathlib import Path
from types import SimpleNamespace

import octordle_solver.data.compute_best_second_guess as compute_module

from octordle_solver.data.compute_best_second_guess import (
    compute_best_second_guesses,
    get_all_possibilities,
    possibility_to_key,
    write_best_second_guesses,
)


def make_fake_puzzle_cls(cases):
    class FakePuzzle:
        def __init__(self):
            self.guesses = []
            self.remaining_words = []
            self.all_answers = []

        def make_guess(self, _starting_guess, possibility):
            case = cases[tuple(possibility)]
            self.guesses = [case["guess_display"]]
            self.remaining_words = case["remaining_words"]
            self.all_answers = [SimpleNamespace(word=word) for word in case["all_answers"]]

    return FakePuzzle


def test_get_all_possibilities_count():
    possibilities = get_all_possibilities()
    assert len(possibilities) == 243
    assert (0, 0, 0, 0, 0) in possibilities
    assert (2, 2, 2, 2, 2) in possibilities


def test_possibility_to_key():
    assert possibility_to_key((0, 1, 2, 1, 0)) == "01210"
    assert possibility_to_key([2, 2, 0, 1, 1]) == "22011"


def test_compute_best_second_guesses_handles_all_statuses():
    possibilities = [
        (0, 0, 0, 0, 0),
        (1, 1, 1, 1, 1),
        (2, 2, 2, 2, 2),
    ]
    cases = {
        (0, 0, 0, 0, 0): {
            "guess_display": "G0",
            "remaining_words": [],
            "all_answers": [],
        },
        (1, 1, 1, 1, 1): {
            "guess_display": "G1",
            "remaining_words": ["A"],
            "all_answers": [],
        },
        (2, 2, 2, 2, 2): {
            "guess_display": "G2",
            "remaining_words": ["A", "B"],
            "all_answers": ["SLATE", "CRANE"],
        },
    }
    fake_puzzle_cls = make_fake_puzzle_cls(cases)
    statuses = []

    results, invalid_state_count = compute_best_second_guesses(
        possibilities,
        puzzle_cls=fake_puzzle_cls,
        starting_guess="CRANE",
        status_callback=statuses.append,
    )

    assert results == {"22222": "SLATE"}
    assert invalid_state_count == 1
    assert len(statuses) == 3
    assert statuses[0].endswith("Best guess: -----")
    assert statuses[1].endswith("Best guess: -----")
    assert statuses[2].endswith("Best guess: SLATE")


def test_write_best_second_guesses(tmp_path: Path):
    output_path = tmp_path / "best_second_guesses.json"

    write_best_second_guesses({"01210": "CRANE"}, output_path)

    assert output_path.exists()
    assert output_path.read_text() == '{\n    "01210": "CRANE"\n}\n'


def test_main_wires_progress_and_writes_results(monkeypatch, capsys):
    possibilities = [(0, 0, 0, 0, 0), (2, 2, 2, 2, 2)]
    observed = {
        "postfixes": [],
        "updates": 0,
        "write_call": None,
    }

    class FakeProgressBar:
        def __init__(self, *, total, desc, unit):
            self.total = total
            self.desc = desc
            self.unit = unit

        def __enter__(self):
            return self

        def __exit__(self, _exc_type, _exc, _tb):
            return False

        def set_postfix_str(self, text):
            observed["postfixes"].append(text)

        def update(self):
            observed["updates"] += 1

    def fake_tqdm(*, total, desc, unit):
        return FakeProgressBar(total=total, desc=desc, unit=unit)

    def fake_compute_best_second_guesses(input_possibilities, *, status_callback, **_kwargs):
        assert input_possibilities == possibilities
        status_callback("status A")
        status_callback("status B")
        return {"00000": "CRANE"}, 7

    def fake_write_best_second_guesses(results, output_path):
        observed["write_call"] = (results, output_path)

    monkeypatch.setattr(compute_module, "get_all_possibilities", lambda: possibilities)
    monkeypatch.setattr(compute_module, "tqdm", fake_tqdm)
    monkeypatch.setattr(compute_module, "compute_best_second_guesses", fake_compute_best_second_guesses)
    monkeypatch.setattr(compute_module, "write_best_second_guesses", fake_write_best_second_guesses)

    compute_module.main()

    captured = capsys.readouterr()
    assert "7 invalid states found." in captured.out
    assert observed["postfixes"] == ["status A", "status B"]
    assert observed["updates"] == 2
    assert observed["write_call"] == ({"00000": "CRANE"}, compute_module.output_file)


def test_main_uses_expected_tqdm_arguments(monkeypatch, capsys):
    observed = {"tqdm_kwargs": None}
    possibilities = [(0, 0, 0, 0, 0), (0, 0, 0, 0, 1), (0, 0, 0, 0, 2)]

    class FakeProgressBar:
        def __enter__(self):
            return self

        def __exit__(self, _exc_type, _exc, _tb):
            return False

        def set_postfix_str(self, _text):
            return None

        def update(self):
            return None

    def fake_tqdm(*, total, desc, unit):
        observed["tqdm_kwargs"] = {"total": total, "desc": desc, "unit": unit}
        return FakeProgressBar()

    def fake_compute_best_second_guesses(_input_possibilities, *, status_callback, **_kwargs):
        status_callback("status")
        return {}, 0

    monkeypatch.setattr(compute_module, "get_all_possibilities", lambda: possibilities)
    monkeypatch.setattr(compute_module, "tqdm", fake_tqdm)
    monkeypatch.setattr(compute_module, "compute_best_second_guesses", fake_compute_best_second_guesses)
    monkeypatch.setattr(compute_module, "write_best_second_guesses", lambda *_args, **_kwargs: None)

    compute_module.main()

    captured = capsys.readouterr()
    assert captured.out == "0 invalid states found.\n"

    assert observed["tqdm_kwargs"] == {
        "total": 3,
        "desc": "Evaluating possibilities",
        "unit": "state",
    }
