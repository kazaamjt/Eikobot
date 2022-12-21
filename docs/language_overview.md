# Eiko language overview

This overview assumes the user hase some knowledge of programming.  
The language itself is designed to mimic Python and
Python is required for writing `plugins` and `handlers`.  

Furthmore, knowledge of Pythons typing system is highle recommended.  

## The compile command

The base `eikobot` command is used to invoke everything required.  

In this tutorial, only the `compile` subcommand is of interest to us.  
Its `-f` flag is used to tell the compiler what file to read.  
Eikobot does not have a `repl`, it can only read files.  

In this case, to see the results of our compilation, we'll use `--output-model`.  
We'll also create a new file named `hello.eiko` and give it the following contents:  

```python
from std import debug_msg

debug_msg("hello world")
```

NOTE: Technically the entrypoint file doesn't have to be a `.eiko` file,
but other files need to be `.eiko` for them to be detected by the import system.  

We can then compile it like so:

```bash
eikobot compile -f hello.eiko
```

This should give us the following output as a result:

```txt
INFO Compiling hello.eiko
DEBUG_MSG hello world
INFO Done
INFO Compiled in 0:00:00.002391
```

Our debug message was printed.  

Another usefull function in the standard library is the `inspect` function.  
Use it to print objects to the screen in the examples that follow.  

## Comments

The hashtag (`#`) denotes a comment.  
The compiler completely ignores these.  

```python
a = 1 # This is a comment
```

There is no multiline comment.  

## Variables

In the eiko language, variables and properties cannot be reassigned.  
Once something is given a value, it cannot be changed.  
This is by design, as it, in general, makes working with desired state easier.  

For example, assigning the variable A twice, is not valid and will give an error:

```Python
a = "This is a string"
a = "This is illegal"
```

and when compiling, this happens:

```txt
INFO Compiling hello.eiko
ERROR CompilationError: Illegal operation: Tried to reassign 'a'.
    File "/home/yaron/hello.eiko", line 2
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

Also note that a forward declaration requires typing.  
A forward declaration without typing is not valid.  

Similarly, declaring the type of variable after it had already been assigned,
or was given a type declaration, is not valid.  

So this:

```Python
a = ""
a: str
```

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
Indexes can however, be used to access a specific element.  

So using a list looks like this:

```Python
new_list = ["Apple", "banana", "mango"]
new_list.append("pear")

new_list[2]  # "pear"
```

One can append after a list has been created or accessed.  

A list also has typing.  
When not typed, it takes all it's initial values and expresses the value as a union of those types.  
Its typing is expressed as `list[element_type]`, where `element_type` is a type expression of any kind.  

So a list of integers would be typed like this:

```Python
new_list: list[int] = [1, 2, 3]
```

This also means that a list needs either values OR typing when initialized.  

### Dicts

Dictionaries are mappings. They map a key to a value.  
Both keys and values can be any type.  

```Python
new_dict: dict[str, str] = {
    "key_1": "value_1",
    "key_2": "value_2",
    "key_3": "value_3",
}
```

Just like variables, keys cannot be reassigned, nor can keys or values be deleted.  
Note the typing, expressed as `dict[key_type, value_type]`.  
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

```Python
car = Car("toyota", 3)
```

Properties of a resource can be accessed using a `.`:

```Python
car.brand  # "toyota"
```

These properties ofcourse can be nested resources:

```Python
resource Wheel:
    Brand: str
    age: int

resource Car:
    brand: str
    wheels: list[Wheel]

car = Car(
    "Toyota",
    [
        Wheel("Toyota", 3),
        Wheel("Toyota", 3),
        Wheel("Toyota", 3),
        Wheel("Michelin", 1)
    ],
)

a = car.wheels[3].age
```

#### Custom constructors

While the default constructor might suffice in many cases,
sometimes we may want to create a custom constrctor.  
For example when the value of one property can be used
to fill in the value of other properties.  

A costructor looks much like one in Python does.  
Using the `def` keyword.  
To overwrite the default constructor, call it `__init__`.  
The first argument will always be the `self` argument, that should not have typing.  

For example:  

```Python
resource TestResource:
    prop_1: str
    prop_2: int
    prop_3: str

    def __init__(self, prop_1: str, prop_2: int):
        self.prop_1 = prop_1
        self.prop_2 = prop_2
        self.prop_3 = prop_1 + str(prop_2)

a = TestResource("test", 1)
```

Note that all properties have to be set in the constructor.  
The Compiler will throw an error if this happens.  

#### inheritance

Like in many Object Oriented languages, there is inheritance.  
A `resource` can inherit from another resource.  
It will not inherit any constructors or handlers, only properties.  
Ofcourse, a default constructor will still be generated.  

### typedefs

Typedefs allow for aliasing and narrowing of types.  
It currently can not be used in conjunction with a `resource`,
only basic types.  

It's most basic usage is to alias a type like so:  

```Python
typedef StrAlias str
```

Which creates a `StrAlias` type.  
This new type is considered a subtype of `str`,
meaning that things that accept a str, will accept our new `StrAlias` as well:  

```Python
typedef StrAlias str

