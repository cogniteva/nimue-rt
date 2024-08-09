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
import sys
import os
import re
import importlib
import pkgutil
from pathlib import Path
# ---------------------------------------------------------------------------


class ModuleLoader:
  def __init__(self, venv_path, config):
    self.venv_path = venv_path
    self.config = config
    self.metadata = {}

  @staticmethod
  def list_all_modules():
    module_names = sorted(
        [name for _, name, _ in pkgutil.iter_modules()]
    )
    return module_names

  def activate_virtualenv(self):
    """
    Activate the virtual environment located at `self.venv_path`.
    """
    if not self.venv_path:
      return True

    try:
      venv_path = Path(self.venv_path)
      # the directory containing the site-packages
      site_packages_path = next(venv_path.rglob('site-packages'))
      if os.path.isdir(site_packages_path):
        # add the site-packages to sys.path
        sys.path.insert(0, str(site_packages_path))
        return True
      else:
        return False
    except Exception:
      return False

  def import_module_from_virtualenv(self, module_name):
    """
    Import a module from the specified virtual environment and add its version to metadata.
    """
    # Activate the virtual environment
    if not self.activate_virtualenv():
      return None

    # Import the module
    module = importlib.import_module(module_name)

    self.metadata['name'] = module_name

    # Retrieve configuration for matching attributes
    version_config = self.config.get('module', {}).get('version', [])
    attributes_match_patterns = version_config.get('attributes_match', ['.*version.*'])

    # Compile regex patterns
    match_patterns = [re.compile(pattern) for pattern in attributes_match_patterns]

    # Retrieve all attributes of the module
    all_attributes = dir(module)

    # Create a dictionary to store attribute names and their values, filtering for simple types
    simple_types = (str, int, float, bool)
    attributes_dict = {}
    for attr in all_attributes:
      try:
        value = getattr(module, attr)
        if isinstance(value, simple_types) and any(pattern.match(attr) for pattern in match_patterns):
          attributes_dict[attr] = value
      except Exception:
        return None

    # Add all attributes to metadata
    self.metadata['version'] = attributes_dict

    return module
