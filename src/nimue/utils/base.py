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
import importlib.util
import logging
import os
import re
import site
import sys
from contextlib import contextmanager
from pathlib import Path

import pluginlib

from nimue.utils.logging import append_to_log_report

# ---------------------------------------------------------------------------
log = logging.getLogger(__name__)
# ---------------------------------------------------------------------------


def find_replace_values(d, to_find, to_replace):
  """
  Recursively replace all occurrences of a substring `foo` with `bar` in a dictionary `d`.

  Parameters:
  d (dict): The dictionary to process.
  foo (str): The substring to find.
  bar (str): The substring to replace `foo` with.
  """
  if isinstance(d, dict):
    for key, value in d.items():
      if isinstance(value, dict):
        find_replace_values(value, to_find, to_replace)
      elif isinstance(value, list):
        for i, item in enumerate(value):
          if isinstance(item, (dict, list, str)):
            value[i] = find_replace_values(item, to_find, to_replace)
      elif isinstance(value, str):
        d[key] = value.replace(to_find, str(to_replace))
  elif isinstance(d, list):
    for i, item in enumerate(d):
      if isinstance(item, (dict, list, str)):
        d[i] = find_replace_values(item, to_find, to_replace)
  elif isinstance(d, str):
    d = d.replace(to_find, str(to_replace))
  return d


def normalize_path(file):
  return os.path.normpath(str(Path(file).resolve().absolute()))


@contextmanager
def redirect_stdout_stderr(stdout_obj, stderr_obj, silent_stdout=False, silent_stderr=False):
  old_stdout = sys.stdout
  old_stderr = sys.stderr

  class DualWriter:
    def __init__(self, primary, secondary, silent=False):
      self.primary = primary
      self.secondary = secondary
      self.silent = silent

    def write(self, data):
      if not self.silent:
        self.primary.write(data)
      self.secondary.write(data)

    def flush(self):
      if not self.silent:
        self.primary.flush()
      self.secondary.flush()

  sys.stdout = DualWriter(sys.stdout, stdout_obj, silent=silent_stdout)
  sys.stderr = DualWriter(sys.stderr, stderr_obj, silent=silent_stderr)

  try:
    yield
  finally:
    sys.stdout = old_stdout
    sys.stderr = old_stderr


def get_plugins_loader(plugin_group, package_name='nimue_plugins'):
  """get the pluginlib interface to import and access plugins of a targeted type

  Args:
    plugin_group(str): Retrieve plugins of a group ('comparing', ...)

  Returns:
    Class: Interface for importing and accessing plugins
  """
  # get the plugin loader
  loader = pluginlib.PluginLoader()

  # return early if the group is already loaded
  if loader is not None and plugin_group in loader.plugins:
    return loader

  try:
    # get the semicolon delimited list of paths from environment
    plugins_paths = os.getenv('NIMUE_PLUGINS_PATHS')

    # create a list of paths
    if plugins_paths is not None:
      plugins_paths = plugins_paths.split(';')
    else:
      plugins_paths = []

    # find the location of the package
    package_spec = importlib.util.find_spec(package_name)
    if package_spec and package_spec.submodule_search_locations:
        # Use the first location listed in submodule_search_locations
      package_path = Path(package_spec.submodule_search_locations[0])
      plugins_fallback_path = str(package_path)
      plugins_paths.insert(0, plugins_fallback_path)

    if not plugins_fallback_path:
      # compute a fallback path relative to project
      plugins_fallback_path = str(Path.joinpath(
          Path(__file__).parent.parent.parent.relative_to
          (Path(__file__).parent.parent.parent.parent),
          package_name))
      plugins_paths.insert(0, plugins_fallback_path)

    # add some extra paths from site-packages directories
    sitepackages = site.getsitepackages() + [site.getusersitepackages()]
    for path in sitepackages:
      plugins_paths.insert(0, str(Path.joinpath(Path(path), package_name)))

    # append the plugin type to each of paths
    plugins_type_paths = [os.path.join(p, plugin_group) for p in plugins_paths]
    # remove non-existing paths
    plugins_type_paths = [p for p in plugins_type_paths if os.path.isdir(p)]

    # test if there is at least one valid path
    if not plugins_type_paths:
      log.error("There are not valid paths pointed out by '%s'",
                'NIMUE_PLUGINS_PATHS')
      return None

    # recursively load plugins from paths
    loader = pluginlib.PluginLoader(paths=plugins_type_paths)

  except pluginlib.PluginImportError as e:
    if e.friendly:
      log.error("{}".format(e))
    else:
      log.error("Unexpected error loading %s plugins", plugin_group)
    return None

  # and return loader
  return loader


def looks_like_a_file_path(path):
  """
  Check if the given path is a file path.

  Args:
    path (str): The path to check.

  Returns:
    bool: True if it looks like a file path, False otherwise.
  """
  if not isinstance(path, str):
    return False

  # Check if the path is an existing file
  if os.path.isfile(path):
    return True

  return False


def resolve_interpolated_variables(expression: str, data) -> str:
  """
  Resolve a variable from expression based on data.

  Returns:
      str: The resolved value as a string.
  """
  # Find all variables in the expression
  variables = re.findall(r'\${(.*?)}', expression)

  # Resolve each variable
  for var in variables:
    resolved_value = data.get(var, None)
    if resolved_value is None:
      raise ValueError(f"Unable to resolve '{var}' for expression '{expression}'")
    expression = find_replace_values(expression, f'${{{var}}}', resolved_value)
  return str(expression)


def compare_files(nimue_data, load_function, compare_function, **params):
  """
  Compares two files specified in the nimue_data dictionary using the provided
  load and compare functions. Logs warnings if files don't exist, logs results
  of the comparison, and appends differences to a log report if files are not equal.

  Args:
      nimue_data (dict): Dictionary containing information about the files to compare.
      load_function (callable): Function to load the file contents.
      compare_function (callable): Function to compare the loaded file contents.
      **params: Additional parameters (currently unused).
  """
  try:
      # Construct the test file path
    path_test = 'nrt.' + nimue_data['node_path.key']
    if nimue_data['node_path.index'] is None:
      file_test = nimue_data[path_test]
    else:
      file_test = nimue_data[path_test][nimue_data['node_path.index']]

    # Check if the test file exists
    if not Path(file_test).exists():
      log.warning(f"File {file_test} doesn't exist")
      return True

    # Construct the nrt file path
    file_nrt = (Path(nimue_data['nrt.test.paths.transient']) /
                'storage' / Path(file_test).relative_to(Path(file_test).anchor))

    # Check if the nrt file exists
    if not Path(file_nrt).exists():
      log.warning(f"File {file_nrt} doesn't exist")
      return True

    # Load and compare the files using the provided functions
    data1 = load_function(file_nrt, **params)
    data2 = load_function(file_test, **params)
    ddiff = compare_function(data1, data2, **params)

    # Check if there are differences
    if not bool(ddiff):
      log.info("Files are equal")
      return True

    # Append differences to the log report and log the result
    append_to_log_report(nimue_data, ddiff)
    log.info("Files are not equal")
    return False

  except Exception as e:
    raise e
