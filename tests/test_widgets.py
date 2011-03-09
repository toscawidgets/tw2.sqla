import tw2.core as twc, tw2.sqla as tws, tw2.forms as twf, sqlalchemy as sa
from webob import Request
from cStringIO import StringIO

import elixir as el
import transaction
from sqlalchemy.ext.declarative import declarative_base
import nose

import tw2.core.testbase as tw2test

class ElixirBase(object):
    def setup(self):
        el.metadata = sa.MetaData('sqlite:///:memory:')
        el.session = tws.transactional_session()

        class DbTestCls1(el.Entity):
            name = el.Field(el.String)
            def __unicode__(self):
                return self.name

        class DbTestCls2(el.Entity):
            nick = el.Field(el.String)
            other_id = el.Field(el.Integer)
            other = el.ManyToOne(DbTestCls1, field=other_id, backref='others')
            def __unicode__(self):
                return self.nick
        
        class DbTestCls3(el.Entity):
            id1 = el.Field(el.Integer, primary_key=True)
            id2 = el.Field(el.Integer, primary_key=True)
        
        self.DbTestCls1 = DbTestCls1
        self.DbTestCls2 = DbTestCls2
        self.DbTestCls3 = DbTestCls3
    
        el.setup_all()
        el.metadata.create_all()

        self.DbTestCls1(id=1, name='foo1')
        self.DbTestCls1(id=2, name='foo2')
        self.DbTestCls2(id=1, nick='bob1')
        self.DbTestCls2(id=2, nick='bob2')
        self.DbTestCls2(id=3, nick='bob3')
        transaction.commit()

        return super(ElixirBase, self).setup()

class SQLABase(object):
    def setup(self):
        self.session = tws.transactional_session()
        Base = declarative_base(metadata=sa.MetaData('sqlite:///:memory:'))
        Base.query = self.session.query_property()

        class DbTestCls1(Base):
            __tablename__ = 'Test'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String(50))
            def __unicode__(self):
                return self.name
        class DbTestCls2(Base):
            __tablename__ = 'Test2'
            id = sa.Column(sa.Integer, primary_key=True)
            nick = sa.Column(sa.String(50))
            other_id = sa.Column(sa.Integer, sa.ForeignKey('Test.id'))
            other = sa.orm.relation(DbTestCls1, backref=sa.orm.backref('others'))
            def __unicode__(self):
                return self.nick
        class DbTestCls3(Base):
            __tablename__ = 'Test3'
            id1 = sa.Column(sa.Integer, primary_key=True)
            id2 = sa.Column(sa.Integer, primary_key=True)

        self.DbTestCls1 = DbTestCls1
        self.DbTestCls2 = DbTestCls2
        self.DbTestCls3 = DbTestCls3
    
        Base.metadata.create_all()

        self.session.add(self.DbTestCls1(id=1, name='foo1'))
        self.session.add(self.DbTestCls1(id=2, name='foo2'))
        self.session.add(self.DbTestCls2(id=1, nick='bob1'))
        self.session.add(self.DbTestCls2(id=2, nick='bob2'))
        self.session.add(self.DbTestCls2(id=3, nick='bob3'))
        transaction.commit()

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
        self.widget = self.widget(entity=self.DbTestCls1)
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
        self.widget = self.widget(entity=self.DbTestCls1)
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
        self.widget = self.widget(entity=self.DbTestCls1)
        return super(SingleSelectT, self).setup()

class TestSingleSelectElixir(ElixirBase, SingleSelectT): pass
class TestSingleSelectSQLA(SQLABase, SingleSelectT): pass

