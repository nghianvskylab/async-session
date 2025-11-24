1. Create venv
```bash
python3 -m venv venv
```

```bash
source venv/bin/activate
```

```bash
poetry install
```

2. Run application

```bash
poetry run uvicorn api.main:app --reload
```