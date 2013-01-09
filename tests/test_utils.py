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

    def test_from_dict_modify_to_none(self):
        # Do this to set up an object with name => 'bazaar'
        self.test_from_dict_new()

        # Now try to modify that object and set its name to None
        d = {
            'id': 2,
            'name': None,
        }
        x = self.DBTestCls1.query.filter_by(id=2).first()
        e = twsu.from_dict(x, d)
        self.session.flush()

        eq_(e.id, 2)
        eq_(e.name, None)
        eq_(len(e.others), 0)

    def test_from_dict_modify_many_to_many(self):
        d = {
            'id': 1,
            'surname': 'user1',
            'roles': [],
        }
        u = twsu.from_dict(self.session.query(self.DBTestCls3).one(), d)
        self.session.add(u)
        self.session.flush()

        assert(self.session.query(self.DBTestCls3).count() == 1)
        assert(self.session.query(self.DBTestCls4).count() == 1)
        assert(u.id == 1)
        assert(u.surname == 'user1')
        assert(u.roles == [])

    def test_from_dict_modify_one_to_one(self):
        d = {
            'id': None,
            'name': 'user1',
            'account': {
                'account_name': 'account2',
            }
        }
        u = twsu.from_dict(self.session.query(self.DBTestCls6).one(), d)
        self.session.add(u)
        self.session.flush()

        assert(u.id == 1)
        assert(u.name == 'user1')
        assert(u.account.account_name == 'account2')
        assert(self.session.query(self.DBTestCls5).count() == 1)

    def test_from_dict_modify_one_to_one_to_none(self):
        d = {
            'id': None,
            'name': 'user1',
            'account': None
        }
        u = twsu.from_dict(self.session.query(self.DBTestCls6).one(), d)
        self.session.flush()

        assert(u.id == 1)
        assert(u.name == 'user1')
        assert(u.account == None)
        assert(self.session.query(self.DBTestCls5).count() == 0)

    def test_from_dict_new_many_to_one_by_id(self):
        d = {
            'id': None,
            'nick': 'bazaar',
            'other_id': 1,
        }
        e = twsu.from_dict(self.DBTestCls2(), d)
        self.session.add(e)
        self.session.flush()
        assert(e.id == 3)
        assert(e.nick == 'bazaar')
        assert(len(e.other.others) == 2)
        assert(e in e.other.others)

    def test_from_dict_new_many_to_many_by_id(self):
        d = {
            'id': None,
            'surname': 'user1',
            'roles': [self.admin_role],
        }
        u = twsu.from_dict(self.DBTestCls3(), d)
        self.session.add(u)
        self.session.flush()
        assert(u.id == 2)
        assert(u.surname == 'user1')
        assert(u.roles == [self.admin_role])

    def test_from_dict_new_one_to_one_by_id(self):
        d = {
            'id': None,
            'name': 'user1',
            'account': self.DBTestCls5(account_name='account2'),
        }
        u = twsu.from_dict(self.DBTestCls6(), d)
        self.session.add(u)
        self.session.flush()
        assert(u.id == 2)
        assert(u.name == 'user1')
        assert(u.account.account_name == 'account2')
        assert(self.session.query(self.DBTestCls5).count() == 2)

    def test_from_dict_new_one_to_one_by_id_no_account(self):
        d = {
            'id': None,
            'name': 'user1',
            'account': None,
        }
        u = twsu.from_dict(self.DBTestCls6(), d)
        self.session.add(u)
        self.session.flush()
        assert(u.id == 2)
        assert(u.name == 'user1')
        assert(u.account == None)
        assert(self.session.query(self.DBTestCls5).count() == 1)

    def test_from_dict_old_many_to_one_by_dict_recall(self):
        assert(self.DBTestCls2.query.first().nick == 'bob')
        d = {
            'nick': 'updated',
            'other': {
                'id': 1
            }
        }

        e = twsu.from_dict(self.DBTestCls2.query.first(), d)
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
        self.session.flush()
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
        self.session.flush()
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

        class DBTestCls3(el.Entity):
            surname = el.Field(el.String)
            roles = el.ManyToMany('DBTestCls4')

        class DBTestCls4(el.Entity):
            rolename = el.Field(el.String)
            users = el.ManyToMany('DBTestCls3')

        class DBTestCls5(el.Entity):
            account_name = el.Field(el.String, required=True)
            user = el.OneToOne('DBTestCls6', inverse='account')

        class DBTestCls6(el.Entity):
            name = el.Field(el.String)
            account_id = el.Field(el.Integer, required=False)
            account = el.ManyToOne(DBTestCls5, field=account_id, inverse='user', uselist=False)

        self.DBTestCls1 = DBTestCls1
        self.DBTestCls2 = DBTestCls2
        self.DBTestCls3 = DBTestCls3
        self.DBTestCls4 = DBTestCls4
        self.DBTestCls5 = DBTestCls5
        self.DBTestCls6 = DBTestCls6

        el.setup_all()
        el.metadata.create_all()
        foo = self.DBTestCls1(id=1, name='foo')
        bob = self.DBTestCls2(id=1, nick='bob', other=foo)
        george = self.DBTestCls2(id=2, nick='george')
        fred = self.DBTestCls3(id=1, surname='fred')
        admin = self.DBTestCls4(id=1, rolename='admin')
        fred.roles.append(admin)
        account1 = self.DbTestCls5(id=1, account_name='account1')
        bob1 = self.DbTestCls6(id=1, name='bob1', account_id=1)

        testapi.setup()
        self.admin_role = admin

    #def tearDown(self):
    #    import elixir as el
    #    el.drop_all()


