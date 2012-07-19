import tw2.core as twc, tw2.forms as twf, webob, sqlalchemy as sa, sys
import sqlalchemy.types as sat, tw2.dynforms as twd
from zope.sqlalchemy import ZopeTransactionExtension
import transaction, utils


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

    def __init__(self, entity, required=False, **kw):
        super(RelatedValidator, self).__init__(**kw)
        cols = sa.orm.class_mapper(entity).primary_key
        if len(cols) != 1:
            raise twc.WidgetError('RelatedValidator can only act on tables that have a single primary key column')
        self.entity = entity
        self.primary_key = cols[0]
        self.required=required

    def to_python(self, value, state=None):
        if not value:
            if self.required:
                raise twc.ValidationError('required', self)
            return None

        # How could this happen (that we are already to_python'd)?
        if isinstance(value, self.entity):
            return value

        if isinstance(self.primary_key.type, sa.types.Integer):
            try:
                value = int(value)
            except ValueError:
                raise twc.ValidationError('norel', self)
        value = self.entity.query.filter(getattr(self.entity, self.primary_key.name)==value).first()
        if not value:
            raise twc.ValidationError('norel', self)
        return value

    def from_python(self, value, state=None):
        if not value:
            return value
        if not isinstance(value, self.entity):
            raise twc.ValidationError(
                'from_python not passed instance of self.entity but ' +
                'instead "%s" of type "%s".' % (str(value), str(type(value))))
        return value and unicode(sa.orm.object_mapper(value).primary_key_from_instance(value)[0])


class RelatedItemValidator(twc.Validator):
    """Validator for related object

    `entity`
        The SQLAlchemy class to use. This must be mapped to a single table with a single primary key column.
        It must also have the SQLAlchemy `query` property; this will be the case for Elixir classes,
        and can be specified using DeclarativeBase (and is in the TG2 default setup).

    This validator is used to make sure at least one value of the list is defined.
    """

    def __init__(self, entity, required=False, **kw):
        super(RelatedItemValidator, self).__init__(**kw)
        self.required=required
        self.entity = entity
        self.item_validator = RelatedValidator(entity=self.entity)

    def to_python(self, value, state=None):
        value = [twc.safe_validate(self.item_validator, v) for v in value]
        value = [v for v in value if v is not twc.Invalid]
        if not value and self.required:
            raise twc.ValidationError('required', self)
        return value

    def from_python(self, value, state=None):
        return value

class RelatedOneToOneValidator(twc.Validator):
    """Validator for related object

    `entity`
        The SQLAlchemy class to use. This must be mapped to a single table with a single primary key column.
        It must also have the SQLAlchemy `query` property; this will be the case for Elixir classes,
        and can be specified using DeclarativeBase (and is in the TG2 default setup).

    This validator should be used for the one to one relation.
    """

    def __init__(self, entity, required=False, **kw):
        super(RelatedOneToOneValidator, self).__init__(**kw)
        self.required=required
        self.entity = entity

    def to_python(self, value, state=None):
        """We just validate, there is at least one value
        """
        def has_value(dic):
            """Returns bool

            Returns True if there is at least one value defined in the given
            dic
            """
            for v in dic.values():
                if type(v) == dict:
                    if has_value(v):
                        return True
                if v:
                    return True
            return False
        
        if self.required:
            if not has_value(value):
                raise twc.ValidationError('required', self)
        return value

    def from_python(self, value, state=None):
        return value


class DbPage(twc.Page):
    entity = twc.Param('SQLAlchemy mapped class to use', request_local=False)
    _no_autoid = True
    @classmethod
    def post_define(cls):
        if hasattr(cls, 'entity') and not hasattr(cls, 'title'):
            cls.title = twc.util.name2label(cls.entity.__name__)

