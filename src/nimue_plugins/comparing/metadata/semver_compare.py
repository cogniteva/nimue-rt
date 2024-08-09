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

import semver

import nimue_plugins.comparing
from nimue.utils.base import resolve_interpolated_variables
from nimue.utils.logging import silent_logging_decorator
# ---------------------------------------------------------------------------
log = logging.getLogger(__name__)                 #
# ---------------------------------------------------------------------------


class SemverComparator(nimue_plugins.comparing.MetadataComparator):

  _alias_ = 'comparing.metadata.semver'
  _version_ = '1.0.0'

  @staticmethod
  @silent_logging_decorator(_alias_)
  def compare(nimue_data, **params) -> bool:
    version = params.get('version', '')
    version_resolved = resolve_interpolated_variables(version, nimue_data)

    expression = params.get('expression', '')
    expression_resolved = resolve_interpolated_variables(expression, nimue_data)

    log.info("Comparing versions using expression:")
    log.info(f"{version}{expression}' expanded as: '{version_resolved}{expression_resolved}'")

    try:
      # Use semver to evaluate the expression
      result = semver.match(version_resolved, expression_resolved)
      if result:
        log.info("Versions match")
      else:
        log.error("Versions doesn't' match")
      return result
    except Exception as e:
      log.error(f"Error in comparing versions for '{version}{expression}': {e}")
      return False
