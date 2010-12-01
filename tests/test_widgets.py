import tw2.core as twc, tw2.sqla as tws, tw2.forms as twf, sqlalchemy as sa
from webob import Request
from cStringIO import StringIO

import elixir as el
import transaction
from sqlalchemy.ext.declarative import declarative_base

import tw2.core.testbase as tw2test

class ElixirBase(object):
    def setup(self):
        el.metadata = sa.MetaData('sqlite:///:memory:')

        class DBTestCls1(el.Entity):
            name = el.Field(el.String)
            def __unicode__(self):
                return self.name
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

        self.DBTestCls1(id=1, name='foo1')
        self.DBTestCls1(id=2, name='foo2')
        self.DBTestCls2(id='bob')
        transaction.commit()

        return super(ElixirBase, self).setup()

class SQLABase(object):
    def setup(self):
        Base = declarative_base(metadata=sa.MetaData('sqlite:///:memory:'))
        Base.query = tws.transactional_session().query_property()

        class DBTestCls1(Base):
            __tablename__ = 'Test'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String(50))
            def __unicode__(self):
                return self.name
        class DBTestCls2(Base):
            __tablename__ = 'Test2'
            id = sa.Column(sa.String, primary_key=True)
            other_id = sa.Column(sa.Integer, sa.ForeignKey('Test.id'))
            other = sa.orm.relation(DBTestCls1, backref=sa.orm.backref('others'))
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
        session.add(self.DBTestCls1(id=1, name='foo1'))
        session.add(self.DBTestCls1(id=2, name='foo2'))
        session.add(self.DBTestCls2(id='bob'))
        session.commit()

        return super(SQLABase, self).setup()

class RadioButtonT(tw2test.WidgetTest):
    widget = tws.DbRadioButtonList
    attrs = {'css_class':'something', 'id' : 'something'}
    params = {'checked':None}
    expected = """
    <ul class="something" name="something" id="something">
    <li>
        <input type="radio" name="something" value="1" id="something:0"/>
        <label for="something:0">foo1</label>
    </li>
    <li>
        <input type="radio" name="something" value="2" id="something:1"/>
        <label for="something:1">foo2</label>
    </li>
    </ul>"""
    
    def setup(self):
        self.widget = self.widget(entity=self.DBTestCls1)
        return super(RadioButtonT, self).setup()

class TestRadioButtonElixir(ElixirBase, RadioButtonT): pass
class TestRadioButtonSQLA(SQLABase, RadioButtonT): pass

class CheckBoxT(tw2test.WidgetTest):
    widget = tws.DbCheckBoxList
    attrs = {'css_class':'something', 'id' : 'something'}
    params = {'checked':None}
    expected = """
    <ul class="something" name="something" id="something">
    <li>
        <input type="checkbox" name="something" value="1" id="something:0"/>
        <label for="something:0">foo1</label>
    </li>
    <li>
        <input type="checkbox" name="something" value="2" id="something:1"/>
        <label for="something:1">foo2</label>
    </li>
    </ul>"""

    def setup(self):
        self.widget = self.widget(entity=self.DBTestCls1)
        return super(CheckBoxT, self).setup()

class TestCheckBoxElixir(ElixirBase, CheckBoxT): pass
class TestCheckBoxSQLA(SQLABase, CheckBoxT): pass

class SingleSelectT(tw2test.WidgetTest):
    widget = tws.DbSingleSelectField
    attrs = {'css_class':'something', 'id' : 'something'}
    params = {'checked':None}
    expected = """
    <select class="something" name="something" id="something">
    <option ></option>
    <option value="1">foo1</option>
    <option value="2">foo2</option>
    </select>"""
    
    def setup(self):
        self.widget = self.widget(entity=self.DBTestCls1)
        return super(SingleSelectT, self).setup()

class TestSingleSelectElixir(ElixirBase, SingleSelectT): pass
class TestSingleSelectSQLA(SQLABase, SingleSelectT): pass

class FormPageT(tw2test.WidgetTest):
    def setup(self):
        self.widget = self.widget(entity=self.DBTestCls1)
        return super(FormPageT, self).setup()

    widget = tws.DbFormPage
    attrs = {
        'child': twf.TableForm(
            children=[
                twf.TextField(id='name'),
            ]),
        'title': 'some title'
    }
    expected = """<html>
<head><title>some title</title></head>
<body id="dbformpage_d:page"><h1>some title</h1><form method="post" id="dbformpage_d:form" enctype="multipart/form-data">
     <span class="error"></span>
    <table id="dbformpage_d">
    <tr class="odd" id="dbformpage_d:name:container">
        <th>Name</th>
        <td>
            <input name="dbformpage_d:name" id="dbformpage_d:name" type="text">
            <span id="dbformpage_d:name:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="dbformpage_d:error"></span>
    </td></tr>
</table>
    <input type="submit" id="submit" value="Save">
</form></body>
</html>"""

    declarative = True

    def test_request_get(self):
        environ = {'REQUEST_METHOD': 'GET',
                   }
        req=Request(environ)
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """<html>
<head><title>some title</title></head>
<body id="dbformpage_d:page"><h1>some title</h1><form method="post" id="dbformpage_d:form" enctype="multipart/form-data">
     <span class="error"></span>
    <table id="dbformpage_d">
    <tr class="odd" id="dbformpage_d:name:container">
        <th>Name</th>
        <td>
            <input name="dbformpage_d:name" id="dbformpage_d:name" type="text">
            <span id="dbformpage_d:name:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="dbformpage_d:error"></span>
    </td></tr>
</table>
    <input type="submit" id="submit" value="Save">
</form></body>
</html>""")

    def _test_request_post_invalid(self):
        # i have commented this because the post is in fact
        # valid, there are no arguments sent to the post, but the
        # widget does not require them
        environ = {'REQUEST_METHOD': 'POST',
                   'wsgi.input': StringIO(''),

                   }
        req=Request(environ)
        r = self.widget().request(req)
        assert_eq_xml(r.body, """<html>
<head><title>some title</title></head>
<body id="dbformpage_d:page"><h1>some title</h1><form method="post" id="dbformpage_d:form" enctype="multipart/form-data">
     <span class="error"></span>
    <table id="dbformpage_d">
    <tr class="odd" id="dbformpage_d:name:container">
        <th>Name</th>
        <td>
            <input name="dbformpage_d:name" id="dbformpage_d:name" type="text">
            <span id="dbformpage_d:name:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="dbformpage_d:error"></span>
    </td></tr>
</table>
    <input type="submit" id="submit" value="Save">
</form></body>
</html>""")


class TestFormPageElixir(ElixirBase, FormPageT):
    def test_request_post_valid(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='dbformpage_d:name=a'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        r = self.widget().request(req)
        assert r.body == """Form posted successfully {'name': u'a'}""", r.body

class TestFormPageSQLA(SQLABase, FormPageT):
    def test_neither_pylons_nor_elixir(self):
        raise NotImplementedError("Gotta write this test.")

    def test_no_DBSession(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='dbformpage_d:name=a'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        try:
            r = self.widget().request(req)
            assert False
        except KeyError, e:
            msg = '\'pylons config must contain a DBSession\''
            assert(str(e) == msg)

    def test_request_post_valid(self):
        import pylons
        pylons.configuration.config.setdefault('DBSession', self.session)
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='dbformpage_d:name=a'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        r = self.widget().request(req)
        assert r.body == """Form posted successfully {'name': u'a'}""", r.body
