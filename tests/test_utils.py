import tw2.core as twc, tw2.sqla as tws, sqlalchemy as sa
import tw2.sqla.utils as twsu
import testapi

class BaseObject(object):
    """ Contains all tests to be run over Elixir and sqlalchemy-declarative """
    def setUp(self):
        raise NotImplementedError, "Must be subclassed."

    def test_from_dict_simple(self):
        d = {
            'id' : 1,
        }
        e = twsu.from_dict(self.DBTestCls1(), d, getattr(self, 'session', None))
        assert( e.id == 1 )
        assert( e.name == 'foo' )
        assert( len(e.others) == 1 )
        assert( e.others[0].id == 1 )
        assert( e.others[0].nick == 'bob' )
        assert( e.others[0].other == e )

    def test_from_dict_empty(self):
        d = {}
        e = twsu.from_dict(self.DBTestCls1(), d, getattr(self, 'session', None))
        assert( e.id == None )
        assert( e.name == None )
        assert( e.others == [] )

    def test_from_dict_new(self):
        d = {
            'id' : '',
            'name' : 'bazaar',
        }
        e = twsu.from_dict(self.DBTestCls1(), d, getattr(self, 'session', None))
        if hasattr(self, 'session'):
            self.session.commit()
        assert( e.id == 2 )
        assert( e.name == 'bazaar' )
        assert( len(e.others) == 0 )

    def test_from_dict_new_many_to_one(self):
        d = {
            'id' : '',
            'nick' : 'bazaar',
            'other_id' : 1,
        }
       
        e = twsu.from_dict(self.DBTestCls2(), d, getattr(self, 'session', None))
        if hasattr(self, 'session'):
            self.session.commit()
        assert( e.id == 2 )
        assert( e.nick == 'bazaar' )
        assert( e in e.other.others )

    def test_from_dict_new_one_to_many(self):
        # TODO...
        pass


class TestSQLA(BaseObject):
    def setUp(self):
        from sqlalchemy.ext.declarative import declarative_base
        Base = declarative_base(metadata=sa.MetaData('sqlite:///:memory:'))
        Base.query = tws.transactional_session().query_property()

        class DBTestCls1(Base):
            __tablename__ = 'Test'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String(50))
        class DBTestCls2(Base):
            __tablename__ = 'Test2'
            id = sa.Column(sa.Integer, primary_key=True)
            nick = sa.Column(sa.String)
            other_id = sa.Column(sa.Integer, sa.ForeignKey('Test.id'))
            other = sa.orm.relation(DBTestCls1, backref=sa.orm.backref('others'))
        self.DBTestCls1 = DBTestCls1
        self.DBTestCls2 = DBTestCls2
    
        Base.metadata.create_all()

        session = sa.orm.sessionmaker()()
        self.session = session
        foo = self.DBTestCls1(id=1, name='foo')
        session.add(foo)
        session.commit()

        bob = self.DBTestCls2(id=1, nick='bob')
        bob.other = foo
        session.add(bob)
        session.commit()

        testapi.setup()

