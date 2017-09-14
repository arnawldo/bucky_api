from bucky import db


class User(db.Model):
    """Class for user instances

    User instances will be managed by sql-alchemy magic

    Attributes:
        id -- unique identification of user
        username -- username of user
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)

    def __repr__(self):
        return 'User <{}>'.format(self.username)
