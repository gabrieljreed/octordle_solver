use std::collections::{HashMap, HashSet};

use pyo3::prelude::*;
use rayon::prelude::*;

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/// Convert a 5-letter ASCII word (any case) to a fixed `[u8; 5]` of uppercase bytes.
pub fn str_to_word(s: &str) -> PyResult<[u8; 5]> {
    let b = s.as_bytes();
    if b.len() != 5 {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
            "Word must be exactly 5 ASCII letters, got '{}' (len {})",
            s,
            s.len()
        )));
    }
    Ok([
        b[0].to_ascii_uppercase(),
        b[1].to_ascii_uppercase(),
        b[2].to_ascii_uppercase(),
        b[3].to_ascii_uppercase(),
        b[4].to_ascii_uppercase(),
    ])
}

/// Score a guess against an answer.  Returns a 5-byte array where each byte
/// is one of: `b'Y'` (correct position), `b'M'` (misplaced), `b'N'` (not present).
///
/// Handles duplicate letters the same way Wordle does: exact matches are
/// consumed first, then remaining answer letters are matched left-to-right
/// for the misplaced check.
pub fn score_guess_internal(guess: &[u8; 5], answer: &[u8; 5]) -> [u8; 5] {
    let mut feedback = [b'N'; 5];
    // Count of each answer letter not consumed by an exact match.
    let mut remaining = [0u8; 26];

    // First pass: mark exact matches.
    for i in 0..5 {
        if guess[i] == answer[i] {
            feedback[i] = b'Y';
        } else {
            remaining[(answer[i] - b'A') as usize] += 1;
        }
    }

    // Second pass: mark misplaced letters.
    for i in 0..5 {
        if feedback[i] == b'Y' {
            continue;
        }
        let idx = (guess[i] - b'A') as usize;
        if remaining[idx] > 0 {
            feedback[i] = b'M';
            remaining[idx] -= 1;
        }
    }

    feedback
}

/// Generate groups from a pre-parsed word, for use in internal Rust code.
pub fn generate_groups_internal(
    given: &[u8; 5],
    remaining_words: &[String],
) -> PyResult<Vec<Group>> {
    let mut map: HashMap<[u8; 5], Vec<String>> = HashMap::new();

    for word in remaining_words {
        let w = str_to_word(word)?;
        let feedback = score_guess_internal(given, &w);
        map.entry(feedback).or_default().push(word.clone());
    }

    Ok(map
        .into_iter()
        .map(|(possibility, words)| Group {
            words,
            possibility: String::from_utf8(possibility.to_vec())
                .expect("feedback bytes are always valid UTF-8"),
        })
        .collect())
}

// ---------------------------------------------------------------------------
// PyO3 types & functions
// ---------------------------------------------------------------------------

/// A group of remaining words that all produce the same feedback pattern
/// when a particular guess is played.
#[pyclass]
#[derive(Clone, Debug)]
pub struct Group {
    #[pyo3(get)]
    pub words: Vec<String>,
    /// 5-character string of 'Y', 'M', 'N' representing the feedback pattern.
    #[pyo3(get)]
    pub possibility: String,
}

#[pymethods]
impl Group {
    #[new]
    fn new(words: Vec<String>, possibility: String) -> Self {
        Group { words, possibility }
    }

    fn __repr__(&self) -> String {
        let mut result = self.possibility.clone();
        for word in &self.words {
            result.push_str(&format!("\n\t{word}"));
        }
        result
    }

    fn __str__(&self) -> String {
        self.__repr__()
    }

    fn __bool__(&self) -> bool {
        !self.words.is_empty()
    }

    fn __eq__(&self, other: &Group) -> bool {
        self.words == other.words && self.possibility == other.possibility
    }
}

