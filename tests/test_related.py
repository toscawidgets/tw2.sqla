import tw2.core as twc, tw2.sqla as tws, sqlalchemy as sa

#-----------------------
# Elixir
#-----------------------
import elixir as el
el.metadata = sa.MetaData('sqlite:///:memory:')

class ElTest(el.Entity):
    name = el.Field(el.String)
class ElTest2(el.Entity):
    id = el.Field(el.String, primary_key=True)
class ElTest3(el.Entity):
    id1 = el.Field(el.Integer, primary_key=True)
    id2 = el.Field(el.Integer, primary_key=True)
el.setup_all()
el.metadata.create_all()

ElTest(id=1)
ElTest2(id='bob')
el.session.commit()


def test_int_el():
    vld = tws.RelatedValidator(ElTest)
    assert(vld.to_python('1') is ElTest.get(1))
    assert(vld.from_python(ElTest.get(1)) == u'1')
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
        
def test_nonint_el():
    vld = tws.RelatedValidator(ElTest2)
    assert(vld.to_python('bob') is ElTest2.get('bob'))
    assert(vld.from_python(ElTest2.get('bob')) == u'bob')
    try:
        vld.to_python('x')
        assert(False)
    except twc.ValidationError:
        pass

def test_twopk_el():
    try:
        tws.RelatedValidator(ElTest3)
        assert(False)
    except twc.WidgetError, e:
        assert(str(e) == 'RelatedValidator can only act on tables that have a single primary key column')

def test_null():
    vld = tws.RelatedValidator(ElTest)
    assert(vld.from_python(None) is None)
    assert(vld.to_python('') is None)


#-----------------------
# SQLAlchemy declarative
#-----------------------
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base(metadata=sa.MetaData('sqlite:///:memory:'))
Base.query = tws.transactional_session().query_property()

class DecTest(Base):
    __tablename__ = 'Test'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50))
class DecTest2(Base):
    __tablename__ = 'Test2'
    id = sa.Column(sa.String, primary_key=True)
class DecTest3(Base):
    __tablename__ = 'Test3'
    id1 = sa.Column(sa.Integer, primary_key=True)
    id2 = sa.Column(sa.Integer, primary_key=True)

Base.metadata.create_all()

session = sa.orm.sessionmaker()()
session.add(DecTest(id=1))
session.add(DecTest2(id='bob'))
session.commit()


def test_int_dec():
    vld = tws.RelatedValidator(DecTest)
    t1 = vld.to_python('1')    
    assert(isinstance(t1, DecTest))
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
        
def test_nonint_dec():
    vld = tws.RelatedValidator(DecTest2)
    t1 = vld.to_python('bob')
    assert(isinstance(t1, DecTest2))
    assert(t1.id == 'bob')
    assert(vld.from_python(t1) == u'bob')
    try:
        vld.to_python('x')
        assert(False)
    except twc.ValidationError:
        pass

def test_twopk_dec():
    try:
        tws.RelatedValidator(DecTest3)
        assert(False)
    except twc.WidgetError, e:
        assert(str(e) == 'RelatedValidator can only act on tables that have a single primary key column')
