from ocr_service.models.transaction_type import TransactionType
from ocr_service.models.transaction_category import TransactionCategory


class Transaction:
    def __init__(
        self,
        date,
        description,
        amount,
        type: TransactionType,
        category: TransactionCategory,
    ):
        self.date = date
        self.description = description
        self.amount = amount
        self.type = type
        self.category = category

    def __str__(self):
        return f"""
Transaction(date={self.date}, 
    description={self.description}, 
    amount={self.amount:.2f},
    type={self.type},
    category={self.category})
"""