a: str
b = StrAlias("test")

a = b
```

But, the inverse is not true.  
When expecting a StrAlias, a value of type `str` will not suffice:  

```Python
typedef StrAlias str

a: StrAlias = "test"
```

Besides simple aliassing, typedefs also allow for conditionals.  
For example, when creating a service,
the port it listens on will never be less than 1 or higher than 65535.  

Using a type condition, denoted by an `if`-statement following our typedef declaration,
we can specify our required condition.  
Note that this if statement runs inside it's own context where `self` is a reference:

```Python
typedef NetworkPort int if 1 <= self and self <= 65535
```

Now we can use NetworkPort as a type and are safe in the knownledge it's value will always be correct.  
When used as the type of a property for a resource, the compiler will even try to coerce the type:  

```Python
typedef NetworkPort int if 1 <= self and self <= 65535

resource Service:
    port: NetworkPort

s = Service(8080)
```

Further testing will also show our custom resource `Service` does not accept bad values:  

```Python
s = Service(-1)
```

## importing and modules

The Eiko language has modules and an import system.  
These are very similar to the way python does things.  

Let's start with the import system.  

### Imports

Imports allwos us to use code defined elsewhere.  
For example the `std` or standard library contains several convenience typedefs,
resources and plugins. (We'll come back later to the subject of plugins.)  

One such plugin is the `inspect` plugin, which prints an object to the console,
recursivly going over it's properties.  

To access this function, we can simply import the `std` module
and access `inspect` using a dot, eg: `std.inspect`.  

Let's take our earlier car example and inspect it:  

```Python
import std

resource Wheel:
    brand: str
    age: int

resource Car:
    brand: str
    wheels: list[Wheel]

car = Car(
    "Toyota",
    [
        Wheel("Toyota", 3),
        Wheel("Toyota", 3),
        Wheel("Toyota", 3),
        Wheel("Michelin", 1)
    ],
)

std.inspect(car)
```

This will output something akin to this:  

```txt
INFO Compiling test.eiko
INSPECT Car 'Toyota': {
    str 'brand': str "Toyota",
    list[Wheel] 'wheels': [
        Wheel 'Toyota': {
            str 'Brand': str "Toyota",
            int 'age': int 3,
        },
        Wheel 'Toyota': {
            str 'Brand': str "Toyota",
            int 'age': int 3,
        },
        Wheel 'Toyota': {
            str 'Brand': str "Toyota",
            int 'age': int 3,
        },
        Wheel 'Michelin': {
            str 'Brand': str "Michelin",
            int 'age': int 1,
        },
    ],
}
INFO Done
INFO Compiled in 0:00:00.003875
```

Importing somthing from a package is also possible,
using `from ... import ...` syntax, like so:  

```Python
from std import inspect

inspect(car)
```

### modules

Sometimes a single file will be too much to hold all your code and
you'll want to seperate out some code in to different files.  

This is where models come in.  
Models allows the compiler to use code spread out over different files.  
The simplest way to create a new module is just by creating a `.eiko` file,
next to the main file you're compiling.  
The Eikobot compiler automatically picks up files with the `.eiko` extension.  

For example, create the file `module_1` and put a variable in it:

```Python
a = "this is an import test"
```

Then, in the `hello.eiko` file, import this variable and print it:

```Python
from std import debug_msg
import module_1

debug_msg(module_1.a)
```

If files aren't enough, you can also gather related files together in a
directory and turn said directory in to a module.  
This can be done by adding a `__init__.eiko` file to the directory, like in python.  
This file can be empty, or it can contain code.  

As an example let's create the following file structure:  

```txt
module_2 /
    __init__.eiko
    submodule_1.eiko
    submodule_2.eiko
```

importing from the `__init__.eiko` file can be done like so:  

```Python
from module_2 import ...
```

And to import the submodules, or, import from the submodules:  

```Python
from module_2 import sumodule_1
from module_2.submodule_2 import ...
```

You could also not bother with seperate imports like this and just
import the top level module and access everything through dots:  

```Python
import module_2

module_2.submodule_1.something
```

Modules do not currently support relative imports like in python.  

## plugins

Plugins allow the programmer to write code in python and directly call it
from the Eiko code, with some limitations.  

Plugins are fully typed python functions decorated with the `@eiko_plugin()` decorator.  
To start adding plugins, create a python file with the same name as the file or
module you want to add the plugin to.  
The plugin can then be used inside this file or imported from outside this file,
like any other thing.  

for example, we could create a plugin in `hello.py` next to `hello.eiko`,
that concatenates 2 strings:

NOTE: this plugin ofcourse isn't very usfull as eiko supports string concatination using `+`.

```Python
from eikobot.core.plugin import eiko_plugin