/// Simulate Wordle feedback for `guess` against `answer`.
///
/// Returns a 5-character string: `'Y'` = correct position, `'M'` = misplaced,
/// `'N'` = not present.  Handles duplicate letters correctly.
#[pyfunction]
pub fn score_guess(guess: &str, answer: &str) -> PyResult<String> {
    let g = str_to_word(guess)?;
    let a = str_to_word(answer)?;
    let result = score_guess_internal(&g, &a);
    Ok(String::from_utf8(result.to_vec()).expect("feedback bytes are always valid UTF-8"))
}

/// Group `remaining_words` by the feedback pattern produced when `given_word`
/// is guessed.  Returns one [`Group`] per distinct pattern.
#[pyfunction]
pub fn generate_groups(given_word: &str, remaining_words: Vec<String>) -> PyResult<Vec<Group>> {
    let given = str_to_word(given_word)?;
    generate_groups_internal(&given, &remaining_words)
}

// ---------------------------------------------------------------------------
// AnswerPossibility
// ---------------------------------------------------------------------------

const PENALTY_WEIGHT: f64 = 0.1;
const REMAINING_WORD_BONUS: f64 = 2.0;

/// A candidate guess together with the groups it would create over the
/// remaining words.  Higher fitness = better guess.
#[pyclass]
#[derive(Clone, Debug)]
pub struct AnswerPossibility {
    #[pyo3(get)]
    pub word: String,
    #[pyo3(get)]
    pub groups: Vec<Group>,
    /// Cached: size of the largest group (-1 when there are no groups).
    max_group_size_cached: i64,
}

impl AnswerPossibility {
    pub fn new(word: String, groups: Vec<Group>) -> Self {
        let max_group_size_cached = groups
            .iter()
            .map(|g| g.words.len() as i64)
            .max()
            .unwrap_or(-1);
        AnswerPossibility {
            word,
            groups,
            max_group_size_cached,
        }
    }

    /// True when `self` is a strictly better guess than `other`.
    /// Mirrors Python's `AnswerPossibility.__gt__`.
    pub fn is_better_than(&self, other: &AnswerPossibility) -> bool {
        let sg = self.groups.len();
        let og = other.groups.len();
        if sg == og {
            if sg == 0 {
                return true;
            }
            // Smaller max group size is better.
            return self.max_group_size_cached < other.max_group_size_cached;
        }
        // More groups is better.
        sg > og
    }
}

#[pymethods]
impl AnswerPossibility {
    #[new]
    fn py_new(word: String, groups: Vec<Group>) -> Self {
        Self::new(word, groups)
    }

    #[getter]
    fn max_group_size(&self) -> i64 {
        self.max_group_size_cached
    }

    fn __gt__(&self, other: &AnswerPossibility) -> bool {
        self.is_better_than(other)
    }

    fn __str__(&self) -> String {
        format!(
            "{}: {} groups, largest group {}",
            self.word,
            self.groups.len(),
            self.max_group_size_cached
        )
    }

    fn __repr__(&self) -> String {
        self.__str__()
    }
}

// ---------------------------------------------------------------------------
// Fitness scoring
// ---------------------------------------------------------------------------

/// Internal: compute fitness score without going through PyO3.
pub fn calculate_fitness_score_internal(ap: &AnswerPossibility, remaining_words: &[String]) -> f64 {
    let fitness = ap.groups.len() as f64 - ap.max_group_size_cached as f64 * PENALTY_WEIGHT;
    let bonus = if remaining_words.contains(&ap.word) {
        REMAINING_WORD_BONUS
    } else {
        0.0
    };
    fitness + bonus
}

/// Compute a fitness score for a candidate guess given the remaining words.
/// Mirrors Python's `calculate_fitness_score`.
#[pyfunction]
pub fn calculate_fitness_score(ap: &AnswerPossibility, remaining_words: Vec<String>) -> f64 {
    calculate_fitness_score_internal(ap, &remaining_words)
}

// ---------------------------------------------------------------------------
// get_all_answers
// ---------------------------------------------------------------------------

