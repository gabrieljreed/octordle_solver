use pyo3::prelude::*;

pub mod solver;

/// Top-level module exported to Python as `octordle_solver_rs`.
#[pymodule]
fn octordle_solver_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(solver::score_guess, m)?)?;
    m.add_function(wrap_pyfunction!(solver::generate_groups, m)?)?;
    m.add_function(wrap_pyfunction!(solver::calculate_fitness_score, m)?)?;
    m.add_function(wrap_pyfunction!(solver::get_all_answers, m)?)?;
    m.add_function(wrap_pyfunction!(solver::get_best_guess_multiple_puzzles, m)?)?;
    m.add_class::<solver::Group>()?;
    m.add_class::<solver::AnswerPossibility>()?;
    m.add_class::<solver::Guess>()?;
    m.add_class::<solver::Puzzle>()?;
    Ok(())
}
