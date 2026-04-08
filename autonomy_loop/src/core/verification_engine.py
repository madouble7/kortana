import json
from jsonschema import validate, ValidationError

def verify_node_integrity(node_json, schema):
    try:
        data = json.loads(node_json)
        validate(instance=data, schema=schema)
        return True
    except (ValidationError, json.JSONDecodeError):
        return False