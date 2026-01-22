import base64
import binascii

s = "rF9lqonu2TyXXbnlS+tBFG+btHKbp20EGKUYMs14GhUPm08ugKh7WIN6A3oSd3XehGgrPASKxWf8lWXPmQQ31j2AqJk0JAAlUHoGE7CvkVtEa4KEeuSGE6z7vbdyE8TYbBB4gj2zkyb4VoW5SIO5bQ=="

print(f"Original string length: {len(s)}")

for i in range(len(s)):
    current_str = s[i:]

    try:
        # validate=False allows characters not in the base64 alphabet to be discarded 
        # (though standard python base64 might still be picky about padding or incorrect chars)
        decoded = base64.b64decode(current_str)
        
        # Attempt to decode as UTF-8 text
        try:
            text = decoded.decode('utf-8')
            # If successful text decode, print it
            print(f"Offset {i}: {text}")
        except UnicodeDecodeError:
            # If not valid UTF-8, print the bytes representation
            print(f"Offset {i} (bytes): {decoded}")
            
    except Exception:
        # Ignore decoding errors
        pass
