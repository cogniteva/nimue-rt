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

import h5py
from deepdiff import DeepDiff

import nimue_plugins.comparing
from nimue.utils.base import compare_files
from nimue.utils.logging import silent_logging_decorator

log = logging.getLogger(__name__)                 #
# ---------------------------------------------------------------------------


class HDF5Comparator(nimue_plugins.comparing.FileComparator):

  _alias_ = 'comparing.files.hdf5'
  _version_ = '1.0.0'

  @staticmethod
  def load_data(file_path, **params):
    """
    Load datasets from an HDF5 file into a dictionary.

    Args:
        file_path (str): Path to the HDF5 file.
        **params: Additional parameters.

    Returns:
        dict: A dictionary containing dataset names and their data.
    """
    data = {}
    with h5py.File(file_path, 'r') as f:
      def visit(name, node):
        if isinstance(node, h5py.Dataset):
          data[name] = node[()]
      f.visititems(visit)
    return data

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
                         HDF5Comparator.load_data,
                         HDF5Comparator.compare_data,
                         **params)
