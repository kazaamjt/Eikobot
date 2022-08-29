# Basic language tutorial

This tutorial is to show the weirder sides of the Eiko language.  
It assumes the user hase some knowledge of programming.  

The language itself is designed to mimic Python.  

## The compile command

The base `eikobot` command is used to invoke everything required.  

In this tutorial, only the `compile` subcommand is of interest to us.  
Its `-f` flag is used to tell the compiler what file to read.  
Eikobot does not have a `repl`, it can only read files.  

Due to the backend not being ready, currently writing models doesn't really *do* anything,
but, you can already play around with the language.  

In this case, to see the results of our compilation, we'll use `--output-module`.  
We'll also create a new file named `hello.eiko` and give it the following contents:  

```python
from std import debug_msg

debug_msg("hello world")
```

NOTE: Technically the entrypoint file doesn't have to be a `.eiko` file,
other files need to be `.eiko` for them to be detected by the import system.  

We can then compile it like so:

```bash
eikobot compile -f hello.eiko --output-model
```

This should give us the following output as a result:

```
INFO Compiling hello.eiko
DEBUG_MSG hello world
INFO Model result:
Context '__main__': {
    Context 'std': {
        var 'debug_msg' plugin: Plugin 'debug_msg'
        var 'print' plugin: Plugin 'print'
    }
    var 'debug_msg' plugin: Plugin 'debug_msg'
}
```

Our debug message was printed.  
Don't worry too much about the model result that was printed.  
This is mostly for debugging and testing purposes.  

## Variables

The first quirk one will run in to using the Eiko language,
is variables and properties cannot be reassigned.  
Once something is given a value, it cannot be changed.  
This is by design as it, in general, makes working with desired state easier.  

For example, assigning the variable A twice, is not valid and will give an error:

```Python
a = "This is a string"
a = "This is illegal"
```

and when compiling, this happens:

```
INFO Compiling illegal_vars.eiko
ERROR CompilationError: Illegal operation: Tried to reassign 'a'.
    File "/home/yaron/projects/eikobot-tests/illegal_vars.eiko", line 2
        a = "This is illegal"
        ^
```

On the other hand, the Eiko language is fully typed and allows for forward declarations.  
Variables also infer their type when assigned a value.  
This means, the following code is valid:  

```Python
a = 7
b: int

if a < 5:
    b = 1
else:
    b = 2
```

But this is not:

```Python
a: int
a = "some string"
```

## Comments

The hashtag (`#`) denotes a comment.  
The compiler completely ignores these.  

There are no multiline comments.  

## Types and Typing

In the previous section we already got a taste of typing.  
Here we will delve a bit deeper.  
First off, the basic types:  

- Booleans: bool (`True` and `False`)
- Floating point numbers: float (`3.14`)
- integers: int (`7`)
- strings: str (`"This is a string"`)
- a none type: None (`None`)

### Strings

Strings have escape sequences, like most languages, and can be denoted by either `"` or `'`:  

```Python
"This test shows off escape \\ sequence parsing.\n"
```

Also notable are raw-strings and f-strings:

```Python
r"This is an example of a raw string.\n"
f"This is an f-string. 5 + 3 = {5 + 3}"
```

Raw strings ignore escape sequences, while f-strings evaluate expressions put between `{}`.  

### None

Much like in Python, the None value always refers to the same instance of the `None` object.  

### Lists

Lists can hold any object type and behave much like they would in other languages.  
With one key difference, elements cannot be removed from them,
nor can an index be used to assign a value or reassign a value.  
Indexes can be used to access a specific element.  

So using a list looks like this:

```Python
new_list = ["Apple", "banana", "mango"]
new_list.append("pear")

new_list[2]  # "pear"
```

Currently one can append after a list has been accessed, but this might change in the future,
for similar reasons that variables cannot be reassigned.  

A list also has typing.  
When not typed, it takes all it's initial values and expresses the value as a union of those types.  
Its typing is expressed as `List[element_type]`, where `element_type` is a type expression of any kind.  

So a list of integers would eb typed like this:

```Python
new_list: List[int] = [1, 2, 3]
```

This also means that a list needs either values OR typing when initialized.  

### Dicts

Dictionaries are mappings. They map a key to a value.  
Both keys and values can be any type.  

```Python
new_dict: Dict[str, str] = {
    "key_1": "value_1",
    "key_2": "value_2",
    "key_3": "value_3",
}
```

Just like variables, keys cannot be reassigned, nor can keys or values be deleted.  
Note the typing, expressed as `Dict[key_type, value_type]`.  
When not typed, it takes all it's initial keys and values,
and expresses the value as a union of those types.  

### Resources

Finaly we have the `resource` type.  
`resource` works in a similar way to `struct` or `class` in other languages to create custom objects.  

Using the `resource` keyword, indenting, and typing, we can define it's name and properties:

```Python
resource Car:
    brand: str
    number_of_doors: int
    number_of_wheels: int = 4
```

`resource` automatically has a default constructor created, using all it's properties.  
Properties become the arguments of the constructor, in are in the same order.  
They have to be typed.  
A property without default value must have a value passed at creation.  

Calling the constructor is as simple as just calling the class:

```
car = Car("toyota", 3)
```

Properties of a resource can be accessed using a `.`:

```Python

```
