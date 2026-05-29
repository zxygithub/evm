# EVM Security Architecture

## Encryption (v3)

### Key Derivation

```
Machine Identity (hostname + uid + arch)
        │
        ▼
  PBKDF2-HMAC-SHA256 (100,000 iterations, random 16-byte salt)
        │
        ▼
    Master Key (32 bytes)
        │
        ├─── HKDF-Expand (info="evm-encryption") ──→ enc_key (32 bytes)
        │
        └─── HKDF-Expand (info="evm-authentication") ──→ mac_key (32 bytes)
```

### Encryption Process

```
Plaintext
    │
    ▼
HMAC-CTR Stream Cipher (enc_key, random 16-byte IV)
    │
    ▼
Ciphertext
    │
    ▼
HMAC-SHA256 (mac_key, salt + IV + ciphertext)  ← Encrypt-then-MAC
    │
    ▼
ENCv3:<salt_b64>:<iv_b64>:<mac_b64>:<ciphertext_b64>
```

### Decryption Process

1. Parse the `ENCv3:` format into salt, IV, MAC, ciphertext
2. Derive master key via PBKDF2 from machine identity + salt
3. Derive enc_key and mac_key via HKDF-Expand
4. Verify MAC using constant-time comparison (`hmac.compare_digest`)
5. If MAC valid, decrypt with HMAC-CTR
6. If MAC invalid, raise `DecryptionError`

### Auto-Migration

Reading v1 (`ENC:`) or v2 (`ENCv2:`) ciphertexts automatically:
1. Decrypts using the legacy algorithm
2. Re-encrypts using v3
3. Saves the v3 ciphertext back to storage
4. Logs the migration in history

## File Permissions

All sensitive files are created with `chmod 600` (owner read/write only):

| File | Permission | When Set |
|------|-----------|----------|
| `env.json` | 600 | Every save |
| `env.json.lock` | 600 | Created on first write |
| `schema.json` | 600 | Every save |
| `history.jsonl` | 600 | On creation |
| Backup files | 600 | On creation |

## Concurrency Safety

### File Locking

- Uses a shared `.lock` file (not the temp file) for inter-process synchronization
- `fcntl.flock(LOCK_EX | LOCK_NB)` with configurable timeout (default 5s)
- Lock acquired before write, released after atomic `shutil.move`
- Prevents last-writer-wins race conditions between concurrent processes

### Atomic Writes

1. Write to a temp file (`tempfile.mkstemp`)
2. `fsync()` to ensure data is on disk
3. `shutil.move()` for atomic rename
4. `chmod 600` on the final file

## Shell Safety

### Export Escaping

- **Values**: `shlex.quote()` for all `.sh` exports
- **Keys**: `shlex.quote()` for all `.sh` exports (prevents injection via malicious key names)
- **Import validation**: `.env` imports reject keys not matching `^[A-Za-z_][A-Za-z0-9_]*$`

### Example Attack Prevention

```bash
# Malicious .env file:
$(whoami)=payload

# EVM behavior: Key rejected during import (doesn't match valid pattern)
# Shell export: key is quoted → export '$(whoami)'='payload' (safe, literal string)
```

## History Safety

- `set` operations do NOT log plaintext values (only key names)
- `set_secret` operations do NOT log values at all
- History file is `chmod 600`
- History operations catch only `OSError` (not bare `Exception`) to avoid hiding programming errors

## Known Limitations

### Machine Binding

Encryption keys are derived from:
- `platform.node()` (hostname)
- `os.getuid()` (user ID)
- `platform.machine()` (CPU architecture)

**Consequence**: Changing hostname, migrating to another machine, or running in a container with a different hostname will make existing secrets unrecoverable.

**Mitigation**: 
- EVM prints a warning on first use of `--secret`
- EVM prints a warning when `get --secret` outputs to a terminal (scrollback risk)
- For portable secrets, users should manage encryption externally

### No User Password

EVM does not support a user-defined master password. The key derivation is fully automatic (and fully machine-bound). This is a design trade-off: zero configuration vs. no portability.

### Encryption Strength

HMAC-CTR with HKDF key separation is a strong construction, but:
- The effective entropy is limited by the machine identity (not user-chosen)
- On shared machines, any process running as the same user can derive the same key
- For high-security use cases, consider an external secrets manager (Vault, AWS Secrets Manager, etc.)
