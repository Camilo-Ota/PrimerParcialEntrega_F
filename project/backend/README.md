# Backend — Emergency Control

Python/FastAPI backend for the Emergency Control agent.

The solver is now a **Uniform-Cost Graph Search (UCS)** agent. The search state
is separated from node/history metadata and is canonicalized for graph search.
Battery dominance is handled with a Pareto-style check over the same physical
world: a state is dominated when another route reaches that world with
`g <= g_other` and residual battery `>= battery_other`. Successor generation
restricts `DROP` to capacity-releasing cases described in `design.md`.

## Structure

- `src/main.py` — FastAPI entry point.
- `src/agent.py` — public solver facade.
- `src/state.py` — immutable canonical physical state.
- `src/node.py` — search node (`g`, parent, action, depth).
- `src/actions.py` — `Applicable` and deterministic `Result`.
- `src/search.py` — UCS Graph Search and battery dominance.
- `src/simulator.py` — physical plan validator.
- `tests/` — search and integration tests.

## Run

```bash
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

## API

`POST /api/solve` accepts a scenario JSON and returns the existing frontend
contract:

```json
{
  "solution_found": true,
  "total_cost": 42,
  "steps": [],
  "message": "UCS solution found."
}
```

## Tests

```bash
cd backend
python -m pytest tests
```

The solver does not modify `scenario.json` to make the search easier.
