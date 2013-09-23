import tw2.core as twc, tw2.sqla as tws, tw2.forms as twf, sqlalchemy as sa
from webob import Request
from cStringIO import StringIO

import transaction
from sqlalchemy.ext.declarative import declarative_base

import tw2.core.testbase as tw2test

class WidgetTest(tw2test.WidgetTest):
    engines = ['mako', 'genshi']
    declarative = True
    # NOTE: widget should have a default value to make sure the tests in
    # tw2test.WidgetTest are run.
    widget = twc.Widget


class WidgetEntityTest(WidgetTest):

    def setUp(self):
        self.widget = self._widget_cls(
            entity=getattr(self, self._entity_cls_str))
        return super(WidgetEntityTest, self).setUp()

class WidgetRequiredEntityTest(WidgetTest):

    def setUp(self):
        self.widget = self._widget_cls(
            entity=getattr(self, self._entity_cls_str),
            validator=twc.Required
        )
        return super(WidgetRequiredEntityTest, self).setUp()


# Only run elixir tests if it is importable.
el = None
try:
    import elixir as el
except ImportError:
    pass


class InfoField(twf.InputField): pass
class FakeValidator(twc.Validator): pass


class ElixirBase(object):
    def setUp(self):
        el.metadata = sa.MetaData('sqlite:///:memory:')
        el.session = tws.transactional_session()
        # Make sure the DB is clean between the tests
        el.cleanup_all(drop_tables=True)

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

        class DbTestCls4(el.Entity):
            surname = el.Field(el.String)
            roles = el.ManyToMany('DbTestCls5')
            def __unicode__(self):
                return self.surname

        class DbTestCls5(el.Entity):
            rolename = el.Field(el.String)
            users = el.ManyToMany('DbTestCls4')
            def __unicode__(self):
                return self.rolename

        class DbTestCls6(el.Entity):
            name = el.Field(el.String)
            tws_edit_link = '/edit/$'
            def __unicode__(self):
                return self.name

        class DbTestCls7(el.Entity):
            nick = el.Field(el.String)
            other_id = el.Field(el.Integer, required=True)
            other = el.ManyToOne(DbTestCls6, field=other_id, backref='others')
            def __unicode__(self):
                return self.nick

        class DbTestCls8(el.Entity):
            account_name = el.Field(el.String, required=True)
            user = el.OneToOne('DbTestCls9', inverse='account')
            def __unicode__(self):
                return self.account_name

        class DbTestCls9(el.Entity):
            name = el.Field(el.String)
            account_id = el.Field(el.Integer, required=True)
            account = el.ManyToOne(DbTestCls8, field=account_id, inverse='user', uselist=False)
            def __unicode__(self):
                return self.name

        class DbTestCls10(el.Entity):
            name = el.Field(el.String, primary_key=True)
            def __unicode__(self):
                return self.name

        class DbTestCls11(el.Entity):
            account_name = el.Field(el.String, required=True)
            account_number = el.Field(el.String, required=True)
            user = el.OneToOne('DbTestCls12', inverse='account')
            def __unicode__(self):
                return self.account_name

        class DbTestCls12(el.Entity):
            name = el.Field(el.String, required=True)
            account_id = el.Field(el.Integer, required=False)
            account = el.ManyToOne(DbTestCls11, field=account_id,
                                   inverse='user', uselist=False)
            def __unicode__(self):
                return self.name

        class DbTestCls13(el.Entity):
            name = el.Field(el.String, info={'edit_widget': InfoField},
                            required=True)
            def __unicode__(self):
                return self.name

        class DbTestCls14(el.Entity):
            name = el.Field(
                el.String,
                info={'edit_widget': InfoField(validator=FakeValidator)},
                required=True)
            other_id = el.Field(el.Integer, required=True)
            other = el.ManyToOne(
                DbTestCls13,
                field=other_id,
                backref='others',
                info={'view_widget': tws.NoWidget}
            )
            def __unicode__(self):
                return self.name

        self.DbTestCls1 = DbTestCls1
        self.DbTestCls2 = DbTestCls2
        self.DbTestCls3 = DbTestCls3
        self.DbTestCls4 = DbTestCls4
        self.DbTestCls5 = DbTestCls5
        self.DbTestCls6 = DbTestCls6
        self.DbTestCls7 = DbTestCls7
        self.DbTestCls8 = DbTestCls8
        self.DbTestCls9 = DbTestCls9
        self.DbTestCls10 = DbTestCls10
        self.DbTestCls11 = DbTestCls11
        self.DbTestCls12 = DbTestCls12
        self.DbTestCls13 = DbTestCls13
        self.DbTestCls14 = DbTestCls14

        el.setup_all()
        el.metadata.create_all()

        foo1 = self.DbTestCls1(id=1, name='foo1')
        self.DbTestCls1(id=2, name='foo2')
        self.DbTestCls2(id=1, nick='bob1')
        self.DbTestCls2(id=2, nick='bob2')
        bob3 = self.DbTestCls2(id=3, nick='bob3')
        foo1.others.append(bob3)
        assert(self.DbTestCls1.query.first().others == [bob3])
        toto1 = self.DbTestCls4(id=1, surname='toto1')
        self.DbTestCls4(id=2, surname='toto2')
        admin = self.DbTestCls5(id=1, rolename='admin')
        self.DbTestCls5(id=2, rolename='owner')
        self.DbTestCls5(id=3, rolename='anonymous')
        toto1.roles.append(admin)
        assert(self.DbTestCls4.query.first().roles == [admin])
        self.DbTestCls6(id=1, name='foo1')
        self.DbTestCls6(id=2, name='foo2')
        self.DbTestCls7(id=1, nick='bob1', other_id=1)
        self.DbTestCls7(id=2, nick='bob2', other_id=1)
        account1 = self.DbTestCls8(id=2, account_name='account1')
        bob1 = self.DbTestCls9(id=1, name='bob1', account_id=2)
        assert(self.DbTestCls8.query.first().user == bob1)
        assert(self.DbTestCls9.query.first().account == account1)
        account1 = self.DbTestCls11(
            id=2, account_name='account1', account_number='number1')
        bob1 = self.DbTestCls12(id=1, name='bob1', account_id=2)
        assert(self.DbTestCls11.query.first().user == bob1)
        assert(self.DbTestCls12.query.first().account == account1)
        transaction.commit()

        return super(ElixirBase, self).setUp()

    def teardown(self):
        transaction.abort()


class SQLABase(object):
    def setUp(self):
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

        join_table = sa.Table('Test4_Test5', Base.metadata,
            sa.Column('Test4', sa.Integer, sa.ForeignKey('Test4.id'), primary_key=True),
            sa.Column('Test5', sa.Integer, sa.ForeignKey('Test5.id'), primary_key=True)
        )
        class DbTestCls4(Base):
            __tablename__ = 'Test4'
            id = sa.Column(sa.Integer, primary_key=True)
            surname = sa.Column(sa.String(50))
            def __unicode__(self):
                return self.surname
        class DbTestCls5(Base):
            __tablename__ = 'Test5'
            id = sa.Column(sa.Integer, primary_key=True)
            rolename = sa.Column(sa.String(50))
            users = sa.orm.relationship('DbTestCls4', secondary=join_table, backref='roles')
            def __unicode__(self):
                return self.rolename
        class DbTestCls6(Base):
            __tablename__ = 'Test6'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String(50))
            tws_edit_link = '/edit/$'
            def __unicode__(self):
                return self.name
        class DbTestCls7(Base):
            __tablename__ = 'Test7'
            id = sa.Column(sa.Integer, primary_key=True)
            nick = sa.Column(sa.String(50))
            other_id = sa.Column(sa.Integer, sa.ForeignKey('Test6.id'), nullable=False)
            other = sa.orm.relation(DbTestCls6, backref=sa.orm.backref('others'))
            def __unicode__(self):
                return self.nick
        class DbTestCls8(Base):
            __tablename__ = 'Test8'
            id = sa.Column(sa.Integer, primary_key=True)
            account_name = sa.Column(sa.String(50), nullable=False)
            def __unicode__(self):
                return self.account_name
        class DbTestCls9(Base):
            __tablename__ = 'Test9'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String(50))
            account_id = sa.Column(sa.Integer, sa.ForeignKey('Test8.id'), nullable=False)
            account = sa.orm.relation(DbTestCls8, backref=sa.orm.backref('user', uselist=False))
            def __unicode__(self):
                return self.name
        class DbTestCls10(Base):
            __tablename__ = 'Test10'
            name = sa.Column(sa.String(50), primary_key=True)
            def __unicode__(self):
                return self.name

        class DbTestCls11(Base):
            __tablename__ = 'Test11'
            id = sa.Column(sa.Integer, primary_key=True)
            account_name = sa.Column(sa.String(50), nullable=False)
            account_number = sa.Column(sa.String(50), nullable=False)
            def __unicode__(self):
                return self.account_name
        class DbTestCls12(Base):
            __tablename__ = 'Test12'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String(50), nullable=False)
            account_id = sa.Column(sa.Integer, sa.ForeignKey('Test11.id'),
                                   nullable=True)
            account = sa.orm.relation(DbTestCls11, backref=sa.orm.backref('user', uselist=False))
            def __unicode__(self):
                return self.name

        class DbTestCls13(Base):
            __tablename__ = 'Test13'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String(50), info={'edit_widget': InfoField},
                             nullable=False)
            def __unicode__(self):
                return self.name

        class DbTestCls14(Base):
            __tablename__ = 'Test14'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(
                sa.String(50),
                info={'edit_widget': InfoField(validator=FakeValidator)},
                nullable=False)
            other_id = sa.Column(sa.Integer, sa.ForeignKey('Test13.id'), nullable=False)
            other = sa.orm.relation(
                DbTestCls13,
                backref=sa.orm.backref('others'),
                info={'view_widget': tws.NoWidget}
            )
            def __unicode__(self):
                return self.name


        self.DbTestCls1 = DbTestCls1
        self.DbTestCls2 = DbTestCls2
        self.DbTestCls3 = DbTestCls3
        self.DbTestCls4 = DbTestCls4
        self.DbTestCls5 = DbTestCls5
        self.DbTestCls6 = DbTestCls6
        self.DbTestCls7 = DbTestCls7
        self.DbTestCls8 = DbTestCls8
        self.DbTestCls9 = DbTestCls9
        self.DbTestCls10 = DbTestCls10
        self.DbTestCls11 = DbTestCls11
        self.DbTestCls12 = DbTestCls12
        self.DbTestCls13 = DbTestCls13
        self.DbTestCls14 = DbTestCls14

        Base.metadata.create_all()

        foo1 = self.DbTestCls1(id=1, name='foo1')
        self.session.add(foo1)
        self.session.add(self.DbTestCls1(id=2, name='foo2'))
        self.session.add(self.DbTestCls2(id=1, nick='bob1'))
        self.session.add(self.DbTestCls2(id=2, nick='bob2'))
        bob3 = self.DbTestCls2(id=3, nick='bob3')
        foo1.others.append(bob3)
        self.session.add(bob3)
        assert(self.DbTestCls1.query.first().others == [bob3])
        toto1 = self.DbTestCls4(id=1, surname='toto1')
        self.session.add(toto1)
        self.session.add(self.DbTestCls4(id=2, surname='toto2'))
        admin = self.DbTestCls5(id=1, rolename='admin')
        self.session.add(admin)
        self.session.add(self.DbTestCls5(id=2, rolename='owner'))
        self.session.add(self.DbTestCls5(id=3, rolename='anonymous'))
        toto1.roles.append(admin)
        assert(self.DbTestCls4.query.first().roles == [admin])
        self.session.add(self.DbTestCls6(id=1, name='foo1'))
        self.session.add(self.DbTestCls6(id=2, name='foo2'))
        self.session.add(self.DbTestCls7(id=1, nick='bob1', other_id=1))
        self.session.add(self.DbTestCls7(id=2, nick='bob2', other_id=1))
        account1 = self.DbTestCls8(id=2, account_name='account1')
        self.session.add(account1)
        bob1 = self.DbTestCls9(id=1, name='bob1', account_id=2)
        self.session.add(bob1)
        assert(self.DbTestCls8.query.first().user == bob1)
        assert(self.DbTestCls9.query.first().account == account1)
        account1 = self.DbTestCls11(
            id=2, account_name='account1', account_number='number1')
        self.session.add(account1)
        bob1 = self.DbTestCls12(id=1, name='bob1', account_id=2)
        self.session.add(bob1)
        assert(self.DbTestCls11.query.first().user == bob1)
        assert(self.DbTestCls12.query.first().account == account1)
        transaction.commit()

        return super(SQLABase, self).setUp()

    def teardown(self):
        transaction.abort()


