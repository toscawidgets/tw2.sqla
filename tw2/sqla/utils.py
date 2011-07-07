import sqlalchemy as sa
things = ['new', 'dirty', 'deleted']

def from_dict(obj, data, protect_prm_tamp=True):
    """
    Update a mapped object with data from a JSON-style nested dict/list
    structure.

    To protect against parameter tampering attacks, primary key fields are 
    never overwritten.
    """

    mapper = sa.orm.object_mapper(obj)
    pk_props = set(p.key for p in mapper.primary_key)

    for key, value in data.iteritems():
        if isinstance(value, dict):
            record = getattr(obj, key)
            if not record:
                record = mapper.get_property(key).mapper.class_()
                setattr(obj, key, record)
            from_dict(record, value, protect_prm_tamp)
        elif isinstance(value, list) and \
             value and isinstance(value[0], dict):
            from_list(
                mapper.get_property(key).mapper.class_,
                getattr(obj, key),
                value,
                protect_prm_tamp
            )
        elif key not in pk_props:
            setattr(obj, key, value)
    return obj


def from_list(entity, objects, data, force_delete=False, protect_prm_tamp=True):
    """
    Update a list of mapped objects with data from a JSON-style nested dict/list
    structure.
    
    To protect against parameter tampering attacks, if the primary key field(s) 
    for a row do not exactly match an existing object then a new object is created.
    """

    mapper = sa.orm.class_mapper(entity)    
    pkey_fields = [f.key for f in mapper.primary_key]
    obj_map = dict((tuple(mapper.primary_key_from_instance(o)), o) for o in objects)
    for row in data:
        if not isinstance(row, dict):
            raise Exception(
                    'Cannot send mixed (dict/non dict) data '
                    'to list relationships in from_dict data.')
        pkey = tuple(row.get(f) for f in pkey_fields)
        obj = obj_map.pop(pkey, None)
        if not obj and protect_prm_tamp:
            obj = entity()
            from_dict(obj, row, protect_prm_tamp)
            obj.query.session.add(obj)
            objects.append(obj)
        elif not obj:
            obj = update_or_create(entity, row)
            obj.query.session.add(obj)
            objects.append(obj)
        else:
            from_dict(obj, row, protect_prm_tamp)

    for d in obj_map.values():
        objects.remove(d)
        if force_delete:
            # Only fully delete 'unreferenced' objects if explicitly told to do
            # so.  You would *not* want to do this in a database of friends
            # where sally and suzie stop being friends but you do not want suzie
            # deleted from the database alltogether.
            d.query.session.delete(d)


def update_or_create(cls, data, protect_prm_tamp=True):

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
        record = cls()
        session.add(record)

    record = from_dict(record, data, protect_prm_tamp)
    return record