class DbFormPage(DbPage, twf.FormPage):
    """
    A page that contains a form with database synchronisation. The `fetch_data` method loads a record
    from the database, based on the primary key in the URL (no parameters for a new record). The
    `validated_request` method saves the data to the database.
    """
    redirect = twc.Param('Location to redirect to after successful POST', request_local=False)
    _no_autoid = True

    def fetch_data(self, req):
        data = req.GET.mixed()
        filter = dict((col.name, data.get(col.name))
                        for col in sa.orm.class_mapper(self.entity).primary_key)
        self.value = req.GET and self.entity.query.filter_by(**filter).first() or None

    @classmethod
    def validated_request(cls, req, data, protect_prm_tamp=True, do_commit=True):
        if 'id' not in data and 'id' in req.GET:
            # If the 'id' is in the query string, we get it
            data['id'] = req.GET['id']
        utils.update_or_create(cls.entity, data,
                               protect_prm_tamp=protect_prm_tamp)
        if do_commit:
            transaction.commit()

        if hasattr(cls, 'redirect'):
            return webob.Response(request=req, status=302, location=cls.redirect)
        else:
            return super(DbFormPage, cls).validated_request(req, data)


class DbListForm(DbPage, twf.FormPage):
    """
    A page that contains a list form with database synchronisation. The `fetch_data` method loads a full
    table from the database. The `validated_request` method saves the data to the database.
    """
    redirect = twc.Param('Location to redirect to after successful POST', request_local=False)
    _no_autoid = True

    def fetch_data(self, req):
        self.value = self.entity.query.all()
        
    @classmethod
    def validated_request(cls, req, data, protect_prm_tamp=True, do_commit=True):
        utils.from_list(cls.entity, cls.entity.query.all(), data,
                        force_delete=True, protect_prm_tamp=protect_prm_tamp)
        if do_commit:
            transaction.commit()

        if hasattr(cls, 'redirect'):
            return webob.Response(request=req, status=302, location=cls.redirect)
        else:
            return super(DbListForm, cls).validated_request(req, data)


class DbListPage(DbPage, twc.Page):
    """
    A page that contains a list with database synchronisation. The `fetch_data` method loads a full
    table from the database; there is no submit or write capability.    
    """
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


# Note: this does not inherit from LinkField, as few of the parameters apply
class DbLinkField(twc.Widget):
    template = "tw2.forms.templates.link_field"
    link = twc.Param('Path to link to')
    entity = twc.Param('SQLAlchemy mapped class to use', request_local=False)
    
    def prepare(self):
        super(DbLinkField, self).prepare()
        if self.value:
            qs = '&'.join(col.name + "=" + getattr(self.value, col.name)
                                for col in sa.orm.class_mapper(self.entity).primary_key)
        else:
            qs = ''
        self.safe_modify('attrs')
        self.attrs['href'] = self.link + '?' + qs
        self.text = unicode(self.value or '')


class DbSelectionField(twf.SelectionField):
    entity = twc.Param('SQLAlchemy mapped class to use', request_local=False)


class DbSingleSelectionField(DbSelectionField):
    def prepare(self):
        self.options = [(getattr(x, self.validator.primary_key.name), unicode(x)) for x in self.entity.query.all()]
        super(DbSingleSelectionField, self).prepare()

    @classmethod
    def post_define(cls):
        if getattr(cls, 'entity', None):
            required=getattr(cls, 'required', False)
            cls.validator = RelatedValidator(entity=cls.entity, required=required)


class DbMultipleSelectionField(DbSelectionField):
    def prepare(self):
        self.options = [(getattr(x, self.item_validator.primary_key.name), unicode(x)) for x in self.entity.query.all()]
        super(DbMultipleSelectionField, self).prepare()

    @classmethod
    def post_define(cls):
        if getattr(cls, 'entity', None):
            required=getattr(cls, 'required', False)
            cls.validator = RelatedItemValidator(required=required, entity=cls.entity)
            # We should keep item_validator to make sure the values are well transformed.
            cls.item_validator = RelatedValidator(entity=cls.entity)


class DbSingleSelectField(DbSingleSelectionField, twf.SingleSelectField):
    pass

class DbRadioButtonList(DbSingleSelectionField, twf.RadioButtonList):
    pass

class DbCheckBoxList(DbMultipleSelectionField, twf.CheckBoxList):
    pass
    
class DbCheckBoxTable(DbMultipleSelectionField, twf.CheckBoxTable):
    pass


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