@eiko_plugin()
def concat(string_1: str, string_2: str) -> str:
    return string_1 + string_2
```

Next, call the plugin, inside `hello.eiko`:

```Python
from std import inspect

a = concat("ha", "ha")
inspect(a)
```

The variable `a` now contains the string `"haha"`.  
Also note how the plugin has the python typing of `str`.  
The Eiko compiler will automatically convert python types to eiko objects and back,
but it is only able to do so for `str`, `int`, `bool` and `float`.  

If you are unsure about what type you will receive as an argument,
know that most anything in the Eiko language inherits from `eikobot.core.type.EikoBaseType`.  

lastly, plugins can raise an exception to indicate something is up.  
When raising an exception, use or inherit from `eikobot.core.plugin.EikoPluginException`.  

When a Python plugin raises an exception that isn't an `EikoPluginException`,
the compiler will catch it and can produce the python stacktrace using the `--enable-plugin-stacktrace` parameter.  

For example, continuing off of our earlier example with cars, we'll make a plugin that calculates
how long before you have replace a tire.  
Naturally this plugin will only except resources of type `Car`.  
We'll use the `EikoPluginException` to do some type checking.  
(Due to engine limitations, typing for plugins is somewhat limited.)  

So, let's make a `cars.eiko` file:

```Python
resource Wheel:
    brand: str
    age: int

resource Car:
    brand: str
    wheels: list[Wheel]
```

and then, in our python file `cars.py`, we write the plugin:

```Python
from eikobot.core.plugin import EikoPluginException, eiko_plugin
from eikobot.core.types import EikoList, EikoResource


@eiko_plugin()
def tires_that_should_be_replaced(car: EikoResource) -> EikoList:
    if car.type.name != "Car":
        raise EikoPluginException("Expected a resource of type 'Car'.")

    wheels: EikoList = car.properties.get("wheels")  # type: ignore
    wheels_to_replace = EikoList(element_type=wheels.type.element_type)
    for wheel in wheels.elements:
        if wheel.properties.get("age") > 5:  # type: ignore
            wheels_to_replace.append(wheel)

    return wheels_to_replace
```

Now there's a lot to unpack here.  
First, we check that the type of the resource passed is a Car.  
The compiler will make sure it is in fact an Eikoresource.  

Then we get the list of wheels.  
For `mypy`'s sake, we could do an `isinstance` check here to make sure
the wheels property is indeed a list.  
However the eiko compiler already did type checks for us, so we can assume this is correct.  

Then we create a new `EikoList`.  
But an `EikoList` requires knowing it's element type upon creation.  
Rather then trying to construct this type manually from scratch,
we pass a reference to the element type of the wheels list.  

Now, let's make a car with wheels and see if the need to be replaced.  

In our `hello.eiko` file:  

```Python
import std

from cars import Car, Wheel, tires_that_should_be_replaced

car = Car(
    "Toyota",
    [
        Wheel("Toyota", 7),
        Wheel("Toyota", 7),
        Wheel("Toyota", 7),
        Wheel("Michelin", 4)
    ],
)

std.inspect(tires_that_should_be_replaced(car))
```

When we compile `hello.eiko` with the command `eikobot compile -f hello.eiko --enable-plugin-stacktrace`,
it will actually show a stacktrace in this case, because there is a little bug in our plugin.  
In this case, it's because `Wheel.age` returns an `EikoInt`, not a python `int`.  
We can access the Python value by accessing `EIkoInt.value`.  

So when fix the problematic line:  

```Python
if wheel.properties.get("age").value > 5:  # type: ignore
```

The plugin will return a list of wheels that need to be replaced:

```txt
INFO Compiling hello.eiko
INSPECT [
    Wheel 'Toyota': {
        str 'brand': str "Toyota",
        int 'age': int 7,
    },
    Wheel 'Toyota': {
        str 'brand': str "Toyota",
        int 'age': int 7,
    },
    Wheel 'Toyota': {
        str 'brand': str "Toyota",
        int 'age': int 7,
    },
]
INFO Done
INFO Compiled in 0:00:00.003532
```

## handlers

Handlers are pieces of Python code that tell Eikobot _how_ to deploy a resource.  
A handler class is created by subclassing either `Handler`, `CRUDHandler` or `AsyncCRUDHandler`.  
All of these can be found in `eikobot.core.handlers`.  

In virtually all cases, you will want to subclass the `AsyncCRUDHandler`.  
Since pretty much every resource being read or deployed will involve networkIO,
using the async handler may have better performance while extra complexity is minimal.  
