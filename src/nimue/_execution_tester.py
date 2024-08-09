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
import logging
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from box import Box

from nimue._execution_tracer import ExecutionTracer
from nimue.utils.base import find_replace_values, get_plugins_loader, looks_like_a_file_path

# ---------------------------------------------------------------------------
log = logging.getLogger(__name__)
# ---------------------------------------------------------------------------


class ExecutionTester:
  def __init__(self, config: Dict[str, Any]) -> None:
    self.config = config
    # extract global settings
    self.options = self.config['options'].get('test', {})
    self.venv_path = self.options.get('venv_path', '.venv')
    self.retry_on_failure = self.options.get('retry_on_failure', 3)
    self.failure_exit_code = self.options.get('failure_exit_code', 1)

    self.plugins = self.init_plugins()
    if self.plugins is None:
      raise ValueError("No plugins found")

  @staticmethod
  def find_all_plugins(config):
    """
    Recursively find all nodes with the key 'plugin' and 'enabled': True in the nested dictionary.

    Args:
      config (dict): The nested dictionary to search.

    Returns:
      dict: A dictionary with parent nodes as keys and list of plugins as values.
    """
    def search_plugins(node, parent_key='', found_plugins={}):
      if isinstance(node, dict):
        if 'plugin' in node and node.get('enabled', False):
          if parent_key not in found_plugins:
            found_plugins[parent_key] = []
          found_plugins[parent_key].append(node)
        for key, value in node.items():
          if key != 'plugin':
            new_parent_key = f"{parent_key}.{key}" if parent_key else key
            search_plugins(value, new_parent_key, found_plugins)
      elif isinstance(node, list):
        for item in node:
          search_plugins(item, parent_key, found_plugins)

      return found_plugins

    return search_plugins(config)

  def init_plugins(self) -> Optional[Dict[str, Any]]:
    plugin_group = 'comparing'
    loader = get_plugins_loader(plugin_group)
    # exit early if we failed to get the interface of the loader
    if loader is None:
      log.error(f"Failed to load plugins for plugin group '{plugin_group}'")
      return None

    # Get the nested dictionary of plugins
    plugins_loaded = loader.plugins

    # get the list of plugins used in all the test mode configuration
    plugins_required = ExecutionTester.find_all_plugins(self.config['test'].get(plugin_group, {}))

    # check if plugins exists
    for plugin_sequence in plugins_required.values():
      for plugin_node in plugin_sequence:
        plugin_id = plugin_node['plugin']
        plugin_group = '.'.join(plugin_id.split('.')[:2])
        if plugin_group not in plugins_loaded or plugin_id not in plugins_loaded[plugin_group]:
          log.error(
              f"Plugin '{plugin_id}' not found")

    plugins = {
      'loaded' :  plugins_loaded,
      'required': plugins_required
    }

    return plugins

  @staticmethod
  def extract_archive(archive_path: str) -> Optional[str]:
    transient_path = None
    try:
      transient_path = tempfile.mkdtemp(prefix='nimue-transient-')
      log.debug(f"Extracting archive to {transient_path}")
      with zipfile.ZipFile(archive_path, 'r') as zip_ref:
        zip_ref.extractall(transient_path)
    except Exception as e:
      log.error(f"Error extracting archive to {transient_path}: {e}")

    return transient_path

  @staticmethod
  def load_metadata_config(transient_path: str) -> Optional[Dict[str, Any]]:
    metadata = None
    try:
      config_path = Path(transient_path) / 'METADATA/config.yaml'
      log.debug(f"Loading test config from {config_path}")
      with open(config_path, 'r') as f:
        metadata = yaml.safe_load(f)
    except Exception as e:
      log.error(f"Error loading metadata from {config_path}: {e}")
    return metadata

  @staticmethod
  def restore_arguments_placeholders(metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
      for path_name in metadata['trace']['paths']:
        path_variable_name = "${" + f"{path_name}" + "_path}"
        path_placeholder = os.path.join(path_variable_name, '')
        path_location = os.path.join(metadata['trace']['paths'][path_name], '')
        metadata_trace_arguments = find_replace_values(
            metadata['trace']['arguments'], path_placeholder, path_location)
        metadata['trace']['arguments'] = metadata_trace_arguments
    except Exception as e:
      log.error(f"Error replacing placeholders for {path_placeholder}: {e}")
      return None
    return metadata

  @staticmethod
  def setup_working_environment(metadata: Dict[str, Any]) -> None:
    try:
      env_vars = metadata['trace']['environment']
      os.environ.update(env_vars)
      log.debug("Environment variables set")
      return True
    except Exception as e:
      log.error(f"Error setting environment: {e}")
      return False

  def execute_module(self, metadata_nrt: Dict[str, Any]) -> Dict[str, Any]:
    module_name = metadata_nrt['module']['name']
    args = metadata_nrt['trace']['arguments']
    tracer = ExecutionTracer(self.config['options']['test'],
                             self.config['trace'],
                             module_name,
                             *args,
                             metadata_nrt=metadata_nrt
                             )
    tracer.trace_execution()
    tracer.update_metadata()
    log.debug(f"Exit code: {tracer.metadata_exec['trace']['exitcode']}")
    return tracer.metadata_exec

  def trace_hooks(self, transient_path: str, metadata: Dict[str, Any], exec_result: Dict[str, Any], hook: str) -> None:
    hook_commands = self.config['test'].get(hook, [])
    if not hook_commands:
      return

    for command in hook_commands:
      log.info(f"Tracing {hook} command: {command}")
      subprocess.run(command, shell=True, check=True)

  def must_perform_compare(self, metadata_exec: Dict[str, Any]) -> bool:
    test_exit_codes = self.config['test'].get(
        'exit_codes', {}).get('compare_test', []) or []
    skip_exit_codes = self.config['test'].get(
        'exit_codes', {}).get('compare_skip', []) or []
    skip_exit_codes.append(self.failure_exit_code)

    actual_exitcode = metadata_exec.get('trace', {}).get('exitcode', self.failure_exit_code)

    # must skip this exit code
    if actual_exitcode in skip_exit_codes:
      return False

    # must test this exit code
    if not test_exit_codes or actual_exitcode in test_exit_codes:
      return True

    return False

  def list_paths_with_extensions(self, node, parent_key='', index=None, alt_ext='.default'):
    """
    Recursively list all paths in the dictionary. Add file extension if the value is a file.

    Args:
      node (dict or list): The dictionary or list to traverse.
      parent_key (str): The current path being traversed.

    Returns:
      list: A list of paths with extensions.
    """
    paths = []

    def add_extension(value, key):
      if (isinstance(value, str) and 'files.' in key or looks_like_a_file_path(value)):
        _, ext = os.path.splitext(value)
        return ext if ext else alt_ext
      return ''

    if isinstance(node, dict):
      if parent_key:
        node_name = parent_key if index is None else f"{parent_key}[{index}]"
        # add intermediate node
        paths.append({'id' : parent_key, 'alt_id': parent_key, 'name': node_name,
                      'key': parent_key, 'extension': '', 'index': index})
      for key, value in node.items():
        new_key = f"{parent_key}.{key}" if parent_key else key
        paths.extend(self.list_paths_with_extensions(value, new_key, None))
    elif isinstance(node, list):
      # add intermediate node
      if parent_key:
        node_name = parent_key if index is None else f"{parent_key}[{index}]"
        paths.append({'id' : parent_key, 'alt_id': parent_key, 'name': node_name,
                      'key': parent_key, 'extension': '', 'index': index})
      for index, item in enumerate(node):
        if (isinstance(item, str) and
            'files.' in parent_key or
            looks_like_a_file_path(item)):
          extension = add_extension(item, parent_key)
          new_key = f"{parent_key}{extension}"
          alt_key = f"{parent_key}{alt_ext}"
          node_name = new_key if index is None else f"{new_key}[{index}]"
          paths.append({'id' : new_key, 'alt_id': alt_key, 'name': node_name,
                        'key': parent_key, 'extension': extension, 'index': index})
        else:
          paths.extend(self.list_paths_with_extensions(item, parent_key, index))
    else:
      extension = add_extension(node, parent_key)
      new_key = f"{parent_key}{extension}" if extension else parent_key
      alt_key = f"{parent_key}{alt_ext}" if extension else parent_key
      node_name = new_key if index is None else f"{new_key}[{index}]"
      paths.append({'id' : new_key, 'alt_id': alt_key, 'name': node_name,
                    'key': parent_key, 'extension': extension, 'index': index})

    return paths

  def compare_metadata_nrt_exec(self,
                                metadata_nrt:  Dict[str, Any],
                                metadata_exec: Dict[str, Any]) -> Dict[str, int]:

    missing_key = '{missing}'
    node_paths = self.list_paths_with_extensions(metadata_nrt)

    box_nrt = Box(metadata_nrt, default_box=True,
                  box_dots=True, default_box_attr=missing_key)
    box_exec = Box(metadata_exec, default_box=True,
                   box_dots=True, default_box_attr=missing_key)

    compare_stats = {
      'total': 0,
      'succeed': 0,
      'warned': 0,
      'failed': 0,
      'errored': 0
    }

    for node_path in node_paths:
      node_path_id = node_path['id'] if node_path['id'] in self.plugins['required'] else node_path['alt_id']

      # check if there is a comparing plugin for this path
      if node_path_id in self.plugins['required']:
        for plugin_node in self.plugins['required'].get(node_path_id, {}):
          plugin_id = plugin_node['plugin']
          plugin_group = '.'.join(plugin_id.split('.')[:2])
          plugin = self.plugins['loaded'][plugin_group].get(plugin_id, None)
          if plugin_node.get('enabled', False) and plugin:
            compare_stats['total'] += 1

            # build the data to compare
            box_nimue_data = Box({
                'nrt': box_nrt,
                'exec': box_exec,
                'node_path': node_path,
                'plugin_id': plugin_id,
                'files': {
                  'log': None,
                  'report': None
                },
              },
               default_box=True,
               box_dots=True,
               default_box_attr=missing_key)

            plugin_policy = plugin_node.get('policy', 'reject')
            plugin_params = plugin_node.get('params', {}) or {}

            # try to call the plugin
            try:
              if not plugin.compare(box_nimue_data, **plugin_params):
                if plugin_policy == 'warn':
                  log.info(f"Test warn running plugin '{plugin_id}' with data from path '{node_path['name']}'")
                  compare_stats['warned'] += 1
                else:
                  log.info(f"Test fail running plugin '{plugin_id}' with data from path '{node_path['name']}'")
                  if box_nimue_data['files']['report']:
                    log.info(f"Report: {box_nimue_data['files']['report']}")
                  compare_stats['failed'] += 1
              else:
                compare_stats['succeed'] += 1
            except Exception as e:
              compare_stats['errored'] += 1
              log.error(f"Error running plugin {plugin_id} with data from path '{node_path['name']}'")
              log.error(f"{e}")

    return compare_stats

  @staticmethod
  def is_whitelisted_path(path: str, whitelist_keywords: List[str]) -> bool:
    """
    Check if the given path contains any of the whitelist keywords.

    Parameters:
      path (str): The path to check.
      whitelist_keywords (list): A list of keywords to whitelist.

    Returns:
      bool: True if the path contains any of the whitelist keywords, False otherwise.
    """
    return any(keyword in str(path) for keyword in whitelist_keywords)

  @staticmethod
  def clean_transient_directories(directories: List[str],
                                  whitelist: Optional[List[str]] = None,
                                  blacklist: Optional[List[str]] = None,
                                  whitelist_keywords: Optional[List[str]] = None) -> None:
    """
    Safely delete directories listed in the provided list.

    Parameters:
      directories (list): A list of directory paths to delete.
      whitelist (list): Directories allowed to be removed.
      blacklist (list): Directories not allowed to be removed.
      whitelist_keywords (list): A list of keywords that must be in the path to allow deletion.

    Raises:
      ValueError: If an attempt is made to delete a protected or root directory.
    """
    # set default whitelists and blacklists if not provided
    if whitelist is None:
      whitelist = []
    if blacklist is None:
      blacklist = ["/", "/bin", "/boot", "/dev", "/etc",
                   "/lib", "/proc", "/root", "/sys", "/usr", "/var"]
    if whitelist_keywords is None:
      whitelist_keywords = []

    for dir_path in directories:
      try:
        # normalize the path to avoid issues with trailing slashes
        path = Path(os.path.normpath(dir_path))

        # ensure the directory is not root
        if path == Path("/"):
          raise ValueError("Attempt to delete root directory is not allowed.")

        # check if path is in the blacklist
        if path in [Path(p) for p in blacklist]:
          raise ValueError(
              f"Attempt to delete a protected directory is not allowed: {path}")

        # if a whitelist is provided, ensure the path is within the whitelist
        if whitelist and path not in [Path(p) for p in whitelist]:
          raise ValueError(
              f"Attempt to delete a directory not in the whitelist: {path}")

        # check if the path contains any of the whitelist keywords
        if not ExecutionTester.is_whitelisted_path(path, whitelist_keywords):
          raise ValueError(f"Directory not whitelisted for deletion: {path}")

        # check if the directory exists before attempting to delete
        if path.exists() and path.is_dir():
          log.debug(f"Deleting directory: {path}")
          shutil.rmtree(path)
        else:
          log.warning(f"Directory not found or is not a directory: {path}")
      except Exception as e:
        log.error(f"{e}")

  @staticmethod
  def cleanup(transient_path: str) -> None:
    whitelist_keywords = ['/nimue-transient-']
    ExecutionTester.clean_transient_directories([transient_path],
                                                whitelist_keywords=whitelist_keywords)

  def trace_nrt(self, archive: str) -> dict:
    transient_path = self.extract_archive(archive)
    if transient_path is None:
      log.error("Failed to extract archive")
      return

    metadata_nrt = ExecutionTester.load_metadata_config(transient_path)
    if metadata_nrt is None:
      log.error("Failed to load metadata config")
      self.cleanup(transient_path)
      return

    # add transient_path to metadata
    metadata_nrt['test'] = {
      'paths': {
        'transient' : transient_path
      }
    }

    metadata_nrt = ExecutionTester.restore_arguments_placeholders(metadata_nrt)
    if metadata_nrt is None:
      log.error("Failed to restore working directory placeholders")
      self.cleanup(transient_path)
      return

    self.trace_hooks(transient_path, metadata_nrt, {}, 'before_run')

    if not ExecutionTester.setup_working_environment(metadata_nrt):
      log.error("Failed to setting up environment")
      self.cleanup(transient_path)
      return

    metadata_exec = self.execute_module(metadata_nrt)

    self.trace_hooks(transient_path, metadata_nrt, metadata_exec, 'after_run')

    success = True
    compare_results = {}

    if self.must_perform_compare(metadata_exec):
      success = False

      compare_results = self.compare_metadata_nrt_exec(metadata_nrt, metadata_exec)

      if compare_results['total'] == compare_results['succeed']:
        success = True
        log.info((f"{compare_results['succeed']}/{compare_results['total']}"
                  f" tests passed."))
      elif compare_results['total'] == compare_results['succeed'] + compare_results['warned']:
        success = True
        log.info((f"{compare_results['succeed']}/{compare_results['total']}"
                  f" tests passed. Other tests have have warnings."))
      elif compare_results['failed'] == 0 and compare_results['errored'] > 0:
        log.info((f"{compare_results['errored']}/{compare_results['total']}"
                  f" tests raised errors."))
      elif compare_results['errored'] == 0:
        log.info((f"{compare_results['failed']}/{compare_results['total']}"
                  f" tests failed. {compare_results['succeed']}/{compare_results['total']} tests passed."))
      else:
        log.info((f"{compare_results['failed']}/{compare_results['total']}"
                  f" tests failed. {compare_results['errored']}/{compare_results['total']} tests with errors."
                  f" {compare_results['succeed']}/{compare_results['total']} tests passed."))

      if success:
        log.info(f"[OK] Regression non detected for {archive}")
      else:
        log.info(f"[KO] Regression detected for {archive}")

    else:
      log.info(f"[--] Test skipped according to `compare_skip/compare_test` exit codes directive: {archive}")
      log.info(f"[--] Exit code: {metadata_exec['trace']['exitcode']}")

    # cleanup
    remove_transient = self.options.get('remove_transient', 'always')
    if (remove_transient == 'always' or
       (success is True and remove_transient == 'on_success') or
       (success is False and remove_transient == 'on_error')):
      ExecutionTester.cleanup(transient_path)

    return compare_results
# -----------------------------------------------------------------------------
