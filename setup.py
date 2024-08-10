"""
    Setup file for nimue.
    Use setup.cfg to configure your project.

    This file was generated with PyScaffold 4.5.
    PyScaffold helps you to put up the scaffold of your new Python project.
    Learn more under: https://pyscaffold.org/
"""
from setuptools import setup
from setuptools_scm.version import SEMVER_MINOR, guess_next_simple_semver, release_branch_semver_version

def custom_version():
  """
  Custom version scheme for setuptools_scm.

  This function defines a custom version scheme that:
  - Uses `release_branch_semver_version` to determine the version for release branches.
  - Falls back to the guessed next simple semantic version if the release branch version is not different.
  - Formats the version according to the semantic versioning minor scheme.
  """

  def my_release_branch_semver_version(version):
    """
    Determine the version for a release branch.

    If the release branch version is the same as the guessed next version, format the version
    using a custom format.

    Args:
      version (setuptools_scm.version.ScmVersion): The current version object.

    Returns:
      str: The formatted version string.
    """
    v = release_branch_semver_version(version)
    # Check if the release branch version is the same as the guessed next simple semver
    if v == version.format_next_version(guess_next_simple_semver, retain=SEMVER_MINOR):
      # Return the formatted guessed next version
      return version.format_next_version(guess_next_simple_semver, fmt="{guessed}", retain=SEMVER_MINOR)
    return v

  return {
    'version_scheme': my_release_branch_semver_version,
    'local_scheme': 'no-local-version',
  }

if __name__ == "__main__":
    try:
        setup(
          name="nimue-rt",
          use_scm_version=custom_version
        )
    except:  # noqa
        print(
            "\n\nAn error occurred while building the project, "
            "please ensure you have the most updated version of setuptools, "
            "setuptools_scm and wheel with:\n"
            "   pip install -U setuptools setuptools_scm wheel\n\n"
        )
        raise
