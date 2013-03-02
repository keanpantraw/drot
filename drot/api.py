import contextlib
import inspect


def model(**kwargs):
    """Decorate class, making it suitable for dict <-> object conversion.
    """
    def _class_wrapper(clazz):
        clazz.__drotted = True
        clazz.__drot_parser_hooks = kwargs

        clazz.to_dict = _to_dict
        clazz.to_object = _to_object

        attributes = set(k for k, v in vars(clazz).iteritems()
                         if _is_attribute(v)
                         and not k.startswith('_'))
        clazz.__drot_mapping_attributes = attributes

        property_map = dict((v.fget.__name__, v.fset)
                            for k, v in vars(clazz).iteritems()
                            if _is_property_setter(v))
        clazz.__drot_property_map = property_map
        return clazz
    return _class_wrapper


simple_model = model()


def _is_function(arg):
    return callable(arg) or inspect.ismethoddescriptor(arg)


def _is_property_getter(arg):
    return isinstance(arg, property) and arg.fset


def _is_property_setter(arg):
    return isinstance(arg, property) and arg.fset is None


def _is_attribute(arg):
    return not (_is_function(arg) or _is_property_setter(arg))


def _to_dict(self, excluded=None):
    """Transforms object to it's dictionary representation"""
    idset = set([])
    with _memorized(self, idset):
        return _to_dict_internal(self, idset, excluded=excluded)


def _to_dict_internal(self, idset, excluded=None):
    result = {}
    for key in self.__drot_mapping_attributes - set(excluded or []):
        if hasattr(self, key):
            item = getattr(self, key)
            result[key] = _transform_item(item, idset)
    return result


@classmethod
def _to_object(cls, dictionary):
    """Creates object from it's dictionary representation
    with respect to specified parsers"""
    dictionary = dict((k, v) for k, v in dictionary.iteritems()
                      if k in cls.__drot_mapping_attributes)

    item = cls()
    for key, value in dictionary.iteritems():

        if key in cls.__drot_parser_hooks:
            value = cls.__drot_parser_hooks[key](value)

        if key in cls.__drot_property_map:
            cls.__drot_property_map[key](item, value)
        else:
            setattr(item, key, value)
    return item


def _check_reference_cycle(item, idset):
    if idset and id(item) in idset:
        raise ValueError("Reference cycle: "
                         "item %s shouldn't reference itself" % repr(item))


@contextlib.contextmanager
def _memorized(item, idset):
    idset.add(id(item))
    yield
    idset.remove(id(item))


def _transform_item(item, idset):
    """Transform item to it's dictionary representation"""

    _check_reference_cycle(item, idset)
    with _memorized(item, idset):
        if getattr(item, '__drotted', False):
            return _to_dict_internal(item, idset=idset)

        if isinstance(item, list):
            return [_transform_item(member, idset) for member in item]

        if isinstance(item, dict):
            return dict((key, _transform_item(item[key], idset))
                        for key in item)
    return item
