# ISI Nurikabe

Nurikabe solver created for the ISI course assignment. The project solves 5x5 Nurikabe puzzles and visualizes the solving process in a Tkinter desktop application.

The application includes several predefined levels, including solvable and intentionally unsolvable puzzles, and allows comparing different constraint-solving strategies by the number of iterations and profiling output.

## Features

- 5x5 Nurikabe puzzle solver
- Tkinter GUI with puzzle visualization
- Built-in predefined puzzle levels
- Support for solvable and unsolvable examples
- Optional step-by-step visualization of solver iterations
- Iteration counter for comparing algorithms
- Profiling output using Python's `cProfile`
- Three solving approaches:
  - Depth-first search (DFS)
  - Backtracking with MRV, degree heuristic, and LCV ordering
  - Forward checking

## Nurikabe Rules Covered

The solver checks the main Nurikabe constraints:

- Numbered cells are part of white islands.
- Each island must contain exactly one numbered cell.
- Island size must match the number in its numbered cell.
- Different islands must remain separated.
- Black cells must form one connected wall.
- Invalid black-cell loops are rejected.

## Project Structure

```text
.
+-- README.md
`-- Nurikabe_BelusakLuc
    |-- Nurikabe_BelusakLuc.py   # Main Python application and solver
    `-- Nurikabe_BelusakLuc.pdf  # Project documentation/report
```

## Requirements

- Python 3
- Tkinter
- tqdm

Tkinter is included with many Python installations. On Linux, it may need to be installed separately.

Install the Python dependency:

```bash
pip install tqdm
```

## Running the Application

From the repository root:

```bash
cd Nurikabe_BelusakLuc
python Nurikabe_BelusakLuc.py
```

If your system uses `python3` instead of `python`:

```bash
python3 Nurikabe_BelusakLuc.py
```

## Using the GUI

- `Ďalší Level` switches to the next predefined puzzle.
- `DFS` solves the current level using depth-first search.
- `Backtracking` solves the current level using backtracking with heuristics.
- `Forward Checking` solves the current level using forward checking.
- `Zobraziť iterácie` enables or disables visualization of intermediate solving states.
- `Počet iterácií` shows how many assignments the selected algorithm tried.

When an algorithm finishes, the window title indicates whether a solution was found. Profiling information is printed to the console.

## Implementation Notes

The solver represents each cell as:

- `W` for white island cells
- `B` for black wall cells
- `None` for unassigned cells during search

The predefined puzzles are stored directly in `Nurikabe_BelusakLuc.py` as 5x5 matrices, where `0` represents an empty cell and positive numbers represent island clues.

## Author

Jozef Belusak
