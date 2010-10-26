import tw2.core as twc, tw2.forms as twf, webob, sqlalchemy as sa, sys
import sqlalchemy.types as sat, tw2.dynforms as twd
from zope.sqlalchemy import ZopeTransactionExtension
import transaction

from tw2.sqla.utils import from_dict

class RelatedValidator(twc.IntValidator):
    """Validator for related object
    
    `entity`
        The SQLAlchemy class to use. This must have a single primary key column.
    """
    msgs = {
        'norel': 'No related object found',
    }
    
    def __init__(self, entity, **kw):
        super(RelatedValidator, self).__init__(**kw)
        tableattr = ['table', '__table__'][hasattr(entity, '__table__')]
        cols = getattr(entity, tableattr).primary_key.columns
        if len(cols) != 1:
            raise twc.WidgetError('RelatedValidator can only act on tables that have a single primary key column')
        self.entity = entity
        self.int = isinstance(list(cols)[0].type, sa.types.Integer)
        
    def to_python(self, value):
        if not value:
            return None
        if self.int:
            try:
                value = int(value)
            except ValueError:
                raise twc.ValidationError('norel', self)
        if hasattr(self.entity, 'get'):
            value = self.entity.get(value)
        else:
            tableattr = ['table', '__table__'][hasattr(self.entity,
                                                       '__table__')]
            col = getattr(self.entity, tableattr).primary_key.columns.keys()[0]
            value = self.entity.query.filter(
                getattr(self.entity, col)==value).one()
        if not value:
            raise twc.ValidationError('norel', self)
        return value

    def from_python(self, value):
        return value and unicode(value.mapper.primary_key_from_instance(value)[0])


class DbFormPage(twf.FormPage):
    entity = twc.Param('SQLAlchemy mapped class to use', request_local=False)
    redirect = twc.Param('Location to redirect to after successful POST', request_local=False)
    _no_autoid = True

    def fetch_data(self, req):
        self.value = req.GET and self.entity.query.filter_by(**req.GET.mixed()).first() or None

    @classmethod
    def validated_request(cls, req, data):
        if req.GET:
            v = cls.entity.query.filter_by(**req.GET.mixed()).first()
        else:
            print "Creating..."
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
            v = from_dict(v, data)
            # TBD what about setups with multiple engines and sessions?
            pylons.configuration.config['DBSession'].add(v)
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


class AutoField(object):

    name_mapping = {
        'password':     twf.PasswordField,
        'email':        twf.TextField(validator=twc.EmailValidator),
        'ipaddress':    twf.TextField(validator=twc.IpAddressValidator),
    }

    type_mapping = {
        sat.String:     twf.TextField,
        sat.Integer:    twf.TextField(validator=twc.IntValidator),
        sat.DateTime:   twd.CalendarDateTimePicker,
        sat.Date:       twd.CalendarDatePicker,
        sat.Binary:     twf.FileField,
        sat.Boolean:    twf.CheckBox,
    }

    def factory(self, column):
        if column.name in self.name_mapping:
            widget = self.name_mapping[column.name]
        else:
            for t in self.type_mapping:
                if isinstance(column.type, t):
                    widget = self.type_mapping[t]
            else:
                raise twc.WidgetError("Cannot automatically create a widget for '%s'" % column.name)
        if column.nullable:
            widget = widget(id=column.name)
        else:
            widget = widget(id=column.name, validator=twc.Required)        
        return widget


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
