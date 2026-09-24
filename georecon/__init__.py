"""GeoRecon+: fast IP geolocation and reputation lookups."""

__version__ = "1.0.0"

from georecon.lookup import Lookup, lookup  # noqa: F401
from georecon.models import ConnectionInfo, GeoInfo, LookupResult, Reputation  # noqa: F401
