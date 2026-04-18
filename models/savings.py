class SavingsGoal:
    def __init__(self, id, name, target_amount, date):
        self.id = id
        self.name = name
        self.target_amount = target_amount # 0 or -1 means no ceiling
        self.date = date

    @classmethod
    def from_db_row(cls, row):
        return cls(
            id=row[0],
            name=row[1],
            target_amount=row[2],
            date=row[3]
        )

class SavingsContribution:
    def __init__(self, id, savings_id, amount, date):
        self.id = id
        self.savings_id = savings_id
        self.amount = amount
        self.date = date

    @classmethod
    def from_db_row(cls, row):
        return cls(
            id=row[0],
            savings_id=row[1],
            amount=row[2],
            date=row[3]
        )
