class MoxaError(Exception):
    """
    Base exception for all exceptions raised by moxa_io
    """


class MoxaIoError(MoxaError):
    """
    For exceptions raised during an unsupported moxa model type
    """


class MultiSlotError(MoxaError):
    """
    For exceptions raised during multiple slot types found for a rack
    """


class DuplRackError(MoxaError):
    """
    For exceptions raised during a duplicate rack number
    """


class ChanTypeRackError(MoxaError):
    """
    For exceptions raised during unsupported channel type for the rack
    """


class ChanNumRackError(MoxaError):
    """
    For exceptions raised during an unsupported channel number for a rack
    """