class RadioButtonT(WidgetEntityTest):
    _widget_cls = tws.DbRadioButtonList
    _entity_cls_str = 'DbTestCls1'
    attrs = {'css_class':'something', 'id' : 'something'}
    params = {'checked':None}
    expected = """
    <ul class="something" id="something">
    <li>
        <input type="radio" name="something" value="1" id="something:0"/>
        <label for="something:0">foo1</label>
    </li>
    <li>
        <input type="radio" name="something" value="2" id="something:1"/>
        <label for="something:1">foo2</label>
    </li>
    </ul>"""

    def test_validation(self):
        value = self.widget.validate({'something':'1'})
        assert(value is self.DbTestCls1.query.get(1))

if el:
    class TestRadioButtonElixir(ElixirBase, RadioButtonT): pass

class TestRadioButtonSQLA(SQLABase, RadioButtonT): pass

class RadioButtonRequiredT(WidgetRequiredEntityTest):
    _widget_cls = tws.DbRadioButtonList
    _entity_cls_str = 'DbTestCls1'
    attrs = {'css_class':'something', 'id' : 'something'}
    params = {'checked':None}
    expected = """
    <ul class="something" id="something">
    <li>
        <input type="radio" name="something" value="1" id="something:0"/>
        <label for="something:0">foo1</label>
    </li>
    <li>
        <input type="radio" name="something" value="2" id="something:1"/>
        <label for="something:1">foo2</label>
    </li>
    </ul>"""

    def test_validation(self):
        try:
            self.widget.validate({})
            assert(False)
        except twc.ValidationError, ve:
            assert(ve.widget.error_msg == twc.Validator.msgs['required'])
        value = self.widget.validate({'something':'1'})
        assert(value is self.DbTestCls1.query.get(1))

if el:
    class TestRadioButtonRequiredElixir(ElixirBase, RadioButtonRequiredT): pass

class TestRadioButtonRequiredSQLA(SQLABase, RadioButtonRequiredT): pass

class CheckBoxT(WidgetEntityTest):
    _widget_cls = tws.DbCheckBoxList
    _entity_cls_str = 'DbTestCls1'
    attrs = {'css_class':'something', 'id' : 'something'}
    params = {'checked':None}
    expected = """
    <ul class="something" id="something">
    <li>
        <input type="checkbox" name="something" value="1" id="something:0"/>
        <label for="something:0">foo1</label>
    </li>
    <li>
        <input type="checkbox" name="something" value="2" id="something:1"/>
        <label for="something:1">foo2</label>
    </li>
    </ul>"""

    def test_validation(self):
        value = self.widget.validate({'something':'1'})
        assert(value == [self.DbTestCls1.query.get(1)])

if el:
    class TestCheckBoxElixir(ElixirBase, CheckBoxT): pass

class TestCheckBoxSQLA(SQLABase, CheckBoxT): pass

class CheckBoxRequiredT(WidgetRequiredEntityTest):
    _widget_cls = tws.DbCheckBoxList
    _entity_cls_str = 'DbTestCls1'
    attrs = {'css_class':'something', 'id' : 'something'}
    params = {'checked':None}
    expected = """
    <ul class="something" id="something">
    <li>
        <input type="checkbox" name="something" value="1" id="something:0"/>
        <label for="something:0">foo1</label>
    </li>
    <li>
        <input type="checkbox" name="something" value="2" id="something:1"/>
        <label for="something:1">foo2</label>
    </li>
    </ul>"""

    def test_validation(self):
        try:
            self.widget.validate({'something':''})
            assert(False)
        except twc.ValidationError, ve:
            assert(ve.msg == twc.Validator.msgs['required'])
        value = self.widget.validate({'something':'1'})
        assert(value == [self.DbTestCls1.query.get(1)])
        value = self.widget.validate({'something':['1', '2']})
        assert(value == [self.DbTestCls1.query.get(1), self.DbTestCls1.query.get(2)])

if el:
    class TestCheckBoxRequiredElixir(ElixirBase, CheckBoxRequiredT): pass

class TestCheckBoxRequiredSQLA(SQLABase, CheckBoxRequiredT): pass

class CheckBoxTableT(WidgetEntityTest):
    _widget_cls = tws.DbCheckBoxTable
    _entity_cls_str = 'DbTestCls1'
    attrs = {'css_class':'something', 'id' : 'something'}
    params = {'checked':None}
    expected = """
    <table class="something" id="something"><tbody>
    <tr>
        <td>
            <input type="checkbox" name="something" value="1" id="something:0">
            <label for="something:0">foo1</label>
        </td>
    </tr><tr>
        <td>
            <input type="checkbox" name="something" value="2" id="something:1">
            <label for="something:1">foo2</label>
        </td>
    </tr>
    </tbody></table>
    """

    def test_validation(self):
        value = self.widget.validate({'something':'1'})
        assert(value == [self.DbTestCls1.query.get(1)])

if el:
    class TestCheckBoxTableElixir(ElixirBase, CheckBoxTableT): pass

class TestCheckBoxTableSQLA(SQLABase, CheckBoxTableT): pass

class CheckBoxTableRequiredT(WidgetRequiredEntityTest):
    _widget_cls = tws.DbCheckBoxTable
    _entity_cls_str = 'DbTestCls1'
    attrs = {'css_class':'something', 'id' : 'something'}
    params = {'checked':None}
    expected = """
    <table class="something" id="something"><tbody>
    <tr>
        <td>
            <input type="checkbox" name="something" value="1" id="something:0">
            <label for="something:0">foo1</label>
        </td>
    </tr><tr>
        <td>
            <input type="checkbox" name="something" value="2" id="something:1">
            <label for="something:1">foo2</label>
        </td>
    </tr>
    </tbody></table>
    """

    def test_validation(self):
        try:
            self.widget.validate({})
            assert(False)
        except twc.ValidationError, ve:
            assert(ve.msg == twc.Validator.msgs['required'])
        value = self.widget.validate({'something':'1'})
        assert(value == [self.DbTestCls1.query.get(1)])

if el:
    class TestCheckBoxTableRequestElixir(ElixirBase, CheckBoxTableRequiredT): pass

class TestCheckBoxTableRequestSQLA(SQLABase, CheckBoxTableRequiredT): pass

class SingleSelectT(WidgetEntityTest):
    _widget_cls = tws.DbSingleSelectField
    _entity_cls_str = 'DbTestCls1'
    attrs = {'css_class':'something', 'id' : 'something'}
    params = {'checked':None}
    expected = """
    <select class="something" name="something" id="something">
    <option ></option>
    <option value="1">foo1</option>
    <option value="2">foo2</option>
    </select>"""

    def test_validation(self):
        value = self.widget.validate({'something':'1'})
        assert(value is self.DbTestCls1.query.get(1))

if el:
    class TestSingleSelectElixir(ElixirBase, SingleSelectT): pass

class TestSingleSelectSQLA(SQLABase, SingleSelectT): pass

class SingleSelectRequiredT(WidgetRequiredEntityTest):
    _widget_cls = tws.DbSingleSelectField
    _entity_cls_str = 'DbTestCls1'
    attrs = {'css_class':'something', 'id' : 'something'}
    params = {'checked':None}
    expected = """
    <select class="something" name="something" id="something">
    <option ></option>
    <option value="1">foo1</option>
    <option value="2">foo2</option>
    </select>"""

    def test_validation(self):
        try:
            self.widget.validate({'something':''})
            assert(False)
        except twc.ValidationError, ve:
            assert(ve.widget.error_msg == twc.Validator.msgs['required'])
        value = self.widget.validate({'something':'1'})
        assert(value is self.DbTestCls1.query.get(1))

if el:
    class TestSingleSelectRequiredElixir(ElixirBase, SingleSelectRequiredT): pass

class TestSingleSelectRequiredSQLA(SQLABase, SingleSelectRequiredT): pass

