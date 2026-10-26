# Env Key Matrix

Env Key Matrix compares the variable names in multiple dotenv files and shows which environments define each key. It never prints configuration values, making it useful for reviewing `.env.local`, staging, and production drift without pasting secrets into a report.

## Usage

```bash
python env_key_matrix.py .env.local .env.staging .env.production
python env_key_matrix.py .env.example .env.production --json
python -m unittest discover -v
```

Keys missing from one or more files, duplicate assignments, and malformed non-comment lines produce a nonzero result. Exit codes are `0` when all files have the same clean key set, `1` when drift or file issues are found, and `2` when an input file is missing.

The parser reads assignment names only. It does not expand variables, evaluate shell expressions, or contact a network service. Values are used only as part of reading lines and are never included in text or JSON output.

## Development

Python 3.10 or newer. The project uses only the Python standard library.

## License

MIT
