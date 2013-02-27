import functools


def definition(clazz):
    """Decorate class, making it suitable for dict <-> object conversion"""
    clazz.__drot_formatters = {}
    clazz.__drot_parsers = {}
    clazz.__drotted = True
    clazz.to_dict = _to_dict
    clazz.to_object = _to_object

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
        cls.__drot_formatters[field_name] = func
        if func.func_code.co_argcount != 1:
            raise AssertionError("Formatter function "
                                 "should accept one argument")
        return func
    return wrapper


def parser(cls, field_name):
    """Marks parser that will be used to parse dictionary field
    with name field_name before creation of corresponding object

    parsers must be class methods
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


def _to_dict(self):
    """Transforms object to it's dictionary representation
    with respect to formatters"""
    result = {}
    for key in self._mapping_attributes:
        if hasattr(self, key):
            item = getattr(self, key)
            transform = self.__drot_formatters.get(key, _transform_item)
            result[key] = transform(item)
    return result


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
        self._mapping_attributes = kwargs.keys()
        initializer(self, *args, **kwargs)
    return wrapper


def _transform_item(item):
    """Transform item to it's dictionary representation"""

    if any(isinstance(item, cls) for cls in (list, set)):
        return [_transform_item(member) for member in item]

    if isinstance(item, dict):
        return dict((key, _transform_item(item[key]))
                    for key in item)

    if any([isinstance(item, cls) for cls in
           (int, float, basestring, bool, None.__class__)]):
        return item

    if getattr(item, '__drotted', False):
        return item.to_dict()

    raise NotImplementedError("Object to dictionary conversion "
                              "is not implemented for "
                              "item %s with type %s" % (item, item.__class__))
