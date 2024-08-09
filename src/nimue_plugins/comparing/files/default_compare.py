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
import filecmp
import logging

import nimue_plugins.comparing
from nimue.utils.base import compare_files
from nimue.utils.logging import silent_logging_decorator

log = logging.getLogger(__name__)                 #
# ---------------------------------------------------------------------------


class DefaultComparator(nimue_plugins.comparing.FileComparator):

  _alias_ = 'comparing.files.default'
  _version_ = '1.0.0'

  @staticmethod
  def load_data(file_path, **params):
    """
    Load datasets from a file into a dictionary.

    Args:
        file_path (str): Path to the file.
        **params: Additional parameters.

    Returns:
        file_path (str): Path to the file.
    """
    return file_path

  @staticmethod
  def compare_data(data1, data2, **params):
    return not filecmp.cmp(data1, data2, shallow=False)

  @staticmethod
  @silent_logging_decorator(_alias_)
  def compare(nimue_data, **params):
    """
    Compares two JSON files specified in the nimue_data dictionary.
    Logs warnings if files don't exist, logs results of the comparison,
    and appends differences to a log report if files are not equal.
    """
    return compare_files(nimue_data,
                         DefaultComparator.load_data,
                         DefaultComparator.compare_data,
                         **params)
