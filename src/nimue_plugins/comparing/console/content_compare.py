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
import difflib
import logging
import re

import nimue_plugins.comparing
from nimue.utils.logging import silent_logging_decorator, append_to_log_report

log = logging.getLogger(__name__)                 #
# ---------------------------------------------------------------------------


class ContentComparator(nimue_plugins.comparing.ConsoleComparator):

  _alias_ = 'comparing.console.content'
  _version_ = '1.0.0'

  @staticmethod
  def clean_log_line(line, clean_patterns):
    """
    Cleans a log line by applying all given regex patterns.

    Args:
        line (str): The log line to clean.
        clean_patterns (list): A list of regex patterns to apply for cleaning.

    Returns:
        str: The cleaned log line.
    """
    for pattern in clean_patterns:
      line = re.sub(pattern, '', line)
    return line

  @staticmethod
  @silent_logging_decorator(_alias_)
  def compare(nimue_data, **params):
    # console nrt
    path_nrt = 'nrt.' + nimue_data['node_path.key']
    console_nrt = nimue_data[path_nrt]
    console_nrt_lines = [ContentComparator.clean_log_line(
      line, params.get('clean_patterns', {})) for line in console_nrt.split('\n')]

    # console exec
    path_exec = 'nrt.' + nimue_data['node_path.key']
    console_exec = nimue_data[path_exec]
    console_exec_lines = [ContentComparator.clean_log_line(
      line, params.get('clean_patterns', {})) for line in console_exec.split('\n')]

    ddiff = difflib.unified_diff(console_nrt_lines,
                                 console_exec_lines,
                                 lineterm='')

    list_ddiff = list(ddiff)
    if list_ddiff:
      append_to_log_report(nimue_data, list_ddiff)

    # Use SequenceMatcher to compute the similarity ratio
    matcher = difflib.SequenceMatcher(None, console_nrt_lines, console_exec_lines)
    similarity_score = matcher.ratio()

    if similarity_score >= params.get('min_similarity', 1.0):
      log.info("Console output match")
      return True

    log.info("Console output doesn't match")
    return False