class ListPageT(WidgetEntityTest):
    _widget_cls = tws.DbListPage
    _entity_cls_str = 'DbTestCls1'
    attrs = {
        'child': twf.GridLayout(
            children=[
                twf.LabelField(id='name'),
                # TODO -- test this with label=None, diff between elixir and sqla
                twf.LinkField(id='id', link='foo?id=$',
                              text='Edit', label='Edit'),
            ]),
        'newlink': twf.LinkField(link='cls1', text='New', value=1),
        'title': 'Db Test Cls1'
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

if el:
    class TestListPageElixir(ElixirBase, ListPageT): pass

class TestListPageSQLA(SQLABase, ListPageT): pass


class FormPageT(WidgetEntityTest):
    _widget_cls = tws.DbFormPage
    _entity_cls_str = 'DbTestCls1'
    attrs = {
        'child': twf.TableForm(
            children=[
                twf.HiddenField(id='id'),
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
        <th><label for="name">Name</label></th>
        <td>
            <input name="dbformpage_d:name" id="dbformpage_d:name" type="text">
            <span id="dbformpage_d:name:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <input type="hidden" name="dbformpage_d:id" id="dbformpage_d:id"/>
        <span id="dbformpage_d:error"></span>
    </td></tr>
</table>
    <input type="submit" value="Save">
</form></body>
</html>"""

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
        <th><label for="name">Name</label></th>
        <td>
            <input name="dbformpage_d:name" value="foo1" id="dbformpage_d:name" type="text">
            <span id="dbformpage_d:name:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <input type="hidden" name="dbformpage_d:id" value="1" id="dbformpage_d:id"/>
        <span id="dbformpage_d:error"></span>
    </td></tr>
</table>
    <input type="submit" value="Save">
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
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING' :'id=2'}
        req=Request(environ)
        assert(req.GET)
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """<html>
<head><title>some title</title></head>
<body id="dbformpage_d:page"><h1>some title</h1><form method="post" id="dbformpage_d:form" enctype="multipart/form-data">
     <span class="error"></span>
    <table id="dbformpage_d">
    <tr class="odd" id="dbformpage_d:name:container">
        <th><label for="name">Name</label></th>
        <td>
            <input name="dbformpage_d:name" value="foo2" id="dbformpage_d:name" type="text">
            <span id="dbformpage_d:name:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <input type="hidden" name="dbformpage_d:id" value="2" id="dbformpage_d:id"/>
        <span id="dbformpage_d:error"></span>
    </td></tr>
</table>
    <input type="submit" value="Save">
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
        tw2test.assert_eq_xml(r.body, """<html>
<head><title>some title</title></head>
<body id="dbformpage_d:page"><h1>some title</h1><form method="post" id="dbformpage_d:form" enctype="multipart/form-data">
     <span class="error"></span>
    <table id="dbformpage_d">
    <tr class="odd" id="dbformpage_d:name:container">
        <th><label for="name">Name</label></th>
        <td>
            <input name="dbformpage_d:name" id="dbformpage_d:name" type="text">
            <span id="dbformpage_d:name:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="dbformpage_d:error"></span>
    </td></tr>
</table>
    <input type="submit" value="Save">
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
        assert r.body == """Form posted successfully {'id': '', 'name': u'a'}""", r.body

    def test_request_post_counts_new(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='dbformpage_d:name=a'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        assert(self.DbTestCls1.query.count() == 2)
        r = self.widget().request(req)
        assert(self.DbTestCls1.query.count() == 3)

    def test_request_post_counts_update(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='dbformpage_d:name=b&dbformpage_d:id=1'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        assert(self.DbTestCls1.query.count() == 2)
        r = self.widget().request(req)
        assert(self.DbTestCls1.query.count() == 2)

    def test_request_post_content_update(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='dbformpage_d:name=b&dbformpage_d:id=1'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        original = self.DbTestCls1.query.filter(self.DbTestCls1.id==1).one()
        assert(original.name == 'foo1')
        r = self.widget().request(req)
        updated = self.DbTestCls1.query.filter(self.DbTestCls1.id==1)
        assert(updated.count() == 1)
        updated = updated.one()
        assert(updated.name == 'b')

if el:
    class TestFormPageElixir(ElixirBase, FormPageT): pass

class TestFormPageSQLA(SQLABase, FormPageT):
    def test_no_query_property(self):
        old_prop = self.widget.entity.query
        self.widget.entity.query = None

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
        except AttributeError, e:
            assert(str(e) == 'entity has no query_property()')
        finally:
            self.widget.entity.query = old_prop


class ListFormT(WidgetEntityTest):
    _widget_cls = tws.DbListForm
    _entity_cls_str = 'DbTestCls1'
    attrs = {
        'child': twf.Form(
            child=twf.GridLayout(
                children=[
                    twf.HiddenField(id='id', validator=twc.IntValidator),
                    twf.TextField(id='name'),
                ])
            ),
        'title': 'some title'
    }
    expected = """<html>
<head><title>some title</title></head>
<body id="dblistform_d:page"><h1>some title</h1><form method="post" id="dblistform_d:form" enctype="multipart/form-data">
     <span class="error"></span>
    <table id="dblistform_d">
    <tr><th>Name</th></tr>
    <tr class="error"><td colspan="0" id="dblistform_d:error">
    </td></tr>
</table>
    <input type="submit" value="Save">
</form></body>
</html>"""

    def test_request_get_edit(self):
        environ = {
            'REQUEST_METHOD': 'GET',
        }
        req=Request(environ)
        self.mw.config.debug = True
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """<html>
<head><title>some title</title></head>
<body id="dblistform_d:page"><h1>some title</h1><form method="post" id="dblistform_d:form" enctype="multipart/form-data">
     <span class="error"></span>
    <table id="dblistform_d">
    <tr><th>Name</th></tr>
    <tr id="dblistform_d:0" class="odd">
    <td>
        <input name="dblistform_d:0:name" value="foo1" id="dblistform_d:0:name" type="text">
    </td>
    <td>
        <input name="dblistform_d:0:id" type="hidden" id="dblistform_d:0:id" value="1">
    </td>
</tr>
<tr id="dblistform_d:1" class="even">
    <td>
        <input name="dblistform_d:1:name" value="foo2" id="dblistform_d:1:name" type="text">
    </td>
    <td>
        <input name="dblistform_d:1:id" type="hidden" id="dblistform_d:1:id" value="2">
    </td>
</tr>
    <tr class="error"><td colspan="2" id="dblistform_d:error">
    </td></tr>
</table>
    <input type="submit" value="Save">
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
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING' :'id=2'}
        req=Request(environ)
        assert(req.GET)
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """<html>
<head><title>some title</title></head>
<body id="dblistform_d:page"><h1>some title</h1><form method="post" id="dblistform_d:form" enctype="multipart/form-data">
     <span class="error"></span>
    <table id="dblistform_d">
    <tr><th>Name</th></tr>
    <tr id="dblistform_d:0" class="odd">
    <td>
        <input name="dblistform_d:0:name" value="foo1" id="dblistform_d:0:name" type="text">
    </td>
    <td>
        <input name="dblistform_d:0:id" type="hidden" id="dblistform_d:0:id" value="1">
    </td>
</tr>
<tr id="dblistform_d:1" class="even">
    <td>
        <input name="dblistform_d:1:name" value="foo2" id="dblistform_d:1:name" type="text">
    </td>
    <td>
        <input name="dblistform_d:1:id" type="hidden" id="dblistform_d:1:id" value="2">
    </td>
</tr>
    <tr class="error"><td colspan="2" id="dblistform_d:error">
    </td></tr>
</table>
    <input type="submit" value="Save">
</form></body>
</html>""")

    def test_request_post_valid(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='dblistform_d:0:name=a&dblistform_d:0:id=1'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        r = self.widget().request(req)
        assert r.body == """Form posted successfully [{'id': 1, 'name': u'a'}]""", r.body

    def test_request_post_counts_new(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='dblistform_d:0:name=a&dblistform_d:0:id=1'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        assert(self.DbTestCls1.query.count() == 2)
        r = self.widget().request(req)
        assert(self.DbTestCls1.query.count() == 1)

    def test_request_post_counts_update(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='dblistform_d:0:name=a&dblistform_d:0:id=1&dblistform_d:1:name=b&dblistform_d:1:id=2'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        assert(self.DbTestCls1.query.count() == 2)
        r = self.widget().request(req)
        assert(self.DbTestCls1.query.count() == 2)

    # TODO: this test should pass, but needs fixing
    def _test_request_post_content_update(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='dblistform_d:0:name=b&dblistform_d:0:id=1'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        original = self.DbTestCls1.query.filter(self.DbTestCls1.id==1).one()
        assert(original.name == 'foo1')
        r = self.widget().request(req)
        updated = self.DbTestCls1.query.filter(self.DbTestCls1.id=='1')
        assert(updated.count() == 1)
        updated = updated.one()
        assert(updated.name == 'b')

if el:
    class TestListFormElixir(ElixirBase, ListFormT): pass

class TestListFormSQLA(SQLABase, ListFormT): pass


class AutoListPageT(WidgetEntityTest):
    _widget_cls = tws.AutoListPage
    _entity_cls_str = 'DbTestCls1'
    attrs = {'title': 'Db Test Cls1'}

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

    def test_exception_manytoone(self):
        class WackPolicy(tws.WidgetPolicy):
            pass
        props = filter(
            lambda x : x.key == 'other',
            sa.orm.class_mapper(self.DbTestCls2).iterate_properties)
        assert(len(props) == 1)
        try:
            w = WackPolicy.factory(props[0])
            assert(False)
        except twc.WidgetError, e:
            assert(str(e) == "Cannot automatically create a widget " +
                   "for many-to-one relation 'other'")

    def test_exception_onetomany(self):
        class WackPolicy(tws.WidgetPolicy):
            pass
        props = filter(
            lambda x : x.key == 'others',
            sa.orm.class_mapper(self.DbTestCls1).iterate_properties)
        assert(len(props) == 1)
        try:
            w = WackPolicy.factory(props[0])
            assert(False)
        except twc.WidgetError, e:
            assert(str(e) == "Cannot automatically create a widget " +
                   "for one-to-many relation 'others'")

    def test_exception_onetoone(self):
        class WackPolicy(tws.WidgetPolicy):
            pass
        props = filter(
            lambda x : x.key == 'account',
            sa.orm.class_mapper(self.DbTestCls9).iterate_properties)
        assert(len(props) == 1)
        try:
            w = WackPolicy.factory(props[0])
            assert(False)
        except twc.WidgetError, e:
            assert(str(e) == "Cannot automatically create a widget " +
                   "for one-to-one relation 'account'")

    def test_exception_default(self):
        class WackPolicy(tws.WidgetPolicy):
            pass
        props = filter(
            lambda x : x.key == 'name',
            sa.orm.class_mapper(self.DbTestCls1).iterate_properties)
        assert(len(props) == 1)
        try:
            w = WackPolicy.factory(props[0])
            assert(False)
        except twc.WidgetError, e:
            assert(str(e) == "Cannot automatically create a widget for 'name'")

    def test_name_widgets(self):
        class AwesomePolicy(tws.WidgetPolicy):
            name_widgets = { 'name' : twf.LabelField, }

        props = filter(
            lambda x : x.key == 'name',
            sa.orm.class_mapper(self.DbTestCls1).iterate_properties)
        assert(len(props) == 1)
        try:
            w = AwesomePolicy.factory(props[0])
        except twc.WidgetError, e:
            assert(False)

    def test_info_on_prop(self):
        """Test we use first the data defined in the hint
        """
        class AwesomePolicy(tws.EditPolicy):
            name_widgets = { 'name' : twf.LabelField, }

        props = filter(
            lambda x : x.key == 'name',
            sa.orm.class_mapper(self.DbTestCls13).iterate_properties)
        assert(len(props) == 1)
        try:
            w = AwesomePolicy.factory(props[0])
            assert(issubclass(w, InfoField))
            assert(w.validator)
        except twc.WidgetError, e:
            assert(False)

    def test_info_validator_on_prop(self):
        """Test we use first the data defined in the hint
        """
        class AwesomePolicy(tws.EditPolicy): pass

        props = filter(
            lambda x: x.key == 'name',
            sa.orm.class_mapper(self.DbTestCls14).iterate_properties)
        assert(len(props) == 1)
        try:
            w = AwesomePolicy.factory(props[0])
            assert(issubclass(w, InfoField))
            assert(isinstance(w.validator, FakeValidator))
        except twc.WidgetError, e:
            assert(False)

    def test_info_widget_on_relation(self):
        """Test we use first the data defined in the hint
        """
        class AwesomePolicy(tws.ViewPolicy): pass

        props = filter(
            lambda x: x.key == 'other',
            sa.orm.class_mapper(self.DbTestCls14).iterate_properties)
        assert(len(props) == 1)
        try:
            w = AwesomePolicy.factory(props[0])
            assert(w is None)
        except twc.WidgetError, e:
            assert(False)

    def test_orig_children(self):
        """ Tests overriding properties (`orig_children`) """

        class SomeListPage(tws.DbListPage):
            _no_autoid = True
            entity = self.DbTestCls1
            title = 'Db Test Cls1'

            class child(tws.AutoViewGrid):
                name = twf.InputField(type='text')

        environ = {
            'REQUEST_METHOD': 'GET',
        }
        req=Request(environ)
        self.mw.config.debug = True
        r = SomeListPage.request(req)
        tw2test.assert_eq_xml(r.body, """
<html><head><title>Db Test Cls1</title></head><body><h1>Db Test Cls1</h1>
<table>
    <tr><th>Name</th><th>Others</th></tr>
    <tr id="0" class="odd">
    <td>
        <input type="text" name="0:name" value="foo1" id="0:name"/>
    </td>
    <td>
      <div id="0:others">
           <a id="0:others:0">bob3</a>
      </div>
    </td><td></td></tr>
<tr id="1" class="even">
    <td>
        <input type="text" name="1:name" value="foo2" id="1:name"/>
    </td><td>
      <div id="1:others">
      </div>
    </td><td></td>
    </tr>
    <tr class="error"><td colspan="2" id=":error">
    </td></tr></table></body></html>""")


    def test_request_get(self):
        """ Good lookin' """
        environ = {
            'REQUEST_METHOD': 'GET',
        }
        req=Request(environ)
        self.mw.config.debug = True
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """
<html>
<head><title>Db Test Cls1</title></head>
<body id="autolistpage_d:page">
<h1>Db Test Cls1</h1>
<table id="autolistpage_d">
    <tr><th>Name</th><th>Others</th></tr>
    <tr id="autolistpage_d:0" class="odd">
    <td>
        <span>foo1<input name="autolistpage_d:0:name" type="hidden" id="autolistpage_d:0:name" value="foo1"></span>
    </td>
    <td>
      <div id="autolistpage_d:0:others">
         <a id="autolistpage_d:0:others:0">bob3</a>
      </div>
    </td>
    <td>
    </td>
</tr>
<tr id="autolistpage_d:1" class="even">
    <td>
        <span>foo2<input name="autolistpage_d:1:name" type="hidden" id="autolistpage_d:1:name" value="foo2"></span>
    </td>
    <td>
      <div id="autolistpage_d:1:others">
      </div>
    </td>
    <td>
    </td>
</tr>
    <tr class="error"><td colspan="2" id="autolistpage_d:error">
    </td></tr>
</table></body></html>""")

if el:
    class TestAutoListPageElixir(ElixirBase, AutoListPageT): pass

class TestAutoListPageSQLA(SQLABase, AutoListPageT): pass


class AutoListPageOneToOneRelationT(WidgetEntityTest):
    _widget_cls = tws.AutoListPage
    _entity_cls_str = 'DbTestCls9'
    attrs = {'title': 'Db Test Cls9'}

    # Doesn't make much sense... an AutoList widget with fetch_data not called?
    expected = """
    <html>
    <head><title>Db Test Cls9</title></head>
    <body id="autolistpage_d:page">
    <h1>Db Test Cls9</h1>
    <table id="autolistpage_d">
        <tr><th>Name</th><th>Account</th></tr>
        <tr class="error"><td colspan="0" id="autolistpage_d:error">
        </td></tr>
    </table>
    </body>
    </html>
    """

    def test_request_get(self):
        environ = {
            'REQUEST_METHOD': 'GET',
        }
        req=Request(environ)
        self.mw.config.debug = True
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """
        <html>
        <head><title>Db Test Cls9</title></head>
        <body id="autolistpage_d:page">
        <h1>Db Test Cls9</h1>
        <table id="autolistpage_d">
            <tr><th>Name</th><th>Account</th></tr>
            <tr id="autolistpage_d:0" class="odd">
            <td>
                <span>bob1<input type="hidden" name="autolistpage_d:0:name" value="bob1" id="autolistpage_d:0:name"/></span>
            </td>
            <td>
              <span>account1<input type="hidden" name="autolistpage_d:0:account" value="account1" id="autolistpage_d:0:account" required="required" /></span>
            </td>
            <td>
            </td>
            </tr>
            <tr class="error"><td colspan="1" id="autolistpage_d:error">
            </td></tr>
        </table>
        </body>
        </html>""")


if el:
    class TestAutoListPageOneToOneRelationElixir(ElixirBase, AutoListPageOneToOneRelationT): pass

class TestAutoListPageOneToOneRelationSQLA(SQLABase, AutoListPageOneToOneRelationT): pass

# TODO -- do AutoListPageEDIT here

class AutoTableFormT1(WidgetEntityTest):
    _widget_cls = tws.AutoTableForm
    _entity_cls_str = 'DbTestCls1'
    attrs = { 'id' : 'foo_form' }
    expected = """
<form method="post" id="foo_form:form" enctype="multipart/form-data">
     <span class="error"></span>
    <table id="foo_form">
    <tr class="odd" id="foo_form:name:container">
        <th><label for="name">Name</label></th>
        <td>
            <input name="foo_form:name" id="foo_form:name" type="text">
            <span id="foo_form:name:error"></span>
        </td>
        </tr>
    <tr class="even" id="foo_form:others:container">
        <th><label for="others">Others</label></th>
        <td>
            <ul id="foo_form:others">
                <li>
                    <input type="checkbox" name="foo_form:others" value="1" id="foo_form:others:0"/>
                    <label for="foo_form:others:0">bob1</label>
                </li><li>
                    <input type="checkbox" name="foo_form:others" value="2" id="foo_form:others:1"/>
                    <label for="foo_form:others:1">bob2</label>
                </li><li>
                    <input type="checkbox" name="foo_form:others" value="3" id="foo_form:others:2"/>
                    <label for="foo_form:others:2">bob3</label>
                </li>
            </ul>
            <span id="foo_form:others:error"></span>
        </td>
    </tr>
   <tr class="error"><td colspan="2">
        <span id="foo_form:error"></span>
    </td></tr>
</table>
    <input type="submit" value="Save">
</form>"""

if el:
    class TestAutoTableForm1Elixir(ElixirBase, AutoTableFormT1): pass

class TestAutoTableForm1SQLA(SQLABase, AutoTableFormT1): pass


class AutoTableFormT2(WidgetEntityTest):
    _widget_cls = tws.AutoTableForm
    _entity_cls_str = 'DbTestCls2'
    attrs = { 'id' : 'foo_form' }
    expected = """
<form id="foo_form:form" enctype="multipart/form-data" method="post">
     <span class="error"></span>
    <table id="foo_form">
    <tr class="odd"  id="foo_form:nick:container">
        <th><label for="nick">Nick</label></th>
        <td >
            <input name="foo_form:nick" type="text" id="foo_form:nick"/>
            <span id="foo_form:nick:error"></span>
        </td>
    </tr>
     <tr class="even"  id="foo_form:other:container">
        <th><label for="other">Other</label></th>
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
    <input type="submit" value="Save"/>
</form>
"""

if el:
    class TestAutoTableForm2Elixir(ElixirBase, AutoTableFormT2): pass

class TestAutoTableForm2SQLA(SQLABase, AutoTableFormT2): pass


class AutoTableFormT4(WidgetEntityTest):
    _widget_cls = tws.AutoTableForm
    _entity_cls_str = 'DbTestCls4'
    attrs = { 'id' : 'foo_form' }
    expected = """
    <form method="post" id="foo_form:form" enctype="multipart/form-data">
        <span class="error"></span>
        <table id="foo_form">
            <tr class="odd" id="foo_form:surname:container">
                <th><label for="surname">Surname</label></th>
                <td>
                    <input name="foo_form:surname" id="foo_form:surname" type="text" />
                    <span id="foo_form:surname:error"></span>
                </td>
            </tr><tr class="even" id="foo_form:roles:container">
                <th><label for="roles">Roles</label></th>
                <td>
                    <ul id="foo_form:roles">
                        <li>
                            <input type="checkbox" name="foo_form:roles" value="1" id="foo_form:roles:0" />
                            <label for="foo_form:roles:0">admin</label>
                        </li><li>
                            <input type="checkbox" name="foo_form:roles" value="2" id="foo_form:roles:1" />
                            <label for="foo_form:roles:1">owner</label>
                        </li><li>
                            <input type="checkbox" name="foo_form:roles" value="3" id="foo_form:roles:2" />
                            <label for="foo_form:roles:2">anonymous</label>
                        </li>
                    </ul>
                    <span id="foo_form:roles:error"></span>
                </td>
            </tr>
            <tr class="error">
                <td colspan="2">
                    <span id="foo_form:error"></span>
                </td>
            </tr>
        </table>
        <input type="submit" value="Save" />
    </form>"""

if el:
    class TestAutoTableForm4Elixir(ElixirBase, AutoTableFormT4): pass

class TestAutoTableForm4SQLA(SQLABase, AutoTableFormT4): pass


class AutoTableFormT5(WidgetEntityTest):
    _widget_cls = tws.AutoTableForm
    _entity_cls_str = 'DbTestCls5'
    attrs = { 'id' : 'foo_form' }
    expected = """
    <form method="post" id="foo_form:form" enctype="multipart/form-data">
        <span class="error"></span>
        <table id="foo_form">
        <tr class="odd" id="foo_form:rolename:container">
            <th><label for="rolename">Rolename</label></th>
            <td>
                <input name="foo_form:rolename" id="foo_form:rolename" type="text" />
                <span id="foo_form:rolename:error"></span>
            </td>
        </tr><tr class="even" id="foo_form:users:container">
            <th><label for="users">Users</label></th>
            <td>
                <ul id="foo_form:users">
                    <li>
                        <input type="checkbox" name="foo_form:users" value="1" id="foo_form:users:0" />
                        <label for="foo_form:users:0">toto1</label>
                    </li><li>
                        <input type="checkbox" name="foo_form:users" value="2" id="foo_form:users:1" />
                        <label for="foo_form:users:1">toto2</label>
                    </li>
                </ul>
                <span id="foo_form:users:error"></span>
            </td>
        </tr><tr class="error">
            <td colspan="2">
                <span id="foo_form:error"></span>
            </td>
        </tr>
        </table>
        <input type="submit" value="Save" />
    </form>"""

if el:
    class TestAutoTableForm5Elixir(ElixirBase, AutoTableFormT5): pass

class TestAutoTableForm5SQLA(SQLABase, AutoTableFormT5): pass


class AutoTableFormT6(WidgetEntityTest):
    _widget_cls = tws.AutoTableForm
    _entity_cls_str = 'DbTestCls6'
    attrs = { 'id' : 'foo_form' }
    expected = """
<form method="post" id="foo_form:form" enctype="multipart/form-data">
    <span class="error"></span>
    <table id="foo_form">
    <tr class="odd" id="foo_form:name:container">
        <th><label for="name">Name</label></th>
        <td>
            <input name="foo_form:name" id="foo_form:name" type="text">
            <span id="foo_form:name:error"></span>
        </td>
        </tr>
    <tr class="even" id="foo_form:others:container">
        <th><label for="others">Others</label></th>
        <td>
            <ul id="foo_form:others">
                <li>
                    <input type="checkbox" name="foo_form:others" value="1" id="foo_form:others:0"/>
                    <label for="foo_form:others:0">bob1</label>
                </li><li>
                    <input type="checkbox" name="foo_form:others" value="2" id="foo_form:others:1"/>
                    <label for="foo_form:others:1">bob2</label>
                </li>
            </ul>
            <span id="foo_form:others:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="foo_form:error"></span>
    </td></tr>
    </table>
    <input type="submit" value="Save">
</form>"""

if el:
    class TestAutoTableForm6Elixir(ElixirBase, AutoTableFormT6): pass

class TestAutoTableForm6SQLA(SQLABase, AutoTableFormT6): pass


class AutoTableFormT7(WidgetEntityTest):
    _widget_cls = tws.AutoTableForm
    _entity_cls_str = 'DbTestCls7'
    attrs = { 'id' : 'foo_form' }
    expected = """
<form id="foo_form:form" enctype="multipart/form-data" method="post">
    <span class="error"></span>
    <table id="foo_form">
    <tr class="odd"  id="foo_form:nick:container">
        <th><label for="nick">Nick</label></th>
        <td >
            <input name="foo_form:nick" type="text" id="foo_form:nick"/>
            <span id="foo_form:nick:error"></span>
        </td>
    </tr>
     <tr class="even required"  id="foo_form:other:container">
        <th><label for="other">Other</label></th>
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
    <input type="submit" value="Save"/>
</form>
"""

if el:
    class TestAutoTableForm7Elixir(ElixirBase, AutoTableFormT7): pass

class TestAutoTableForm7SQLA(SQLABase, AutoTableFormT7): pass


class AutoViewGridT(WidgetEntityTest):
    _widget_cls = tws.AutoViewGrid
    _entity_cls_str = 'DbTestCls1'
    attrs = { 'id' : 'autogrid' }

    expected = """
    <table id='autogrid'>
    <tr><th>Name</th><th>Others</th></tr>
    <tr class="error"><td colspan="0" id="autogrid:error"></td></tr>
    </table>"""

    def test_edit_link(self):
        values = self.DbTestCls6.query.all()
        w = tws.AutoViewGrid(entity=self.DbTestCls6,
                             value=values, **self.attrs)
        tw2test.assert_eq_xml(w.display(), """
<table id="autogrid">
<tr>
  <th>Name</th>
  <th>Others</th>
  <th>Edit</th>
</tr>
<tr id="autogrid:0" class="odd">
  <td>
    <span>foo1<input type="hidden" name="autogrid:0:name" value="foo1" id="autogrid:0:name"/></span>
  </td>
  <td>
    <div id="autogrid:0:others">
         <a id="autogrid:0:others:0">bob1</a>
         <a id="autogrid:0:others:1">bob2</a>
    </div>
  </td>
  <td>
      <a href="/edit/1" id="autogrid:0:edit">edit</a>
  </td>
  <td>
  </td>
</tr>
<tr id="autogrid:1" class="even">
  <td>
    <span>foo2<input type="hidden" name="autogrid:1:name" value="foo2" id="autogrid:1:name"/></span>
  </td>
  <td>
    <div id="autogrid:1:others">
    </div>
  </td>
  <td>
    <a href="/edit/2" id="autogrid:1:edit">edit</a>
  </td>
  <td></td>
</tr>
<tr class="error">
  <td colspan="2" id="autogrid:error"></td>
</tr>
</table>""")


    def test_foreign_edit_link(self):
        values = self.DbTestCls6.query.all()
        self.DbTestCls7.tws_edit_link = '/edit7/$'
        w = tws.AutoViewGrid(entity=self.DbTestCls6,
                             value=values, **self.attrs)
        tw2test.assert_eq_xml(w.display(), """
<table id="autogrid">
<tr>
  <th>Name</th>
  <th>Others</th>
  <th>Edit</th>
</tr>
<tr id="autogrid:0" class="odd">
  <td>
    <span>foo1<input type="hidden" name="autogrid:0:name" value="foo1" id="autogrid:0:name"/></span>
  </td>
  <td>
    <div id="autogrid:0:others">
         <a href="/edit7/1" id="autogrid:0:others:0">bob1</a>
         <a href="/edit7/2" id="autogrid:0:others:1">bob2</a>
    </div>
  </td>
  <td>
      <a href="/edit/1" id="autogrid:0:edit">edit</a>
  </td>
  <td>
  </td>
</tr>
<tr id="autogrid:1" class="even">
  <td>
    <span>foo2<input type="hidden" name="autogrid:1:name" value="foo2" id="autogrid:1:name"/></span>
  </td>
  <td>
    <div id="autogrid:1:others">
    </div>
  </td>
  <td>
    <a href="/edit/2" id="autogrid:1:edit">edit</a>
  </td>
  <td></td>
</tr>
<tr class="error">
  <td colspan="2" id="autogrid:error"></td>
</tr>
</table>""")

if el:
    class TestAutoViewGridElixir(ElixirBase, AutoViewGridT): pass

class TestAutoViewGridSQLA(SQLABase, AutoViewGridT): pass


class AutoGrowingGridT(WidgetEntityTest):
    _widget_cls = tws.AutoGrowingGrid
    _entity_cls_str = 'DbTestCls1'
    attrs = { 'id' : 'autogrid' }
    # TBD -- should the values from the db show up here?
    expected = """
    <table id="autogrid">
        <tr>
            <th>Name</th><th>Others</th><th></th>
            <td><input style="display:none" type="image" id="autogrid:undo" src="/resources/tw2.dynforms.widgets/static/undo.png" title="Undo" alt="Undo" onclick="twd_grow_undo(this); return false;" /></td>
        </tr>
        <tr style="display:none;" id="autogrid:0" class="odd">
        <td>
            <input name="autogrid:0:name" type="text" id="autogrid:0:name" onchange="twd_grow_add(this);" />
        </td><td>
            <ul onchange="twd_grow_add(this);" id="autogrid:0:others">
                <li>
                    <input type="checkbox" name="autogrid:0:others" value="1" id="autogrid:0:others:0" />
                    <label for="autogrid:0:others:0">bob1</label>
                </li><li>
                    <input type="checkbox" name="autogrid:0:others" value="2" id="autogrid:0:others:1" />
                    <label for="autogrid:0:others:1">bob2</label>
                </li><li>
                    <input type="checkbox" name="autogrid:0:others" value="3" id="autogrid:0:others:2" />
                    <label for="autogrid:0:others:2">bob3</label>
                </li>
            </ul>
        </td><td>
            <input src="/resources/tw2.dynforms.widgets/static/del.png" style="display:none;" value="" name="autogrid:0:del" onclick="twd_grow_del(this); return false;" alt="Delete row" type="image" id="autogrid:0:del" />
        </td>
        <td>
        </td>
    </tr><tr id="autogrid:1" class="even">
        <td>
            <input name="autogrid:1:name" type="text" id="autogrid:1:name" onchange="twd_grow_add(this);" />
        </td><td>
            <ul onchange="twd_grow_add(this);" id="autogrid:1:others">
                <li>
                    <input type="checkbox" name="autogrid:1:others" value="1" id="autogrid:1:others:0" />
                    <label for="autogrid:1:others:0">bob1</label>
                </li><li>
                    <input type="checkbox" name="autogrid:1:others" value="2" id="autogrid:1:others:1" />
                    <label for="autogrid:1:others:1">bob2</label>
                </li><li>
                    <input type="checkbox" name="autogrid:1:others" value="3" id="autogrid:1:others:2" />
                    <label for="autogrid:1:others:2">bob3</label>
                </li>
            </ul>
        </td><td>
            <input src="/resources/tw2.dynforms.widgets/static/del.png" style="display:none;" value="" name="autogrid:1:del" onclick="twd_grow_del(this); return false;" alt="Delete row" type="image" id="autogrid:1:del" />
        </td>
        <td>
        </td>
    </tr>
    </table>"""

if el:
    class TestAutoGrowingGridElixir(ElixirBase, AutoGrowingGridT): pass

class TestAutoGrowingGridSQLA(SQLABase, AutoGrowingGridT): pass


class AutoGrowingGridAsChildT(WidgetEntityTest):
    _widget_cls = tws.DbFormPage
    _entity_cls_str = 'DbTestCls1'
    attrs = { 'id' : 'autogrid', 'title' : 'Test',
              'child' : tws.AutoGrowingGrid}
    # TBD -- should the values from the db show up here?
    expected = """
    <html><head><title>Test</title></head>
    <body id="autogrid:page"><h1>Test</h1>
    <table id="autogrid">
        <tr>
            <th>Name</th><th>Others</th><th></th>
            <td><input style="display:none" type="image" id="autogrid:undo" src="/resources/tw2.dynforms.widgets/static/undo.png" title="Undo" alt="Undo" onclick="twd_grow_undo(this); return false;" /></td>
        </tr>
        <tr style="display:none;" id="autogrid:0" class="odd">
        <td>
            <input name="autogrid:0:name" id="autogrid:0:name" onchange="twd_grow_add(this);" type="text" />
        </td><td>
            <ul onchange="twd_grow_add(this);" id="autogrid:0:others">
                <li>
                    <input type="checkbox" name="autogrid:0:others" value="1" id="autogrid:0:others:0" />
                    <label for="autogrid:0:others:0">bob1</label>
                </li><li>
                    <input type="checkbox" name="autogrid:0:others" value="2" id="autogrid:0:others:1" />
                    <label for="autogrid:0:others:1">bob2</label>
                </li><li>
                    <input type="checkbox" name="autogrid:0:others" value="3" id="autogrid:0:others:2" />
                    <label for="autogrid:0:others:2">bob3</label>
                </li>
            </ul>
        </td><td>
        <input src="/resources/tw2.dynforms.widgets/static/del.png" style="display:none;" value="" name="autogrid:0:del" onclick="twd_grow_del(this); return false;" alt="Delete row" type="image" id="autogrid:0:del" />
        </td>
        <td>
        </td>
    </tr><tr id="autogrid:1" class="even">
        <td>
            <input name="autogrid:1:name" id="autogrid:1:name" onchange="twd_grow_add(this);" type="text" />
        </td><td>
            <ul onchange="twd_grow_add(this);" id="autogrid:1:others">
                <li>
                    <input type="checkbox" name="autogrid:1:others" value="1" id="autogrid:1:others:0" />
                    <label for="autogrid:1:others:0">bob1</label>
                </li><li>
                    <input type="checkbox" name="autogrid:1:others" value="2" id="autogrid:1:others:1" />
                    <label for="autogrid:1:others:1">bob2</label>
                </li><li>
                    <input type="checkbox" name="autogrid:1:others" value="3" id="autogrid:1:others:2" />
                    <label for="autogrid:1:others:2">bob3</label>
                </li>
            </ul>
        </td><td>
            <input src="/resources/tw2.dynforms.widgets/static/del.png" style="display:none;" value="" name="autogrid:1:del" onclick="twd_grow_del(this); return false;" alt="Delete row" type="image" id="autogrid:1:del" />
        </td>
        <td>
        </td>
    </tr>
    </table></body></html>"""

if el:
    class TestAutoGrowingGridAsChildElixir(ElixirBase, AutoGrowingGridAsChildT): pass

class TestAutoGrowingGridAsChildSQLA(SQLABase, AutoGrowingGridAsChildT): pass


class AutoGrowingGridAsChildWithRelationshipT(WidgetEntityTest):
    _widget_cls = twf.TableForm
    _entity_cls_str = 'DbTestCls2'
    attrs = { 'title' : 'Test',
              'child' : tws.AutoGrowingGrid(id='others')}
    # TBD -- should the values from the db show up here?
    expected = """
    <form method="post" id="others:form" enctype="multipart/form-data">
    <span class="error"></span>
    <table id="others">
        <tr>
            <th>Nick</th><th>Other</th><th></th>
            <td><input style="display:none" type="image" id="others:undo" src="/resources/tw2.dynforms.widgets/static/undo.png" alt="Undo" title="Undo" onclick="twd_grow_undo(this); return false;"></td>
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
        <input src="/resources/tw2.dynforms.widgets/static/del.png" style="display:none;" value="" name="others:0:del" id="others:0:del" onclick="twd_grow_del(this); return false;" alt="Delete row" type="image">
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
            <input src="/resources/tw2.dynforms.widgets/static/del.png" style="display:none;" value="" name="others:1:del" id="others:1:del" onclick="twd_grow_del(this); return false;" alt="Delete row" type="image">
        </td>
        <td>
        </td>
    </tr>
    </table>
    <input type="submit" value="Save">
    </form>"""

if el:
    class TestAutoGrowingGridAsChildWithRelationshipElixir(
        ElixirBase, AutoGrowingGridAsChildWithRelationshipT):
        pass

class TestAutoGrowingGridAsChildWithRelationshipSQLA(
SQLABase, AutoGrowingGridAsChildWithRelationshipT): pass


class AutoEditRelationInTableT(WidgetEntityTest):
    _widget_cls = tws.AutoTableForm
    _entity_cls_str = 'DbTestCls9'
    attrs = {'css_class':'something', 'id' : 'something'}
    params = {'checked':None}
    expected = """
    <form method="post" class="something" id="something:form" enctype="multipart/form-data">
     <span class="error"></span>
    <table id="something">
    <tr class="odd" id="something:name:container">
        <th><label for="name">Name</label></th>
        <td>
            <input name="something:name" type="text" id="something:name" />
            <span id="something:name:error"></span>
        </td>
    </tr><tr class="even required" id="something:account:fieldset:container">
        <th><label for="account">Account</label></th>
        <td>
            <fieldset id="something:account:fieldset">
    <legend></legend>
    <table id="something:account">
    <tr class="odd required" id="something:account:account_name:container">
        <th><label for="account_name">Account Name</label></th>
        <td>
            <input name="account:account_name" type="text" value="" id="something:account:account_name" />
            <span id="something:account:account_name:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="something:account:error"></span>
    </td></tr>
</table>
</fieldset>
            <span id="something:account:fieldset:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="something:error"></span>
    </td></tr>
</table>
    <input type="submit" value="Save" />
</form>
"""

    def test_validation(self):
        value = self.widget.validate({'something': {'name': 'Bob3', 'account': {'account_name': 'accounttest'}}})
        assert(value == {'account': {'account_name': 'accounttest'}, 'name': 'Bob3'})

    def test_validation_no_account_name(self):
        try:
            self.widget.validate({'something': {'name': 'Bob3', 'account': {}}})
            assert(False)
        except twc.ValidationError, ve:
            # The exception is raise but it's very strange that the error was lost
            assert(ve.widget.error_msg == '')

    def test_validation_no_account(self):
        try:
            self.widget.validate({'something': {'name': 'Bob3'}})
            assert(False)
        except twc.ValidationError, ve:
            # The exception is raise but it's very strange that the error was lost
            assert(ve.widget.error_msg == '')

if el:
    class TestAutoEditRelationInTableElixir(ElixirBase, AutoEditRelationInTableT): pass

class TestAutoEditRelationInTableSQLA(SQLABase, AutoEditRelationInTableT): pass

class AutoEditRelationInFormT(WidgetEntityTest):
    _widget_cls = tws.DbFormPage
    _entity_cls_str = 'DbTestCls9'
    attrs = { 'id' : 'autoedit', 'title' : 'Test',
              'child' : tws.AutoTableForm}

    expected = """
<html>
<head><title>Test</title></head>
<body id="autoedit:page"><h1>Test</h1><form method="post" id="autoedit:form" enctype="multipart/form-data">
    <span class="error"></span>
    <table id="autoedit">
    <tr class="odd" id="autoedit:name:container">
        <th><label for="name">Name</label></th>
        <td>
            <input name="dbformpage_d:name" type="text" id="autoedit:name" />
            <span id="autoedit:name:error"></span>
        </td>
    </tr><tr class="even required" id="autoedit:account:fieldset:container">
        <th><label for="account">Account</label></th>
        <td>
            <fieldset id="autoedit:account:fieldset">
                <legend></legend>
                <table id="autoedit:account">
                <tr class="odd required" id="autoedit:account:account_name:container">
                    <th><label for="account_name">Account Name</label></th>
                    <td>
                        <input name="account:account_name" type="text" value="" id="autoedit:account:account_name" />
                        <span id="autoedit:account:account_name:error"></span>
                    </td>
                </tr>
                <tr class="error"><td colspan="2">
                    <span id="autoedit:account:error"></span>
                </td></tr>
                </table>
            </fieldset>
            <span id="autoedit:account:fieldset:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="autoedit:error"></span>
    </td></tr>
    </table>
    <input type="submit" value="Save" />
</form></body>
</html>
"""

    def test_request_get_edit(self):
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING' :'id=1'}
        req=Request(environ)
        assert(req.GET)
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """
<html>
<head><title>Test</title></head>
<body id="autoedit:page"><h1>Test</h1><form method="post" id="autoedit:form" enctype="multipart/form-data">
    <span class="error"></span>
    <table id="autoedit">
    <tr class="odd" id="autoedit:name:container">
        <th><label for="name">Name</label></th>
        <td>
            <input name="dbformpage_d:name" type="text" value="bob1" id="autoedit:name" />
            <span id="autoedit:name:error"></span>
        </td>
    </tr><tr class="even required" id="autoedit:account:fieldset:container">
        <th><label for="account">Account</label></th>
        <td>
            <fieldset id="autoedit:account:fieldset">
                <legend></legend>
                <table id="autoedit:account">
                <tr class="odd required" id="autoedit:account:account_name:container">
                    <th><label for="account_name">Account Name</label></th>
                    <td>
                        <input name="account:account_name" type="text" value="account1" id="autoedit:account:account_name" />
                        <span id="autoedit:account:account_name:error"></span>
                    </td>
                </tr>
                <tr class="error"><td colspan="2">
                    <span id="autoedit:account:error"></span>
                </td></tr>
                </table>
            </fieldset>
            <span id="autoedit:account:fieldset:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="autoedit:error"></span>
    </td></tr>
    </table>
    <input type="submit" value="Save" />
</form></body>
</html>
""")

    def test_request_post_redirect(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='autoedit:name=toto&autoedit:account:account_name=plop'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        r = self.widget(redirect="/foo").request(req)
        assert( r.status_int == 302 and r.location=="/foo" )

    def test_request_get(self):
        environ = {'REQUEST_METHOD': 'GET'}
        req=Request(environ)
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """
<html>
<head><title>Test</title></head>
<body id="autoedit:page"><h1>Test</h1><form method="post" id="autoedit:form" enctype="multipart/form-data">
    <span class="error"></span>
    <table id="autoedit">
    <tr class="odd" id="autoedit:name:container">
        <th><label for="name">Name</label></th>
        <td>
            <input name="dbformpage_d:name" type="text" id="autoedit:name" />
            <span id="autoedit:name:error"></span>
        </td>
    </tr><tr class="even required" id="autoedit:account:fieldset:container">
        <th><label for="account">Account</label></th>
        <td>
            <fieldset id="autoedit:account:fieldset">
                <legend></legend>
                <table id="autoedit:account">
                <tr class="odd required" id="autoedit:account:account_name:container">
                    <th><label for="account_name">Account Name</label></th>
                    <td>
                        <input name="account:account_name" type="text" value="" id="autoedit:account:account_name" />
                        <span id="autoedit:account:account_name:error"></span>
                    </td>
                </tr>
                <tr class="error"><td colspan="2">
                    <span id="autoedit:account:error"></span>
                </td></tr>
                </table>
            </fieldset>
            <span id="autoedit:account:fieldset:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="autoedit:error"></span>
    </td></tr>
    </table>
    <input type="submit" value="Save" />
</form></body>
</html>
""")

    def _test_request_post_invalid(self):
        environ = {'REQUEST_METHOD': 'POST',
                   'wsgi.input': StringIO(''),
                   }
        req=Request(environ)
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """<html>
<head><title>Test</title></head>
<body id="autoedit:page"><h1>Test</h1><form id="autoedit:form" enctype="multipart/form-data" method="post">
    <span class="error"></span>
    <table id="autoedit">
    <tr class="odd"  id="autoedit:name:container">
        <th>Name</th>
        <td >
            <input name="autoedit:name" type="text" value="" id="autoedit:name"/>

            <span id="autoedit:name:error"></span>
        </td>
    </tr>
    <tr class="even required"  id="autoedit:account:fieldset:container">
        <th>Account</th>
        <td >
            <fieldset id="autoedit:account:fieldset">
                <legend></legend>
                <table id="autoedit:account">
                <tr class="odd required error"  id="autoedit:account:account_name:container">
                    <th>Account Name</th>
                    <td >
                        <input name="autoedit:account:account_name" type="text" value="" id="autoedit:account:account_name"/>

                        <span id="autoedit:account:account_name:error">Enter a value</span>
                    </td>
                </tr>
                <tr class="error"><td colspan="2">
                    <span id="autoedit:account:error"></span>
                </td></tr>
                </table>
            </fieldset>
            <span id="autoedit:account:fieldset:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="autoedit:error"></span>
    </td></tr>
    </table>
    <input type="submit" value="Save"/>
</form>
</body>
</html>""")

    def test_request_post_valid(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='autoedit:account:account_name=account2'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        r = self.widget().request(req)
        assert r.body == """Form posted successfully {'account': {'account_name': u'account2'}, 'name': ''}""", r.body

    def test_request_post_counts_new(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='autoedit:account:account_name=account2'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        assert(self.DbTestCls9.query.count() == 1)
        assert(self.DbTestCls8.query.count() == 1)
        r = self.widget().request(req)
        assert(self.DbTestCls9.query.count() == 2)
        assert(self.DbTestCls8.query.count() == 2)

    def test_request_post_counts_update(self):
        environ = {'wsgi.input': StringIO(''), 'QUERY_STRING': 'id=1'}
        req=Request(environ)
        # req.GET['id'] = '1'
        req.method = 'POST'
        req.body='autoedit:account:account_name=account2&autoedit:name=bob2'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        assert(self.DbTestCls9.query.count() == 1)
        assert(self.DbTestCls8.query.count() == 1)
        r = self.widget().request(req)
        assert(self.DbTestCls9.query.count() == 1)
        assert(self.DbTestCls8.query.count() == 1)

    def test_request_post_content_update(self):
        environ = {'wsgi.input': StringIO(''), 'QUERY_STRING': 'id=1'}
        req=Request(environ)
        # req.GET['id'] = '1'
        req.method = 'POST'
        req.body='autoedit:account:account_name=account2&autoedit:name=bob2'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        original = self.DbTestCls9.query.filter(self.DbTestCls9.id==1).one()
        assert(original.name == 'bob1')
        original = self.DbTestCls8.query.filter(self.DbTestCls8.id==2).one()
        assert(original.account_name == 'account1')
        r = self.widget().request(req)
        updated = self.DbTestCls9.query.filter(self.DbTestCls9.id==1)
        assert(updated.count() == 1)
        updated = updated.one()
        assert(updated.name == 'bob2')
        updated = self.DbTestCls8.query.filter(self.DbTestCls8.id==2)
        assert(updated.count() == 1)
        updated = updated.one()
        assert(updated.account_name == 'account2')

if el:
    class TestAutoEditRelationInFromElixir(ElixirBase, AutoEditRelationInFormT): pass

class TestAutoEditRelationInFormSQLA(SQLABase, AutoEditRelationInFormT): pass


class NonRequiredOneToOneRelationT(WidgetEntityTest):
    _widget_cls = tws.DbFormPage
    _entity_cls_str = 'DbTestCls12'
    attrs = { 'id' : 'autoedit', 'title' : 'Test',
              'child' : tws.AutoTableForm}

    expected = """
<html>
<head><title>Test</title></head>
<body id="autoedit:page"><h1>Test</h1><form method="post" id="autoedit:form" enctype="multipart/form-data">
    <span class="error"></span>
    <table id="autoedit">
    <tr class="odd required" id="autoedit:name:container">
        <th><label for="name">Name</label></th>
        <td>
            <input name="dbformpage_d:name" type="text" value="" id="autoedit:name" />
            <span id="autoedit:name:error"></span>
        </td>
    </tr><tr class="even" id="autoedit:account:fieldset:container">
        <th><label for="account">Account</label></th>
        <td>
            <fieldset id="autoedit:account:fieldset">
                <legend></legend>
                <table id="autoedit:account">
                <tr class="odd" id="autoedit:account:account_name:container">
                    <th><label for="account_name">Account Name</label></th>
                    <td>
                        <input name="account:account_name" type="text" value="" id="autoedit:account:account_name" />
                        <span id="autoedit:account:account_name:error"></span>
                    </td>
                </tr>
                <tr class="even" id="autoedit:account:account_number:container">
                  <th><label for="account_number">Account Number</label></th>
                  <td>
                    <input name="account:account_number" type="text" value="" id="autoedit:account:account_number" />
                    <span id="autoedit:account:account_number:error"></span>
                  </td>
                </tr>
                <tr class="error"><td colspan="2">
                    <span id="autoedit:account:error"></span>
                </td></tr>
                </table>
            </fieldset>
            <span id="autoedit:account:fieldset:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="autoedit:error"></span>
    </td></tr>
    </table>
    <input type="submit" value="Save" />
</form></body>
</html>
"""

    def test_request_get_edit(self):
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING' :'id=1'}
        req=Request(environ)
        assert(req.GET)
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """
<html>
<head><title>Test</title></head>
<body id="autoedit:page"><h1>Test</h1><form method="post" id="autoedit:form" enctype="multipart/form-data">
    <span class="error"></span>
    <table id="autoedit">
    <tr class="odd required" id="autoedit:name:container">
        <th><label for="name">Name</label></th>
        <td>
            <input name="dbformpage_d:name" type="text" value="bob1" id="autoedit:name" />
            <span id="autoedit:name:error"></span>
        </td>
    </tr><tr class="even" id="autoedit:account:fieldset:container">
        <th><label for="account">Account</label></th>
        <td>
            <fieldset id="autoedit:account:fieldset">
                <legend></legend>
                <table id="autoedit:account">
                <tr class="odd" id="autoedit:account:account_name:container">
                    <th><label for="account_name">Account Name</label></th>
                    <td>
                        <input name="account:account_name" type="text" value="account1" id="autoedit:account:account_name" />
                        <span id="autoedit:account:account_name:error"></span>
                    </td>
                </tr>
                <tr class="even" id="autoedit:account:account_number:container">
                  <th><label for="account_number">Account Number</label></th>
                  <td>
                    <input name="account:account_number" type="text" value="number1" id="autoedit:account:account_number" />
                    <span id="autoedit:account:account_number:error"></span>
                  </td>
                </tr>
                <tr class="error"><td colspan="2">
                    <span id="autoedit:account:error"></span>
                </td></tr>
                </table>
            </fieldset>
            <span id="autoedit:account:fieldset:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="autoedit:error"></span>
    </td></tr>
    </table>
    <input type="submit" value="Save" />
</form></body>
</html>
""")

    def test_request_post_redirect(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='autoedit:name=toto&autoedit:account:account_name=plop&autoedit:account:account_number=num'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        r = self.widget(redirect="/foo").request(req)
        assert( r.status_int == 302 and r.location=="/foo" )

    def test_request_get(self):
        environ = {'REQUEST_METHOD': 'GET'}
        req=Request(environ)
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """
<html>
<head><title>Test</title></head>
<body id="autoedit:page"><h1>Test</h1><form method="post" id="autoedit:form" enctype="multipart/form-data">
    <span class="error"></span>
    <table id="autoedit">
    <tr class="odd required" id="autoedit:name:container">
        <th><label for="name">Name</label></th>
        <td>
            <input name="dbformpage_d:name" type="text" value="" id="autoedit:name" />
            <span id="autoedit:name:error"></span>
        </td>
    </tr><tr class="even" id="autoedit:account:fieldset:container">
        <th><label for="account">Account</label></th>
        <td>
            <fieldset id="autoedit:account:fieldset">
                <legend></legend>
                <table id="autoedit:account">
                <tr class="odd" id="autoedit:account:account_name:container">
                  <th><label for="account_name">Account Name</label></th>
                  <td>
                      <input name="account:account_name" type="text" value="" id="autoedit:account:account_name" />
                      <span id="autoedit:account:account_name:error"></span>
                  </td>
                </tr>
                <tr class="even" id="autoedit:account:account_number:container">
                  <th><label for="account_number">Account Number</label></th>
                  <td>
                    <input name="account:account_number" type="text" value="" id="autoedit:account:account_number" />
                    <span id="autoedit:account:account_number:error"></span>
                  </td>
                </tr>
                <tr class="error"><td colspan="2">
                    <span id="autoedit:account:error"></span>
                </td></tr>
                </table>
            </fieldset>
            <span id="autoedit:account:fieldset:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="autoedit:error"></span>
    </td></tr>
    </table>
    <input type="submit" value="Save" />
</form></body>
</html>
""")

    def test_request_post_invalid(self):
        environ = {'REQUEST_METHOD': 'POST',
                   'wsgi.input': StringIO(''),
                   }
        req=Request(environ)
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """<html>
<head><title>Test</title></head>
<body id="autoedit:page"><h1>Test</h1><form method="post" id="autoedit:form" enctype="multipart/form-data">
  <span class="error"></span>
  <table id="autoedit">
  <tr class="odd required error" id="autoedit:name:container">
    <th><label for="name">Name</label></th>
    <td>
        <input name="dbformpage_d:name" type="text" value="" id="autoedit:name" />
        <span id="autoedit:name:error">Enter a value</span>
    </td>
  </tr>
  <tr class="even" id="autoedit:account:fieldset:container">
    <th><label for="account">Account</label></th>
    <td>
      <fieldset id="autoedit:account:fieldset">
        <legend></legend>
        <table id="autoedit:account">
        <tr class="odd" id="autoedit:account:account_name:container">
        <th><label for="account_name">Account Name</label></th>
          <td>
              <input name="account:account_name" type="text" value="" id="autoedit:account:account_name" />
              <span id="autoedit:account:account_name:error"></span>
          </td>
        </tr><tr class="even" id="autoedit:account:account_number:container">
          <th><label for="account_number">Account Number</label></th>
          <td>
              <input name="account:account_number" type="text" value="" id="autoedit:account:account_number" />
              <span id="autoedit:account:account_number:error"></span>
          </td>
        </tr>
        <tr class="error"><td colspan="2">
          <span id="autoedit:account:error"></span>
        </td></tr>
        </table>
      </fieldset>
      <span id="autoedit:account:fieldset:error"></span>
    </td>
  </tr>
  <tr class="error"><td colspan="2">
      <span id="autoedit:error"></span>
  </td></tr>
  </table>
  <input type="submit" value="Save" />
</form></body>
</html>""")

    def test_request_post_partial_onetoone_invalid(self):
        environ = {'REQUEST_METHOD': 'POST',
                   'wsgi.input': StringIO(''),
                   }
        req=Request(environ)
        req.method = 'POST'
        req.body='autoedit:account:account_name=account2&autoedit:name=name2'
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """<html>
<head>
  <title>Test</title>
</head>
<body id="autoedit:page"><h1>Test</h1><form method="post" id="autoedit:form" enctype="multipart/form-data">
  <span class="error"></span>
  <table id="autoedit">
  <tr class="odd required" id="autoedit:name:container">
      <th><label for="name">Name</label></th>
      <td>
          <input name="dbformpage_d:name" type="text" value="name2" id="autoedit:name" />
          <span id="autoedit:name:error"></span>
      </td>
  </tr><tr class="even" id="autoedit:account:fieldset:container">
      <th><label for="account">Account</label></th>
      <td>
        <fieldset id="autoedit:account:fieldset">
          <legend></legend>
          <table id="autoedit:account">
          <tr class="odd" id="autoedit:account:account_name:container">
              <th><label for="account_name">Account Name</label></th>
              <td>
                  <input name="account:account_name" type="text" value="account2" id="autoedit:account:account_name" />
                  <span id="autoedit:account:account_name:error"></span>
              </td>
          </tr><tr class="even error" id="autoedit:account:account_number:container">
              <th><label for="account_number">Account Number</label></th>
              <td>
                  <input name="account:account_number" type="text" value="" id="autoedit:account:account_number" />
                  <span id="autoedit:account:account_number:error">Enter a value</span>
              </td>
          </tr>
          <tr class="error"><td colspan="2">
              <span id="autoedit:account:error"></span>
          </td></tr>
          </table>
        </fieldset>
        <span id="autoedit:account:fieldset:error"></span>
      </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="autoedit:error"></span>
    </td></tr>
</table>
    <input type="submit" value="Save" />
</form></body>
</html>""")

    def test_request_post_valid(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='autoedit:name=name2'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        r = self.widget().request(req)
        assert r.body == """Form posted successfully {'account': None, 'name': u'name2'}""", r.body

    def test_request_post_full_valid(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='autoedit:account:account_name=account2&autoedit:account:account_number=number2&autoedit:name=name2'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        r = self.widget().request(req)
        assert r.body == """Form posted successfully {'account': {'account_name': u'account2', 'account_number': u'number2'}, 'name': u'name2'}""", r.body

    def test_request_post_counts_new(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='autoedit:account:account_name=account2&autoedit:account:account_number=number2&autoedit:name=name2'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        assert(self.DbTestCls12.query.count() == 1)
        assert(self.DbTestCls11.query.count() == 1)
        r = self.widget().request(req)
        assert(self.DbTestCls12.query.count() == 2)
        assert(self.DbTestCls11.query.count() == 2)

    def test_request_post_counts_new_no_onetoone(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='autoedit:name=name2'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        assert(self.DbTestCls12.query.count() == 1)
        assert(self.DbTestCls11.query.count() == 1)
        r = self.widget().request(req)
        assert(self.DbTestCls12.query.count() == 2)
        assert(self.DbTestCls11.query.count() == 1)

    def test_request_post_counts_update(self):
        environ = {'wsgi.input': StringIO(''), 'QUERY_STRING': 'id=1'}
        req=Request(environ)
        # req.GET['id'] = '1'
        req.method = 'POST'
        req.body='autoedit:account:account_name=account2&autoedit:account:account_number=number2&autoedit:name=bob2'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        assert(self.DbTestCls12.query.count() == 1)
        assert(self.DbTestCls11.query.count() == 1)
        r = self.widget().request(req)
        assert(self.DbTestCls12.query.count() == 1)
        assert(self.DbTestCls11.query.count() == 1)

    def test_request_post_counts_update_no_onetoone(self):
        environ = {'wsgi.input': StringIO(''), 'QUERY_STRING': 'id=1'}
        req=Request(environ)
        # req.GET['id'] = '1'
        req.method = 'POST'
        req.body='autoedit:name=bob2'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        assert(self.DbTestCls12.query.count() == 1)
        assert(self.DbTestCls11.query.count() == 1)
        r = self.widget().request(req)
        assert(self.DbTestCls12.query.count() == 1)
        assert(self.DbTestCls11.query.count() == 0)

    def test_request_post_content_update(self):
        environ = {'wsgi.input': StringIO(''), 'QUERY_STRING': 'id=1'}
        req=Request(environ)
        # req.GET['id'] = '1'
        req.method = 'POST'
        req.body='autoedit:account:account_name=account2&autoedit:account:account_number=number2&autoedit:name=bob2'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        original = self.DbTestCls12.query.filter(self.DbTestCls12.id==1).one()
        assert(original.name == 'bob1')
        original = self.DbTestCls11.query.filter(self.DbTestCls11.id==2).one()
        assert(original.account_name == 'account1')
        r = self.widget().request(req)
        updated = self.DbTestCls12.query.filter(self.DbTestCls12.id==1)
        assert(updated.count() == 1)
        updated = updated.one()
        assert(updated.name == 'bob2')
        updated = self.DbTestCls11.query.filter(self.DbTestCls11.id==2)
        assert(updated.count() == 1)
        updated = updated.one()
        assert(updated.account_name == 'account2')
        assert(updated.account_number == 'number2')

if el:
    class TestNonRequiredOneToOneRelationElixir(
        ElixirBase, NonRequiredOneToOneRelationT): pass

class TestNonRequiredOneToOneRelationSQLA(SQLABase,
                                          NonRequiredOneToOneRelationT): pass


class AutoTableFormAsChildT(WidgetEntityTest):
    _widget_cls = tws.DbFormPage
    _entity_cls_str = 'DbTestCls7'
    attrs = { 'id' : 'autotable', 'title' : 'Test',
              'child' : tws.AutoTableForm}
    expected = """
<html>
<head><title>Test</title></head>
<body id="autotable:page"><h1>Test</h1><form method="post" id="autotable:form" enctype="multipart/form-data">
    <span class="error"></span>
    <table id="autotable">
    <tr class="odd" id="autotable:nick:container">
        <th><label for="nick">Nick</label></th>
        <td>
            <input name="dbformpage_d:nick" type="text" id="autotable:nick" />
            <span id="autotable:nick:error"></span>
        </td>
    </tr><tr class="even required" id="autotable:other:container">
        <th><label for="other">Other</label></th>
        <td>
            <select id="autotable:other" name="dbformpage_d:other">
                <option></option>
                <option value="1">foo1</option>
                <option value="2">foo2</option>
            </select>
            <span id="autotable:other:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="autotable:error"></span>
    </td></tr>
    </table>
    <input type="submit" value="Save" />
</form></body>
</html>
"""

    def test_request_get_edit(self):
        environ = {
            'REQUEST_METHOD': 'GET',
        }
        req=Request(environ)
        self.mw.config.debug = True
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """
<html>
<head><title>Test</title></head>
<body id="autotable:page"><h1>Test</h1><form method="post" id="autotable:form" enctype="multipart/form-data">
    <span class="error"></span>
    <table id="autotable">
    <tr class="odd" id="autotable:nick:container">
        <th><label for="nick">Nick</label></th>
        <td>
            <input name="dbformpage_d:nick" type="text" id="autotable:nick" />
            <span id="autotable:nick:error"></span>
        </td>
    </tr><tr class="even required" id="autotable:other:container">
        <th><label for="other">Other</label></th>
        <td>
            <select id="autotable:other" name="dbformpage_d:other">
                <option></option>
                <option value="1">foo1</option>
                <option value="2">foo2</option>
            </select>
            <span id="autotable:other:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="autotable:error"></span>
    </td></tr>
    </table>
    <input type="submit" value="Save" />
</form></body>
</html>
""")

    def test_request_post_redirect(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='autotable:other=1'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        r = self.widget(redirect="/foo").request(req)
        assert( r.status_int == 302 and r.location=="/foo" )

    def test_request_get(self):
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING' :'id=1'}
        req=Request(environ)
        assert(req.GET)
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """
<html>
<head><title>Test</title></head>
<body id="autotable:page"><h1>Test</h1><form id="autotable:form" enctype="multipart/form-data" method="post">
    <span class="error"></span>
    <table id="autotable">
    <tr class="odd"  id="autotable:nick:container">
        <th><label for="nick">Nick</label></th>
        <td >
            <input name="dbformpage_d:nick" type="text" id="autotable:nick" value="bob1"/>

            <span id="autotable:nick:error"></span>
        </td>
    </tr>
    <tr class="even required"  id="autotable:other:container">
        <th><label for="other">Other</label></th>
        <td >
            <select name="dbformpage_d:other" id="autotable:other">
                <option ></option>
                <option selected="selected" value="1">foo1</option>
                <option value="2">foo2</option>
            </select>
            <span id="autotable:other:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="autotable:error"></span>
    </td></tr>
    </table>
    <input type="submit" value="Save"/>
</form>
</body>
</html>""")

    def test_request_post_valid(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='autotable:nick=toto1&autotable:other=2'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        r = self.widget().request(req)
        assert """Form posted successfully {'nick': u'toto1', 'other':""" in r.body, r.body

    def test_request_post_invalid_no_other(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='autotable:nick=toto1'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """
<html>
<head><title>Test</title></head>
<body id="autotable:page"><h1>Test</h1><form id="autotable:form" enctype="multipart/form-data" method="post">
     <span class="error"></span>
    <table id="autotable">
    <tr class="odd"  id="autotable:nick:container">
        <th><label for="nick">Nick</label></th>
        <td >
            <input name="dbformpage_d:nick" type="text" id="autotable:nick" value="toto1"/>

            <span id="autotable:nick:error"></span>
        </td>
    </tr>
    <tr class="even required error"  id="autotable:other:container">
        <th><label for="other">Other</label></th>
        <td >
            <select name="dbformpage_d:other" id="autotable:other">
                <option ></option>
                <option value="1">foo1</option>
                <option value="2">foo2</option>
            </select>
            <span id="autotable:other:error">Enter a value</span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="autotable:error"></span>
    </td></tr>
    </table>
    <input type="submit" value="Save"/>
</form>
</body>
</html>""")

    def test_request_post_invalid_nonexisting_other(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='autotable:nick=toto1&autotable:other=10'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """
<html>
<head><title>Test</title></head>
<body id="autotable:page"><h1>Test</h1><form id="autotable:form" enctype="multipart/form-data" method="post">
    <span class="error"></span>
    <table id="autotable">
    <tr class="odd"  id="autotable:nick:container">
        <th><label for="nick">Nick</label></th>
        <td >
            <input name="dbformpage_d:nick" type="text" id="autotable:nick" value="toto1"/>

            <span id="autotable:nick:error"></span>
        </td>
    </tr>
    <tr class="even required error"  id="autotable:other:container">
        <th><label for="other">Other</label></th>
        <td >
            <select name="dbformpage_d:other" id="autotable:other">
                <option ></option>
                <option value="1">foo1</option>
                <option value="2">foo2</option>
            </select>
            <span id="autotable:other:error">No related object found</span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <span id="autotable:error"></span>
    </td></tr>
    </table>
    <input type="submit" value="Save"/>
</form>
</body>
</html>""")

    def test_request_post_counts_new(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='autotable:nick=toto1&autotable:other=1'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        assert(self.DbTestCls7.query.count() == 2)
        r = self.widget().request(req)
        assert(self.DbTestCls7.query.count() == 3)

    def test_request_post_counts_update(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='autotable:nick=toto1&autotable:other=1&autotable:id=1'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        assert(self.DbTestCls1.query.count() == 2)
        r = self.widget().request(req)
        assert(self.DbTestCls1.query.count() == 2)

if el:
    class TestAutoTableFormAsChildTElixir(ElixirBase, AutoTableFormAsChildT): pass

class TestAutoTableFormAsChildTSQLA(SQLABase, AutoTableFormAsChildT): pass

class FormPageRequiredCheckboxT(WidgetTest):
    def setUp(self):
        attrs = {
                'child': twf.TableForm(
                    children=[
                        twf.HiddenField(id='id'),
                        twf.TextField(id='name'),
                        tws.DbCheckBoxList(id='others', entity=self.DbTestCls2, validator=twc.Required),
                    ]),
                'title': 'some title',
                'entity': self.DbTestCls1,
            }
        self.widget = self._widget_cls(**attrs)
        return super(FormPageRequiredCheckboxT, self).setUp()

    _widget_cls = tws.DbFormPage
    expected = """
<html>
<head><title>some title</title></head>
<body id="dbformpage_d:page"><h1>some title</h1><form method="post" id="dbformpage_d:form" enctype="multipart/form-data">
    <span class="error"></span>
    <table id="dbformpage_d">
    <tr class="odd" id="dbformpage_d:name:container">
        <th><label for="name">Name</label></th>
        <td>
            <input name="dbformpage_d:name" id="dbformpage_d:name" type="text" />
            <span id="dbformpage_d:name:error"></span>
        </td>
    </tr><tr class="even required" id="dbformpage_d:others:container">
        <th><label for="others">Others</label></th>
        <td>
            <ul id="dbformpage_d:others">
            <li>
                <input type="checkbox" name="dbformpage_d:others" value="1" id="dbformpage_d:others:0" />
                <label for="dbformpage_d:others:0">bob1</label>
            </li><li>
                <input type="checkbox" name="dbformpage_d:others" value="2" id="dbformpage_d:others:1" />
                <label for="dbformpage_d:others:1">bob2</label>
            </li><li>
                <input type="checkbox" name="dbformpage_d:others" value="3" id="dbformpage_d:others:2" />
                <label for="dbformpage_d:others:2">bob3</label>
            </li>
</ul>
            <span id="dbformpage_d:others:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <input name="dbformpage_d:id" type="hidden" id="dbformpage_d:id" />
        <span id="dbformpage_d:error"></span>
    </td></tr>
    </table>
    <input type="submit" value="Save" />
</form></body>
</html>
"""
    def test_request_post_redirect(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='dbformpage_d:name=toto1&dbformpage_d:others=2'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        r = self.widget(redirect="/foo").request(req)
        assert( r.status_int == 302 and r.location=="/foo" )

    def test_request_get(self):
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING' :'id=1'}
        req=Request(environ)
        assert(req.GET)
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """
<html>
<head><title>some title</title></head>
<body id="dbformpage_d:page"><h1>some title</h1><form id="dbformpage_d:form" enctype="multipart/form-data" method="post">
    <span class="error"></span>
    <table id="dbformpage_d">
    <tr class="odd"  id="dbformpage_d:name:container">
        <th><label for="name">Name</label></th>
        <td >
            <input name="dbformpage_d:name" type="text" id="dbformpage_d:name" value="foo1"/>

            <span id="dbformpage_d:name:error"></span>
        </td>
    </tr>
    <tr class="even required"  id="dbformpage_d:others:container">
        <th><label for="others">Others</label></th>
        <td >
            <ul id="dbformpage_d:others">
                <li>
                    <input type="checkbox" name="dbformpage_d:others" value="1" id="dbformpage_d:others:0"/>
                    <label for="dbformpage_d:others:0">bob1</label>
                </li>
                <li>
                    <input type="checkbox" name="dbformpage_d:others" value="2" id="dbformpage_d:others:1"/>
                    <label for="dbformpage_d:others:1">bob2</label>
                </li>
                <li>
                    <input type="checkbox" checked="checked" name="dbformpage_d:others" value="3" id="dbformpage_d:others:2"/>
                    <label for="dbformpage_d:others:2">bob3</label>
                </li>
            </ul>
            <span id="dbformpage_d:others:error"></span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <input type="hidden" name="dbformpage_d:id" value="1" id="dbformpage_d:id"/>
        <span id="dbformpage_d:error"></span>
    </td></tr>
    </table>
    <input type="submit" value="Save"/>
</form>
</body>
</html>
""")

    def test_request_post_valid(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='dbformpage_d:name=toto1&dbformpage_d:others=2'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        r = self.widget().request(req)
        assert """Form posted successfully""" in r.body, r.body

    def test_request_post_invalid_no_others(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='dbformpage_d:name=toto1'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """
<html>
<head><title>some title</title></head>
<body id="dbformpage_d:page"><h1>some title</h1><form id="dbformpage_d:form" enctype="multipart/form-data" method="post">
    <span class="error"></span>
    <table id="dbformpage_d">
    <tr class="odd"  id="dbformpage_d:name:container">
        <th><label for="name">Name</label></th>
        <td >
            <input name="dbformpage_d:name" type="text" id="dbformpage_d:name" value="toto1"/>

            <span id="dbformpage_d:name:error"></span>
        </td>
    </tr>
    <tr class="even required error"  id="dbformpage_d:others:container">
        <th><label for="others">Others</label></th>
        <td >
            <ul id="dbformpage_d:others">
                <li>
                    <input type="checkbox" name="dbformpage_d:others" value="1" id="dbformpage_d:others:0"/>
                    <label for="dbformpage_d:others:0">bob1</label>
                </li>
                <li>
                    <input type="checkbox" name="dbformpage_d:others" value="2" id="dbformpage_d:others:1"/>
                    <label for="dbformpage_d:others:1">bob2</label>
                </li>
                <li>
                    <input type="checkbox" name="dbformpage_d:others" value="3" id="dbformpage_d:others:2"/>
                    <label for="dbformpage_d:others:2">bob3</label>
                </li>
            </ul>
            <span id="dbformpage_d:others:error">Enter a value</span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <input type="hidden" name="dbformpage_d:id" value="" id="dbformpage_d:id"/>
        <span id="dbformpage_d:error"></span>
    </td></tr>
    </table>
    <input type="submit" value="Save"/>
</form>
</body>
</html>
""")

    def test_request_post_invalid_non_existing_others(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='dbformpage_d:name=toto1&dbformpage_d:others=10'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        r = self.widget().request(req)
        tw2test.assert_eq_xml(r.body, """
<html>
<head><title>some title</title></head>
<body id="dbformpage_d:page"><h1>some title</h1><form id="dbformpage_d:form" enctype="multipart/form-data" method="post">
     <span class="error"></span>
    <table id="dbformpage_d">
    <tr class="odd"  id="dbformpage_d:name:container">
        <th><label for="name">Name</label></th>
        <td >
            <input name="dbformpage_d:name" type="text" id="dbformpage_d:name" value="toto1"/>

            <span id="dbformpage_d:name:error"></span>
        </td>
    </tr>
    <tr class="even required error"  id="dbformpage_d:others:container">
        <th><label for="others">Others</label></th>
        <td >
            <ul id="dbformpage_d:others">
                <li>
                    <input type="checkbox" name="dbformpage_d:others" value="1" id="dbformpage_d:others:0"/>
                    <label for="dbformpage_d:others:0">bob1</label>
                </li>
                <li>
                    <input type="checkbox" name="dbformpage_d:others" value="2" id="dbformpage_d:others:1"/>
                    <label for="dbformpage_d:others:1">bob2</label>
                </li>
                <li>
                    <input type="checkbox" name="dbformpage_d:others" value="3" id="dbformpage_d:others:2"/>
                    <label for="dbformpage_d:others:2">bob3</label>
                </li>
            </ul>
            <span id="dbformpage_d:others:error">Enter a value</span>
        </td>
    </tr>
    <tr class="error"><td colspan="2">
        <input type="hidden" name="dbformpage_d:id" value="" id="dbformpage_d:id"/>
        <span id="dbformpage_d:error"></span>
    </td></tr>
    </table>
    <input type="submit" value="Save"/>
</form>
</body>
</html>
""")

    def test_request_post_counts_new(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='dbformpage_d:name=toto1&dbformpage_d:others=1'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        assert(self.DbTestCls1.query.count() == 2)
        r = self.widget().request(req)
        assert(self.DbTestCls1.query.count() == 3)

    def test_request_post_counts_update(self):
        environ = {'wsgi.input': StringIO('')}
        req=Request(environ)
        req.method = 'POST'
        req.body='dbformpage_d:name=toto1&dbformpage_d:others=1&dbformpage_d:id=1'
        req.environ['CONTENT_LENGTH'] = str(len(req.body))
        req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

        self.mw.config.debug = True
        assert(self.DbTestCls1.query.count() == 2)
        r = self.widget().request(req)
        assert(self.DbTestCls1.query.count() == 2)

if el:
    class TestFormPageRequiredCheckboxTElixir(ElixirBase, FormPageRequiredCheckboxT): pass

class TestFormPageRequiredCheckboxTSQLA(SQLABase, FormPageRequiredCheckboxT): pass


class DbLinkFieldT(WidgetTest):
    _widget_cls = tws.DbLinkField
    params = {'link':'/test'}
    expected = """<a href="/test?id=1">foo1</a>"""

    def setUp(self):
        self.widget = self._widget_cls(entity=self.DbTestCls1, value=self.DbTestCls1.query.get(1))
        return super(DbLinkFieldT, self).setUp()

    def test_encode(self):
        d = self.DbTestCls10(name="fr&ed")
        w = tws.DbLinkField(entity=self.DbTestCls10, value=d, link='/test')
        tw2test.assert_eq_xml(w.display(), """<a href="/test?name=fr%26ed">fr&amp;ed</a>""")

    def test_ident(self):
        d = self.DbTestCls10(name="fred")
        w = tws.DbLinkField(entity=self.DbTestCls10, value=d, link='/test/$')
        tw2test.assert_eq_xml(w.display(), '<a href="/test/fred">fred</a>')

    def test_text(self):
        d = self.DbTestCls10(name="fred")
        w = tws.DbLinkField(entity=self.DbTestCls10, value=d, link='/test/$',
                            text='edit')
        tw2test.assert_eq_xml(w.display(), '<a href="/test/fred">edit</a>')

    def test_many_pkeys(self):
        d = self.DbTestCls3(id1=1, id2=2)
        w = tws.DbLinkField(entity=self.DbTestCls3, value=d, link='/test/$',
                            text='edit')
        try:
            w.display()
            assert(False)
        except twc.WidgetError, e:
            expected = ("Can't replace '$' in /test/$ since there is many "
            "primary keys. For this special case remove the '$' and let the "
            "widget making the query string.")
            assert(str(e) == expected)

    def test_no_value(self):
        w = tws.DbLinkField(entity=self.DbTestCls10, link='/test/$')
        tw2test.assert_eq_xml(w.display(), '<a ></a>')

    def test_no_link(self):
        w = tws.DbLinkField(entity=self.DbTestCls10, text='edit')
        tw2test.assert_eq_xml(w.display(), '<a>edit</a>')

    def test_parent_value(self):
        d = self.DbTestCls10(name="fred")
        w = tws.AutoTableForm(
                children=[
                    tws.DbLinkField(
                        'edit', entity=self.DbTestCls10, link='/test/$')
                ],
                value=d,
                entity=None
                )
        tw2test.assert_eq_xml(w.display(), """
<form enctype="multipart/form-data" method="post">
  <span class="error"></span>
  <table>
  <tr class="odd"  id="edit:container">
      <th><label for="edit">Edit</label></th>
      <td>
          <a href="/test/fred" id="edit">fred</a>
          <span id="edit:error"></span>
      </td>
  </tr>
  <tr class="error"><td colspan="2">
      <span id=":error"></span>
  </td></tr>
  </table>
  <input type="submit" value="Save"/>
</form>
""")


if el:
    class TestLinkFieldElixir(ElixirBase, DbLinkFieldT): pass

class TestLinkFieldSQLA(SQLABase, DbLinkFieldT): pass
