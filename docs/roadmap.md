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
- [ ] add `isinstance`
- [x] inheritance for `resource`
- [x] add protected strings (strings that will not be printed)
- [ ] add `Tuple` data type and automatic unpacking of tuples
- [ ] add `for` keyword, to loop over lists, dicts and tuples
- [ ] expand type system to take module in to account when resolving types
- [ ] add `enum`
- [ ] add `Promise` (A piece of data that will be filled in during the deploy step)

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
- [x] add `std.ssh.Command`. Runs a command on a machine.
- [x] add `File` and `FileHandler`
- [x] add `std.get_pass`

### Engine

- [x] add `CRUDHandlers` and `HandlerContext`, that reflect how a resource is deployed
- [x] add exporter, that generates tasks and links these tasks to each other correctly
- [x] add deployer that takes tasks and executes them
- [x] add linked pydantic classes
- [ ] add logging to HandlerContext
- [ ] add dry run to the `deploy`