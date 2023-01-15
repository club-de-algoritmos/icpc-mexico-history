class IcpcApiError(Exception):
    """Error that happened when querying the ICPC API."""
    pass


class ProcessingError(Exception):
    """Error that happened while processing data, most likely from the ICPC API."""
    pass
