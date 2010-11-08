import tw2.core as twc, tw2.forms as twf, webob, sqlalchemy as sa, sys
import sqlalchemy.types as sat, tw2.dynforms as twd
from zope.sqlalchemy import ZopeTransactionExtension
import transaction

from tw2.sqla.utils import from_dict

def table_for(entity):
    mapper = sa.orm.class_mapper(entity)
    if len(mapper.tables) != 1:
        raise twc.WidgetError('Can only act on entities that map to a single table')
    return mapper.tables[0]


class RelatedValidator(twc.IntValidator):
    """Validator for related object
    
    `entity`
        The SQLAlchemy class to use. This must be mapped to a single table with a single primary key column.
        It must also have the SQLAlchemy `query` property; this will be the case for Elixir classes,
        and can be specified using DeclarativeBase (and is in the TG2 default setup).
    """
    msgs = {
        'norel': 'No related object found',
    }
    
    def __init__(self, entity, **kw):
        super(RelatedValidator, self).__init__(**kw)
        cols = list(table_for(entity).primary_key.columns)
        if len(cols) != 1:
            raise twc.WidgetError('RelatedValidator can only act on tables that have a single primary key column')
        self.entity = entity
        self.primary_key = cols[0]
        
    def to_python(self, value):
        if not value:
            return None
        if isinstance(self.primary_key.type, sa.types.Integer):
            try:
                value = int(value)
            except ValueError:
                raise twc.ValidationError('norel', self)
        value = self.entity.query.filter(getattr(self.entity, self.primary_key.name)==value).first()
        if not value:
            raise twc.ValidationError('norel', self)
        return value

    def from_python(self, value):
        return value and unicode(sa.orm.object_mapper(value).primary_key_from_instance(value)[0])


class DbFormPage(twf.FormPage):
    entity = twc.Param('SQLAlchemy mapped class to use', request_local=False)
    redirect = twc.Param('Location to redirect to after successful POST', request_local=False)
    _no_autoid = True

    @classmethod
    def post_define(cls):
        if hasattr(cls, 'entity') and not hasattr(cls, 'title'):
            cls.title = twc.util.name2label(table_for(cls.entity).name)

    def fetch_data(self, req):
        self.value = req.GET and self.entity.query.filter_by(**req.GET.mixed()).first() or None

    @classmethod
    def validated_request(cls, req, data):
        if req.GET:
            v = cls.entity.query.filter_by(**req.GET.mixed()).first()
        else:
            v = cls.entity()

        pylons = None
        try:
            import pylons
        except Exception:
            pass

        if hasattr(v, 'from_dict'):
            # In the case of elixir
            v.from_dict(data)
        elif pylons:
            # TBD Is this really a good enough test that we're running pylons?
            # In the case of pylons/turbogears
            # TBD what about setups with multiple engines and sessions?
            session = pylons.configuration.config['DBSession']
            v = from_dict(v, data, session=session)
            transaction.commit()
        else:
            raise UnimplementedError, "Neither elixir nor pylons"

        if hasattr(cls, 'redirect'):
            return webob.Response(request=req, status=302, location=cls.redirect)
        else:
            return super(DbFormPage, cls).validated_request(req, data)


class DbListPage(twc.Page):
    entity = twc.Param('SQLAlchemy mapped class to use', request_local=False)
    newlink = twc.Param('New item widget', default=None)
    template = 'tw2.sqla.templates.dblistpage'
    _no_autoid = True
    
    def fetch_data(self, req):
        self.value = self.entity.query.all()

    @classmethod
    def post_define(cls):
        if cls.newlink:
            cls.newlink = cls.newlink(parent=cls)
        if hasattr(cls, 'entity'):
            if not hasattr(cls, 'title'):
                cls.title = twc.util.name2label(table_for(cls.entity).name)
            if hasattr(cls, 'edit'):
                cls.edit = cls.edit(redirect=cls._gen_compound_id(for_url=True), entity=cls.entity, id=cls.id+'_edit')
                cls.newlink = twf.LinkField(link=cls.edit._gen_compound_id(for_url=True), text='New', value=1, parent=cls)
                class mypol(cls.child.policy):
                    pkey_widget = twf.LinkField(text='$', link=cls.id+'_edit?id=$')
                cls.child = cls.child(policy=mypol, _auto_widgets=False)

    def __init__(self, **kw):
        super(DbListPage, self).__init__(**kw)
        if self.newlink:
            self.newlink = self.newlink.req()

    def prepare(self):
        super(DbListPage, self).prepare()
        if self.newlink:
            self.newlink.prepare()


class DbSelectionField(twf.SelectionField):
    entity = twc.Param('SQLAlchemy mapped class to use', request_local=False)

    def prepare(self):
        self.options = [(x.id, unicode(x)) for x in self.entity.query.all()]
        super(DbSelectionField, self).prepare()    


class DbSingleSelectField(DbSelectionField, twf.SingleSelectField):
    @classmethod
    def post_define(cls):
        if getattr(cls, 'entity', None):
            cls.validator = RelatedValidator(entity=cls.entity)
    
class DbCheckBoxList(DbSelectionField, twf.CheckBoxList):
    @classmethod
    def post_define(cls):
        if getattr(cls, 'entity', None):
            cls.item_validator = RelatedValidator(entity=cls.entity)


