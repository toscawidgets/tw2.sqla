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
            record = getattr(entity, key)
            if not record:
                record = mapper.get_property(key).mapper.class_()
                setattr(entity, key, record)
            from_dict(record, value)
        elif isinstance(value, list) and \
             value and isinstance(value[0], dict):
            from_list(mapper.get_property(key).mapper.class_, getattr(entity, key), value)
        else:
            setattr(entity, key, value)
    return entity


def from_list(entity, objects, data):
    mapper = sa.orm.class_mapper(entity)    
    pkey_fields = [f.key for f in mapper.primary_key]
    obj_map = dict((mapper.primary_key_from_instance(o), o) for o in objects)
    for row in data:
        if not isinstance(row, dict):
            raise Exception(
                    'Cannot send mixed (dict/non dict) data '
                    'to list relationships in from_dict data.')
        pkey = tuple(row.get(f) for f in pkey_fields)
        obj = obj_map.pop(pkey, None)
        if not obj:
            obj = entity()
            objects.append(obj)
        from_dict(obj, row)
    for d in obj_map.values():
        objects.remove(d)


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
