# amortizer

This is a simple Dash app to plot a loan amortization (mainly a mortgage).

## Dev Setup

To install dependencies use [`uv`](https://docs.astral.sh/uv/).

```bash
pip install uv
```

```bash
uv sync
```

To build the executable, run

```bash
uv run pyinstaller -F amortizer.py
```
