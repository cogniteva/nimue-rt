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
import argparse
import logging
import logging.handlers
import os
import sys
from typing import List

from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler

# ---------------------------------------------------------------------------
from nimue import __version__
from nimue._config import load_nimue_config
from nimue._execution_tester import ExecutionTester
from nimue._execution_tracer import ExecutionTracer

__author__ = "Cogniteva SAS"
__copyright__ = "Cogniteva SAS"
__license__ = "MIT"
# ---------------------------------------------------------------------------
log = logging.getLogger(__name__)
# ---------------------------------------------------------------------------


def setup_logging() -> None:
  """Setup and configure logging."""

  def setup_logging_levels() -> None:
    """Setup custom logging levels including TRACE."""
    logging.TRACE = 5
    logging.addLevelName(logging.TRACE, "TRACE")

    def trace(self, message, *args, **kws):
      if self.isEnabledFor(logging.TRACE):
        self._log(logging.TRACE, message, args, **kws)

    logging.Logger.trace = trace

    # Setup logging aliases according to RFC5424
    logging.addLevelName(logging.TRACE,    "(~~)")
    logging.addLevelName(logging.DEBUG,    "(%%)")
    logging.addLevelName(logging.INFO,     "(II)")
    logging.addLevelName(logging.WARNING,  "(WW)")
    logging.addLevelName(logging.ERROR,    "(EE)")
    logging.addLevelName(logging.CRITICAL, "(CC)")
    logging.addLevelName(logging.NOTSET,   "(--)")

  def console_colors(enabled: bool) -> None:
    """Set console colors based on the enabled flag."""
    if not enabled:
      # Set the NO_COLOR environment variable
      os.environ['NO_COLOR'] = '1'

  def setup_console(enable_colors: bool) -> Console:
    """Setup rich console for logging."""
    console_colors(enable_colors)
    return Console(
        record=False,
        color_system=None,
    )

  def setup_rich_handler(console: Console) -> RichHandler:
    """Setup the rich handler for logging."""
    return RichHandler(
        console=console,
        enable_link_path=False,
        markup=True,
        omit_repeated_times=False,
        rich_tracebacks=True,
        show_level=True,
        show_path=False,
        show_time=False
    )

  # Setup logging levels including TRACE
  setup_logging_levels()

  # Setup console
  console = setup_console(enable_colors=False)

  # Setup rich handler
  rich_handler = setup_rich_handler(console)

  # Setup the logger
  logging.basicConfig(
      level=logging.WARNING,
      format="%(message)s",
      datefmt="[%X]",
      handlers=[rich_handler]
  )


def parse_args(args: List[str]) -> argparse.Namespace:
  """Parse command line arguments.

  Args:
      args (List[str]): List of arguments to parse.

  Returns:
      argparse.Namespace: Parsed arguments namespace.
  """
  parser = argparse.ArgumentParser(description='Nimue regression testing')

  # add the --version argument
  parser.add_argument("--version", action="version",
                      version=f"nimue {__version__}")

  # add the -v/--verbose and -vv/--very-verbose arguments
  parser.add_argument("-v", "--verbose", dest="loglevel",
                      help="set loglevel to INFO", action="store_const", const=logging.INFO)
  parser.add_argument("-vv", "--very-verbose", dest="loglevel",
                      help="set loglevel to DEBUG", action="store_const", const=logging.DEBUG)

  # add the -c/--config argument for custom config
  parser.add_argument("-c", "--config", type=str, dest="config",
                      help="path to a custom Nimue config file", required=False)

  # subparsers for different commands
  subparsers = parser.add_subparsers(dest='command', help='sub-command help')

  # parser for the trace command
  parser_trace = subparsers.add_parser('trace', help='trace a module execution')
  parser_trace.add_argument('archive', type=str, help='the archive file to store the trace')
  parser_trace.add_argument('module_name', type=str, help='the module to trace')
  parser_trace.add_argument('module_args', nargs=argparse.REMAINDER, help='arguments for the module')

  # parser for the test command
  parser_test = subparsers.add_parser('test', help='run a traced module from an archive')
  parser_test.add_argument('archive', type=str, help='the archive file to run the trace from')

  # parse the arguments
  try:
    parsed_args = parser.parse_args(args)
  except argparse.ArgumentError as e:
    log.error(f"Argument parsing error: {e}")
    parser.print_usage()
    sys.exit(1)
  except Exception as e:
    log.error(f"Unexpected error: {e}")
    parser.print_usage()
    sys.exit(1)

  # set log level if not set
  if not hasattr(parsed_args, 'loglevel') or parsed_args.loglevel is None:
    parsed_args.loglevel = logging.WARNING

  return parsed_args


def main(args):
  # take environment variables from .env
  load_dotenv()

  # setup logging
  setup_logging()

  # parse arguments
  args = parse_args(args)

  # adjust logging level based on parsed arguments
  if args.loglevel:
    logging.getLogger().setLevel(args.loglevel)

  # load nimue config
  config_path, config = load_nimue_config(args.config)

  if config:
    if config_path:
      log.info(f"Loading config from {config_path}")
    else:
      log.info("Using default config")
  else:
    log.error("No .nimue config available.")
    return

  if args.command == 'trace':
    log.info("Starting execution tracer")

    log.info(f"{args.module_name} {' '.join(args.module_args)}")
    tracer = ExecutionTracer(config['options']['trace'],
                             config['trace'],
                             args.module_name,
                             *args.module_args)
    tracer.trace_execution()
    log.info(f"Exit code: {tracer.metadata_exec['trace']['exitcode']}")
    if tracer.must_store_test():
      log.info("Tracing finished")
      tracer.update_metadata()
      tracer.record_files(args.archive)
      tracer.update_metadata_paths()
      tracer.save_metadata(args.archive)
    else:
      log.error("Tracing aborted")

  elif args.command == 'test':
    tester = ExecutionTester(config)
    log.info(f"Running test for {args.archive}")
    tester.trace_nrt(args.archive)


def cli():
  """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

  This function can be used as entry point to create console scripts with setuptools.
  """
  main(sys.argv[1:])


if __name__ == "__main__":
  # ^  This is a guard statement that will prevent the following code from
  #    being executed in the case someone imports this file instead of
  #    executing it as a script.
  #    https://docs.python.org/3/library/__main__.html
  cli()
