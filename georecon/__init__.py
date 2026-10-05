"""GeoRecon+: fast IP geolocation and reputation lookups."""

try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _dist_version

    __version__ = _dist_version("georecon-plus")
except PackageNotFoundError:  # running straight from a source checkout
    __version__ = "1.1.0"

from georecon.lookup import Lookup, lookup  # noqa: F401
from georecon.models import ConnectionInfo, GeoInfo, LookupResult, Reputation  # noqa: F401
