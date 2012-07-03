import tw2.core as twc
import tw2.sqla as tws
import sqlalchemy as sa
import transaction
import tw2.sqla.utils as twsu
import testapi

from nose.tools import eq_


class BaseObject(object):
    """ Contains all tests to be run over Elixir and sqlalchemy-declarative """
    def setUp(self):
        raise NotImplementedError("Must be subclassed.")

    def test_query_from_dict_simple(self):
        d = {
            'id': 1,
        }
        e = twsu.from_dict(self.DBTestCls1.query.filter_by(**d).first(), d)
        if hasattr(self, 'session'):
            self.session.flush()
        assert(e.id == 1)
        assert(e.name == 'foo')
        assert(len(e.others) == 1)
        assert(e.others[0].id == 1)
        assert(e.others[0].nick == 'bob')
        assert(e.others[0].other == e)

    def test_query_from_dict_empty(self):
        d = {}
        x = self.DBTestCls1()
        self.session.add(x)
        e = twsu.from_dict(x, d)
        if hasattr(self, 'session'):
            self.session.flush()

        assert(e.id == 2)
        assert(e.name == None)
        assert(e.others == [])

    def test_from_dict_new(self):
        d = {
            'id': None,
            'name': 'bazaar',
        }
        x = self.DBTestCls1()
        self.session.add(x)
        e = twsu.from_dict(x, d)
        if hasattr(self, 'session'):
            self.session.flush()

        assert(e.id == 2)
        assert(e.name == 'bazaar')
        assert(len(e.others) == 0)

##
## Not sure if this test should even be possible, but its sure broken now
##
#def test_from_dict_new_many_to_one_by_id(self):
#    #d = {
#    #    #'id': None,
#    #    #'nick': 'bazaar',
#    #    #'other_id': 1,
#    #}
#    #e = twsu.from_dict(self.DBTestCls2(), d, getattr(self, 'session', None))
#    #if hasattr(self, 'session'):
#    #    #self.session.flush()
#    #assert(e.id == 3)
#    #assert(e.nick == 'bazaar')
#    #print e.id, e.nick, e.other
#    #for q in e.other.others:
#    #    #print "", q.id, q.nick, q.other
#    #assert(e in e.other.others)

    def test_from_dict_old_many_to_one_by_dict_recall(self):
        assert(self.DBTestCls2.query.first().nick == 'bob')
        d = {
            'nick': 'updated',
            'other': {
                'id': 1
            }
        }

        e = twsu.from_dict(self.DBTestCls2.query.first(), d)
        if hasattr(self, 'session'):
            self.session.flush()
        assert(self.DBTestCls2.query.first().nick == 'updated')
        assert(self.DBTestCls1.query.first().others[0].nick == 'updated')

    def test_from_dict_old_many_to_one_by_dict(self):
        d = {
            'id': None,
            'nick': 'bazaar',
            'other': {
                'name': 'foo'
            }
        }

        x = self.DBTestCls2()
        self.session.add(x)
        e = twsu.from_dict(x, d)
        if hasattr(self, 'session'):
            self.session.flush()
        assert(e.id == 3)
        assert(e.nick == 'bazaar')
        assert(e.other.name == 'foo')

    def test_from_dict_new_many_to_one_by_dict(self):
        d = {
            'id': None,
            'nick': 'bazaar',
            'other': {
                'name': 'blamaz'
            }
        }

        x = self.DBTestCls2()
        self.session.add(x)
        e = twsu.from_dict(x, d)
        if hasattr(self, 'session'):
            self.session.flush()
        print e.id
        print e.nick
        print e.other
        assert(e.id == 3)
        assert(e.nick == 'bazaar')
        assert(e in e.other.others)
        assert(e.other.name == 'blamaz')
        assert(e.other.id == 2)

    def test_from_dict_new_one_to_many_by_dict(self):
        d = {
            'id': None,
            'name': 'qatar',
            'others': [
                {'nick': 'blang'},
                {'nick': 'blong'},
            ]
        }

        x = self.DBTestCls1()
        self.session.add(x)
        e = twsu.from_dict(x, d)
        if hasattr(self, 'session'):
            self.session.flush()
        print e.id
        print e.name
        print e.others
        assert(e.id == 2)
        assert(e.name == 'qatar')
        assert(e.others[0].nick == 'blang')
        assert(e.others[0].id == 3)
        assert(e.others[1].nick == 'blong')
        assert(e.others[1].id == 4)

    def test_from_dict_mixed_list(self):
        d = {
            'id': None,
            'name': 'qatar',
            'others': [
                {'nick': 'blang'},
                'foo',
            ]
        }

        try:
            e = twsu.from_dict(self.DBTestCls1(), d)
            assert(False)
        except Exception, e:
            assert(str(e) == 'Cannot send mixed (dict/non dict) data ' +
                             'to list relationships in from_dict data.')

    def test_from_dict_prm_tamp_mto(self):
        # When updating a DBTestCls2 object,
        # it should only be possible to modify
        # a DBTestCls1 object that is related to that object.
        prev_name = self.DBTestCls1.query.get(1).name
        twsu.from_dict(self.DBTestCls2.query.get(2), {
            'other': {'id': 1, 'name': prev_name + '_fred'}})
        assert(self.DBTestCls1.query.get(1).name == prev_name)

    def test_from_dict_prm_tamp_otm(self):
        # When updating a DBTestCls1 object,
        # it should only be possible to modify
        # a DBTestCls2 object that is related to that object.
        prev_nick = self.DBTestCls2.query.get(1).nick
        prev_id = self.DBTestCls2.query.get(1).id
        prev_count = self.DBTestCls2.query.count()
        twsu.from_dict(self.DBTestCls1(), {'others': [
            {'id': prev_id, 'nick': prev_nick + '_fred'}]})
        obj = self.DBTestCls2.query.get(1)
        count = self.DBTestCls2.query.count()
        assert(prev_nick == obj.nick)
        assert(prev_id == obj.id)
        assert(count == prev_count + 1)

    def test_update_or_create(self):
        d = {'name': 'winboat'}
        e = twsu.update_or_create(self.DBTestCls1, d)
        self.session.flush()
        assert(e.id == 2)
        assert(e.name == 'winboat')

        d = {'id': 1, 'name': 'winboat'}
        e = twsu.update_or_create(self.DBTestCls1, d)
        self.session.flush()
        assert(e.id == 1)
        assert(e.name == 'winboat')

    def test_update_or_create_with_zero(self):
        """ Ensure that 0 doesn't get interpreted as None.

        For the following issue:  http://bit.ly/OiFUfb
        """

        d = {'name': 'winboat', 'some_number': 0}
        e = twsu.update_or_create(self.DBTestCls1, d)
        self.session.flush()
        eq_(e.some_number, 0)

    def test_update_or_create_exception(self):
        d = {
            'id': 55,
            'name': 'failboat'
        }
        try:
            e = twsu.update_or_create(self.DBTestCls1, d)
            assert(False)
        except Exception, e:
            assert([s in str(e) for s in ['cannot create', 'with pk']])


