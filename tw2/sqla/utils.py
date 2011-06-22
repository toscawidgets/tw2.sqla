import sqlalchemy as sa

def from_dict(entity, data):
    """
    Update a mapped class with data from a JSON-style nested dict/list
    structure.
    Adapted from elixir.entity
    """

    mapper = sa.orm.object_mapper(entity)

    pk_props = mapper.primary_key
    for p in pk_props:
        data.pop(p.key, None)

    for key, value in data.iteritems():
        if isinstance(value, dict):
            rel_class = mapper.get_property(key).mapper.class_
            record = update_or_create(rel_class, value)
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
                record = update_or_create(rel_class, row)
                new_attr_value.append(record)
            setattr(entity, key, new_attr_value)
        else:
            setattr(entity, key, value)
    return entity

def update_or_create(cls, data):
    """
    Adapted from elixir.entity
    """

    try:
        session = cls.query.session
    except AttributeError:
        raise AttributeError("entity has no query_property()")

    pk_props = sa.orm.class_mapper(cls).primary_key
    # if all pk are present
    if [1 for p in pk_props if data.get(p.key)]:
        pk_tuple = tuple([data[prop.key] for prop in pk_props])
        record = cls.query.get(pk_tuple)
        if record is None:
            raise Exception("cannot create with pk")
    else:
        add = True        
        record = cls()
        session.add(record)
        
    record = from_dict(record, data)
    return record
