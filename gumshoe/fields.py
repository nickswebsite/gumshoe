import datetime
import time

from django.core.exceptions import ValidationError
from rest_framework import serializers

from gumshoe.models import IssueType, Priority


class PkListField(serializers.Field):
    def to_representation(self, obj):
        if hasattr(obj, "all"):
            return [o.pk for o in obj.all()]
        else:
            return [o.pk for o in obj]

    def to_internal_value(self, value):
        if isinstance(value, list):
            return value
        else:
            msg = self.error_messages["invalid"]
            raise ValidationError(msg)


class PkField(serializers.Field):
    def to_representation(self, obj):
        if obj is not None:
            return obj.pk
        return None

    def to_internal_value(self, value):
        if isinstance(value, int) or value is None:
            return value
        msg = self.error_messages["invalid"]
        raise ValidationError(msg)


class ShortNameField(serializers.Field):
    def to_representation(self, value):
        return value.short_name

    def to_internal_value(self, data):
        if not isinstance(data, str):
            raise ValidationError(self.error_messages["invalid"])

        try:
            return self.model.objects.get(short_name=data)
        except self.model.DoesNotExist:
            raise ValidationError(self.error_messages["invalid"])


class IssueTypeField(ShortNameField):
    model = IssueType


class PriorityField(ShortNameField):
    model = Priority


class UnixtimeField(serializers.DateTimeField):
    def __init__(self, *args, **kwds):
        is_java_time = kwds.pop("millis", False)
        if is_java_time:
            self.scaling = 1000
        else:
            self.scaling = 1

        super(UnixtimeField, self).__init__(*args, **kwds)

    def to_representation(self, value):
        return int(time.mktime(value.timetuple())) * self.scaling

    def to_internal_value(self, value):
        return datetime.datetime.fromtimestamp(int(value) / self.scaling)