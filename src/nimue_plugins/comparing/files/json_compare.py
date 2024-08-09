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
import json
import logging

from deepdiff import DeepDiff

import nimue_plugins.comparing
from nimue.utils.base import compare_files
from nimue.utils.logging import silent_logging_decorator

log = logging.getLogger(__name__)                 #
# ---------------------------------------------------------------------------


class JSONComparator(nimue_plugins.comparing.FileComparator):

  _alias_ = 'comparing.files.json'
  _version_ = '1.0.0'

  @staticmethod
  def load_data(file_path, **params):
    with open(file_path, 'r') as f:
      return json.load(f)

  @staticmethod
  def compare_data(data1, data2, **params):
    return DeepDiff(data1, data2)

  @staticmethod
  @silent_logging_decorator(_alias_)
  def compare(nimue_data, **params):
    """
    Compares two JSON files specified in the nimue_data dictionary.
    Logs warnings if files don't exist, logs results of the comparison,
    and appends differences to a log report if files are not equal.
    """
    return compare_files(nimue_data,
                         JSONComparator.load_data,
                         JSONComparator.compare_data,
                         **params)
