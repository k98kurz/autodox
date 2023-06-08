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

The valid options will for each will be described below.

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


## ISC License

Copyleft (c) 2023 k98kurz

Permission to use, copy, modify, and/or distribute this software
for any purpose with or without fee is hereby granted, provided
that the above copyleft notice and this permission notice appear in
all copies.

Exceptions: this permission is not granted to Alphabet/Google, Amazon,
Apple, Microsoft, Netflix, Meta/Facebook, Twitter, or Disney; nor is
permission granted to any company that contracts to supply weapons or
logistics to any national military; nor is permission granted to any
national government or governmental agency; nor is permission granted to
any employees, associates, or affiliates of these designated entities.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
