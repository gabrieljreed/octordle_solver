from octordle_solver.dictionary import dictionary


def test_dictionary():
    assert isinstance(dictionary.words, list)
    assert isinstance(dictionary.valid_guesses, list)
    assert isinstance(dictionary.valid_answers, list)
