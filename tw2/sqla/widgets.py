import tw2.core as twc, tw2.forms as twf, webob, sqlalchemy as sa, sys
import sqlalchemy.types as sat, tw2.dynforms as twd
from zope.sqlalchemy import ZopeTransactionExtension
import transaction

from itertools import product

from tw2.sqla.utils import from_dict

def table_for(entity):
    mapper = sa.orm.class_mapper(entity)
    if len(mapper.tables) != 1:
        raise twc.WidgetError('Can only act on entities that map to a single table')
    return mapper.tables[0]

def is_manytoone(prop):
    return isinstance(prop, sa.orm.RelationshipProperty) and \
            prop.direction.name == 'MANYTOONE'

def is_onetomany(prop):
    return isinstance(prop, sa.orm.RelationshipProperty) and \
            prop.direction.name == 'ONETOMANY'


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
        if not value:
            return value
        if not isinstance(value, self.entity):
            raise twc.ValidationError(
                'from_python not passed instance of self.entity but ' +
                'instead "%s" of type "%s".' % (str(value), str(type(value))))
        return value and unicode(sa.orm.object_mapper(value).primary_key_from_instance(value)[0])


class DbFormPage(twf.FormPage):
    entity = twc.Param('SQLAlchemy mapped class to use', request_local=False)
    redirect = twc.Param('Location to redirect to after successful POST', request_local=False)
    _no_autoid = True

    @classmethod
    def post_define(cls):
        if hasattr(cls, 'entity') and not hasattr(cls, 'title'):
            cls.title = twc.util.name2label(cls.entity.__name__)

    def fetch_data(self, req):
        self.value = req.GET and self.entity.query.filter_by(**req.GET.mixed()).first() or None

    @classmethod
    def validated_request(cls, req, data):
        if req.GET:
            v = cls.entity.query.filter_by(**req.GET.mixed()).first()
        else:
            v = cls.entity()

        session = None
        if not hasattr(v, 'from_dict'):
            try:
                import pylons
                if not 'DBSession' in pylons.configuration.config:
                    raise KeyError, 'pylons config must contain a DBSession'
                session = pylons.configuration.config['DBSession']
            except ImportError:
                pass
        
        if not session and not hasattr(v, 'from_dict'):
            raise NotImplementedError, "Neither elixir nor pylons"

        v = from_dict(v, data, session=session)
        transaction.commit()

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
                cls.title = twc.util.name2label(cls.entity.__name__)

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

class DbRadioButtonList(DbSelectionField, twf.RadioButtonList):
    @classmethod
    def post_define(cls):
        if getattr(cls, 'entity', None):
            cls.item_validator = RelatedValidator(entity=cls.entity)

class DbCheckBoxTable(DbSelectionField, twf.CheckBoxTable):
    @classmethod
    def post_define(cls):
        if getattr(cls, 'entity', None):
            cls.item_validator = RelatedValidator(entity=cls.entity)