class ListPageT(tw2test.WidgetTest):
    def setup(self):
        self.widget = self.widget(entity=self.DbTestCls1)
        return super(ListPageT, self).setup()

    widget = tws.DbListPage
    attrs = {
        'child': twf.GridLayout(
            children=[
                twf.LabelField(id='name'),
                # TODO -- test this with label=None, diff between elixir and sqla
                twf.LinkField(id='id', link='foo?id=$',
                              text='Edit', label='Edit'),
            ]),
        'newlink' : twf.LinkField(link='cls1', text='New', value=1)
    }

    # This is kind of non-sensical.  A DbListPage with no call to fetch_data?
    expected = """<html>
<head><title>Db Test Cls1</title></head>
<body id="dblistpage_d:page">
<h1>Db Test Cls1</h1>
    <table id="dblistpage_d">
    <tr><th>Name</th><th>Edit</th></tr>
    <tr class="error"><td colspan="0" id="dblistpage_d:error">
    </td></tr>
</table>
<a href="cls1">New</a>
</body>
</html>"""

    declarative = True
    def test_request_get(self):
        # This makes much more sense.
        environ = {
            'REQUEST_METHOD': 'GET',
        }
        req=Request(environ)
        self.mw.config.debug = True
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """
<html>
<head><title>Db Test Cls1</title></head>
    <body id="dblistpage_d:page"><h1>Db Test Cls1</h1>
            <table id="dblistpage_d">
                <tr><th>Name</th><th>Edit</th></tr>
                <tr id="dblistpage_d:0" class="odd">
                <td>
                    <span>foo1<input type="hidden" name="dblistpage_d:0:name" value="foo1" id="dblistpage_d:0:name"/></span>
                </td>
                <td>
                    <a href="foo?id=1" id="dblistpage_d:0:id">Edit</a>
                </td>
                <td>
                </td>
            </tr>
            <tr id="dblistpage_d:1" class="even">
                <td>
                    <span>foo2<input type="hidden" name="dblistpage_d:1:name" value="foo2" id="dblistpage_d:1:name"/></span>
                </td>
                <td>
                    <a href="foo?id=2" id="dblistpage_d:1:id">Edit</a>
                </td>
                <td>
                </td>
            </tr>
            <tr class="error"><td colspan="2" id="dblistpage_d:error"></td></tr>
        </table>
        <a href="cls1">New</a>
</body>
</html>""")
 


class TestListPageElixir(ElixirBase, ListPageT): pass

class TestListPageSQLA(SQLABase, ListPageT):
    def setup(self):
        super(TestListPageSQLA, self).setup()
        import pylons
        pylons.configuration.config.setdefault('DBSession', self.session)

class FormPageT(tw2test.WidgetTest):
    def setup(self):
        self.widget = self.widget(entity=self.DbTestCls1)
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
    def test_request_get_edit(self):
        # TODO -- this never actually tests line 68 of tw2.sqla.widgets
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING' : 'id=1'
        }
        req=Request(environ)
        self.mw.config.debug = True
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """<html>
<head><title>some title</title></head>
<body id="dbformpage_d:page"><h1>some title</h1><form method="post" id="dbformpage_d:form" enctype="multipart/form-data">
     <span class="error"></span>
    <table id="dbformpage_d">
    <tr class="odd" id="dbformpage_d:name:container">
        <th>Name</th>
        <td>
            <input name="dbformpage_d:name" value="foo1" id="dbformpage_d:name" type="text">
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
 
   
    def test_request_post_redirect(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='dbformpage_d:name=a'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        r = self.widget(redirect="/foo").request(req)
        assert( r.status_int == 302 and r.location=="/foo" )

    def test_request_get(self):
        environ = {'REQUEST_METHOD': 'GET',}
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

class TestFormPageElixir(ElixirBase, FormPageT): pass

class TestFormPageSQLA(SQLABase, FormPageT):
    def setup(self):
        super(TestFormPageSQLA, self).setup()
        import pylons
        pylons.configuration.config.setdefault('DBSession', self.session)

    def test_neither_pylons_nor_elixir(self):
        import sys
      
        # Temporarily hide pylons from the importer
        import pylons 
        tmp = sys.modules['pylons']
        sys.modules['pylons'] = None

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
        except NotImplementedError, e:
            assert(str(e) == 'Neither elixir nor pylons')
        finally:
            sys.modules['pylons'] = tmp

    def test_no_DBSession(self):
        # Temporarily remove the pylons configuration
        import sys
        tmp = {}
        for m in sys.modules.keys():
            if 'pylons' in m.lower():
                tmp[m] = sys.modules[m]
                del sys.modules[m]

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
        finally:
            # Restore pylons
            for k, v in tmp.iteritems():
                sys.modules[k] = v

class AutoListPageT(tw2test.WidgetTest):
    def setup(self):
        self.widget = self.widget(entity=self.DbTestCls1)
        return super(AutoListPageT, self).setup()


    widget = tws.AutoListPage
   
    # Doesn't make much sense... an AutoList widget with fetch_data not called?
    expected = """
    <html>
    <head><title>Db Test Cls1</title></head>
    <body id="autolistpage_d:page">
    <h1>Db Test Cls1</h1>
    <table id="autolistpage_d">
        <tr><th>Name</th><th>Others</th></tr>
        <tr class="error"><td colspan="0" id="autolistpage_d:error">
        </td></tr>
    </table>
    </body>
    </html> 
    """

### TODO -- reenable this
##    declarative = True
#    def test_request_get(self):
#        # This makes much more sense.
#        environ = {
#            'REQUEST_METHOD': 'GET',
#        }
#        req=Request(environ)
#        self.mw.config.debug = True
#        r = self.widget().request(req)
#        tw2test.assert_eq_xml(r.body, """
#<html>
#<head><title>Db Test Cls1</title></head>
#    <body id="dblistpage_d:page"><h1>Db Test Cls1</h1>
#            <table id="dblistpage_d">
#                <tr><th>Name</th><th>Edit</th></tr>
#                <tr id="dblistpage_d:0" class="odd">
#                <td>
#                    <span>foo1<input type="hidden" name="dblistpage_d:0:name" value="foo1" id="dblistpage_d:0:name"/></span>
#                </td>
#                <td>
#                    <a href="foo?id=1" id="dblistpage_d:0:id">Edit</a>
#                </td>
#                <td>
#                </td>
#            </tr>
#            <tr id="dblistpage_d:1" class="even">
#                <td>
#                    <span>foo2<input type="hidden" name="dblistpage_d:1:name" value="foo2" id="dblistpage_d:1:name"/></span>
#                </td>
#                <td>
#                    <a href="foo?id=2" id="dblistpage_d:1:id">Edit</a>
#                </td>
#                <td>
#                </td>
#            </tr>
#            <tr class="error"><td colspan="2" id="dblistpage_d:error"></td></tr>
#        </table>
#        <a href="cls1">New</a>
#</body>
#</html>""")



