from sqlalchemy import MetaData, Table, Column, String, Unicode, Integer, DateTime, ForeignKey, func
from datetime import datetime


md = MetaData()

users = Table(
    'users', md,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=False, unique=True),
    Column('joined', DateTime, default=datetime.utcnow),
)

posts = Table(
    'posts', md,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('content', Unicode),
    Column('stamp', DateTime, server_default=func.now()),
)

from sqlalchemy import create_engine

e = create_engine('sqlite://')
md.bind = e
md.create_all()

e.execute(
    users.insert(),
    [
        {'name': 'joffrey'},
        {'name': 'tywin'},
        {'name': 'tyrion'},
        {'name': 'jamie'},
        {'name': 'cersei'},
    ]
)

e.execute(
    posts.insert(),
    [
        {'user_id': 1, 'content': u"I am the king!"},
        {'user_id': 1, 'content': u"I've been very busy"},
        {'user_id': 1, 'content': u"I command you to go back up there and fight!"},
        {'user_id': 2, 'content': u"You really think a crown gives you power?"},
        {'user_id': 2, 'content': u"A lion doesn't concern himself with the opinion of a sheep"},
        {'user_id': 3, 'content': u"This is duty, not desire"},
        {'user_id': 3, 'content': u"A Lannister always pays his debts"},
        {'user_id': 4, 'content': u"Has anyone ever told you you're as boring as you're ugly?"},
        {'user_id': 4, 'content': u"The things I do for love..."},
        {'user_id': 5, 'content': u"If you ever call me 'sister' again, I'll strangle you in your sleep"},
    ]
)


from sqlalchemy import select

all_users = e.execute(select([users.c.name, users.c.joined])).fetchall()
k1 = e.execute(users.select().where(users.c.name == 'joffrey')).first()
k2 = e.execute(select([users.c.name]).where(users.c.name == 'joffrey')).first()


q1 = posts.join(users).select()

q2 = select(
    [posts.c.id, posts.c.user_id, posts.c.content, users.c.name]
).select_from(posts.join(users))

q3 = select(
    [posts.c.id, posts.c.user_id, posts.c.content, users.c.name]
).where(posts.c.user_id == users.c.id)

# reflecting all previous tables
md2 = MetaData()
md2.bind = e
md2.reflect(views=True)

# reflecting one table
md3 = MetaData()
usr = Table('users', md3, autoload=True, autoload_with=e)


# BEGIN ORM

from sqlalchemy.orm import relationship, mapper


# Manual mapping with custom Base

class ManualBase(object):
    def __repr__(self):
        if hasattr(self, 'name'):
            return self.name
        elif hasattr(self, 'content'):
            return self.content
        return self


class User(ManualBase):
    pass


class Post(ManualBase):
    pass

# Map User and Post to our table constructs
mapper(
    Post,
    posts,
    properties={'user': relationship(User)},
)

mapper(User, users)


# Session creation

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base, declared_attr, DeferredReflection

Session = sessionmaker(bind=e)

session = Session()


# Override base class for ORM

class MyBase(object):

    id = Column(Integer, primary_key=True)

    def __repr__(self):
        if hasattr(self, 'name'):
            return self.name
        elif hasattr(self, 'content'):
            return self.content
        return self

# override here
Base = declarative_base(cls=MyBase)


# mixin
class HasOwner(object):

    @declared_attr
    def user_id(self):
        return Column(String, ForeignKey('decl_users.id'))

    @declared_attr
    def user(self):
        return relationship(DeclUser)


class DeclUser(Base):
    __tablename__ = 'decl_users'

    name = Column(String)
    joined = Column(DateTime, default=datetime.utcnow)


class DeclPost(HasOwner, Base):
    __tablename__ = 'decl_posts'

    content = Column(Unicode)
    stamp = Column(DateTime, server_default=func.now())


Base.metadata.create_all(e)

walt = DeclUser(name='walter')
session.add_all([walt, DeclUser(name='hank'), DeclUser(name='skylar'), DeclUser(name='marie')])
hank = session.query(DeclUser).filter(DeclUser.name == 'hank').first()
session.delete(hank)
walt.name = 'heisenberg'
p = DeclPost(content=u"I am the danger!", user=walt)
session.add(p)
print walt is p.user
session.commit()
walt.name = 'walt'
session.commit()


# ORM reflection

RefBase = declarative_base(cls=DeferredReflection)


class RefUser(RefBase):
    __tablename__ = 'users'


class RefPost(RefBase):
    __tablename__ = 'posts'
    user_id = Column(String, ForeignKey('users.id'))
    user = relationship(RefUser)


RefBase.prepare(e)

# Reflected declarative ready!

md.drop_all(e)
md2.drop_all(e)
Base.metadata.drop_all(e)
RefBase.metadata.drop_all(e)
