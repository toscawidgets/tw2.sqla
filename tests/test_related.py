import tw2.core as twc, tw2.sqla as tws, sqlalchemy as sa, elixir as el

el.metadata = sa.MetaData('sqlite:///:memory:')
class Test(el.Entity):
    name = el.Field(el.String)
class Test2(el.Entity):
    id = el.Field(el.String, primary_key=True)
class Test3(el.Entity):
    id1 = el.Field(el.Integer, primary_key=True)
    id2 = el.Field(el.Integer, primary_key=True)
el.setup_all()
el.metadata.create_all()

Test(id=1)
Test2(id='bob')
el.session.commit()
el.session = tws.transactional_session()


def test_int():
    vld = tws.RelatedValidator(Test)
    assert(vld.to_python('1') is Test.get(1))
    assert(vld.from_python(Test.get(1)) == u'1')
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
        
def test_nonint():
    vld = tws.RelatedValidator(Test2)
    assert(vld.to_python('bob') is Test2.get('bob'))
    assert(vld.from_python(Test2.get('bob')) == u'bob')
    try:
        vld.to_python('x')
        assert(False)
    except twc.ValidationError:
        pass

def test_twopk():
    try:
        tws.RelatedValidator(Test3)
        assert(False)
    except twc.WidgetError, e:
        assert(str(e) == 'RelatedValidator can only act on tables that have a single primary key column')

def test_null():
    vld = tws.RelatedValidator(Test)
    assert(vld.from_python(None) is None)
    assert(vld.to_python('') is None)
