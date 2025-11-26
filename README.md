## Local development

1. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies

```bash
poetry install
```

3. Run the application

```bash
poetry run uvicorn api.main:app --reload
```

## Docker workflow

Build the images (API and Postgres) with the provided Makefile target:

```bash
make build-docker
```

Then start the stack:

```bash
make start
```