class TestAutoListPageElixir(ElixirBase, AutoListPageT): pass
class TestAutoListPageSQLA(SQLABase, AutoListPageT):
    def setup(self):
        super(TestAutoListPageSQLA, self).setup()
        import pylons
        pylons.configuration.config.setdefault('DBSession', self.session)

# TODO -- do AutoListPageEDIT here

class AutoTableFormT1(tw2test.WidgetTest):
    def setup(self):
        self.widget = self.widget(entity=self.DbTestCls1)
        return super(AutoTableFormT1, self).setup()

    widget = tws.AutoTableForm
    attrs = { 'id' : 'foo_form' }
    expected = """
<form method="post" id="foo_form:form" enctype="multipart/form-data">
     <span class="error"></span>
    <table id="foo_form">
    <tr class="odd" id="foo_form:name:container">
        <th>Name</th>
        <td>
            <input name="foo_form:name" id="foo_form:name" type="text">
            <span id="foo_form:name:error"></span>
        </td>
        </tr>
     <tr class="even"  id="foo_form:others:container">
        <th>Others</th>
        <td >
            <select name="foo_form:others" id="foo_form:others">
             <option ></option>
             <option value="1">bob1</option>
             <option value="2">bob2</option>
             <option value="3">bob3</option>
            </select>
            <span id="foo_form:others:error"></span>
        </td>
    </tr>
   <tr class="error"><td colspan="2">
        <span id="foo_form:error"></span>
    </td></tr>
</table>
    <input type="submit" id="submit" value="Save">
</form>"""

class TestAutoTableForm1Elixir(ElixirBase, AutoTableFormT1): pass
class TestAutoTableForm1SQLA(SQLABase, AutoTableFormT1):
    def setup(self):
        super(TestAutoTableForm1SQLA, self).setup()
        import pylons
        pylons.configuration.config.setdefault('DBSession', self.session)

class AutoTableFormT2(tw2test.WidgetTest):
    def setup(self):
        self.widget = self.widget(entity=self.DbTestCls2)
        return super(AutoTableFormT2, self).setup()

    widget = tws.AutoTableForm
    attrs = { 'id' : 'foo_form' }
    expected = """
<form id="foo_form:form" enctype="multipart/form-data" method="post">
     <span class="error"></span>
    <table id="foo_form">
    <tr class="odd"  id="foo_form:nick:container">
        <th>Nick</th>
        <td >
            <input name="foo_form:nick" type="text" id="foo_form:nick"/>
            <span id="foo_form:nick:error"></span>
        </td>
    </tr>
     <tr class="even"  id="foo_form:other:container">
        <th>Other</th>
        <td >
            <select name="foo_form:other" id="foo_form:other">
         <option ></option>
         <option value="1">foo1</option>
         <option value="2">foo2</option>
</select>
            <span id="foo_form:other:error"></span>
        </td>
    </tr>
   <tr class="error"><td colspan="2">
        <span id="foo_form:error"></span>
    </td></tr>
</table>
    <input type="submit" value="Save" id="submit"/>
</form>
"""

