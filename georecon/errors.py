"""Errors raised by georecon."""


class GeoReconError(Exception):
    """Base class for all georecon errors."""

    exit_code = 1


class InvalidTargetError(GeoReconError):
    """The target is not a usable IP address."""

    exit_code = 2


class NetworkError(GeoReconError):
    """A remote provider could not be reached."""

    exit_code = 3


class ProviderError(GeoReconError):
    """A provider answered with an error payload."""

    exit_code = 4
