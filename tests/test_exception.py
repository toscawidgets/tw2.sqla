import tw2.core as twc, tw2.sqla as tws, sqlalchemy as sa
import transaction
import tw2.sqla.utils as twsu
import testapi

class BaseObject(object):
    """ Contains all tests to be run over Elixir and sqlalchemy-declarative """
    def setUp(self):
        raise NotImplementedError, "Must be subclassed."


# TODO -- How can we test this with Elixir?

class TestSQLA(BaseObject):
    def setUp(self):
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.orm import mapper
        from sqlalchemy.sql import join

        from sqlalchemy import Table, Column, Integer, String, ForeignKey

        self.session = tws.transactional_session()
        Base = declarative_base(metadata=sa.MetaData('sqlite:///:memory:'))
        Base.query = self.session.query_property()

        users_table = Table('users', Base.metadata,
                Column('user_id', Integer, primary_key=True),
                Column('name', String(40)),
        )
        addresses_table = Table('addresses', Base.metadata,
                Column('address_id', Integer, primary_key=True),
                Column('user_id', Integer, ForeignKey('users.user_id')),
                Column('place', String(40)),
        )
        
        class DBTestCls1(object):
            pass

        j = join(users_table, addresses_table)

        mapper(DBTestCls1, j, properties={
            'user_id': [users_table.c.user_id, addresses_table.c.user_id]
        })
    
        Base.metadata.create_all()
        
        self.DBTestCls1 = DBTestCls1

        transaction.commit()

        testapi.setup()
    
    #def tearDown(self):
    #    Base.metadata.drop_all()
