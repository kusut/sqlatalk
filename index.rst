.. include:: <s5defs.txt>

SQLAlchemy
==============================

:Author: kusut
:Date: 2013/06/29


Meta
----

Code-heavy talk. For better viewing, you can view the slides online at: http://slides.kusut.web.id/sqlalchemy

You can get the code at http://github.com/kusut/sqlatalk (sprinkle some print statements or drop a pdb)


What
----

SQLAlchemy

- is not **just** a great ORM
- has a *lower level* part called SQLAlchemy Core
- provides consistent interface across a lot of relational DBs
- gives us SQL (relational algebra) abstraction in python
- is non-opinionated and flexible
- raised the Gittip contribution option :D


Overview
--------

Explain this
 
.. image:: sqla_arch_small.png
   :align: center



Core
----

.. sourcecode:: python

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


Core
----

Creating the tables

.. sourcecode:: python

   e = create_engine('sqlite://')

   # create individually
   users.create(e)
   posts.create(e)

   # create all tables in the metadata
   md.create_all(e)

   # to drop tables, subtitute 'create' with 'drop'

   # you can bind an engine to the metadata
   md.bind = e


Core
----

Executing queries

.. sourcecode:: python

   e.execute("SELECT 1, 'foo'")
   e.execute("SELECT :x, :y", x=1, y='foo')
   e.execute(text("SELECT :x, :y"), x=1, y='foo')

   e.execute(some_table.select())
   e.execute(some_table.insert(), **kwargs)

   # each of these returns a ResultProxy object


Core
----

ResultProxy

- ``inserted_primary_key``
- ``last_inserted_params`` and ``last_updated_params``
- ``fetchall`` returns a list of RowProxy object
- ``fetchone`` and ``first`` returns a RowProxy object
- etc..



Core
----

.. sourcecode:: python

   # inserting
   e.execute(users.insert(), name='joffrey')
   e.execute(users.insert(),
    [{'name': 'tywin'}, {'name': 'tyrion'}, {'name': 'jamie'}, {'name': 'cersei'}])


   #  select
   e.execute(users.select()).fetchall()
   e.execute(select([users.c.name, users.c.joined])).fetchall()


   # filtering
   e.execute(users.select().where(users.c.name='joffrey')).fetchone()
   e.execute(select([users.c.name]).where(users.c.name == 'joffrey')).first()


Core
----

Joining

.. sourcecode:: python

   q1 = posts.join(users).select()  # all columns, explicit


   # some columns, explicit
   q2 = select(
       [posts.c.id, posts.c.user_id, posts.c.content, users.c.name]
   ).select_from(posts.join(users))


   # some columns, implicit
   q3 = select(
       [posts.c.id, posts.c.user_id, posts.c.content, users.c.name]
   ).where(posts.c.user_id == users.c.id)


Core
----

Reflecting existing tables

.. sourcecode:: python

  
   reflected_md = MetaData()
   reflected_md.reflect(e)  # views=True

   # check sorted_tables attribute for reflected tables
   # are they the same tables?

   # tables can be reflected individually too
   reflected_users = Table('users', another_metadata, autoload=True)
   reflected_users = Table('users', another_metadata, autoload=True, autoload_with=e)


ORM
---

Data mapper vs active record

Session handles the 'talking' to the database

Domain models: python classes that are mapped to Table constructs. You can do this manually
(classical mapping) or use declarative_base.

We still have the power of SQL expression language in the ORM


ORM Session
-----------

.. sourcecode:: python

   from sqlalchemy.orm import sessionmaker
   Session = sessionmaker(bind=e)
   session = Session()

   # unit of work
   # do lots of stuff
   # ....
   session.commit()    # flush, rollback and abort methods are available
   # all in 1 transaction, SQLAlchemy handle inter-row dependencies if required


ORM Session
-----------

.. sourcecode:: python

   # for a not-so-representative example:
   # lets say we have Post and User classes in the ORM, mapped to our previous Tabels

   walt = User(name='walter')
   session.add_all([walt, User(name='hank'), User(name='skylar'), User(name='marie')])
   hank = session.query(User).filter(User.name == 'hank').first()
   session.delete(hank)
   walt.name = 'heisenberg'
   p = Post(content=u"I am the danger!", user=walt)
   session.add(p)

   p.user is walt    # True, identity map

   session.commit()

   walt.name = 'walt'
   session.commit()
   

ORM
---

Manual (classical) mapping

.. sourcecode:: python

   class Post(object):
       pass
   
   class User(object):
       pass

   
   mapper(Post, posts, properties={'user': relationship(User)})  
   mapper(User, user)

   # the second argument to mapper is a Table construct, either reflected or not
   # check 'properties' and 'relationship' for more options
   

ORM
---

.. sourcecode:: python

   # Declarative base
   class User(Base):
       __tablename__ = 'users'

       id = Column(Integer, primary_key=True)
       name = Column(String)
       joined = Column(DateTime, default=datetime.utcnow)


   class Post(Base):
       __tablename__ = 'posts'

       id = Column(Integer, primary_key=True)
       user_id = Column(String, ForeignKey('users.id'))
       content = Column(String)
       stamp = Column(DateTime, server_default=func.now())

       user = relationship(User)              


ORM: Your own default
---------------------

.. sourcecode:: python

   class MyBase(object):

       @declared_attr
       def __tablename__(cls):
           return cls.__name__.lower()       

       id = Column(Integer, primary_key=True)
       timestamp = Column(DateTime, server_default=func.now())

   class HasOwner(object):

       @declared_attr
       def user_id(self):
           return Column(String, ForeignKey('users.id'))

       @declared_attr
       def user(self):
           return relationship(User)


ORM: Your own default
---------------------

.. sourcecode:: python

   Base = declarative_base(cls=MyBase)

   class User(Base):

       name = Column(String)

   class Post(HasOwner, Base):

       content = Column(Unicode)


ORM Declarative Reflection
--------------------------

.. sourcecode:: python

   RefBase = declarative_base(cls=DeferredReflection)

   class RefUser(RefBase):
       __tablename__ = 'users'

   class RefPost(RefBase):
        __tablename__ = 'posts'

        user = relationship(RefUser)

   RefBase.prepare(e)


ORM
---

Web framework helpers:

- Flask-SQLAlchemy (scoped session and convenience)
- zope.sqlalchemy (scoped session,
  delegates transaction management to ``transaction`` module)
- pyramid_tm (uses zope.sqlalchemy, for pyramid views)
- ???


References
----------

Mike Bayer's

- Introduction tutorial:
  `source <https://bitbucket.org/zzzeek/pycon2013_student_package>`_,
  `slides <https://speakerdeck.com/zzzeek/introduction-to-sqlalchemy-pycon-2013>`_, and
  `the video <http://www.youtube.com/watch?v=woKYyhLCcnU>`_.

- Hand coded app:
  `blog <http://techspot.zzzeek.org/2012/03/12/pycon-2012-hand-coded-applications-with-sqlalchemy/>`_ and
  `video <http://www.youtube.com/watch?v=E09qigk_hnY>`_.

- SQLAlchemy session in depth, and more


References
----------

Armin Ronacher's

- `SQLAlchemy and You <http://lucumr.pocoo.org/2011/7/19/sqlachemy-and-you>`_, 
  `SQLAwesome <https://speakerdeck.com/mitsuhiko/why-sqlalchemy-is-awesome>`_

Brandon Rhodes'

- `Flexing SQLAlchemy relational power <http://www.youtube.com/watch?v=399c-ycBvo4>`_


Fin
---

More demo? Questions?

Thanks
