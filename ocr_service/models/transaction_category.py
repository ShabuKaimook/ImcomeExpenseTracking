class TransactionCategory:
    FOOD = 'food'
    TRANSPORT = 'transport'
    ENTERTAINMENT = 'entertainment'
    INTERNET = 'internet'
    INVESTMENT = 'investment'
    WASHING = 'washing'
    
    @staticmethod
    def get_category_list():
        return [
            TransactionCategory.FOOD,
            TransactionCategory.TRANSPORT,
            TransactionCategory.ENTERTAINMENT,
            TransactionCategory.INTERNET,
            TransactionCategory.INVESTMENT,
            TransactionCategory.WASHING
        ]