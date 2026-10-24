"""Offline age encryption and public-artifact verification; no restore operation."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import uuid

LIMIT = 512 * 1024 * 1024
CIPHER_LIMIT = LIMIT + (LIMIT // 65536 + 1) * 16 + 1024
TOTAL_LIMIT = 1024 * 1024 * 1024
MAX_ITEMS = 64
NAME = re.compile(r"payload-([0-9a-f]{32})\.bin\Z")
ARTIFACT = re.compile(r"([0-9a-f]{32})\.age\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")


class Rejected(Exception):
    """A deliberately non-sensitive error reported without input details."""


def require(condition):
    if not condition:
        raise Rejected()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def public_recipient(value):
    # Native age X25519 Bech32 recipient, including checksum and canonical padding.
    require(isinstance(value, str) and len(value) == 62 and value.startswith('age1'))
    alphabet = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l'
    require(all(c in alphabet for c in value[4:]))
    data = [alphabet.index(c) for c in value[4:]]
    hrp = 'age'
    expanded = [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]
    chk = 1
    for v in expanded + data:
        top = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ v
        for bit, generator in enumerate((0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3)):
            if (top >> bit) & 1:
                chk ^= generator
    require(chk == 1)
    accumulator = bits = 0
    decoded = bytearray()
    for v in data[:-6]:
        accumulator = (accumulator << 5) | v
        bits += 5
        if bits >= 8:
            bits -= 8
            decoded.append((accumulator >> bits) & 255)
    require(len(decoded) == 32 and bits < 5 and ((accumulator << (8 - bits)) & 255) == 0)
    return value


def signature(st):
    return (st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_nlink,
            st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def owned(st, directory=False):
    require((stat.S_ISDIR(st.st_mode) if directory else stat.S_ISREG(st.st_mode)))
    require(st.st_uid == os.geteuid())
    require(stat.S_IMODE(st.st_mode) == (0o700 if directory else 0o600))
    if not directory:
        require(st.st_nlink == 1)


def directory(path):
    # Walk every absolute component with openat/O_NOFOLLOW; never resolve symlinks.
    require(isinstance(path, str) and path.startswith('/') and path != '/')
    parts = path.split('/')[1:]
    require(all(x and x not in ('.', '..') for x in parts))
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in parts:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        owned(os.fstat(fd), directory=True)
        return fd
    except BaseException:
        os.close(fd)
        raise


def unchanged_directory(path, fd):
    current = directory(path)
    try:
        require(signature(os.fstat(current)) == signature(os.fstat(fd)))
    finally:
        os.close(current)


def open_file(fd, name):
    opened = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    try:
        owned(os.fstat(opened))
        return opened
    except BaseException:
        os.close(opened)
        raise


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result)
        result[key] = value
    return result


def load_json(data):
    return json.loads(data, object_pairs_hook=no_duplicate_keys)


def read_small(fd, limit=65536):
    require(os.fstat(fd).st_size <= limit)
    os.lseek(fd, 0, os.SEEK_SET)
    data = os.read(fd, limit + 1)
    require(len(data) <= limit)
    return data


def hash_fd(fd):
    os.lseek(fd, 0, os.SEEK_SET)
    h = hashlib.sha256()
    size = 0
    while True:
        chunk = os.read(fd, 65536)
        if not chunk:
            break
        size += len(chunk)
        require(size <= CIPHER_LIMIT)
        h.update(chunk)
    return h.hexdigest(), size


def stable_file(root_fd, name, fd, before):
    require(signature(os.fstat(fd)) == before)
    require(signature(os.stat(name, dir_fd=root_fd, follow_symlinks=False)) == before)


def selection(root_fd):
    handles = []
    try:
        control = open_file(root_fd, 'selection.json')
        handles.append(('selection.json', control, signature(os.fstat(control))))
        spec = load_json(read_small(control))
        require(set(spec) == {'version', 'entries'} and type(spec['version']) is int and spec['version'] == 1)
        entries = spec['entries']
        require(isinstance(entries, list) and 1 <= len(entries) <= MAX_ITEMS)
        seen = set()
        total = 0
        for entry in entries:
            require(isinstance(entry, dict) and set(entry) == {'file', 'size', 'sha256'})
            name = entry['file']
            require(isinstance(name, str) and NAME.fullmatch(name) and name not in seen)
            seen.add(name)
            require(type(entry['size']) is int and 1 <= entry['size'] <= LIMIT)
            require(isinstance(entry['sha256'], str) and HEX.fullmatch(entry['sha256']))
            total += entry['size']
            require(total <= TOTAL_LIMIT)
            fd = open_file(root_fd, name)
            before = signature(os.fstat(fd))
            handles.append((name, fd, before))
            require(os.fstat(fd).st_size == entry['size'])
            require(hash_fd(fd) == (entry['sha256'], entry['size']))
            stable_file(root_fd, name, fd, before)
        require(set(os.listdir(root_fd)) == {'selection.json'} | seen)
        for name, fd, before in handles:
            stable_file(root_fd, name, fd, before)
        return entries, handles
    except BaseException:
        for _, fd, _ in handles:
            os.close(fd)
        raise


def write_file(root_fd, name, data):
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=root_fd)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def encrypt(fd, out_fd, recipient, expected, age):
    # No shell, plugins, inherited age configuration or diagnostic output.
    proc = subprocess.Popen([age, '--encrypt', '--recipient', recipient], stdin=subprocess.PIPE,
                            stdout=out_fd, stderr=subprocess.DEVNULL, close_fds=True,
                            start_new_session=True, env={'PATH': os.defpath, 'LC_ALL': 'C'})
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        h = hashlib.sha256()
        size = 0
        while True:
            block = os.read(fd, 65536)
            if not block:
                break
            size += len(block)
            require(size <= expected['size'])
            h.update(block)
            proc.stdin.write(block)
        proc.stdin.close()
        require(proc.wait(timeout=120) == 0)
        require((h.hexdigest(), size) == (expected['sha256'], expected['size']))
        os.fsync(out_fd)
    finally:
        if proc.stdin and not proc.stdin.closed:
            try:
                proc.stdin.close()
            except OSError:
                pass
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


def b64length(value, length):
    require(re.fullmatch(rb'[A-Za-z0-9+/]+', value) is not None)
    decoded = base64.b64decode(value + b'=' * (-len(value) % 4), validate=True)
    require(len(decoded) == length and base64.b64encode(decoded).rstrip(b'=') == value)


def ciphertext(fd):
    # Structural validation only; payload authentication requires a separate restore.
    os.lseek(fd, 0, os.SEEK_SET)
    header = os.read(fd, 4096)
    lines = header.split(b'\n', 4)
    require(len(lines) == 5 and lines[0] == b'age-encryption.org/v1')
    require(lines[1].startswith(b'-> X25519 '))
    b64length(lines[1][10:], 32)
    b64length(lines[2], 32)
    require(lines[3].startswith(b'--- '))
    b64length(lines[3][4:], 32)
    require(os.fstat(fd).st_size >= sum(len(x) + 1 for x in lines[:4]) + 32)


def validate_kit(root_fd, recipient):
    public_recipient(recipient)
    manifest_fd = open_file(root_fd, 'manifest.sanitized.json')
    checks_fd = None
    try:
        checks_fd = open_file(root_fd, 'checksums.sha256')
        raw = read_small(manifest_fd)
        manifest = load_json(raw)
        require(set(manifest) == {'version', 'encryption', 'recipient_sha256', 'artifacts'})
        require(type(manifest['version']) is int and manifest['version'] == 1)
        require(manifest['encryption'] == 'age-X25519')
        require(manifest['recipient_sha256'] == digest(recipient.encode()))
        artifacts = manifest['artifacts']
        require(isinstance(artifacts, list) and 1 <= len(artifacts) <= MAX_ITEMS)
        names = set()
        computed = {'manifest.sanitized.json': digest(raw)}
        for artifact in artifacts:
            require(isinstance(artifact, dict) and set(artifact) == {'file', 'size', 'sha256'})
            name = artifact['file']
            require(isinstance(name, str) and ARTIFACT.fullmatch(name) and name not in names)
            require(type(artifact['size']) is int and 0 < artifact['size'] <= CIPHER_LIMIT)
            require(isinstance(artifact['sha256'], str) and HEX.fullmatch(artifact['sha256']))
            names.add(name)
            fd = open_file(root_fd, name)
            try:
                ciphertext(fd)
                checksum, size = hash_fd(fd)
                require((checksum, size) == (artifact['sha256'], artifact['size']))
                computed[name] = checksum
            finally:
                os.close(fd)
        require(set(os.listdir(root_fd)) == names | {'manifest.sanitized.json', 'checksums.sha256'})
        expected = ''.join(f'{computed[n]}  {n}\n' for n in sorted(computed)).encode()
        require(read_small(checks_fd) == expected)
    finally:
        os.close(manifest_fd)
        if checks_fd is not None:
            os.close(checks_fd)


def export(input_path, output_path, recipient):
    public_recipient(recipient)
    require(not (input_path == output_path or input_path.startswith(output_path + '/')
                 or output_path.startswith(input_path + '/')))
    age = shutil.which('age', path=os.defpath)
    require(age is not None)
    root_fd = directory(input_path)
    parent_fd = stage_fd = None
    handles = []
    stage_name = None
    published = False
    try:
        parent_fd = directory(output_path)
        root_signature = signature(os.fstat(root_fd))
        entries, handles = selection(root_fd)
        stage_name = '.pending-' + uuid.uuid4().hex
        os.mkdir(stage_name, mode=0o700, dir_fd=parent_fd)
        stage_fd = os.open(stage_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
        artifacts = []
        for entry, (_, fd, before) in zip(entries, handles[1:]):
            stable_file(root_fd, entry['file'], fd, before)
            name = NAME.fullmatch(entry['file']).group(1) + '.age'
            target = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=stage_fd)
            try:
                encrypt(fd, target, recipient, entry, age)
            finally:
                os.close(target)
            stable_file(root_fd, entry['file'], fd, before)
            cipher_fd = open_file(stage_fd, name)
            try:
                ciphertext(cipher_fd)
                checksum, size = hash_fd(cipher_fd)
            finally:
                os.close(cipher_fd)
            artifacts.append({'file': name, 'size': size, 'sha256': checksum})
        manifest = {'version': 1, 'encryption': 'age-X25519',
                    'recipient_sha256': digest(recipient.encode()), 'artifacts': artifacts}
        raw = (json.dumps(manifest, sort_keys=True, separators=(',', ':')) + '\n').encode()
        write_file(stage_fd, 'manifest.sanitized.json', raw)
        sums = {a['file']: a['sha256'] for a in artifacts}
        sums['manifest.sanitized.json'] = digest(raw)
        write_file(stage_fd, 'checksums.sha256', ''.join(f'{sums[n]}  {n}\n' for n in sorted(sums)).encode())
        validate_kit(stage_fd, recipient)
        for name, fd, before in handles:
            stable_file(root_fd, name, fd, before)
        require(signature(os.fstat(root_fd)) == root_signature)
        unchanged_directory(input_path, root_fd)
        unchanged_directory(output_path, parent_fd)
        os.fsync(stage_fd)
        final_name = uuid.uuid4().hex
        require(final_name not in os.listdir(parent_fd))
        os.rename(stage_name, final_name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        published = True
        os.fsync(parent_fd)
        return final_name
    finally:
        for _, fd, _ in handles:
            os.close(fd)
        if stage_fd is not None:
            os.close(stage_fd)
        if stage_name is not None and not published:
            # Directory fd keeps cleanup anchored even if an ancestor was renamed.
            shutil.rmtree(stage_name, dir_fd=parent_fd)
        if parent_fd is not None:
            os.close(parent_fd)
        os.close(root_fd)


def interrupted(_number, _frame):
    # Let the export finally blocks stop age and remove unpublished ciphertext.
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, signal.SIG_IGN)
    raise InterruptedError()


def main():
    os.umask(0o077)
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['export', 'verify'])
    parser.add_argument('--recipient', required=True)
    parser.add_argument('--input')
    parser.add_argument('--output')
    parser.add_argument('--kit')
    args = parser.parse_args()
    try:
        if args.operation == 'export':
            require(args.input and args.output and not args.kit)
            export(args.input, args.output, args.recipient)
        else:
            require(args.kit and not args.input and not args.output)
            fd = directory(args.kit)
            try:
                validate_kit(fd, args.recipient)
            finally:
                os.close(fd)
    except (Exception, KeyboardInterrupt):
        print('Recovery operation rejected; no sensitive diagnostics emitted.', file=sys.stderr)
        return 1
    print('Recovery operation complete; restore remains unverified.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