class WidgetPolicy(object):
    """
    A policy object is used to generate widgets from SQLAlchemy properties. 
    
    In general, the widget's id is set to the name of the property, and if the
    property is not nullable, the validator is set as required. If the desired
    widget is None, then no widget is used for that property.
    
    Several parameters can be overridden to select the widget to use:
    
    `pkey_widget`
        For primary key properties
     
    `onetomany_widget`
        For foreign key properties. In this case the widget's id is set to the
        name of the relation, and its entity is set to the target class.
    
    `manytoone_widget`
        For foreign key properties. In this case the widget's id is set to the
        name of the relation, and its entity is set to the target class.
        
    `name_widgets`
        A dictionary mapping property names to the desired widget. This can be 
        used for names like "password" or "email".
    
    `type_widgets`
        A dictionary mapping SQLAlchemy property types to the desired widget.
        
    `default_widget`
        If the property does not match any of the other selectors, this is used.
        If this is None then an error is raised for properties that do not match.

    Alternatively, the `factory` method can be overriden to provide completely
    customised widget selection.
    """

    pkey_widget = None
    onetomany_widget = None
    manytoone_widget = None
    name_widgets = {}
    type_widgets = {}    
    default_widget = None

    @classmethod
    def factory(cls, prop):
        widget = None
        if is_onetomany(prop):
            if not cls.onetomany_widget:
                raise twc.WidgetError(
                    "Cannot automatically create a widget " +
                    "for one-to-many relation '%s'" % prop.key)
            widget = cls.onetomany_widget(id=prop.key,entity=prop.mapper.class_)
        elif sum([c.primary_key for c in getattr(prop, 'columns', [])]):
            widget = cls.pkey_widget
        elif is_manytoone(prop):
            if not cls.manytoone_widget:
                raise twc.WidgetError(
                    "Cannot automatically create a widget " +
                    "for many-to-one relation '%s'" % prop.key)
            widget = cls.manytoone_widget(id=prop.key,entity=prop.mapper.class_)
        elif prop.key in cls.name_widgets:
            widget = cls.name_widgets[prop.key]
        else:
            for t, c in product(cls.type_widgets,
                                getattr(prop, 'columns', [])):
                if isinstance(c.type, t):
                    widget = cls.type_widgets[t]
                    break
            else:
                if not cls.default_widget:
                    raise twc.WidgetError(
                        "Cannot automatically create a widget " +
                        "for '%s'" % prop.key)
                widget = cls.default_widget

        if widget:
            args = {'id': prop.key}            
            if not sum([c.nullable for c in getattr(prop, 'columns', [])]):
                args['validator'] = twc.Required
            
            widget = widget(**args)

            # TODO - to be determined.  Why is this line necessary?
            # Without it, some tests fail that shouldn't.
            widget.display()

        return widget


class NoWidget(twc.Widget):
    pass


class ViewPolicy(WidgetPolicy):
    """Base WidgetPolicy for viewing data."""
    manytoone_widget = twf.LabelField
    default_widget = twf.LabelField

    ## This gets assigned further down in the file.  It must, because of an
    ## otherwise circular dependency.  
    #onetomany_widget = AutoViewGrid


class EditPolicy(WidgetPolicy):
    """Base WidgetPolicy for editing data."""
    # TODO -- actually set this to something sensible
    onetomany_widget = DbSingleSelectField
    manytoone_widget = DbSingleSelectField
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
                        if is_manytoone(p))
            used_children = set()

            for prop in sa.orm.class_mapper(cls.entity).iterate_properties:
                if is_manytoone(prop):
                    continue

                # Swap ids and objs
                prop = fkey.get(prop.key, prop)

                widget_name = prop.key
                if isinstance(prop, sa.orm.RelationshipProperty):
                    widget_name = prop.local_side[0].name

                matches = [w for w in orig_children if w.key == widget_name]
                widget = len(matches) and matches[0] or None
                if widget:
                    if not issubclass(widget, NoWidget):
                        new_children.append(widget)
                    used_children.add(widget_name)
                else:
                    new_widget = cls.policy.factory(prop)
                    if new_widget:
                        new_children.append(new_widget)
            
            def child_filter(w):
                return w.key not in used_children and \
                       w.key not in [W.key for W in new_children]

            new_children.extend(filter(child_filter, orig_children))
            cls.child = cls.child(children=new_children, entity=cls.entity)


class AutoTableForm(AutoContainer, twf.TableForm):
    policy = EditPolicy

class AutoGrowingGrid(twd.GrowingGridLayout, AutoContainer):
    policy = EditPolicy

class AutoViewGrid(AutoContainer, twf.GridLayout):
    policy = ViewPolicy

# This is assigned here and not above because of a circular dep.
ViewPolicy.onetomany_widget = AutoViewGrid

class AutoListPage(DbListPage):
    _no_autoid = True
    class child(AutoViewGrid):
        pass

class AutoListPageEdit(AutoListPage):
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
