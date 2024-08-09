# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 Cogniteva SAS
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

from asteval import Interpreter

import nimue_plugins.comparing
from nimue.utils.base import resolve_interpolated_variables
from nimue.utils.logging import silent_logging_decorator

log = logging.getLogger(__name__)                 #
# ---------------------------------------------------------------------------


class ValueComparator(nimue_plugins.comparing.ExitCodeComparator):

  _alias_ = 'comparing.exitcode.value'
  _version_ = '1.0.0'

  @staticmethod
  @silent_logging_decorator(_alias_)
  def compare(nimue_data, **params):

    expression = params.get('expression', '')
    expression_resolved = resolve_interpolated_variables(expression, nimue_data)

    log.info("Comparing exit codes using expression:")
    log.info(f"'{expression}' expanded as: '{expression_resolved}'")

    aeval = Interpreter()

    result = aeval(expression_resolved)
    if len(aeval.error) > 0:
      for err in aeval.error:
        log.error(err.get_error())
      return False

    if result is True:
      log.info("Exit codes match")
      return True

    log.error("Exit codes doesn't' match")
    return False
