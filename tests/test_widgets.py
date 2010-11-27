import tw2.core as twc, tw2.sqla as tws, sqlalchemy as sa
import tw2.core.testbase as tw2test

import testapi


class ElixirBase(object):
    def setup(self):
        import elixir as el
        import transaction
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

        super(ElixirBase, self).setup()
        testapi.request(1)

class SQLABase(object):
    def setup(self):
        from sqlalchemy.ext.declarative import declarative_base
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

        super(SQLABase, self).setup()
        testapi.request(1)

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

class TestRadioButtonElixir(ElixirBase, RadioButtonT):
    pass
class TestRadioButtonSQLA(SQLABase, RadioButtonT):
    pass

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

class TestCheckBoxElixir(ElixirBase, CheckBoxT):
    pass
class TestCheckBoxSQLA(SQLABase, CheckBoxT):
    pass

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

class TestSingleSelectElixir(ElixirBase, SingleSelectT):
    pass
class TestSingleSelectSQLA(SQLABase, SingleSelectT):
    pass

