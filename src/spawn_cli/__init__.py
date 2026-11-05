__all__ = ["__version__"]

from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    __version__ = _pkg_version("spawn-cli")
except PackageNotFoundError:  # not installed (e.g. running from source tree)
    __version__ = "0.0.0.dev0"
