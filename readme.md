# Autodox

Tool for generating documentation automatically from code annotations, types,
and docstrings.

## Status

- [ ] Code
- [ ] Tests
- [ ] Docs
- [ ] Package published

## Usage

### Installation

```bash
pip install autodox
```

### Document a module from CLI

Use the following to document a module with default configuration:

```bash
python -m autodox module_name > target_file.md
```

The output can be configured with the following options:
- `-exclude_name=name` to exclude a specific part of the module by name
- `-exclude_type=type` to exclude any module parts of the given type
- `-include_private` to include things prefaced with '_'
- `-include_dunder` to include things prefaced with '__'
- `-include_submodules` to include submodules
- `-document_submodules` to run the module documentation for submodules

### Programmatic access

The autodox package can also be used by importing and running the desired
documentation function(s). The following are included.

- `dox_a_module(module: ModuleType) -> str` produces docs for a module
- `dox_a_value(value: Any) -> str` produces docs for a value
- `dox_a_function(function: Callable) -> str` produces docs for a function
- `dox_a_class(class: type) -> str` produces docs for a class

## Testing

First, clone the repo, set up the virtualenv, and install requirements.

```bash
git clone ...
python -m venv venv/
source venv/bin/activate
pip install -r requirements.txt
```

For windows, replace `source venv/bin/activate` with `source venv/Scripts/activate`.

Then run the test suite with the following:

```bash
python test/test_functions.py
```

There are currently 0 tests.

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
