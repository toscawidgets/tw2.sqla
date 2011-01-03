import sqlalchemy as sa

def from_dict(entity, data, session=None):
    """
    Update a mapped class with data from a JSON-style nested dict/list
    structure.
    Adapted from elixir.entity
    """

    # surrogate can be guessed from autoincrement/sequence but I guess
    # that's not 100% reliable, so we'll need an override

    mapper = sa.orm.object_mapper(entity)
    add = False

    pk_props = mapper.primary_key
    if [1 for p in pk_props if p.key in data and data[p.key]]:
        # If all of our primary keys are present and non-empty, then load.
        kw = dict([(p.key, data[p.key]) for p in pk_props])
        entity = entity.query.filter_by(**kw).one()
    else:
        # If any primary keys were specified as empty, ditch 'em.
        # This happens with ``id = tw2.forms.HiddenField``
        for p in pk_props:
            if p.key in data and not data[p.key]:
                del data[p.key]
        add = True
    
    if hasattr(entity, 'from_dict'):
        # If `entity` is an Elixir entity, then we can just use their method
        entity.from_dict(data)
        return entity

    for key, value in data.iteritems():
        if isinstance(value, dict):
            dbvalue = getattr(entity, key)
            rel_class = mapper.get_property(key).mapper.class_
            pk_props = rel_class.__mapper__.primary_key

            if not [1 for p in pk_props if p.key in data] and \
               dbvalue is not None:
                dbvalue = from_dict(dbvalue, value, session=session)
            else:
                record = update_or_create(rel_class, value, session=session)
                setattr(entity, key, record)
        elif isinstance(value, list) and \
             value and isinstance(value[0], dict):

            rel_class = mapper.get_property(key).mapper.class_
            new_attr_value = []
            for row in value:
                if not isinstance(row, dict):
                    raise Exception(
                            'Cannot send mixed (dict/non dict) data '
                            'to list relationships in from_dict data.')
                record = update_or_create(rel_class, row, session=session)
                new_attr_value.append(record)
            setattr(entity, key, new_attr_value)
        else:
            setattr(entity, key, value)
    if add and session:
        session.add(entity)
    return entity

def update_or_create(cls, data, session=None):
    """
    Adapted from elixir.entity
    """
    
    if hasattr(cls, 'update_or_create'):
        cls.update_or_create(data)
        return cls

    pk_props = cls.__mapper__.primary_key
    add = False
    # if all pk are present
    if not [1 for p in pk_props if data.get(p.key) is None]:
        pk_tuple = tuple([data[prop.key] for prop in pk_props])
        record = cls.query.get(pk_tuple)
        if record is None:
            raise Exception("cannot create with pk")
    else:
        add = True
        record = cls()
    record = from_dict(record, data, session=session)
    if add:
        session.add(record)
    return record
