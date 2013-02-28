import contextlib
import functools
import json


def definition(clazz):
    """Decorate class, making it suitable for dict <-> object conversion"""
    clazz.__drot_formatters = {}
    clazz.__drot_parsers = {}
    clazz.__drotted = True

    clazz.to_dict = _to_dict
    clazz.to_object = _to_object
    clazz.to_json = _to_json
    clazz.from_json = _from_json

    clazz.__init__ = _decorate_init(clazz.__init__)
    return clazz


def formatter(cls, field_name):
    """Marks formatter that will be used to format field
    during class transformation to dictionary.
    Returned value will be used literally in output dictionary.
    """
    def wrapper(func):
        if not getattr(cls, '__drotted', False):
            raise AssertionError("Class %s have no definition" % cls)
        if func.func_code.co_argcount != 1:
            raise AssertionError("Formatter function "
                                 "should accept one argument")

        def patched_func(value, idset=None):
            item = func(value)
            _check_reference_cycle(item, idset)
            return item

        cls.__drot_formatters[field_name] = patched_func
        return func
    return wrapper


def parser(cls, field_name):
    """Marks parser that will be used to parse dictionary field
    with name field_name before creation of corresponding object.
    """
    def wrapper(func):
        if not getattr(cls, '__drotted', False):
            raise AssertionError("Class %s have no definition" % cls)
        cls.__drot_parsers[field_name] = func
        if func.func_code.co_argcount != 1:
            raise AssertionError("Parser function "
                                 "should accept one argument")
        return func
    return wrapper


def _to_dict(self, excluded=None):
    idset = set([])
    with _memorized(self, idset):
        return _to_dict_internal(self, idset, excluded=excluded)


def _to_dict_internal(self, idset, excluded=None):
    """Transforms object to it's dictionary representation
    with respect to formatters"""
    result = {}
    for key in self.__drot_mapping_attributes - set(excluded or []):
        if hasattr(self, key):
            item = getattr(self, key)
            transform = self.__drot_formatters.get(key, _transform_item)
            result[key] = transform(item, idset)
    return result


def _to_json(self, excluded=None):
    """Transforms object to it's json representation"""
    return json.dumps(self.to_dict(excluded=excluded))


@classmethod
def _from_json(cls, json_string=None, *args):
    return cls.to_object(*args, **json.loads(json_string))


@classmethod
def _to_object(cls, *args, **kwargs):
    """Creates object from it's dictionary representation
    with respect to parsers"""
    for name, parser in cls.__drot_parsers.iteritems():
        if name in kwargs:
            kwargs[name] = parser(kwargs[name])
    return cls(*args, **kwargs)


def _decorate_init(initializer):
    """Detect class attributes for serialization"""
    @functools.wraps(initializer)
    def wrapper(self, *args, **kwargs):
        self.__drot_mapping_attributes = set(kwargs.keys())
        initializer(self, *args, **kwargs)
    return wrapper


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

    if any([isinstance(item, cls) for cls in
            (int, float, basestring, bool, None.__class__)]):
        # no point in reference cycles for these
        return item

    _check_reference_cycle(item, idset)
    with _memorized(item, idset):
        if getattr(item, '__drotted', False):
            # item will check itself for reference cycle
            return _to_dict_internal(item, idset=idset)

        if isinstance(item, list):
            return [_transform_item(member, idset) for member in item]

        if isinstance(item, dict):
            return dict((key, _transform_item(item[key], idset))
                        for key in item)

    raise NotImplementedError("Object to dictionary conversion "
                              "is not implemented for "
                              "item %s with type %s" % (item,
                                                        item.__class__))
