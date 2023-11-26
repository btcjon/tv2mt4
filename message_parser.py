import re
from message import Message
import config

class MessageParser:
    def __init__(self):
        self.patterns = {key: re.compile(pattern) for key, pattern in config.PATTERNS.items()}

    def parse(self, raw_message):
        for key, pattern in self.patterns.items():
            match = pattern.match(raw_message)
            if match:
                return Message(symbol=match.group(3), command=match.group(2), parameters=match.groupdict())
        return None

# Duplicate method definitions will be removed.

    def parse_trend(self, raw_message):
        match = self.patterns['trend'].match(raw_message)
        if match:
            return Message(symbol=match.group(3), command=match.group(2))

    def parse_snr(self, raw_message):
        match = self.patterns['snr'].match(raw_message)
        if match:
            return Message(symbol=match.group(1), command=match.group(2))

    def parse_td9(self, raw_message):
        match = self.patterns['td9'].match(raw_message)
        if match:
            return Message(symbol=match.group(3), command=match.group(1))

    def parse_pineconnector(self, raw_message):
        match = self.patterns['pineconnector'].match(raw_message)
        if match:
            return Message(symbol=match.group(3), command=match.group(2), parameters=match.groupdict())
