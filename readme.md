# Autodox

Tool for generating documentation automatically from code annotations, types,
and docstrings.

## Status

- [x] Code
- [x] Docs
- [x] Package published

## Usage

### Installation

```bash
pip install autodox
```

### Document a module from CLI

Use the following to document a module with default configuration:

```bash
autodox module_name [options] > target_file.md
```

The output can be configured with the following options:
- `-exclude_name=name` to exclude a specific part of the module by name
- `-exclude_type=type` to exclude any module parts of the given type
- `-package=module_name` to scope a relative import
- `-header_level=number` to increase the hashtag count in headers by `number`
- `-function_format=format` - can be one of 'header', 'paragraph', or 'list'
- `-method_format=format` - can be one of 'header', 'paragraph', or 'list'
- `-value_format=format` - can be one of 'header', 'paragraph', or 'list'
- `-include_private` to include things prefaced with '_'
- `-include_dunder` to include things prefaced with '__'
- `-include_submodules` to include submodules
- `-document_submodules` to run the module documentation for submodules
- `-debug` to increase the level of debug statements printed (starts at 0)

For experimentation and to learn how the options work, try running the following:

```bash
autodox autodox [options]
```

### Programmatic access

The autodox package can also be used by importing and running the desired
documentation function(s). The following are included.

- `dox_a_module(module: ModuleType, options: dict = None) -> str` produces docs for a module
- `dox_a_value(value: Any, options: dict = None) -> str` produces docs for a value
- `dox_a_function(function: Callable, options: dict = None) -> str` produces docs for a function
- `dox_a_class(cls: type, options: dict = None) -> str` produces docs for a class

The valid options for each will be described below. Additionally, there is a
system for setting up hooks that interact with the doc generation process to
change the inputs or outputs, and that will be described below the options for
the four `dox_a_{thing}` functions.

#### `dox_a_module(module: ModuleType, options: dict = None) -> str`

Produces docs for a module. Valid options are the following:

- `exclude_names: list[str]` - names to exclude from docs
- `exclude_types: list[str]` - types to exclude from docs
- `header_level: int` - number of additional hashtags to add to headers
- `include_private: bool` - if True, includes things with names prefaced by '_'
- `include_dunder: bool` - if True, includes things with names prefaced by '__'
- `include_submodules: bool` - if True, notes will be made about any additional
modules encountered when analyzing the specified module
- `document_submodules: bool` - if True, `dox_a_module` will be called
recursively on any additional modules encountered when analyzing the specified
module

#### `dox_a_value(value: Any, options: dict = None) -> str`

Produces docs for a value. Valid options are the following:

- `header_level: int` - number of additional hashtags to add to headers
- `format: str` - format can be one of 'header', 'paragraph', or 'list'

#### `dox_a_function(function: Callable, options: dict = None) -> str`

Produces docs for a function. Valid options are the following:

- `header_level: int` - number of additional hashtags to add to headers

#### `dox_a_class(cls: type, options: dict = None) -> str`

Produces docs for a class. Valid options are the following:

- `exclude_names: list[str]` - names to exclude from docs
- `header_level: int` - number of additional hashtags to add to headers
- `include_private: bool` - if True, includes things with names prefaced by '_'
- `include_dunder: bool` - if True, includes things with names prefaced by '__'
- `method_format: str` - can be one of 'header', 'paragraph', or 'list'

#### Hooks

There are eight events where custom functionality can be run, specified in the
`Event` enum:
- `AFTER_HEADER`
- `AFTER_PARAGRAPH`
- `AFTER_LIST`
- `BEFORE_VALUE`
- `AFTER_VALUE`
- `BEFORE_FUNCTION`
- `AFTER_FUNCTION`
- `BEFORE_CLASS`
- `AFTER_CLASS`
- `BEFORE_MODULE`
- `AFTER_MODULE`

Handlers for the `BEFORE_` events can be set using the `set_before_handler`
function. These handlers will receive the item to be documented and a dict
containing any options passed into the `dox_a_{thing}` function, and they should
return a tuple containing those two arguments after any modifications are made
to them. Example:

```python
from autodox import Event, set_before_handler
from typing import Callable


def handle_before_function(function: Callable, options: dict):
    # set an option
    options['header_level'] = 2
    return (function, options)

set_before_handler(Event.BEFORE_FUNCTION, handle_before_function)
```

Handlers for the `AFTER_` events can be set using the `set_after_handler`
function. These handlers will receive the str doc after the `dox_a_{thing}`
function has completed executing, and they should return that document after any
modifications are made. Example:

```python
from autodox import Event, set_after_handler


def handle_after_function(doc: str):
    # do some string manipulation
    return doc + 'But really, why would you call this function anyway?\n\n'

set_after_handler(Event.AFTER_FUNCTION, handle_after_function)
```

Muliple handlers can be set for each event, and they will be executed in order,
passing the output from the first as input to the second, etc. Example:

```python
from autodox import Event, set_after_handler


# add 'hello world' to the end of each list item in two steps
def hello(doc: str):
    return doc + ' hello'

def world(doc: str):
    return doc + ' world'

set_after_handler(Event.AFTER_LIST, hello)
set_after_handler(Event.AFTER_LIST, world)
```


## Testing

The test suite for this library is currently limited to hooks (14 tests) and a
few edge cases I encountered using the package (10 tests).

To test, clone the repository and run the following:

```
python test_hooks.py
python test_doxing.py
```

## ISC License

Copyleft (c) 2023 k98kurz

Permission to use, copy, modify, and/or distribute this software
for any purpose with or without fee is hereby granted, provided
that the above copyleft notice and this permission notice appear in
all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
