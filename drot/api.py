import inspect


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


class Definition(object):
    FORMATTER = 'formatter'
    PARSER = 'parser'
    FORMATTERS = '__drot_formatters'
    PARSERS = '__drot_parsers'
    TYPE = '__drot_type'
    ATTRIBUTE = '__drot_attribute'

    def __init__(self, clazz):
        self.cls = clazz

        @classmethod
        def to_object(cls, *args, **kwargs):
            for name, parser in getattr(cls, Definition.PARSERS, {}):
                if name in kwargs:
                    kwargs[name] = parser(kwargs[name])
            return self.cls(*args, **kwargs)

        self.cls.to_dict = _to_dict
        self.cls.to_object = to_object
        self._collect_schema_info()

    def __call__(self, *args, **kwargs):
        """Detect class attributes for serialization"""
        instance = self.cls(*args, **kwargs)
        instance._mapping_attributes = kwargs.keys()
        return instance

    def _collect_schema_info(self):
        """Collect formatters and parsers"""
        self._collect_methods(self.cls, Definition.FORMATTERS,
                              Definition.FORMATTER)
        self._collect_methods(self.cls, Definition.PARSERS,
                              Definition.PARSER)

    def _collect_methods(self, cls, storage_name, method_type):
        if not hasattr(cls, storage_name):
            collected = dict((getattr(x, Definition.ATTRIBUTE), x)
                             for x in inspect.getmembers(cls, inspect.ismethod)
                             if self._drot_type(x) == method_type)
            setattr(cls, storage_name, collected)

    def _drot_type(self, method):
        return getattr(method, Definition.TYPE, None)

    @classmethod
    def formatter(cls, field_name):
        """Formatter that will be used to format field_name
        during transformation to dictionary.
        Returned value will be used literally in output dictionary.
        """
        return cls._patch_method(field_name, Definition.FORMATTER)

    @classmethod
    def parser(cls, field_name):
        """Parser that will be used to parse dictionary field
        with name field_name before creation of corresponding object
        """
        return cls._patch_method(field_name, Definition.PARSER)

    @classmethod
    def _patch_method(cls, field_name, drot_type):
        def wrapper(method):
            setattr(method, Definition.TYPE, drot_type)
            setattr(method, Definition.ATTRIBUTE, field_name)
            return method
        return wrapper
