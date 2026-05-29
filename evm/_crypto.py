#!/usr/bin/env python3
"""
EVM 加密模块

提供安全的加密/解密功能：
- HKDF-Expand: 密钥分离（加密密钥 + MAC 密钥）
- HMAC-CTR: 基于 HMAC 的 CTR 模式流密码
- HMAC-SHA256: 认证加密（Encrypt-then-MAC）

格式: ENCv3:<salt_b64>:<iv_b64>:<mac_b64>:<ciphertext_b64>
"""

import base64
import hashlib
import hmac
import os
import struct

from .exceptions import DecryptionError


def hkdf_expand(prk: bytes, info: bytes, length: int = 32) -> bytes:
    """HKDF-Expand (RFC 5869)

    从伪随机密钥 (PRK) 派生指定长度的输出密钥材料。

    Args:
        prk: 伪随机密钥（至少 hash_len 字节）
        info: 上下文和用途信息
        length: 输出密钥材料长度（字节）

    Returns:
        派生的密钥材料
    """
    hash_len = 32  # SHA-256 输出长度
    n = (length + hash_len - 1) // hash_len
    okm = b''
    t = b''
    for i in range(1, n + 1):
        t = hmac.new(
            prk, t + info + bytes([i]), hashlib.sha256
        ).digest()
        okm += t
    return okm[:length]


def derive_subkeys(master_key: bytes, salt: bytes) -> tuple:
    """从主密钥派生独立的加密和 MAC 子密钥

    使用 HKDF-Expand 和不同的 info 字符串确保密钥分离。

    Args:
        master_key: PBKDF2 输出的主密钥
        salt: 用于 HKDF info 的随机盐

    Returns:
        (enc_key, mac_key) 各 32 字节
    """
    enc_key = hkdf_expand(master_key, salt + b'evm-encryption', 32)
    mac_key = hkdf_expand(master_key, salt + b'evm-authentication', 32)
    return enc_key, mac_key


def hmac_ctr_keystream(key: bytes, iv: bytes, length: int) -> bytes:
    """生成 HMAC-CTR 模式密钥流

    keystream = HMAC(key, IV || 0) || HMAC(key, IV || 1) || ...

    Args:
        key: 加密密钥
        iv: 随机初始化向量（计数器起始值）
        length: 需要的密钥流长度（字节）

    Returns:
        指定长度的密钥流
    """
    stream = b''
    counter = 0
    while len(stream) < length:
        block = hmac.new(
            key, iv + struct.pack('>I', counter), hashlib.sha256
        ).digest()
        stream += block
        counter += 1
    return stream[:length]


def encrypt_v3(plaintext: str, derive_key_fn) -> str:
    """v3 加密: HKDF 密钥分离 + HMAC-CTR + Encrypt-then-MAC

    Args:
        plaintext: 明文
        derive_key_fn: 密钥派生函数 (salt) -> master_key

    Returns:
        ENCv3:<salt_b64>:<iv_b64>:<mac_b64>:<ciphertext_b64>
    """
    salt = os.urandom(16)
    iv = os.urandom(16)
    master_key = derive_key_fn(salt)
    enc_key, mac_key = derive_subkeys(master_key, salt)

    data_bytes = plaintext.encode('utf-8')

    # HMAC-CTR 加密
    keystream = hmac_ctr_keystream(enc_key, iv, len(data_bytes))
    ciphertext = bytes(a ^ b for a, b in zip(data_bytes, keystream))

    # Encrypt-then-MAC: HMAC 覆盖 salt + iv + ciphertext
    mac = hmac.new(
        mac_key, salt + iv + ciphertext, hashlib.sha256
    ).digest()

    salt_b64 = base64.b64encode(salt).decode('ascii')
    iv_b64 = base64.b64encode(iv).decode('ascii')
    mac_b64 = base64.b64encode(mac).decode('ascii')
    ct_b64 = base64.b64encode(ciphertext).decode('ascii')

    return f"ENCv3:{salt_b64}:{iv_b64}:{mac_b64}:{ct_b64}"


def decrypt_v3(encoded: str, derive_key_fn) -> str:
    """v3 解密: 验证 MAC + HMAC-CTR 解密

    Args:
        encoded: salt_b64:iv_b64:mac_b64:ciphertext_b64
        derive_key_fn: 密钥派生函数 (salt) -> master_key

    Returns:
        解密后的明文

    Raises:
        DecryptionError: 格式错误或完整性校验失败
    """
    parts = encoded.split(':')
    if len(parts) != 4:
        raise DecryptionError("Invalid v3 encrypted data format")

    try:
        salt = base64.b64decode(parts[0])
        iv = base64.b64decode(parts[1])
        stored_mac = base64.b64decode(parts[2])
        ciphertext = base64.b64decode(parts[3])
    except Exception as e:
        raise DecryptionError(f"Failed to decode v3 data: {e}")

    master_key = derive_key_fn(salt)
    enc_key, mac_key = derive_subkeys(master_key, salt)

    # 验证 MAC（常量时间比较）
    computed_mac = hmac.new(
        mac_key, salt + iv + ciphertext, hashlib.sha256
    ).digest()
    if not hmac.compare_digest(stored_mac, computed_mac):
        raise DecryptionError(
            "Data integrity check failed — data may be corrupted or tampered"
        )

    # HMAC-CTR 解密
    keystream = hmac_ctr_keystream(enc_key, iv, len(ciphertext))
    plaintext = bytes(a ^ b for a, b in zip(ciphertext, keystream))

    try:
        return plaintext.decode('utf-8')
    except UnicodeDecodeError as e:
        raise DecryptionError(f"Decrypted data is not valid UTF-8: {e}")


__all__ = [
    'hkdf_expand',
    'derive_subkeys',
    'hmac_ctr_keystream',
    'encrypt_v3',
    'decrypt_v3',
]
