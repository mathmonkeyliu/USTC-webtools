import json
import hashlib
import base64
import random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# 已知的固定 Header (32 bytes)
CONSTANT_HEADER = bytes.fromhex("ac5f65aa89eed93c975db9e54beb41146f9bb4729ba76d0418a51832cd781a15")

# 模拟密钥 (真实密钥在云端，此处用 sign.py 的 secret 生成一个替代品)
# 如果你能搞到云函数的源码，替换这里的 key 即可完全破解
SECRET_KEY_STR = "BwPimfkcRKAmHcbL9tnq"
MOCK_AES_KEY = hashlib.sha256(SECRET_KEY_STR.encode('utf-8')).digest() # 32 bytes key

def get_canonical_string(data):
    """
    生成规范化字符串，逻辑同 sign.py，但排除无关字段
    """
    pairs = []
    # 排除不参与 noise 生成的字段
    exclude_keys = ['open_id', 'version', 'timestamp', 'noise', 'sign', 'all_params'] 
    
    for key in sorted(data.keys()):
        if key in exclude_keys:
            continue
            
        value = data[key]
        if isinstance(value, (dict, list)):
            # 保持紧凑格式，无空格
            value = json.dumps(value, separators=(',', ':'), ensure_ascii=False)
        elif isinstance(value, bool):
            value = str(value).lower()
        else:
            value = str(value).strip()
        
        if value:
            pairs.append(f"{key}={value}")
    
    return "&".join(pairs)

def generate_noise(data):
    """
    生成符合结构的 Noise
    """
    # 1. 规范化参数
    canonical_str = get_canonical_string(data)
    print(f"Canonical String: {canonical_str}")
    
    # 2. 计算 SHA-384 摘要 (48 bytes)
    # 这里假设是对字符串+Secret进行哈希，或者仅字符串
    digest = hashlib.sha384((canonical_str + SECRET_KEY_STR).encode('utf-8')).digest()
    
    # 3. 准备明文 (Padding)
    # 48 bytes + 16 bytes padding = 64 bytes
    plaintext = pad(digest, AES.block_size)
    
    # 4. AES-CBC 加密
    iv = random.randbytes(16) # 生成随机 IV
    cipher = AES.new(MOCK_AES_KEY, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(plaintext)
    
    # 5. 组装: Header + IV + Ciphertext
    final_binary = CONSTANT_HEADER + iv + ciphertext
    
    # 6. Base64 编码
    return base64.b64encode(final_binary).decode('utf-8')

if __name__ == "__main__":
    # 测试数据 (来自 record_data.py)
    test_data = {"day":1768752000,"kind_id":5,"share_open":10,"selected_block":[{"hour":21,"min":45,"venue_id":-30,"venue":{"id":-30,"sn":"旁观","school_part":30}},{"hour":22,"min":0,"venue_id":-30,"venue":{"id":-30,"sn":"旁观","school_part":30}}]}
    
    noise = generate_noise(test_data)
    print(f"\nGenerated Noise (Length {len(base64.b64decode(noise))} bytes):")
    print(noise)