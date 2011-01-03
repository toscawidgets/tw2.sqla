import tw2.core as twc, tw2.sqla as tws, sqlalchemy as sa
import transaction
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
        if hasattr(self, 'session'):
            self.session.flush()
        assert( e.id == 1 )
        assert( e.name == 'foo' )
        assert( len(e.others) == 1 )
        assert( e.others[0].id == 1 )
        assert( e.others[0].nick == 'bob' )
        assert( e.others[0].other == e )

    def test_from_dict_empty(self):
        d = {}
        e = twsu.from_dict(self.DBTestCls1(), d, getattr(self, 'session', None))
        if hasattr(self, 'session'):
            self.session.flush()
        assert( e.id == 2 )
        assert( e.name == None )
        assert( e.others == [] )

    def test_from_dict_new(self):
        d = {
            'id' : '',
            'name' : 'bazaar',
        }
        e = twsu.from_dict(self.DBTestCls1(), d, getattr(self, 'session', None))
        if hasattr(self, 'session'):
            self.session.flush()
        assert( e.id == 2 )
        assert( e.name == 'bazaar' )
        assert( len(e.others) == 0 )

    def test_from_dict_new_many_to_one_by_id(self):
        d = {
            'id' : '',
            'nick' : 'bazaar',
            'other_id' : 1,
        }
        e = twsu.from_dict(self.DBTestCls2(), d, getattr(self, 'session', None))
        if hasattr(self, 'session'):
            self.session.flush()
        assert( e.id == 3 )
        assert( e.nick == 'bazaar' )
        assert( e in e.other.others )
    
    def test_from_dict_old_many_to_one_by_dict_recall(self):
        assert( self.DBTestCls2.query.first().nick == 'bob' )
        d = {
            'nick' : 'updated',
            'other' : {
                'id' : 1
            }
        }
       
        e = twsu.from_dict(self.DBTestCls2.query.first(), d,
                           getattr(self, 'session', None))
        if hasattr(self, 'session'):
            self.session.flush()
        assert( self.DBTestCls2.query.first().nick == 'updated' )
        assert( self.DBTestCls1.query.first().others[0].nick == 'updated' )

    def test_from_dict_old_many_to_one_by_dict(self):
        d = {
            'id' : '',
            'nick' : 'bazaar',
            'other' : {
                'id' : 1,
                'name' : 'foo'
            }
        }
       
        e = twsu.from_dict(self.DBTestCls2(), d, getattr(self, 'session', None))
        if hasattr(self, 'session'):
            self.session.flush()
        assert( e.id == 3 )
        assert( e.nick == 'bazaar' )
        assert( e.other.id == 1 )
        assert( e.other.name == 'foo' )

    def test_from_dict_new_many_to_one_by_dict(self):
        d = {
            'id' : '',
            'nick' : 'bazaar',
            'other' : {
                'name' : 'blamaz'
            }
        }
       
        e = twsu.from_dict(self.DBTestCls2(), d, getattr(self, 'session', None))
        if hasattr(self, 'session'):
            self.session.flush()
        assert( e.id == 3 )
        assert( e.nick == 'bazaar' )
        assert( e in e.other.others )
        assert( e.other.name == 'blamaz' )
        assert( e.other.id == 2 ) 

    def test_from_dict_new_one_to_many_by_dict(self):
        d = {
            'id' : '',
            'name' : 'qatar',
            'others' : [
                { 'nick' : 'blang' },
                { 'nick' : 'blong' },
            ]
        }
       
        e = twsu.from_dict(self.DBTestCls1(), d, getattr(self, 'session', None))
        if hasattr(self, 'session'):
            self.session.flush()
        assert( e.id == 2 )
        assert( e.name == 'qatar' )
        assert( e.others[0].nick == 'blang' )
        assert( e.others[0].id == 3 )
        assert( e.others[1].nick == 'blong' )
        assert( e.others[1].id == 4 )
    
    def test_from_dict_mixed_list(self):
        d = {
            'id' : '',
            'name' : 'qatar',
            'others' : [
                { 'nick' : 'blang' },
                'foo',
            ]
        }
      
        try:
            e = twsu.from_dict(self.DBTestCls1(), d,
                               getattr(self, 'session', None))
            assert(False)
        except Exception, e:
            assert(str(e) == 'Cannot send mixed (dict/non dict) data ' +
                             'to list relationships in from_dict data.')
    
    def test_update_or_create_exception(self):
        d = {
            'id' : 55,
            'name' : 'failboat'
        }
        try:
            e = twsu.update_or_create(self.DBTestCls1(), d, self.session)
            assert(False)
        except Exception, e:
            assert(str(e) == 'cannot create with pk')


##
## From a design standpoint, it would be nice to make the tw2.sqla.utils
## functions persistance-layer agnostic.
##
#class TestElixir(BaseObject):
#    def setUp(self):
#        import elixir as el
#        el.metadata = sa.MetaData('sqlite:///:memory:')
#
#        class DBTestCls1(el.Entity):
#            name = el.Field(el.String)
#
#        class DBTestCls2(el.Entity):
#            nick = el.Field(el.String)
#            other = el.ManyToOne(DBTestCls1)
#
#        DBTestCls1.others = el.OneToMany(DBTestCls2)
#        
#        self.DBTestCls1 = DBTestCls1
#        self.DBTestCls2 = DBTestCls2
#
#        el.setup_all()
#        el.metadata.create_all()
#        foo = self.DBTestCls1(id=1, name='foo')
#        bob = self.DBTestCls2(id=1, nick='bob', other=foo)
#        george = self.DBTestCls2(id=2, nick='george')
#
#        transaction.commit()
#
#        testapi.setup()

class TestSQLA(BaseObject):
    def setUp(self):
        from sqlalchemy.ext.declarative import declarative_base
        self.session = tws.transactional_session()
        Base = declarative_base(metadata=sa.MetaData('sqlite:///:memory:'))
        Base.query = self.session.query_property()

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
    
        Base.metadata.create_all()
        
        self.DBTestCls1 = DBTestCls1
        self.DBTestCls2 = DBTestCls2

        foo = self.DBTestCls1(id=1, name='foo')
        self.session.add(foo)

        bob = self.DBTestCls2(id=1, nick='bob')
        bob.other = foo
        self.session.add(bob)
        george = self.DBTestCls2(id=2, nick='george')
        self.session.add(george)

        transaction.commit()

        testapi.setup()
