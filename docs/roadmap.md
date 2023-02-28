# Roadmap

## Phase 1

Phase 1 is all about the MVP.  
Writing the basic tutorials and quickstarts.  

### Compiler

Features and bug fixes:

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
- [x] add a `union` type
- [x] add a `list` type
- [x] add a `dict` type
- [x] automatic/lazy sub imports
- [x] add decorators
- [x] indexes used to track items
- [x] constructors for builtin types
- [x] `Path` type, uses python `Pathlib.Path` underneath
- [x] link handlers to resources
- [x] custom constructors
- [x] add relative imports
- [ ] add `isinstance`
- [x] inheritance for `resource`
- [x] add protected strings (strings that will not be printed)
- [ ] add `Tuple` data type and automatic unpacking of tuples
- [ ] add `for` keyword, to loop over lists, dicts and tuples
- [ ] expand type system to take module in to account when resolving types
- [ ] add `enum`
- [x] add `promise` (A piece of data that will be filled in during the deploy step)

Code cleanup:

- [ ] Implement an `expects` function for parser, raise if token is not correct type
- [x] Implement a `to_py` function on eiko objects, instead of using a conversion table

### STD

- [x] add basic regex.match
- [x] add debug_msg (requires `None`)
- [x] add IPv4/IPv6 types
- [x] File module
- [x] Templates using jinja
- [x] add `Host`, a resource that represents a machine.
- [x] ~~add `std.ssh.Command`. Runs a command on a machine.~~ (Replaced by `std.Cmd`)
- [x] add `File` and `FileHandler`
- [x] add `std.get_pass`
- [x] add `HostModel.execute` and `HostModel.execute_sudo` to execute commands
- [x] add `std.Cmd`, a single command that executes on a given remote host
- [ ] add `std.Script`, a collection of commands that are executed on a remote host

### Engine

- [x] add `Handler`, `CRUDHandler` and `HandlerContext`, that reflect how a resource is deployed
- [x] add exporter, that generates tasks and links these tasks to each other correctly
- [x] add deployer that takes tasks and executes them
- [x] add linked pydantic classes
- [x] add logging to HandlerContext
- [ ] add dry run to `deploy`

## Phase 2: Packages

Phase 2 is all about allowing reuse of code and such.  
The initial idea is to use GIT.  
