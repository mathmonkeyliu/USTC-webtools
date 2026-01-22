import hashlib
import json

def generate_sign(data):
    SECRET_KEY = "BwPimfkcRKAmHcbL9tnq"

    pairs = []
    for key in sorted(data.keys()):
        value = data[key]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, separators=(',', ':'), ensure_ascii=False)
        elif isinstance(value, bool):
            value = str(value).lower()
        else:
            value = str(value).strip()
        if value:
            pairs.append(f"{key}={value}")

    string_to_sign = "&".join(pairs) + SECRET_KEY

    return hashlib.md5(string_to_sign.encode('utf-8')).hexdigest()

if __name__ == "__main__":
    from test_data import data
    print(f"generated_sign: {generate_sign(data)}")