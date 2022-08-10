# Eikobot Desired State Engine

The little Desired State Engine that made it so.  

## Roadmap

### Frontend

- [x] basic lexer
- [x] basic expression parser
- [x] basic types (bool, int, float, string)
- [x] Math and string operations
- [x] Resource definitions
- [x] base import system (`import some_module`)
- [x] basic typing (allowing expressions for typing)
- [x] cli commands
- [x] add `from` imports (`from some_module import some_thing`)
- [x] a plugin system
- [x] add typedefs
- [x] allow for complex types (Type parsing is wholy seperate now)
- [x] add a `None` type
- [x] add `Optional`, allowing for something to be either None or some other type.
- [x] allow for NotSet
- [x] add a `Union` type
- [x] add a `List` type
- [x] add a `Dict` type
- [x] automatic/lazy sub imports
- [ ] custom constructors

### STD

- [x] add basic regex.match
- [x] add debug_msg (requires `None`)
- [ ] add IPv4/IPv6

### Backend

- [ ] crud resource

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
