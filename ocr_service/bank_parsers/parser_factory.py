from .make_parser import Make

class ParserFactory:
    def __init__(self):
        self.parsers = [
            Make()
        ]
        
    def get_parser(self, texts: list):
        for parser in self.parsers:
            if parser.can_handle(texts):
                return parser
        raise Exception("Unsupported bank")