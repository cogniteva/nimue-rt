# Nimue RT

Nimue RT is an experimental regression testing framework designed to simplify and streamline the process of testing and validating Python modules. It supports a wide range of file formats, execution environments, and custom plugins to provide a flexible and powerful testing environment.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [Plugins](#plugins)
- [License](#license)

## Installation

To install Nimue RT, you can use pip:

```bash
pip install nimue-rt
```

## Quick Start

Here's a simple example to get you started with Nimue RT:

1. Create a Nimue configuration file (e.g., `example.nimue`):

```yaml
version: "1.0"

options:
  trace:
    venv_path: "/path/to/venv"
    retry_on_failure: 3
    failure_exit_code: 96
    remove_transient: always
    console: always

trace:
  module:
    version:
      attributes_match:
        - '.*version.*'
```

2. Run a trace:

```bash
nimue trace --config example.nimue your_module_name
```

3. Run a regression test:

```bash
nimue test --config example.nimue path/to/archive.nrt
```

## Usage

### Tracing a Module Execution

Nimue RT allows you to trace the execution of a Python module and save the trace data for future regression testing.

```bash
nimue trace --config example.nimue path/to/archive.nrt your_module_name
```

### Running a Regression Test

Once you have a trace archive, you can use Nimue RT to perform regression tests.

```bash
nimue test --config example.nimue path/to/archive.nrt
```

### Command Line Interface

You can use the following commands with Nimue:

- `nimue trace [options] archive module_name [module_args...]`: Trace a module's execution and store it in an archive.
- `nimue test [options] archive`: Run a regression test using the trace archive.

### Options

- `-c, --config`: Specify a custom Nimue configuration file.
- `--version`: Show the current version of Nimue RT.
- `-v, --verbose`: Set the log level to INFO.
- `-vv, --very-verbose`: Set the log level to DEBUG.


## Configuration

Nimue RT uses a YAML configuration file to define various aspects of tracing and testing. The configuration can include:

- Global options for tracing and testing.
- Module-specific configurations for versioning and environment variables.
- File-specific ignore patterns.
- Plugin configurations for custom comparison logic.

### Example Configuration

```yaml
version: "1.0"

options:
  trace:
    venv_path: "/path/to/venv"
    retry_on_failure: 3
    failure_exit_code: 96
    remove_transient: always
    console: always

trace:
  module:
    version:
      attributes_match:
        - '.*version.*'
  environment:
    capture:
      - FOO
      - BAR
    module_prefixes: true
  files:
    read:
      ignore:
        - "/bin/"
        - "/lib/"
    write:
      ignore:
        - "/tmp/"
```

## Plugins

Nimue RT supports custom plugins for comparing files, console outputs, exit codes, and metadata. Plugins can be used to extend the default behavior and integrate specific comparison logic.

### Available Plugins

- **File Comparators**:
  - `comparing.files.default`: Default file comparator.
  - `comparing.files.yaml`: YAML file comparator.
  - `comparing.files.json`: JSON file comparator.
  - `comparing.files.hdf5`: HDF5 file comparator.
  - `comparing.files.csv`: CSV file comparator.

- **Console Comparators**:
  - `comparing.console.content`: Compares console output content.

- **Exit Code Comparators**:
  - `comparing.exitcode.value`: Compares exit codes using expressions.

- **Metadata Comparators**:
  - `comparing.metadata.semver`: Compares semantic versions using semver.

### Custom Plugins

You can create custom plugins by defining them in Python and registering them with Nimue RT's plugin system.

## License

Nimue RT is licensed under the MIT License. See the [LICENSE](LICENSE.txt) file for more information.
