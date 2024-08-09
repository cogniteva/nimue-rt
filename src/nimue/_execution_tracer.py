# -*- coding: utf-8 -*-
#
# Copyright (c) 2024  Cogniteva SAS
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# ---------------------------------------------------------------------------
import os
import sys
import time
import logging
import zipfile
import yaml
from datetime import datetime
from io import StringIO
from pathlib import Path
import pathspec
from contextlib import contextmanager
from nimue.utils.base import find_replace_values, normalize_path, redirect_stdout_stderr
from nimue._file_storage_manager import FileStorageManager
from nimue._module_loader import ModuleLoader
from nimue import __version__
# ---------------------------------------------------------------------------
log = logging.getLogger(__name__)
# ---------------------------------------------------------------------------


class ExecutionTracer:
  def __init__(self, options, config, module_name, *args, metadata_nrt=None):
    self.config = config
    self.metadata_nrt = metadata_nrt
    self.module_name = module_name
    # convert arguments to a list for YAML compatibility
    self.args = list(args)

    # assign global options
    self.options = options or {}

    self.options['venv_path'] = options.get('venv_path', '.venv')
    self.options['retry_on_failure'] = options.get('retry_on_failure', 3)
    self.options['failure_exit_code'] = options.get('failure_exit_code', 96)

    # Extract ignore patterns from the config
    trace_files_config = self.config.get('files', {})
    self.read_ignore_spec = pathspec.PathSpec.from_lines('gitwildmatch',
                                                         trace_files_config.get('read', {}).get('ignore', []) or [])
    self.write_ignore_spec = pathspec.PathSpec.from_lines('gitwildmatch',
                                                          trace_files_config.get('write', {}).get('ignore', []) or [])

    self.metadata_exec = {
        'module': {},
        'trace': {
            'host': {
                'gid': os.getgid(),
                'name': os.uname().nodename,
                'uid': os.getuid()
            },
            'paths': {
                'working': os.getcwd(),
                'venv': self.options['venv_path']
            },
            'environment': {},
            'arguments': self.args,
            'exitcode': None,
            'stats': {
                'start_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'duration': '0',
                'retries': 0
            },
            'files': {
                'read': set(),
                'written': set()
            },
            'console': {
                'stdout': '',
                'stderr': ''
            }
        }
    }

  @contextmanager
  def replace_open(self):
    original_open = open

    path_storage = ""
    if self.metadata_nrt:
      path_storage = normalize_path(
          os.path.join(
              self.metadata_nrt['test']['paths']['transient'],
              'storage'))

    def open_hook(file, open_mode='r', *args, **kwargs):
      """
      Hook function to open a file with added tracing capabilities.

      Args:
        file (str): The file path to open.
        open_mode (str): The mode in which the file is to be opened.
        *args: Additional arguments for the open function.
        **kwargs: Additional keyword arguments for the open function.

      Returns:
        file object: The opened file object.
      """

      def resolve_file_path(file):
        # check if file is in the read metadata
        if file in self.metadata_nrt['trace']['files']['read']:
          file_nrt = path_storage + file
          if Path(file_nrt).exists():
            return file_nrt
        else:
          file_placeholder = file
          # replace placeholders in file path
          for path_name in self.metadata_exec['trace']['paths']:
            path_variable_name = f"${path_name}_path"
            path_placeholder = os.path.join(path_variable_name, '')
            path_location = os.path.join(self.metadata_exec['trace']['paths'][path_name], '')
            file_placeholder = find_replace_values(file_placeholder, path_location, path_placeholder)

          # check if placeholder file is in the read metadata
          if file_placeholder in self.metadata_nrt['trace']['files']['read']:
            for path_name in self.metadata_nrt['trace']['paths']:
              path_variable_name = f"${path_name}_path"
              path_placeholder = os.path.join(path_variable_name, '')
              path_location = os.path.join(self.metadata_nrt['trace']['paths'][path_name], '')
              file_placeholder = find_replace_values(file_placeholder, path_placeholder, path_location)

            file_nrt = path_storage + file_placeholder
            if Path(file_nrt).exists():
              return file_nrt

        return file

      def record_file_access(file, mode):
        # normalize and resolve file path
        file_path = os.path.normpath(str(Path(file).resolve().absolute()))
        # record read access
        if 'r' in mode:
          self.metadata_exec['trace']['files']['read'].add(file_path)
        # record write/append access
        if any(m in mode for m in ['w', 'a', 'r+']):
          self.metadata_exec['trace']['files']['written'].add(file_path)

      # check if the file should be traced
      if self.should_trace(file, open_mode):
        # handle read mode
        if 'r' in open_mode:
          if not self.metadata_nrt:
            result = original_open(file, open_mode, *args, **kwargs)
          else:
            file = resolve_file_path(normalize_path(file))
            result = original_open(file, open_mode, *args, **kwargs)
        # handle read/write modes
        else:
          result = original_open(file, open_mode, *args, **kwargs)

        record_file_access(file, open_mode)
        return result
      else:
        return original_open(file, open_mode, *args, **kwargs)

    builtins = sys.modules['builtins']
    builtins.open = open_hook
    try:
      yield
    finally:
      builtins.open = original_open

  def should_trace(self, file, open_mode):
    normalized_file = normalize_path(file)
    if 'r' in open_mode and self.read_ignore_spec.match_file(normalized_file):
      return False
    if (('w' in open_mode or 'a' in open_mode or 'r+' in open_mode) and
        self.write_ignore_spec.match_file(normalized_file)):
      return False
    return True

  def trace_execution(self):
    # Extract console settings from config
    console_config = self.options.get('console', 'never')
    silent_stdout = True
    silent_stderr = True
    if console_config == 'on_error':
      silent_stderr = False
    elif console_config == 'always':
      silent_stdout = False
      silent_stderr = False

    # Capture stdout and stderr
    stdout_io = StringIO()
    stderr_io = StringIO()

    retries_total = self.options['retry_on_failure']
    retries_left = retries_total
    success = False
    start_time = datetime.now()
    self.metadata_exec['trace']['stats']['start_time'] = time.strftime('%Y-%m-%d %H:%M:%S')

    while retries_left > 0:
      try:
        retry_current = retries_total-retries_left + 1
        if retry_current > 1:
          log.info(f"Retry trace {retry_current}/{retries_total}")

        with self.replace_open(), redirect_stdout_stderr(stdout_io, stderr_io, silent_stdout, silent_stderr):
          try:
            loader = ModuleLoader(self.options['venv_path'], self.config)
            module = loader.import_module_from_virtualenv(self.module_name)
            if not module:
              raise AttributeError(
                  f"Module '{self.module_name}' not loaded.")

            self.metadata_exec['module'] = loader.metadata
            if hasattr(module, 'main'):
              module.main(self.args)
            else:
              raise AttributeError(
                  f"Module '{self.module_name}' does not have a 'main' function.")
            self.metadata_exec['trace']['exitcode'] = 0
            success = True
            # exit loop on success
            break
          except SystemExit as e:
            # Capture exit codes from sys.exit() calls
            self.metadata_exec['trace']['exitcode'] = e.code
            success = True
            # Exit loop on system exit
            break
          except Exception as e:
            self.metadata_exec['trace']['exitcode'] = self.options['failure_exit_code']
            log.error(e)

      except Exception as e:
        self.metadata_exec['trace']['exitcode'] = self.options['failure_exit_code']
        log.error(e)

      retries_left -= 1
      if retries_left > 0:
        log.info("Retrying...")

    # record end time and duration
    end_time = datetime.now()
    duration = end_time - start_time

    # update metadata
    self.metadata_exec['trace']['console']['stdout'] = stdout_io.getvalue()
    self.metadata_exec['trace']['console']['stderr'] = stderr_io.getvalue()
    self.metadata_exec['trace']['stats']['retries'] = retry_current
    self.metadata_exec['trace']['stats']['end_time'] = end_time.strftime('%Y-%m-%d %H:%M:%S')
    self.metadata_exec['trace']['stats']['duration'] = str(duration).split('.')[0]

    if not success and retries_left == 0:
      log.error("Failed after maximum retries")

  def capture_environment_variables(self):
    # Retrieve environment capture settings from config
    env_capture_config = self.config.get('environment', {}).get('capture', [])
    use_module_prefixes = self.config.get(
        'environment', {}).get('module_prefixes', True)

    env_vars = {}

    if use_module_prefixes:
      module_base = self.module_name.split('.')[0]
      module_prefixes = [module_base, module_base.lower(),
                         module_base.lower().capitalize(), module_base.upper()]
      env_vars.update({k: v for k, v in os.environ.items()
                      if k.startswith(tuple(module_prefixes))})

    for prefix in env_capture_config:
      env_vars.update({k: v for k, v in os.environ.items() if k.startswith(prefix)})

    self.metadata_exec['trace']['environment'] = env_vars

  def normalize_and_replace_arguments(self):
    normalized_args = []
    for arg in self.args:
      try:
        normalized_path = str(Path(arg).resolve().absolute())
        if (normalized_path in self.metadata_exec['trace']['files']['read'] or
            normalized_path in self.metadata_exec['trace']['files']['written']):
          normalized_args.append(normalized_path)
        else:
          normalized_args.append(arg)
      except Exception:
        normalized_args.append(arg)
    return normalized_args

  def update_metadata_paths(self):
    for path in self.metadata_exec['trace']['paths']:
      path_variable_name = "${" + f"{path}" + "_path}"
      self.metadata_exec = find_replace_values(self.metadata_exec,
                                               os.path.join(
                                                   self.metadata_exec['trace']['paths'][path], ''),
                                               os.path.join(path_variable_name, ''))

  def update_metadata(self):
    # Capture environment variables
    self.capture_environment_variables()

    # Convert sets to lists for YAML serialization
    self.metadata_exec['trace']['files']['read'] = list(self.metadata_exec['trace']['files']['read'])
    self.metadata_exec['trace']['files']['written'] = list(
        self.metadata_exec['trace']['files']['written'])

    # Normalize and replace arguments
    self.metadata_exec['trace']['arguments'] = self.normalize_and_replace_arguments()

  def must_store_test(self) -> bool:
    store_exit_codes = self.config.get(
        'exit_codes', {}).get('store_keep', []) or []
    skip_exit_codes = self.config.get(
        'exit_codes', {}).get('store_skip', []) or []
    skip_exit_codes.append(self.options['failure_exit_code'])

    actual_exitcode = self.metadata_exec.get('trace', {}).get('exitcode', self.options['failure_exit_code'])

    # must skip this exit code
    if actual_exitcode in skip_exit_codes:
      return False

    # must test this exit code
    if not store_exit_codes or actual_exitcode in store_exit_codes:
      return True

    return False

  def save_metadata(self, archive_path):
    # Custom representer to handle ordered representation
    def dict_representer(dumper, data):
      return dumper.represent_dict(data.items())

    yaml.add_representer(dict, dict_representer)

    config_data = yaml.dump(self.metadata_exec, indent=2, default_flow_style=False, width=80)
    manifest_content = f"nimue-version: {__version__}"

    with zipfile.ZipFile(archive_path, 'a', zipfile.ZIP_DEFLATED) as zipf:
      zipf.writestr('METADATA/config.yaml', config_data)
      zipf.writestr('METADATA/MANIFEST.txt', manifest_content)
      zipf.writestr('logs/trace/.keep', '')
      zipf.writestr('logs/test/.keep', '')

  def record_files(self, archive):
    FileStorageManager.record_files(self.metadata_exec, archive)