# Disable elixir tests if its not importable.
el = None
try:
    import elixir as el
except ImportError:
    pass

if not el:
    TestElixir = None


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

        join_table = sa.Table('Test3_Test4', Base.metadata,
            sa.Column('Test3', sa.Integer, sa.ForeignKey('Test3.id'), primary_key=True),
            sa.Column('Test4', sa.Integer, sa.ForeignKey('Test4.id'), primary_key=True)
        )
        class DBTestCls3(Base):
            __tablename__ = 'Test3'
            id = sa.Column(sa.Integer, primary_key=True)
            surname = sa.Column(sa.String(50))
            def __unicode__(self):
                return self.surname
        class DBTestCls4(Base):
            __tablename__ = 'Test4'
            id = sa.Column(sa.Integer, primary_key=True)
            rolename = sa.Column(sa.String(50))
            users = sa.orm.relationship('DBTestCls3', secondary=join_table, backref='roles')
            def __unicode__(self):
                return self.rolename

        class DBTestCls5(Base):
            __tablename__ = 'Test5'
            id = sa.Column(sa.Integer, primary_key=True)
            account_name = sa.Column(sa.String(50), nullable=False)

        class DBTestCls6(Base):
            __tablename__ = 'Test6'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String(50))
            account_id = sa.Column(sa.Integer, sa.ForeignKey('Test5.id'), nullable=True)
            account = sa.orm.relation(DBTestCls5, backref=sa.orm.backref('user', uselist=False))

        Base.metadata.create_all()

        self.DBTestCls1 = DBTestCls1
        self.DBTestCls2 = DBTestCls2
        self.DBTestCls3 = DBTestCls3
        self.DBTestCls4 = DBTestCls4
        self.DBTestCls5 = DBTestCls5
        self.DBTestCls6 = DBTestCls6

        foo = self.DBTestCls1(id=1, name='foo')
        self.session.add(foo)

        bob = self.DBTestCls2(id=1, nick='bob')
        bob.other = foo
        self.session.add(bob)
        george = self.DBTestCls2(id=2, nick='george')
        self.session.add(george)

        fred = self.DBTestCls3(id=1, surname='fred')
        admin = self.DBTestCls4(id=1, rolename='admin')
        fred.roles.append(admin)
        self.session.add(fred)
        self.admin_role = admin

        account1 = self.DBTestCls5(id=1, account_name='account1')
        self.session.add(account1)
        bob1 = self.DBTestCls6(id=1, name='bob1', account_id=1)
        self.session.add(bob1)

        transaction.commit()

        testapi.setup()

    #def tearDown(self):
    #    Base.metadata.drop_all()
