# Commit Issues

This is the source code of the X bot [Commitment Issues](https://x.com/issuescommit).

Uses the Github Public API to search for commits and selects the most funny ones.

### Running

You need to install [Poetry](https://python-poetry.org/)

```sh
# Installing all project dependencies
poetry install
```

Create the file `config.py` on `commitmentissues/` with the following structure:
```py
TWITTER_API_KEY = '<token>'
TWITTER_API_SECRET = '<token>'
TWITTER_ACCESS_TOKEN = '<token>'
TWITTER_ACCESS_TOKEN_SECRET = '<token>'
BEARER_TOKEN="<token>"
```

After that, just run the project:

```sh
poetry run python3 commitmentissues/commitmentissues.py
```
