# Eikobot Desired State Engine

The little engine that made it so.  

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

## Linters, type checkers, etc

Currently this project uses:

- `mypy` for type checking
- `isort` to auto format the imports
- `black` to auto format code
- `flake8` to do basic linting (and pointing out where isort and black would make changes)
- `pylint` for it's advanced linting and code smell detection

Note that the `flake8-isort` and `flake8-pylint` plugins are used,
so that only 1 linting command has to be used for 3 linters.  
Flake8 will emit `isort` changes but not auto format them,
isort still needs to be ran afterwards to fix any errors.  

for vscode, adding the following settings to your config is recommended:

```json
{
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.linting.pylintEnabled": true,
    "python.testing.pytestEnabled": true,
    "editor.insertSpaces": true,
}
```
