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
# ---------------------------------------------------------------------------
import inspect
import logging
import os
from datetime import datetime

# ---------------------------------------------------------------------------
from functools import wraps
from pathlib import Path
from tempfile import NamedTemporaryFile
from types import SimpleNamespace

# ---------------------------------------------------------------------------
log = logging.getLogger(__name__)
# ---------------------------------------------------------------------------


def logging_set_context(logger, value):
  """
  Traverse the logger hierarchy and set the context for each handler that supports it.

  Args:
  - logger: The logger instance to start from.
  - value: The context value to set.

  Note:
  - This function will ignore handlers that do not have a set_context method.
  """
  current_logger = logger
  while current_logger:
    for handler in current_logger.handlers:
      if hasattr(handler, 'set_context'):
        try:
          handler.set_context(value)
        except AttributeError:
          # ignore handlers without a set_context method
          pass
    if current_logger.propagate:
      current_logger = current_logger.parent
    else:
      current_logger = None
# ---------------------------------------------------------------------------


def silent_logging_decorator(prefix: str):
  """
  Decorator to add and remove a logging filter around a function call,
  directing log output to a temporary file.
  """
  def decorator(func):
    """
    Actual decorator function that wraps `func` with logging filters.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
      transient_directory = Path(args[0]['nrt.test.paths.transient']) / 'logs' / 'test'
      # node_in_data-pluging_id
      transient_prefix = ('_'.join(args[0]['node_path.key'].split('.')) +
                          '-' + '_'.join(prefix.split('.')))
      # Create a temporary file for logging
      with NamedTemporaryFile(dir=transient_directory,
                              prefix=f"{transient_prefix}-",
                              delete=True) as temp_log_file:
        base_temp_file_path = temp_log_file.name

      temp_log_file_path = base_temp_file_path + '.log'
      temp_report_file_path = base_temp_file_path + '.txt'

      # keep track of the temporal file paths
      args[0]['files.log'] = temp_log_file_path
      args[0]['files.report'] = temp_report_file_path

      # Store previous context and handlers
      previous_context = None
      if hasattr(logging.root.handlers[0], 'context'):
        previous_context = logging.root.handlers[0].context

      # Set the new context
      if hasattr(logging.root.handlers[0], 'set_context'):
        logging.root.handlers[0].set_context(prefix)

      # Create a file handler for the temporary log file
      file_handler = logging.FileHandler(temp_log_file_path)
      formatter = logging.Formatter(
          "%(asctime)s %(levelname)s %(message)s", datefmt="[%X]")
      file_handler.setFormatter(formatter)

      # Add the file handler to the root logger
      logging.root.addHandler(file_handler)

      # Backup current handlers and set only the file handler
      old_handlers = logging.root.handlers[:]
      logging.root.handlers = [file_handler]

      try:
        timestamp_start_c = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_content = (
            f"# Nimue RT - Plugin '{args[0]['plugin_id']}' with data from path '{args[0]['node_path']['name']}'\n"
            f"# Log {timestamp_start_c}\n"
            "# Markers:\n"
            "# (~~) trace,   (%%) debug, (II) information, (!!) notice,\n"
            "# (WW) warning, (EE) error, (CC) critical"
        )
        with open(args[0]['files.log'], 'a') as log_file:
          log_file.write(log_content + '\n')

        return func(*args, **kwargs)
      except Exception as e:
        details = {
            'filename': os.path.basename(inspect.getfile(func)),
            'line_number': inspect.currentframe().f_lineno,
            'function_name': func.__name__
        }
        e.details = SimpleNamespace(**details)
        raise e
      finally:
        # Restore previous context and handlers
        if hasattr(logging.root.handlers[0], 'set_context'):
          logging.root.handlers[0].set_context(previous_context)

        # Restore old handlers
        logging.root.handlers = old_handlers

        # Remove the temporary file handler
        file_handler.close()
        logging.root.removeHandler(file_handler)

        # Ensure temporary log file is deleted if empty
        if os.path.exists(temp_log_file_path):
          if os.path.getsize(temp_log_file_path) == 0:
            args[0]['files.log'] = None
            os.remove(temp_log_file_path)

        # Ensure temporary report file is deleted if empty
        if os.path.exists(temp_report_file_path):
          if os.path.getsize(temp_report_file_path) == 0:
            args[0]['files.log'] = None
            os.remove(temp_report_file_path)

    # Preserve the original function's signature
    wrapper.__signature__ = inspect.signature(func)
    return wrapper

  return decorator


def append_to_log_report(config, data):
  """
  Append data to the log report file specified in the config.

  Args:
      config (dict): Configuration dictionary containing the file path.
      data (str): Data to append to the log report.
  """
  # Extract the file path from the config dictionary
  report_file_path = config.get('files', {}).get('report')

  if not report_file_path:
    raise ValueError("Report file path not found in the config['files.report']")

  if not len(str(data)):
    return

  # Open the file in append mode and write the data
  try:
    # Check if the file is empty
    file_is_empty = not os.path.exists(report_file_path) or os.stat(report_file_path).st_size == 0

    with open(report_file_path, 'a') as report_file:
      # write header if the file is empty
      if file_is_empty:
        timestamp_start_c = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_file.write(f"# Nimue RT - Plugin '{config['plugin_id']}' with data from path "
                          f"'{config['node_path']['name']}'\n")
        report_file.write(f"# Test report {timestamp_start_c}\n")
        log.info(f"Log report: {report_file_path}")

      if isinstance(data, list):
        for line in data:
          report_file.write(str(line) + '\n')
      else:
        report_file.write(str(data) + '\n')
  except IOError as e:
    print(f"An error occurred while writing to the log report: {e}")
