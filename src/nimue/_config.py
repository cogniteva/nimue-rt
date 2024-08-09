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
import yaml
import logging
# ---------------------------------------------------------------------------
log = logging.getLogger(__name__)
# ---------------------------------------------------------------------------


def find_nimue_config():
  search_paths = [
      # Current working directory
      os.getcwd(),
      # Script directory
      os.path.dirname(os.path.abspath(__file__)),
      # User's home directory
      os.path.expanduser('~'),
  ]

  for path in search_paths:
    config_path = os.path.join(path, '.nimue')
    if os.path.isfile(config_path):
      return config_path
  return None


def update_config(d, u):
  for k, v in u.items():
    if isinstance(v, dict):
      d[k] = update_config(d.get(k, {}), v)
    else:
      d[k] = v
  return d


def load_nimue_config(custom_config_path: str = None):
  # define the default configuration
  default_config = {
  }

  # initialize config with default settings
  config = default_config

  # check for a config file found by find_nimue_config
  config_path = find_nimue_config()
  if config_path and os.path.exists(config_path):
    with open(config_path, 'r') as f:
      user_config = yaml.safe_load(f)
      config = update_config(config, user_config)

  # if a custom config file is provided via -c, update the config with its content
  if custom_config_path and os.path.exists(custom_config_path):
    with open(custom_config_path, 'r') as f:
      custom_config = yaml.safe_load(f)
      config = update_config(config, custom_config)
      config_path = custom_config_path

  return config_path, config
