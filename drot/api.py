import functools
import inspect


FORMATTER = 'formatter'
PARSER = 'parser'
FORMATTERS = '__drot_formatters'
PARSERS = '__drot_parsers'
TYPE = '__drot_type'
ATTRIBUTE = '__drot_attribute'


def definition(clazz):
    """Decorate class, making it suitable for dict <-> object conversion"""
    @classmethod
    def to_object(cls, *args, **kwargs):
        for name, parser in getattr(cls, PARSERS, {}):
            if name in kwargs:
                kwargs[name] = parser(kwargs[name])
        return clazz(*args, **kwargs)

    clazz.to_dict = _to_dict
    clazz.to_object = to_object
    _collect_schema_info(clazz)

    clazz.__init__ = _decorate_init(clazz.__init__)


def formatter(field_name):
    """Formatter that will be used to format field_name
    during transformation to dictionary.
    Returned value will be used literally in output dictionary.
    """
    return _patch_method(field_name, FORMATTER)


def parser(field_name):
    """Parser that will be used to parse dictionary field
    with name field_name before creation of corresponding object
    """
    return _patch_method(field_name, PARSER)


def _decorate_init(initializer):
    """Detect class attributes for serialization"""
    @functools.wraps(initializer)
    def wrapper(self, *args, **kwargs):
        self._mapping_attributes = kwargs.keys()
        initializer(self, *args, **kwargs)
    return wrapper


def _collect_schema_info(cls):
    """Collect formatters and parsers"""
    _collect_methods(cls, FORMATTERS,
                     FORMATTER)
    _collect_methods(cls, PARSERS,
                     PARSER)


def _collect_methods(cls, storage_name, method_type):
    if not hasattr(cls, storage_name):
        collected = dict((getattr(x, ATTRIBUTE), x)
                         for x in inspect.getmembers(cls, inspect.ismethod)
                         if _drot_type(x) == method_type)
        setattr(cls, storage_name, collected)


def _drot_type(method):
    return getattr(method, TYPE, None)


def _patch_method(field_name, drot_type):
    def wrapper(method):
        setattr(method, TYPE, drot_type)
        setattr(method, ATTRIBUTE, field_name)
        return method
    return wrapper


def _transform_item(item):
    """Transform item to it's dictionary representation"""

    if any(isinstance(item, cls) for cls in (list, set)):
        return [_transform_item(member) for member in item]

    if isinstance(item, dict):
        return dict((key, _transform_item(item[key])) for key in item)

    if any([isinstance(item, cls) for cls in
           (int, float, basestring, bool, None.__class__)]):
        return item

    transform_method = getattr(item, 'to_dict', None)
    if transform_method and callable(transform_method):
        return item.to_dict()

    raise NotImplementedError("Object to dictionary conversion "
                              "is not implemented for "
                              "item %s with type %s" % (item, item.__class__))


def _to_dict(self):
    """Transforms object to it's dictionary representation"""
    result = {}
    for key in self._mapping_attributes:
        if hasattr(self, key):
            item = getattr(self, key)
            transform = self.__drot_formatters.get(key, _transform_item)
            result[key] = transform(item)
    return result
