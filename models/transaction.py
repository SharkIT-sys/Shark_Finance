class Transaction:
    def __init__(self, id, type, category_id, name, amount, date, recurrence_type, recurrence_interval, recurrence_duration):
        self.id = id
        self.type = type
        self.category_id = category_id
        self.name = name
        self.amount = amount
        self.date = date
        self.recurrence_type = recurrence_type
        self.recurrence_interval = recurrence_interval
        self.recurrence_duration = recurrence_duration

    @classmethod
    def from_db_row(cls, row):
        return cls(
            id=row[0],
            type=row[1],
            category_id=row[2],
            name=row[3],
            amount=row[4],
            date=row[5],
            recurrence_type=row[6],
            recurrence_interval=row[7],
            recurrence_duration=row[8]
        )