#
# From a design standpoint, it would be nice to make the tw2.sqla.utils
# functions persistance-layer agnostic.
#
class TestElixir(BaseObject):
    def setUp(self):
        import elixir as el
        self.session = el.session = tws.transactional_session()
        el.metadata = sa.MetaData('sqlite:///:memory:')

        class DBTestCls1(el.Entity):
            name = el.Field(el.String)
            some_number = el.Field(el.Integer, default=2)

        class DBTestCls2(el.Entity):
            nick = el.Field(el.String)
            other_id = el.Field(el.Integer, colname='other')
            other = el.ManyToOne(DBTestCls1,
                                 field=other_id,
                                 backref='others')

        self.DBTestCls1 = DBTestCls1
        self.DBTestCls2 = DBTestCls2

        el.setup_all()
        el.metadata.create_all()
        foo = self.DBTestCls1(id=1, name='foo')
        bob = self.DBTestCls2(id=1, nick='bob', other=foo)
        george = self.DBTestCls2(id=2, nick='george')

        testapi.setup()

    #def tearDown(self):
    #    import elixir as el
    #    el.drop_all()


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
            some_number = sa.Column(sa.Integer, default=2)

        class DBTestCls2(Base):
            __tablename__ = 'Test2'
            id = sa.Column(sa.Integer, primary_key=True)
            nick = sa.Column(sa.String)
            other_id = sa.Column(sa.Integer, sa.ForeignKey('Test.id'))
            other = sa.orm.relation(DBTestCls1,
                                    backref=sa.orm.backref('others'))

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

    #def tearDown(self):
    #    Base.metadata.drop_all()
