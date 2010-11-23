import tw2.core as twc, tw2.sqla as tws, sqlalchemy as sa
import testapi

class BaseObject(object):
    """ Contains all tests to be run over Elixir and sqlalchemy-declarative """
    def setUp(self):
        raise NotImplementedError, "Must be subclassed."

    def test_null(self):
        vld = tws.RelatedValidator(self.DBTestCls1)
        assert(vld.from_python(None) is None)
        assert(vld.to_python('') is None)

    def test_int(self):
        vld = tws.RelatedValidator(self.DBTestCls1)
        t1 = vld.to_python('1')    
        assert(isinstance(t1, self.DBTestCls1))
        assert(t1.id == 1)
        assert(vld.from_python(t1) == u'1')
        try:
            vld.to_python('x')
            assert(False)
        except twc.ValidationError:
            pass
        try:
            vld.to_python('2')
            assert(False)
        except twc.ValidationError:
            pass

    def test_nonint(self):
        vld = tws.RelatedValidator(self.DBTestCls2)
        t1 = vld.to_python('bob')
        assert(isinstance(t1, self.DBTestCls2))
        assert(t1.id == 'bob')
        assert(vld.from_python(t1) == u'bob')
        try:
            vld.to_python('x')
            assert(False)
        except twc.ValidationError:
            pass

    def test_twopk_dec(self):
        try:
            tws.RelatedValidator(self.DBTestCls3)
            assert(False)
        except twc.WidgetError, e:
            assert(str(e) == 'RelatedValidator can only act on tables that have a single primary key column')

class TestElixir(BaseObject):
    def setUp(self):
        import elixir as el
        import transaction
        el.metadata = sa.MetaData('sqlite:///:memory:')

        class DBTestCls1(el.Entity):
            name = el.Field(el.String)
        class DBTestCls2(el.Entity):
            id = el.Field(el.String, primary_key=True)
        class DBTestCls3(el.Entity):
            id1 = el.Field(el.Integer, primary_key=True)
            id2 = el.Field(el.Integer, primary_key=True)
        
        self.DBTestCls1 = DBTestCls1
        self.DBTestCls2 = DBTestCls2
        self.DBTestCls3 = DBTestCls3
    
        el.setup_all()
        el.metadata.create_all()

        self.DBTestCls1(id=1)
        self.DBTestCls2(id='bob')
        transaction.commit()

        testapi.setup()

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
            id = sa.Column(sa.String, primary_key=True)
        class DBTestCls3(Base):
            __tablename__ = 'Test3'
            id1 = sa.Column(sa.Integer, primary_key=True)
            id2 = sa.Column(sa.Integer, primary_key=True)

        self.DBTestCls1 = DBTestCls1
        self.DBTestCls2 = DBTestCls2
        self.DBTestCls3 = DBTestCls3
    
        Base.metadata.create_all()

        session = sa.orm.sessionmaker()()
        self.session = session
        session.add(self.DBTestCls1(id=1))
        session.add(self.DBTestCls2(id='bob'))
        session.commit()

        testapi.setup()