/// Comparison for sorting: returns the ordering of `a` relative to `b` such
/// that a higher-quality guess sorts first (descending).
fn cmp_answer_possibilities(
    a: &AnswerPossibility,
    b: &AnswerPossibility,
) -> std::cmp::Ordering {
    let ag = a.groups.len();
    let bg = b.groups.len();
    if ag == bg {
        if ag == 0 {
            std::cmp::Ordering::Equal
        } else {
            // Smaller max_group_size is better → comes first.
            a.max_group_size_cached.cmp(&b.max_group_size_cached)
        }
    } else {
        // More groups is better → higher count comes first.
        bg.cmp(&ag)
    }
}

/// Internal: score every candidate and return sorted best-first, without
/// going through PyO3 argument conversion.
pub fn get_all_answers_core(
    remaining_words: &[String],
    valid_guesses: &[String],
) -> PyResult<Vec<AnswerPossibility>> {
    if remaining_words.is_empty() {
        return Ok(vec![]);
    }

    if remaining_words.len() == 1 {
        let word = &remaining_words[0];
        let given = str_to_word(word)?;
        let groups = generate_groups_internal(&given, remaining_words)?;
        return Ok(vec![AnswerPossibility::new(word.clone(), groups)]);
    }

    let mut seen: HashSet<&str> = HashSet::new();
    let mut guesses: Vec<&str> =
        Vec::with_capacity(remaining_words.len() + valid_guesses.len());
    for word in remaining_words.iter().chain(valid_guesses.iter()) {
        if seen.insert(word.as_str()) {
            guesses.push(word.as_str());
        }
    }

    let mut all_possibilities: Vec<AnswerPossibility> = guesses
        .par_iter()
        .map(|word| {
            let given = str_to_word(word).expect("word list contains invalid word");
            let groups = generate_groups_internal(&given, remaining_words)
                .expect("generate_groups failed");
            AnswerPossibility::new((*word).to_owned(), groups)
        })
        .collect();

    all_possibilities.sort_by(cmp_answer_possibilities);
    Ok(all_possibilities)
}

/// Score every candidate guess against the current set of remaining words and
/// return them sorted best-first.  Uses Rayon for data-parallel scoring.
#[pyfunction]
pub fn get_all_answers(
    remaining_words: Vec<String>,
    valid_guesses: Vec<String>,
) -> PyResult<Vec<AnswerPossibility>> {
    get_all_answers_core(&remaining_words, &valid_guesses)
}

// ---------------------------------------------------------------------------
// Guess
// ---------------------------------------------------------------------------

/// A single guess and its Wordle feedback result.
#[pyclass]
#[derive(Clone, Debug)]
pub struct Guess {
    #[pyo3(get)]
    pub word: String,
    /// 5-character string: 'Y' = correct, 'M' = misplaced, 'N' = incorrect.
    #[pyo3(get)]
    pub result: String,
}

#[pymethods]
impl Guess {
    #[new]
    fn new(word: String, result: String) -> Self {
        Guess { word, result }
    }

    fn __repr__(&self) -> String {
        format!("Guess({}, {})", self.word, self.result)
    }

    fn __str__(&self) -> String {
        format!("{}: {}", self.word, self.result)
    }

    fn __eq__(&self, other: &Guess) -> bool {
        self.word == other.word && self.result == other.result
    }
}

/// Convert a Python `str | list[int]` result value to a 5-char Y/M/N string.
/// Integer encoding: 0 = correct (Y), 1 = misplaced (M), 2 = incorrect (N).
fn sanitize_result(result: &Bound<'_, PyAny>) -> PyResult<String> {
    // Try string first.
    if let Ok(s) = result.extract::<String>() {
        if s.len() != 5 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "result string must be exactly 5 characters",
            ));
        }
        return Ok(s.to_uppercase());
    }
    // Fall back to list[int].
    let ints = result.extract::<Vec<i64>>().map_err(|_| {
        pyo3::exceptions::PyTypeError::new_err(
            "result must be a str or list[int] (0=correct, 1=misplaced, 2=incorrect)",
        )
    })?;
    if ints.len() != 5 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "result list must have exactly 5 elements",
        ));
    }
    let mut s = String::with_capacity(5);
    for &v in &ints {
        match v {
            0 => s.push('Y'),
            1 => s.push('M'),
            2 => s.push('N'),
            _ => {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "invalid result value {v}: expected 0 (correct), 1 (misplaced), or 2 (incorrect)"
                )))
            }
        }
    }
    Ok(s)
}

