""" Various sqlalchemy compatibility utils.

    :Author: Ralph Bean <rbean@redhat.com>

"""


def local_name(prop):
    """ Get the name of the local side of a RelationshipProperty.
    Provide compatibility between sqlalchemy 0.8 and earlier.
    """

    if hasattr(prop, 'local_remote_pairs'):
        # sqlalchemy >= 0.8
        return prop.local_remote_pairs[0][0].name
    else:
        # sqlalchemy <= 0.7.9
        return prop.local_side[0].name
