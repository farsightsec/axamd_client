import jsonschema
import pkg_resources
import yaml

_stream_param_schema = yaml.safe_load(pkg_resources.resource_stream(__name__, 'stream-param-schema.yaml'))

def stream_params_validate(stream_params):
    try:
        jsonschema.validate(stream_params, _stream_param_schema)
    except jsonschema.ValidationError:
        e,v,tb = sys.exc_info()
        six.reraise(ValidationError, v, tb)

