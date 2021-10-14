# Eikobot Desired State Engine

The little Desired State Engine that made it so.  

## Example

The basic building block is a *resource*.  
Comparable to class-object structures in other object oriented languages.  
if no constructor is specified, a default one is generated using all properties.  

```
resource Host:
    ip: IpAddress
    ssh_key: str


resource Debian(Host):
    version: int


resource Windows(Host):
    version: str
```

Resources can have a custom constructor:  

```
resource WebServer:
    host: Host
    software: str

    implement default(self, host: Host):
        self.host = host
        self.software = "nginx"
```

But you can also create multiple constructors and overload them:  

```
resource WebServer:
    host: Host
    software: str

    implement default(self, host: Host):
        self.host = host
        software = "nginx"

    implement specific(self, host: Host, software: str):
        self.host = host
        self.software = software
```

Lastly, we can use constraints on top of overloading them.  

```
resource WebServer:
    host: Host
    software: str

    @constraint(isinstance(host, Debian))
    implement debian(self, host: Host):
        self.host = host
        software = "nginx"

    @constraint(isinstance(host, Windows))
    implement windows(self, host: Host):
        self.host = host
        self.software = "iis"
```

Now the correct constructor will be selected based on what type of host it is.  
Note that the above example without the constraints would not be valid,
as both constructors have the same signature and the compiler wouldn't know
which one to use.  

## Linters, type checkers, testing, etc

Currently this project uses:

- `mypy` for advanced type checking
- `isort` to auto format the imports
- `black` to auto format code
- `flake8` to do basic linting (and pointing out where isort and black would make changes)
- `pylint` for advanced linting and code smell detection

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
    "editor.insertSpaces": true,
}
```