class WidgetPolicy(object):
    """
    A policy object is used to generate widgets from SQLAlchemy columns. 
    
    In general, the widget's id is set to the name of the column, and if the
    column is not nullable, the validator is set as required. If the desired
    widget is None, then no widget is used for that column.
    
    Several parameters can be overridden to select the widget to use:
    
    `pkey_widget`
        For primary key columns
        
    `fkey_widget`
        For foreign key columns. In this case the widget's id is set to the
        name of the relation, and its entity is set to the target class.
        
    `name_widgets`
        A dictionary mapping column names to the desired widget. This can be 
        used for names like "password" or "email".
    
    `type_widgets`
        A dictionary mapping SQLAlchemy column types to the desired widget.
        
    `default_widget`
        If the column does not match any of the other selectors, this is used.
        If this is None then an error is raised for columns that do not match.

    Alternatively, the `factory` method can be overriden to provide completely
    customised widget selection.
    """

    pkey_widget = None
    fkey_widget = None
    name_widgets = {}
    type_widgets = {}    
    default_widget = None

    @classmethod
    def factory(cls, column, rel):
        if rel:
            if cls.fkey_widget:
                return cls.fkey_widget(id=rel.key, entity=rel.mapper.class_)
            else:
                return None
        elif column.primary_key:
            widget = cls.pkey_widget
        elif column.name in cls.name_widgets:
            widget = cls.name_widgets[column.name]
        else:
            for t in cls.type_widgets:
                if isinstance(column.type, t):
                    widget = cls.type_widgets[t]
                    break
            else:
                if cls.default_widget:
                    widget = cls.default_widget
                else:
                    raise twc.WidgetError("Cannot automatically create a widget for '%s'" % column.name)
        if widget:
            if column.nullable:
                widget = widget(id=column.name)
            else:
                widget = widget(id=column.name, validator=twc.Required)        
        return widget


class ViewPolicy(WidgetPolicy):
    """Base WidgetPolicy for viewing data."""
    fkey_widget = twf.LabelField
    default_widget = twf.LabelField


class EditPolicy(WidgetPolicy):
    """Base WidgetPolicy for editing data."""
    fkey_widget = DbSingleSelectField
    name_widgets = {
        'password':     twf.PasswordField,
        'email':        twf.TextField(validator=twc.EmailValidator),
        'ipaddress':    twf.TextField(validator=twc.IpAddressValidator),
    }
    type_widgets = {
        sat.String:     twf.TextField,
        sat.Integer:    twf.TextField(validator=twc.IntValidator),
        sat.DateTime:   twd.CalendarDateTimePicker,
        sat.Date:       twd.CalendarDatePicker,
        sat.Binary:     twf.FileField,
        sat.Boolean:    twf.CheckBox,
    }


class AutoContainer(twc.Widget):
    """
    An AutoContainer has its children automatically created from an SQLAlchemy entity,
    using a widget policy.
    """
    entity = twc.Param('SQLAlchemy mapped class to use', request_local=False)
    policy = twc.Param('WidgetPolicy to use')
    
    @classmethod
    def post_define(cls):
        if not hasattr(cls, 'entity') and hasattr(cls, 'parent') and hasattr(cls.parent, 'entity'):            
            try:
                prop = sa.orm.class_mapper(cls.parent.entity).get_property(cls.id)
            except sa.exc.InvalidRequestError:
                prop = None
            if isinstance(prop, sa.orm.RelationshipProperty):
                cls.entity = prop.mapper.class_
            else:
                cls.entity = cls.parent.entity                        
        if hasattr(cls, 'entity') and not getattr(cls, '_auto_widgets', False):
            cls._auto_widgets = True
            if hasattr(cls.child, '_orig_children'):
                orig_children = cls.child._orig_children
            elif hasattr(cls.child, 'children'):
                orig_children = cls.child.children
                cls.child._orig_children = orig_children
            else:
                orig_children = []
            new_children = []
            fkey = dict((p.local_side[0].name, p) 
                        for p in sa.orm.class_mapper(cls.entity).iterate_properties 
                        if isinstance(p, sa.orm.RelationshipProperty) 
                            and p.direction.name == 'MANYTOONE'
                            and len(p.local_side) == 1)
            used_children = set()
            for col in table_for(cls.entity).columns:                
                widget_name = col.name in fkey and fkey[col.name].key or col.name
                if hasattr(orig_children, widget_name):
                    new_children.append(getattr(orig_children, widget_name))
                    used_children.add(widget_name)
                else:
                    new_widget = cls.policy.factory(col, fkey.get(col.name))
                    if new_widget:
                        new_children.append(new_widget)
            for widget in orig_children:
                if widget.id not in used_children:
                    new_children.append(widget)            
            cls.child = cls.child(children=new_children, entity=cls.entity)


class AutoTableForm(AutoContainer, twf.TableForm):
    policy = EditPolicy

class AutoGrowingGrid(twd.GrowingGridLayout, AutoContainer):
    policy = EditPolicy

class AutoViewGrid(AutoContainer, twf.GridLayout):
    policy = ViewPolicy


class AutoListPageEdit(DbListPage):
    _no_autoid = True
    class child(AutoViewGrid):
        pass
    class edit(DbFormPage):
        _no_autoid = True
        child = AutoTableForm


# Borrowed from TG2
def commit_veto(environ, status, headers):
    """Veto a commit.

    This hook is called by repoze.tm in case we want to veto a commit
    for some reason. Return True to force a rollback.

    By default we veto if the response's status code is an error code.
    Override this method, or monkey patch the instancemethod, to fine
    tune this behaviour.

    """
    return not 200 <= int(status.split(None, 1)[0]) < 400

def transactional_session():
    """Return an SQLAlchemy scoped_session. If called from a script, use ZopeTransactionExtension so the session is integrated with repoze.tm. The extention is not enabled if called from the interactive interpreter."""
    return sa.orm.scoped_session(sa.orm.sessionmaker(autoflush=True, autocommit=False,
            extension=sys.argv[0] and ZopeTransactionExtension() or None))
