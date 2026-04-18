class Commitment:
    def __init__(self, id, name, total_amount, date):
        self.id = id
        self.name = name
        self.total_amount = total_amount
        self.date = date

    @classmethod
    def from_db_row(cls, row):
        return cls(
            id=row[0],
            name=row[1],
            total_amount=row[2],
            date=row[3]
        )

class CommitmentPayment:
    def __init__(self, id, commitment_id, amount, date):
        self.id = id
        self.commitment_id = commitment_id
        self.amount = amount
        self.date = date

    @classmethod
    def from_db_row(cls, row):
        return cls(
            id=row[0],
            commitment_id=row[1],
            amount=row[2],
            date=row[3]
        )
