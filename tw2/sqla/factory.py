import tw2.core as twc, tw2.forms as twf, sqlalchemy as sa, sys
import sqlalchemy.types as sat, tw2.dynforms as twd
from widgets import *
from utils import (
    is_relation,
    is_onetoone,
    is_manytomany,
    is_manytoone,
    is_onetomany,
)
import compat


try:
    from itertools import product
except ImportError:
    # Python 2.5 support
    def product(x, y):
        for i in x:
            for j in y:
                yield (i,j)

def sort_properties(localname_from_relationname, localname_creation_order):
    """Returns a function which will sort the SQLAlchemy properties
    """
    def sort_func(prop1, prop2):
        """Sort the given SQLAlchemy properties

        Logic: 1) Column
               2) many to many
               3) one to one

        When a relation has a column on the local side, we put the relation at
        the place of the column.
        """
        weight1 = 0
        weight2 = 0
        if is_onetoone(prop1):
            weight1 += 2
        if is_onetoone(prop2):
            weight2 += 2
        if is_manytomany(prop1):
            weight1 += 1
        if is_manytomany(prop2):
            weight2 += 1
        
        res = cmp(weight1, weight2)
        if res != 0:
            return res

        # If the prop is a relation we try to use the db column creation order
        key1 = localname_from_relationname.get(prop1.key, prop1.key)
        key2 = localname_from_relationname.get(prop2.key, prop2.key)
        creation_order1 = localname_creation_order.get(key1, prop1._creation_order)
        creation_order2 = localname_creation_order.get(key2, prop2._creation_order)
        return cmp(creation_order1, creation_order2)
    return sort_func

def required_widget(prop):
    """Returns bool

    Returns True if the widget corresponding to the given prop should be required
    """
    is_nullable = lambda prop: sum([c.nullable for c in getattr(prop, 'columns', [])])

    if not is_relation(prop):
        if not is_nullable(prop):
            return True
        return False

    if not is_manytoone(prop) and not is_onetoone(prop):
        return False

    localname = compat.local_name(prop)
    # If the local field is required, the relation should be required
    pkey = dict([(p.key, is_nullable(p)) for p in prop.parent.iterate_properties])
    return not pkey.get(localname, True)

