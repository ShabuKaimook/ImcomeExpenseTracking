from abc import ABC, abstractmethod
from ocr_service.models.transaction import Transaction

class BankParser(ABC):
    @abstractmethod
    def can_handle(self, texts: list) -> bool:
        pass

    @abstractmethod
    def parse(self, texts: list) -> Transaction:
        pass