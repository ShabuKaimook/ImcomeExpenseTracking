from ocr_service.bank_parsers.bank_parser import BankParser
from ocr_service.models.transaction import Transaction
from ocr_service.models.transaction_type import TransactionType
from ocr_service.models.transaction_category import TransactionCategory
from ocr_service.models.month import MonthShortName
from datetime import datetime

import re


class Make(BankParser):
    def __init__(self):
        super().__init__()
        self.category_list = TransactionCategory.get_category_list()

    def can_handle(self, texts: list) -> bool:
        return "kbank" in texts[1].lower() or "make" in texts[0].lower()

    def parse(self, texts: list) -> Transaction:
        # date
        now = datetime.now()
        date = now.strftime("%-d/%-m/%Y")
        print("Default date:", date, "\n")
        
        amount = 0.00
        for i, text in enumerate(texts):
            print(text)
            for i, month in enumerate(MonthShortName.get_month_list()):
                if month in text.lower():
                    dateData = texts[2].split()  # [day, month, year]
                    date = f"{dateData[0]}/{i}/{dateData[2]}"
                    del texts[i]  # remove the date text from texts list
                    print("Date found:", date, "\n")
                    break

            # amount
            # remove space in text to make it easier to find amount pattern
            no_space_text = text.replace(" ", "")
            amount_pattern = r"[\d,]+\.\d{2}"
            
            # find the match pattern for amount in text
            amount_match = re.search(amount_pattern, no_space_text)

            if amount_match:
                amount = float(amount_match.group().replace(",", ""))
                print("Amount found:", amount, "\n")
                break

        # type
        type = TransactionType.EXPENSE

        # category
        category = TransactionCategory.FOOD

        # description
        description = "from Make by Kbank: "
        if not texts[-1].startswith("Transaction ID:"):
            for cat in self.category_list:
                if cat in texts[-1].lower():
                    category = cat
                    break
            description += texts[-1]
        else:
            description += "No description"

        return Transaction(
            date=date,
            amount=amount,
            type=type,
            category=category,
            description=description,
        )
