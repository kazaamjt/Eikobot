# Eikobot Desired State Engine

*The little Desired State Engine that made it so.*  

Eikobot is a desired state orchestrator.  
The basic idea is that you describe your infrastructure and eikobot
will make it happen.  

Eikobot is consists of the deployment engine and the Eiko language.  

The language is akin to python, as this is a commonly used language
and the language in which eikobot and eikobot plugins are written.  
It is an Object Oriented language that has some powerfull features.  
The most glaring thing is probably that the language has no functions,
but this is an omission by design.  

Some of it's notable features are:  

- Object oriented
- sees the infrastructure as a tree of resources, rather than a flatland
- completely stateless*

The quickest way to get started is probably by doing some of the [quickstarts](https://github.com/kazaamjt/Eikobot/blob/main/docs/quickstart.md).  
For a more complete idea of how the language works,
please see the [language overview](https://github.com/kazaamjt/Eikobot/blob/main/docs/language_overview.md).  

(*If the model/modules are designed well.)  

## Installation

Eikobot requires python 3.10 or up and has 3 external dependencies that can be installed using pip.  
In fact, Eikobot can be installed using pip as well.  

Here is an example of how to install Eikobot:  
(This should work on most platforms, although the python command is different if you are on windows)

```bash
python3.10 -m venv eikobot-venv
eikobot-venv/bin/pip install eikobot
```

You can now use the eikobot commands,
either by invoking them directly with their venv path:

```bash
eikobot-venv/bin/eikobot
```

Or by activating the venv first:

```bash
. eikobot-venv/bin/activate
eikobot
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
