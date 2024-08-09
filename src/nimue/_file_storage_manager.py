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
import shutil
import zipfile
import logging
import tempfile
from pathlib import Path
# ---------------------------------------------------------------------------
log = logging.getLogger(__name__)
# ---------------------------------------------------------------------------


class FileStorageManager:
  # to add files to the storage
  @staticmethod
  def add_file_to_storage(file_path, storage_dir):
    # do nothing if the file not longer exists
    if not Path(file_path).exists():
      return

    # create the target path within the storage directory, preserving the original hierarchy
    storage_files_dir = Path(storage_dir) / 'storage'
    target_path = storage_files_dir / Path(file_path).relative_to(Path(file_path).anchor)

    # do nothing if this file was already stored
    if target_path.exists():
      return

    # ensure target directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # copy file to target path within storage directory
    log.info(f"Adding {file_path}")
    shutil.copy(file_path, target_path)

  # create zip archive from storage directory
  @staticmethod
  def create_archive(storage_dir, archive_path):
    nrt_path = f"{archive_path}"

    # create zip archive
    log.info(f"Packaging {archive_path}")
    with zipfile.ZipFile(nrt_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
      for root, dirs, files in os.walk(storage_dir):
        for file in files:
          file_path = Path(root) / file
          arcname = file_path.relative_to(storage_dir)
          zipf.write(file_path, arcname=arcname)

  @staticmethod
  def record_files(metadata, archive_path):
    # create a temporary directory with the prefix 'nimue-'
    with tempfile.TemporaryDirectory(prefix='nimue-') as temp_storage_dir:
      # add read files to the storage
      for file_path in metadata['trace']['files']['read']:
        FileStorageManager.add_file_to_storage(file_path, temp_storage_dir)

      # add written files to the storage
      for file_path in metadata['trace']['files']['written']:
        FileStorageManager.add_file_to_storage(file_path, temp_storage_dir)

      # create zip archive from storage directory
      FileStorageManager.create_archive(temp_storage_dir, archive_path)
