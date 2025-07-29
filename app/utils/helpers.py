import re,os
import sys

def determine_type(value):
    if isinstance(value, str):
        return 'string'
    try:
        int(value)
        return 'int'
    except ValueError:
        pass

    try:
        float(value)
        return 'float'
    except ValueError:
        pass

    if value.lower() in ["true", "false"]:
        return 'boolean'

    return 'unknown'

def parse_line_protocol(payload):
    parts = re.split(r' (?=(?:[^"]*"[^"]*")*[^"]*$)', payload)
    measurement_and_tags = parts[0].split(',')
    measurement = measurement_and_tags[0]
    tags = ','.join(measurement_and_tags[1:])
    fields = parts[1] if len(parts) > 1 else ''
    timestamp = parts[2] if len(parts) > 2 else ''

    if (measurement == 'application.httprequests__active' or measurement ==  'jvm_memory_used' or measurement ==  'jvm_gc_pause' or measurement =='jvm_memory_committed' or measurement =='jvm_memory_max'):
        match = re.search(r"([\S\s]*)\s([\S]*)\s([0-9]*)$", payload)
        measurement_and_tags = match.group(1).split(',')
        tags = ','.join(measurement_and_tags[1:])
        fields = match.group(2) if (match.group(2)) else ''
        timestamp = match.group(3) if (match.group(3)) else ''

    if (len(timestamp)!=19):
        timestamp += (19-len(timestamp))*("0")
        print(f"Timestamp length was modified for Measurement: {measurement} ")

    if 'sum=' in fields:
        fields = fields.replace('sum=', 'summation=')
    
    #Tag the messages with the currently running pod to identify as from transformer
    pod_name = os.environ.get("HOSTNAME")
    tags+= f",InfluxTransformerPod={pod_name}"
    print(f"Measurement: {measurement}")
    print(f"Tags: {tags}")
    print(f"Fields: {fields}")
    print(f"Timestamp: {timestamp}")



    sys.stdout.flush()

    return measurement, tags, fields, timestamp

def transform_payload(measurement, tags, fields):
    field_dict = {k: v for k, v in (field.split('=', 1) for field in re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', fields))}
    additional_tags = []
    remaining_fields = []
    all_fields_are_strings = True

    for k, v in field_dict.items():
        if v.startswith('"') and v.endswith('"'):
            v = v.replace(" ", "")
            additional_tags.append(f"{k}={v}")
        else:
            if v.endswith('i'):
                v = v[:-1]
                try:
                    v_int = int(v)
                    remaining_fields.append(f"{k}={v_int}")
                    all_fields_are_strings = False
                except ValueError:
                    additional_tags.append(f"{k}={v}")
            else:
                try:
                    v_float = float(v)
                    remaining_fields.append(f"{k}={v_float}")
                    all_fields_are_strings = False
                except ValueError:
                    v = v.replace(" ", "")
                    additional_tags.append(f"{k}={v}")

    if all_fields_are_strings:
        remaining_fields.append("string_field_indicator=1")

    transformed_tags = f"{tags},{','.join(additional_tags)}" if tags else ','.join(additional_tags)
    transformed_fields = ','.join(remaining_fields)

    return measurement, transformed_tags.rstrip(','), transformed_fields.rstrip(',')