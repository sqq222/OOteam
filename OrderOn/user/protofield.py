from __future__ import absolute_import
import base64
import six

from django.db import models


class ProtobufField(models.Field):

    __metaclass__ = models.SubfieldBase

    def __init__(self, protoclass, *args, **kwargs):
        self.klass = protoclass
        super(ProtobufField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        _args = [self.klass]
        name, path, args, kwargs = super(ProtobufField, self).deconstruct()
        _args.extend(args)
        return name, path, _args, kwargs

    def to_python(self, value):
        if value is None or value == '':
            return ''
        elif isinstance(value, self.klass):
            return value
        else: # decode the stored string value
            protobuf = self.klass.FromString(base64.decodestring(value))
            return protobuf

    def get_prep_value(self, value):
        if value is None or value == '':
            return ''
        elif isinstance(value, six.string_types):
            return value
        else: # protoclass type
            return base64.encodestring(value.SerializeToString())