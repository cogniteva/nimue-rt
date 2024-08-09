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

import pluginlib

from nimue.utils.logging import silent_logging_decorator
# ---------------------------------------------------------------------------
log = logging.getLogger(__name__)                 #
# ---------------------------------------------------------------------------


@pluginlib.Parent('comparing.files')
class FileComparator():
  """
  Base class for comparing tasks
  """
  _alias_ = 'comparing.files'
  _version_ = '1.0.0'

  @staticmethod
  @pluginlib.abstractmethod
  def compare(nimue_data, **params):
    pass


@pluginlib.Parent('comparing.console')
class ConsoleComparator():
  """
  Base class for comparing tasks
  """
  _alias_ = 'comparing.console'
  _version_ = '1.0.0'

  @staticmethod
  @pluginlib.abstractmethod
  def compare(nimue_data, **params):
    pass


@pluginlib.Parent('comparing.metadata')
class MetadataComparator():
  """
  Base class for comparing tasks
  """
  _alias_ = 'comparing.metadata'
  _version_ = '1.0.0'

  @staticmethod
  @pluginlib.abstractmethod
  @silent_logging_decorator(_alias_)
  def compare(nimue_data, **params) -> bool:
    pass


@pluginlib.Parent('comparing.exitcode')
class ExitCodeComparator():
  """
  Base class for comparing tasks
  """
  _alias_ = 'comparing.exitcode'
  _version_ = '1.0.0'

  @staticmethod
  @pluginlib.abstractmethod
  @silent_logging_decorator(_alias_)
  def compare(nimue_data, **params):
    pass
