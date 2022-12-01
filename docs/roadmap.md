# Roadmap

## Phase 1

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
- [x] add a `Union` type
- [x] add a `List` type
- [x] add a `Dict` type
- [x] automatic/lazy sub imports
- [x] add decorators
- [x] indexes used to track items
- [x] constructors for builtin types
- [x] `Path` type, uses python `Pathlib.Path` underneath
- [x] link handlers to resources
- [x] custom constructors
- [x] add relative imports
- [ ] implement `isinstance`
- [ ] inheritance for `resource`
- [ ] add `Tuple` data type and automatic unpacking of tuples
- [ ] add `for` keyword, to loop over lists, dicts and tuples
- [ ] expand type system to take module in to account when resolving types

Code cleanup:

- [ ] Implement an `expects` function for parser, raise if token is not correct type

### STD

- [x] add basic regex.match
- [x] add debug_msg (requires `None`)
- [x] add IPv4/IPv6 types
- [x] File module
- [x] Templates using jinja
- [ ] add `Host`, a resource that represents a machine.
- [ ] add `std.ssh.Command`. Runs a command on a machine.
- [ ] add `File` and `FileHandler`

### Engine

- [x] add `CRUDHandlers` and `HandlerContext`, that reflect how a resource is deployed
- [x] add exporter, that generates tasks and links these tasks to each other correctly
- [x] add deployer that takes tasks and executes them
