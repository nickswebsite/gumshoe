import re

from rest_framework import renderers, parsers

camel_case_to_snake_case_regex = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')
camel_case_to_snake_case_substitution_pattern = r'_\1'

def snake_case_to_camel_case(key):
    components = key.split("_")
    return components[0] + "".join([c.capitalize() for c in components[1:]])

def camel_case_to_snake_case(key):
    return camel_case_to_snake_case_regex.sub(camel_case_to_snake_case_substitution_pattern, key).lower()

def do_transform(data, transformer):
    if isinstance(data, basestring):
        return data
    elif hasattr(data, "items"):
        return {transformer(k): do_transform(v, transformer) for k, v in data.items()}
    elif hasattr(data, "__iter__"):
        return [do_transform(i, transformer) for i in data]
    return data

class CaseConvertingJSONRenderer(renderers.JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        data = do_transform(data, transformer=snake_case_to_camel_case)
        return super(CaseConvertingJSONRenderer, self).render(data, accepted_media_type, renderer_context)

class CaseConvertingJSONParser(parsers.JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        res = super(CaseConvertingJSONParser, self).parse(stream, media_type, parser_context)
        return do_transform(res, transformer=camel_case_to_snake_case)
