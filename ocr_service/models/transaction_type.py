class TransactionType:
    INCOME = "income"
    EXPENSE = "expense"
    
    @staticmethod
    def get_type_list():
        return [
            TransactionType.INCOME,
            TransactionType.EXPENSE
        ]