class TestAutoTableForm2Elixir(ElixirBase, AutoTableFormT2): pass
class TestAutoTableForm2SQLA(SQLABase, AutoTableFormT2):
    def setup(self):
        super(TestAutoTableForm2SQLA, self).setup()
        import pylons
        pylons.configuration.config.setdefault('DBSession', self.session)


class AutoViewGridT(tw2test.WidgetTest):
    def setup(self):
        self.widget = self.widget(entity=self.DbTestCls1)
        return super(AutoViewGridT, self).setup()

    widget = tws.AutoViewGrid
    attrs = { 'id' : 'autogrid' }
    
    expected = """
    <table id='autogrid'>
    <tr><th>Name</th><th>Others</th></tr>
    <tr class="error"><td colspan="0" id="autogrid:error"></td></tr>
    </table>"""


class TestAutoViewGridElixir(ElixirBase, AutoViewGridT): pass
class TestAutoViewGridSQLA(SQLABase, AutoViewGridT):
    def setup(self):
        super(TestAutoViewGridSQLA, self).setup()
        import pylons
        pylons.configuration.config.setdefault('DBSession', self.session)

class AutoGrowingGridT(tw2test.WidgetTest):
    def setup(self):
        self.widget = self.widget(entity=self.DbTestCls1)
        return super(AutoGrowingGridT, self).setup()

    widget = tws.AutoGrowingGrid
    attrs = { 'id' : 'autogrid' }
    # TBD -- should the values from the db show up here?
    expected = """
    <table id="autogrid">
        <tr>
            <th>Name</th><th>Others</th><th></th>
            <td><input style="display:none" type="image" id="autogrid:undo" src="/resources/tw2.dynforms.widgets/static/undo.png" alt="Undo" onclick="twd_grow_undo(this); return false;"></td>
        </tr>
        <tr style="display:none;" id="autogrid:0" class="odd">
        <td>
            <input name="autogrid:0:name" id="autogrid:0:name" onchange="twd_grow_add(this);" type="text">
        </td><td>
        <select onchange="twd_grow_add(this);" id="autogrid:0:others" name="autogrid:0:others">
        <option></option><option value="1">bob1</option><option value="2">bob2</option><option value="3">bob3</option>
        </select>
        </td><td>
            <input src="/resources/tw2.dynforms.widgets/static/del.png" style="display:none;" name="autogrid:0:del" id="autogrid:0:del" onclick="twd_grow_del(this); return false;" alt="Delete row" type="image">
        </td>
        <td>
        </td>
    </tr><tr id="autogrid:1" class="even">
        <td>
            <input name="autogrid:1:name" id="autogrid:1:name" onchange="twd_grow_add(this);" type="text">
        </td><td>
        <select onchange="twd_grow_add(this);" id="autogrid:1:others" name="autogrid:1:others">
        <option></option><option value="1">bob1</option><option value="2">bob2</option><option value="3">bob3</option>
        </select>
        </td><td>
            <input src="/resources/tw2.dynforms.widgets/static/del.png" style="display:none;" name="autogrid:1:del" id="autogrid:1:del" onclick="twd_grow_del(this); return false;" alt="Delete row" type="image">
        </td>
        <td>
        </td>
    </tr>
    </table>"""

class TestAutoGrowingGridElixir(ElixirBase, AutoGrowingGridT): pass
class TestAutoGrowingGridSQLA(SQLABase, AutoGrowingGridT):
    def setup(self):
        super(TestAutoGrowingGridSQLA, self).setup()
        import pylons
        pylons.configuration.config.setdefault('DBSession', self.session)


