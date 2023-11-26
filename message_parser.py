import re
from message import Message

class MessageParser:
    def __init__(self):
        self.patterns = {
            'trend': re.compile(r'(\d+),(up|down|flat),(\w+)'),
            'snr': re.compile(r'(\w+) - Price (enters|is breaking) (D )?(Support|Resistance) Zone'),
            'td9': re.compile(r'1H TD9(buy|sell)( OFF)? (\w+)'),
            'pineconnector': re.compile(r'(\d+),(long|short|closelong|closeshort),(\w+\.PRO)(?:,risk=(\d+))?(?:,tp=(\d+))?(?:,sl=(\d+))?(?:,comment="([^"]+)")?')
        }

    def parse(self, raw_message):
        for key, pattern in self.patterns.items():
            match = pattern.match(raw_message)
            if match:
                return Message(symbol=match.group(3), command=match.group(2), parameters=match.groupdict())
        return None

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
