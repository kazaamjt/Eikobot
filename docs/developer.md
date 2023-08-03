# Internal developer docs

Docs for the development of eikobot itself.  

## Creating and uploading a release

```bash
python -m build
twine upload --repository pypi dist/*
```

## Linters, type checkers, testing, etc

Currently this project uses:

- `mypy` for advanced type checking
- `isort` to auto format the imports
- `black` to auto format code
- `flake8` to do basic linting (and pointing out where isort and black would make changes)
- `pylint` for advanced linting and code smell detection
- `bandit` to scan for security issues

Note that the `flake8-isort` and `flake8-black` plugins are used,
and Flake8 will emit `isort` and `black` issues but not auto format them,
these tools will still need to be ran afterwards to fix any errors.  
The `Flake8-pylint` and `Flake8-mypy` plugins are not used as they are in broken state.  

For vscode, adding the following settings to your config is recommended:

```json
{
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.linting.pylintEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [],
    "editor.insertSpaces": true,
}
```

## Debugging

I often use a `test.eiko` and `test.py` file in the root of the project
for trying new ideas.  
These are ignored by git.  

Add the following to your vscode config to `launch.json`, to be able to debug them:

```json
 {
    "name": "Compile test.eiko",
    "type": "python",
    "request": "launch",
    "module": "eikobot",
    "justMyCode": true,
    "args": [
        "--debug",
        "compile",
        "-f",
        "test.eiko",
        "--output-model"
    ]
},
{
    "name": "Deploy test.eiko",
    "type": "python",
    "request": "launch",
    "module": "eikobot",
    "justMyCode": true,
    "args": [
        "--debug",
        "deploy",
        "-f",
        "test.eiko"
    ]
},
```