class AutoGrowingGridAsChildT(tw2test.WidgetTest):
    def setup(self):
        self.widget = self.widget(entity=self.DbTestCls1)
        return super(AutoGrowingGridAsChildT, self).setup()

    widget = tws.DbFormPage
    attrs = { 'id' : 'autogrid', 'title' : 'Test',
              'child' : tws.AutoGrowingGrid}
    # TBD -- should the values from the db show up here?
    expected = """
    <html><head><title>Test</title></head>
    <body id="autogrid:page"><h1>Test</h1>
    <table id="autogrid">
        <tr>
            <th>Name</th><th>Others</th><th></th>
            <td><input style="display:none" type="image" id="autogrid:undo" src="/resources/tw2.dynforms.widgets/static/undo.png" alt="Undo" onclick="twd_grow_undo(this); return false;"></td>
        </tr>
        <tr style="display:none;" id="autogrid:0" class="odd">
        <td>
            <input name="autogrid:0:name" id="autogrid:0:name" onchange="twd_grow_add(this);" type="text">
        </td><td>
            <select onchange="twd_grow_add(this);" id="autogrid:0:others" name="autogrid:0:others">
            <option></option><option value="1">bob1</option><option value="2">bob2</option><option value="3">bob3</option>
            </select>
        </td><td>
            <input src="/resources/tw2.dynforms.widgets/static/del.png" style="display:none;" name="autogrid:0:del" id="autogrid:0:del" onclick="twd_grow_del(this); return false;" alt="Delete row" type="image">
        </td>
        <td>
        </td>
    </tr><tr id="autogrid:1" class="even">
        <td>
            <input name="autogrid:1:name" id="autogrid:1:name" onchange="twd_grow_add(this);" type="text">
        </td><td>
            <select onchange="twd_grow_add(this);" id="autogrid:1:others" name="autogrid:1:others">
            <option></option><option value="1">bob1</option><option value="2">bob2</option><option value="3">bob3</option>
            </select>
        </td><td>
            <input src="/resources/tw2.dynforms.widgets/static/del.png" style="display:none;" name="autogrid:1:del" id="autogrid:1:del" onclick="twd_grow_del(this); return false;" alt="Delete row" type="image">
        </td>
        <td>
        </td>
    </tr>
    </table></body></html>"""

class TestAutoGrowingGridAsChildElixir(ElixirBase, AutoGrowingGridAsChildT):
    pass
class TestAutoGrowingGridAsChildSQLA(SQLABase, AutoGrowingGridAsChildT):
    def setup(self):
        super(TestAutoGrowingGridAsChildSQLA, self).setup()
        import pylons
        pylons.configuration.config.setdefault('DBSession', self.session)

class AutoGrowingGridAsChildWithRelationshipT(tw2test.WidgetTest):
    def setup(self):
        self.widget = self.widget(entity=self.DbTestCls2)
        return super(AutoGrowingGridAsChildWithRelationshipT, self).setup()

    widget = twf.TableForm
    attrs = { 'title' : 'Test',
              'child' : tws.AutoGrowingGrid(id='others')}
    # TBD -- should the values from the db show up here?
    expected = """
    <form method="post" id="others:form" enctype="multipart/form-data">
    <span class="error"></span>
    <table id="others">
        <tr>
            <th>Nick</th><th>Other</th><th></th>
            <td><input style="display:none" type="image" id="others:undo" src="/resources/tw2.dynforms.widgets/static/undo.png" alt="Undo" onclick="twd_grow_undo(this); return false;"></td>
        </tr>
        <tr style="display:none;" id="others:0" class="odd">
        <td>
        <input name="others:0:nick" id="others:0:nick" onchange="twd_grow_add(this);" type="text">
        </td>
        <td>
        <select onchange="twd_grow_add(this);" id="others:0:other" name="others:0:other">
        <option></option><option value="1">foo1</option><option value="2">foo2</option>
</select>
        </td><td>
            <input src="/resources/tw2.dynforms.widgets/static/del.png" style="display:none;" name="others:0:del" id="others:0:del" onclick="twd_grow_del(this); return false;" alt="Delete row" type="image">
        </td>
        <td>
        </td>
    </tr><tr id="others:1" class="even">
        <td>
        <input name="others:1:nick" id="others:1:nick" onchange="twd_grow_add(this);" type="text">
        </td>
        <td>
        <select onchange="twd_grow_add(this);" id="others:1:other" name="others:1:other">
        <option></option><option value="1">foo1</option><option value="2">foo2</option>
</select>
        </td><td>
            <input src="/resources/tw2.dynforms.widgets/static/del.png" style="display:none;" name="others:1:del" id="others:1:del" onclick="twd_grow_del(this); return false;" alt="Delete row" type="image">
        </td>
        <td>
        </td>
    </tr>
    </table>
    <input type="submit" id="submit" value="Save">
    </form>"""

class TestAutoGrowingGridAsChildWithRelationshipElixir(
    ElixirBase, AutoGrowingGridAsChildWithRelationshipT):
    pass
class TestAutoGrowingGridAsChildWithRelationshipSQLA(
    SQLABase, AutoGrowingGridAsChildWithRelationshipT):
    def setup(self):
        super(TestAutoGrowingGridAsChildWithRelationshipSQLA, self).setup()
        import pylons
        pylons.configuration.config.setdefault('DBSession', self.session)
