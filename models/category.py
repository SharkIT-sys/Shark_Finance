class Category:
    def __init__(self, id, name, type, color):
        self.id = id
        self.name = name
        self.type = type
        self.color = color

    @classmethod
    def from_db_row(cls, row):
        return cls(id=row[0], name=row[1], type=row[2], color=row[3])