// ---------------------------------------------------------------------------
// Puzzle
// ---------------------------------------------------------------------------

/// Holds the state of a single Wordle puzzle: remaining candidates,
/// guess history, and the ranked list of best next guesses.
#[pyclass]
pub struct Puzzle {
    #[pyo3(get, set)]
    pub remaining_words: Vec<String>,
    #[pyo3(get)]
    pub valid_guesses: Vec<String>,
    #[pyo3(get)]
    pub all_answers: Vec<AnswerPossibility>,
    #[pyo3(get)]
    pub guesses: Vec<Guess>,
    get_best_answer: bool,
    // Preserved for reset().
    initial_remaining_words: Vec<String>,
    initial_valid_guesses: Vec<String>,
}

#[pymethods]
impl Puzzle {
    /// Create a new Puzzle.
    ///
    /// Unlike the Python version this constructor requires the word lists
    /// explicitly so the Rust crate has no implicit dictionary dependency.
    #[new]
    #[pyo3(signature = (valid_answers, valid_guesses, get_best_answer=true))]
    pub fn new(
        valid_answers: Vec<String>,
        valid_guesses: Vec<String>,
        get_best_answer: bool,
    ) -> Self {
        Puzzle {
            remaining_words: valid_answers.clone(),
            valid_guesses: valid_guesses.clone(),
            all_answers: vec![],
            guesses: vec![],
            get_best_answer,
            initial_remaining_words: valid_answers,
            initial_valid_guesses: valid_guesses,
        }
    }

    /// Apply a guess and its feedback, filter remaining words, and
    /// (optionally) recompute the ranked answer list.
    ///
    /// `result` may be a `str` ("YYYMN") or a `list[int]`
    /// (0=correct, 1=misplaced, 2=incorrect).
    fn make_guess(&mut self, word: String, result: &Bound<'_, PyAny>) -> PyResult<()> {
        let result_str = sanitize_result(result)?;
        let guess = Guess {
            word: word.clone(),
            result: result_str.clone(),
        };
        self.guesses.push(guess);
        self.filter_remaining(&word, &result_str);
        if self.get_best_answer {
            self.all_answers = get_all_answers_core(&self.remaining_words, &self.valid_guesses)?;
        }
        Ok(())
    }

    /// Recompute and return the ranked answer list for the current state.
    fn get_all_answers(&mut self) -> PyResult<Vec<AnswerPossibility>> {
        if self.remaining_words.is_empty() {
            return Ok(vec![]);
        }
        self.all_answers =
            get_all_answers_core(&self.remaining_words, &self.valid_guesses)?;
        Ok(self.all_answers.clone())
    }

    /// `True` once a guess with result "YYYYY" has been recorded.
    #[getter]
    fn is_solved(&self) -> bool {
        self.guesses.iter().any(|g| g.result == "YYYYY")
    }

    /// Reset the puzzle back to its initial state.
    fn reset(&mut self) {
        self.remaining_words = self.initial_remaining_words.clone();
        self.valid_guesses = self.initial_valid_guesses.clone();
        self.all_answers = vec![];
        self.guesses = vec![];
    }

    /// Filter `remaining_words` to only those consistent with `guess`.
    /// Accepts a [`Guess`] object (mirrors the Python API).
    fn filter_words(&mut self, guess: &Guess) {
        self.filter_remaining(&guess.word, &guess.result);
    }

