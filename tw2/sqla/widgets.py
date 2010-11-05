import tw2.core as twc, tw2.forms as twf, webob, sqlalchemy as sa, sys
import sqlalchemy.types as sat, tw2.dynforms as twd
from zope.sqlalchemy import ZopeTransactionExtension
import transaction

from tw2.sqla.utils import from_dict

class RelatedValidator(twc.IntValidator):
    """Validator for related object
    
    `entity`
        The SQLAlchemy class to use. This map to a single table with a single primary key column.
        It must also have the SQLAlchemy `query` property; this will be the case for Elixir classes,
        and DeclarativeBase depending on configuration.
    """
    msgs = {
        'norel': 'No related object found',
    }
    
    def __init__(self, entity, **kw):
        super(RelatedValidator, self).__init__(**kw)
        mapper = sa.orm.class_mapper(entity)
        if len(mapper.tables) != 1:
            raise twc.WidgetError('RelatedValidator can only act on entities that map to a single table')
        cols = list(mapper.tables[0].primary_key.columns)
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
            cls.title = twc.util.name2label(cls.entity.table.name)

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
                cls.title = twc.util.name2label(cls.entity.table.name)
            if hasattr(cls, 'edit'):
                cls.edit = cls.edit(redirect=cls._gen_compound_id(for_url=True), entity=cls.entity, id=cls.id+'_edit')
                cls.newlink = twf.LinkField(link=cls.edit._gen_compound_id(for_url=True), text='New', value=1)
                class mypol(cls.child.policy):
                    pkey_widget = twf.LinkField(text='$', link=cls.id+'_edit?id=$')
                cls.child = cls.child(policy=mypol)

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
    A policy object is used to generate widgets from SQLAlchemy columns
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
        if hasattr(cls, 'entity'):
            cl = getattr(cls.child, 'children', None)
            ncld = []
            fkey = dict((p.local_side[0].name, p) 
                        for p in sa.orm.class_mapper(cls.entity).iterate_properties 
                        if isinstance(p, sa.orm.RelationshipProperty) 
                            and p.direction.name == 'MANYTOONE'
                            and len(p.local_side) == 1)
            for c in cls.entity.table.columns:
                if cl:
                    w = getattr(cl, c.name, None)
                if cl and w:
                    ncld.append(w)
                else:
                    nw = cls.policy.factory(c, fkey.get(c.name))
                    if nw:
                        ncld.append(nw)
            cls.child = cls.child(children=ncld)


class TableFormPolicy(WidgetPolicy):
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
    
class AutoTableForm(AutoContainer, twf.TableForm):
    policy = TableFormPolicy


class ViewGridPolicy(WidgetPolicy):
    fkey_widget = twf.LabelField
    default_widget = twf.LabelField

class AutoViewGrid(AutoContainer, twf.GridLayout):
    policy = ViewGridPolicy


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
