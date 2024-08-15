# Nimue RT
![nimue-rt](https://raw.githubusercontent.com/cogniteva/nimue-rt/master/docs/_static/nimue-logo.png)

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
nimue trace --config example.nimue path/to/archive.nrt your_module_name
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

Once you have a trace archive, you can use Nimue RT to perform non-regression tests.

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

The `.nimue` configuration file is the core of Nimue RT's functionality, enabling you to define the behavior for tracing and testing modules. This section provides a comprehensive overview of the options and structure available in a `.nimue` configuration file, using `examples/parscival/parscival.nimue` as a reference.

The `.nimue` configuration file typically contains the following main sections:

1. **version**: Defines the version of the configuration file format.
2. **options**: Specifies global options that apply to both tracing and testing.
3. **trace**: Defines settings and behaviors for tracing a module's execution.
4. **test**: Configures the behavior and settings for regression testing based on the traces.

Below is a detailed breakdown of each section and its configuration options.



### `version`

The `version` key indicates the version of the configuration format being used.

```yaml
version: "1.0"
```

This should be updated if there are breaking changes or new features added to the configuration format in future releases of Nimue RT.



### `options`

The `options` section defines global settings that apply to both the trace and test phases.

#### `trace`

The `trace` sub-section contains options for tracing module executions.

```yaml
options:
  trace:
    venv_path: "/tmp/parrun/.venv"
    retry_on_failure: 3
    failure_exit_code: 96
    remove_transient: always
    console: always
```

- **`venv_path`**: The path to the virtual environment that should be used during tracing.
- **`retry_on_failure`**: Number of retries allowed if the trace fails.
- **`failure_exit_code`**: The exit code that indicates a failure during tracing.
- **`remove_transient`**: Specifies when to remove transient data. Options are:
  - `always`: Always remove transient data after tracing.
  - `on_success`: Remove transient data only if tracing is successful.
  - `on_error`: Remove transient data only if tracing fails.
- **`console`**: Defines when to show the console output. Options are:
  - `always`: Always show console output.
  - `on_error`: Show console output only if an error occurs.
  - `never`: Never show console output.

#### `test`

The `test` sub-section contains options for running tests based on the traced execution.

```yaml
  test:
    venv_path: "/tmp/partest/.venv"
    retry_on_failure: 1
    failure_exit_code: 96
    remove_transient: on_success
    console: on_error
    show_test_log: on_error
    max_report_lines: 50
```

- **`venv_path`**: The path to the virtual environment that should be used during testing.
- **`retry_on_failure`**: Number of retries allowed if the test fails.
- **`failure_exit_code`**: The exit code that indicates a failure during testing.
- **`remove_transient`**: Specifies when to remove transient data. Options are the same as in the `trace` section.
- **`console`**: Defines when to show the console output during testing.
- **`show_test_log`**: Specifies when to show the test log. Options are:
  - `always`: Always show the test log.
  - `on_error`: Show the test log only if an error occurs.
  - `never`: Never show the test log.
- **`max_report_lines`**: Limits the number of lines displayed in the test report.



### `trace`

The `trace` section defines how the module tracing should be performed. This includes configurations for environment variables, file handling, and exit codes.

```yaml
trace:
  module:
    version:
      attributes_match:
        - '.*version.*'
```

#### `module`

The `module` sub-section allows you to specify how the module's version information should be captured.

- **`version.attributes_match`**: A list of regular expressions that match the attributes related to versioning within the module. These are used to capture the module's version information.

#### `environment`

The `environment` sub-section defines how environment variables should be handled during tracing.

```yaml
  environment:
    capture:
      - FOO
      - BAR
    module_prefixes: true
```

- **`capture`**: A list of environment variable names or prefixes that should be captured during tracing.
- **`module_prefixes`**: A boolean value indicating whether to capture environment variables that start with the module name or its variations (e.g., lowercased, capitalized).

#### `exit_codes`

The `exit_codes` sub-section configures how different exit codes should be handled during tracing.

```yaml
  exit_codes:
    store_skip:
    store_keep:
      - 0
```

- **`store_skip`**: A list of exit codes for which the trace data should not be stored.
- **`store_keep`**: A list of exit codes for which the trace data should always be stored.

#### `files`

The `files` sub-section defines patterns for files to ignore during tracing.

```yaml
  files:
    read:
      ignore:
        - "/bin/"
        - "/lib/"
    write:
      ignore:
        - "/tmp/"
```

- **`read.ignore`**: A list of patterns for files that should be ignored when reading during tracing.
- **`write.ignore`**: A list of patterns for files that should be ignored when writing during tracing.

### `test`

The `test` section configures how regression testing should be performed using the traces.

```yaml
test:
  module:
    version:
      attributes_match:
        - '.*version.*'
```

#### `module`

The `module` sub-section allows you to specify how the module's version information should be compared during testing.

- **`version.attributes_match`**: A list of regular expressions that match the attributes related to versioning within the module.

#### `comparing`

The `comparing` sub-section defines how different aspects of the module and its execution should be compared between the trace and the test run.

```yaml
  comparing:
    module:
      version:
        - plugin: 'comparing.metadata.semver'
          policy: warn
          enabled: true
          params:
            version: '${exec.module.version.__version__}'
            expression: '>=${nrt.module.version.__version__}'
```

- **`plugin`**: The name of the plugin used to compare the module version.
- **`policy`**: The policy to apply if the comparison fails. Options are `reject` or `warn`.
- **`enabled`**: A boolean indicating whether this comparison should be performed.
- **`params`**: Parameters passed to the plugin, allowing dynamic evaluation using variables such as `${exec.module.version.__version__}`.

#### `before_run` and `after_run`

These sub-sections allow you to define commands or scripts that should be run before or after the test.

```yaml
  before_run:
  after_run:
```

These sections are placeholders for commands that might be run to prepare the environment or clean up after the test.

#### `exit_codes`

The `exit_codes` sub-section configures how different exit codes should be handled during testing.

```yaml
  exit_codes:
    compare_skip:
    compare_test:
```

- **`compare_skip`**: A list of exit codes for which the comparison should be skipped.
- **`compare_test`**: A list of exit codes for which the comparison should be performed.

#### `comparing.trace`

The `trace` sub-section within `comparing` defines how the trace data should be compared during testing.

```yaml
      console:
        stdout:
          - plugin: 'comparing.console.content'
            policy: warn
            enabled: true
            params:
              min_similarity: 0.9
              clean_patterns:
                - '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
```

- **`console.stdout`**: Defines how to compare the standard output of the traced execution.
  - **`plugin`**: The name of the plugin used to compare the console output.
  - **`policy`**: The policy to apply if the comparison fails.
  - **`enabled`**: A boolean indicating whether this comparison should be performed.
  - **`params`**: Parameters passed to the plugin, such as `min_similarity` to define the acceptable similarity ratio and `clean_patterns` to define regex patterns to clean the output before comparison.

#### `files`

The `files` sub-section within `comparing.trace` defines how files read or written during execution should be compared.

```yaml
      files:
        read:
          hdf5:
            - plugin: 'comparing.files.hdf5'
              policy: reject
              enabled: true
              params:
```

- **`read` and `written`**: Define the file types to be compared, such as `hdf5`, `csv`, `json`, `yaml`, and `default`.
- **`plugin`**: The name of the plugin used for file comparison.
- **`policy`**: The policy to apply if the comparison fails.
- **`enabled`**: A boolean indicating whether this comparison should be performed.
- **`params`**: Additional parameters passed to the plugin.

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