def get_reverse_property_name(prop):
    """Returns the reverse property name of the given prop
    """
    if not prop._reverse_property:
        return None
    
    assert len(prop._reverse_property) == 1
    return list(prop._reverse_property)[0].key
    
    
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

    `onetoone_widget`
        For foreign key properties. In this case the widget's id is set to the
        name of the relation, and its entity is set to the target class.
        The relation is just one entity object, not a list like in onetomany.

    `name_widgets`
        A dictionary mapping property names to the desired widget. This can be
        used for names like "password" or "email".

    `type_widgets`
        A dictionary mapping SQLAlchemy property types to the desired widget.

    `default_widget`
        If the property does not match any of the other selectors, this is used.
        If this is None then an error is raised for properties that do not match.

    `add_edit_link`
        Boolean. If True and tws_edit_link is defined as param on the class, we
        add a link to edit this object.

    Alternatively, the `factory` method can be overriden to provide completely
    customised widget selection.
    """

    pkey_widget = None
    onetomany_widget = None
    manytoone_widget = None
    onetoone_widget = None
    name_widgets = {}
    type_widgets = {}
    default_widget = None
    hint_name = None
    add_edit_link = False

    @classmethod
    def factory(cls, prop):
        widget = None
        cols = getattr(prop, 'columns', [])
        if is_onetomany(prop):
            if not cls.onetomany_widget:
                raise twc.WidgetError(
                    "Cannot automatically create a widget " +
                    "for one-to-many relation '%s'" % prop.key)
            prop_cls = prop.mapper.class_
            edit_link = getattr(prop_cls, 'tws_edit_link', None)
            params = {}
            if cls.add_edit_link:
                params['link'] = edit_link
            widget = cls.onetomany_widget(
                id=prop.key,
                entity=prop_cls,
                **params)
        elif sum([c.primary_key for c in getattr(prop, 'columns', [])]):
            widget = cls.pkey_widget
        elif is_manytoone(prop):
            if not cls.manytoone_widget:
                raise twc.WidgetError(
                    "Cannot automatically create a widget " +
                    "for many-to-one relation '%s'" % prop.key)
            widget = cls.manytoone_widget(id=prop.key,entity=prop.mapper.class_)
        elif is_manytomany(prop):
            # Use the same widget as onetomany
            if not cls.onetomany_widget:
                raise twc.WidgetError(
                    "Cannot automatically create a widget " +
                    "for many-to-many relation '%s'" % prop.key)
            prop_cls = prop.mapper.class_
            edit_link = getattr(prop_cls, 'tws_edit_link', None)
            params = {}
            if cls.add_edit_link:
                params['link'] = edit_link
            widget = cls.onetomany_widget(
                id=prop.key,
                entity=prop_cls,
                reverse_property_name=get_reverse_property_name(prop),
                **params
            )
        elif is_onetoone(prop):
            if not cls.onetoone_widget:
                raise twc.WidgetError(
                    "Cannot automatically create a widget " +
                    "for one-to-one relation '%s'" % prop.key)
            required = required_widget(prop)
            widget = cls.onetoone_widget(
                        id=prop.key,
                        entity=prop.mapper.class_,
                        required=required,
                        reverse_property_name=get_reverse_property_name(prop),
                        required_on_parent=(not required),
                    )
        elif prop.key in cls.name_widgets:
            widget = cls.name_widgets[prop.key]        
        elif cols and cls.hint_name and cls.hint_name in cols[0].info:
            if not issubclass(cols[0].info[cls.hint_name], NoWidget):
                widget = cols[0].info[cls.hint_name]
        else:            
            for t, c in product(cls.type_widgets, cols):
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
            if required_widget(prop):
                args['validator'] = twc.Required
            widget = widget(**args)

        return widget


class NoWidget(twc.Widget):
    pass


class ViewPolicy(WidgetPolicy):
    """Base WidgetPolicy for viewing data."""
    hint_name = 'view_widget'
    manytoone_widget = twf.LabelField
    default_widget = twf.LabelField
    add_edit_link = True

    ## This gets assigned further down in the file.  It must, because of an
    ## otherwise circular dependency.
    #onetomany_widget = DbListLinkField
    #onetoone_widget = AutoViewGrid


class EditPolicy(WidgetPolicy):
    """Base WidgetPolicy for editing data."""
    # TODO -- actually set this to something sensible
    hint_name = 'edit_widget'
    onetomany_widget = DbCheckBoxList
    manytoone_widget = DbSingleSelectField

    ## This gets assigned further down in the file.  It must, because of an
    ## otherwise circular dependency.
    #onetoone_widget = AutoEditGrid
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
        if not getattr(cls, 'entity', None) and getattr(cls.parent, 'entity', None):
            cls.entity = cls.parent.entity

        if getattr(cls, 'entity', None) and not getattr(cls, '_auto_widgets', False):
            cls._auto_widgets = True
            fkey = dict((compat.local_name(p), p)
                        for p in sa.orm.class_mapper(cls.entity).iterate_properties
                        if is_manytoone(p) or is_onetoone(p))

            new_children = []
            used_children = set()
            orig_children = getattr(cls.child, 'children', [])
            
            mapper = sa.orm.class_mapper(cls.entity)
            properties = mapper._props.values()
            localname_from_relationname = dict((p.key, compat.local_name(p))
                    for p in mapper.iterate_properties
                    if is_manytoone(p) or is_onetoone(p))
            localname_creation_order =  dict((p.key, p._creation_order)
                    for p in mapper.iterate_properties
                    if not is_relation(p))
            
            properties.sort(sort_properties(localname_from_relationname,
                localname_creation_order))
            reverse_property_name = getattr(cls, 'reverse_property_name', None)
            for prop in properties:

                # Swap ids and objs
                if fkey.get(prop.key):
                    continue

                if prop.key == reverse_property_name:
                    # Avoid circular loop for the one to one relation
                    continue

                widget_name = prop.key
                if isinstance(prop, sa.orm.RelationshipProperty):
                    widget_name = compat.local_name(prop)

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

            edit_link = getattr(cls.entity, 'tws_edit_link', None)
            if cls.policy.add_edit_link and edit_link:
                new_children += [DbLinkField('edit', text='edit',
                                         entity=cls.entity,
                                         link=edit_link)]
            def child_filter(w):
                return w.key not in used_children and \
                       w.key not in [W.key for W in new_children]

            new_children.extend(filter(child_filter, orig_children))

            cls.required_children = []
            if getattr(cls, 'required_on_parent', False):
                for c in new_children:
                    if c.validator.required:
                        cls.required_children += [c]
                        c.validator.required = False
            cls.child = cls.child(children=new_children, entity=cls.entity)


class AutoTableForm(AutoContainer, twf.TableForm):
    policy = EditPolicy

class AutoGrowingGrid(twd.GrowingGridLayout, AutoContainer):
    policy = EditPolicy

class AutoViewGrid(AutoContainer, twf.GridLayout):
    policy = ViewPolicy

class AutoViewFieldSet(AutoContainer, twf.TableFieldSet):
    policy = ViewPolicy

class AutoEditFieldSet(AutoContainer, twf.TableFieldSet):
    policy = EditPolicy

    @classmethod
    def post_define(cls):
        if getattr(cls, 'entity', None):
            required = getattr(cls, 'required', False)
            required_children = getattr(cls, 'required_children', None)
            cls.validator = RelatedOneToOneValidator(
                entity=cls.entity,
                required=required,
                required_children=required_children)

# This is assigned here and not above because of a circular dep.
ViewPolicy.onetomany_widget = DbListLinkField
ViewPolicy.onetoone_widget = twf.LabelField
EditPolicy.onetoone_widget = AutoEditFieldSet

class AutoListPage(DbListPage):
    _no_autoid = True
    class child(AutoViewGrid):
        pass

class AutoListPageEdit(AutoListPage):
    class edit(DbFormPage):
        _no_autoid = True
        child = AutoTableForm