    /// Build and return `all_answers_dict` as a Python `dict[str, AnswerPossibility]`.
    /// Computed on demand so the Rust struct doesn't need to cache it.
    fn all_answers_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, pyo3::types::PyDict>> {
        let dict = pyo3::types::PyDict::new_bound(py);
        for ap in &self.all_answers {
            dict.set_item(&ap.word, ap.clone().into_py(py))?;
        }
        Ok(dict)
    }

    fn __str__(&self) -> String {
        let mut result = String::new();
        for guess in &self.guesses {
            result.push_str(&format!("\t{}\n", guess.__str__()));
        }
        result.push_str(&format!("{} remaining words", self.remaining_words.len()));
        result
    }

    fn __repr__(&self) -> String {
        self.__str__()
    }
}

impl Puzzle {
    /// Internal filter, shared by `make_guess` and `filter_words`.
    fn filter_remaining(&mut self, word: &str, result: &str) {
        let Ok(given) = str_to_word(word) else { return };
        self.remaining_words.retain(|w| {
            let Ok(answer) = str_to_word(w) else { return false };
            let feedback = score_guess_internal(&given, &answer);
            std::str::from_utf8(&feedback).map_or(false, |s| s == result)
        });
    }
}

// ---------------------------------------------------------------------------
// get_best_guess_multiple_puzzles
// ---------------------------------------------------------------------------

/// Choose the best single guess to play across all active Octordle puzzles.
/// Mirrors Python's `get_best_guess_multiple_puzzles`.
#[pyfunction]
pub fn get_best_guess_multiple_puzzles(
    puzzles: Vec<PyRef<'_, Puzzle>>,
) -> PyResult<String> {
    if puzzles.is_empty() {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "puzzles list must not be empty",
        ));
    }

    // Only one puzzle left: return its top-ranked guess.
    if puzzles.len() == 1 {
        return puzzles[0]
            .all_answers
            .first()
            .map(|ap| ap.word.clone())
            .ok_or_else(|| {
                pyo3::exceptions::PyValueError::new_err(
                    "call get_all_answers() on the puzzle before get_best_guess_multiple_puzzles()",
                )
            });
    }

    // A puzzle with exactly 1 remaining word can be solved this turn.
    for p in puzzles.iter() {
        if p.remaining_words.len() == 1 {
            return p
                .all_answers
                .first()
                .map(|ap| ap.word.clone())
                .ok_or_else(|| {
                    pyo3::exceptions::PyValueError::new_err(
                        "call get_all_answers() on the puzzle before get_best_guess_multiple_puzzles()",
                    )
                });
        }
    }

    // An answer with max_group_size == 1 guarantees a solve in the next turn.
    for p in puzzles.iter() {
        for ap in &p.all_answers {
            if ap.max_group_size_cached == 1 {
                return Ok(ap.word.clone());
            }
        }
    }

    // Weighted scoring across all puzzles.
    // Puzzles with fewer remaining words (closer to solved) get higher weight,
    // matching Python: weight = (total_remaining - puzzle_remaining) / total_remaining
    let total_remaining: usize = puzzles.iter().map(|p| p.remaining_words.len()).sum();

    // Collect the union of all candidate words across all puzzles.
    let mut all_words: HashSet<&str> = HashSet::new();
    for p in puzzles.iter() {
        for ap in &p.all_answers {
            all_words.insert(ap.word.as_str());
        }
    }

    let mut best_score = f64::NEG_INFINITY;
    let mut best_word = String::new();

    for word in &all_words {
        let mut total_score = 0.0f64;
        for p in puzzles.iter() {
            let Some(ap) = p.all_answers.iter().find(|a| a.word == *word) else {
                continue;
            };
            let weight = (total_remaining - p.remaining_words.len()) as f64
                / total_remaining as f64;
            total_score +=
                calculate_fitness_score_internal(ap, &p.remaining_words) * weight;
        }
        if total_score > best_score {
            best_score = total_score;
            best_word = (*word).to_owned();
        }
    }

    if best_word.is_empty() {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "no valid guesses found",
        ));
    }
    Ok(best_word)
}
