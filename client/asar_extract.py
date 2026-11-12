import json, struct, sys, os

ASAR = r"D:\其他\DeepSeekHarness\resources\app.asar"

def read_header(path=ASAR):
    with open(path, 'rb') as f:
        data = f.read(16)
        _, _, c, json_size = struct.unpack('<4I', data)
        f.seek(16)
        js = f.read(json_size).decode('utf-8')
    padded = c - 4
    return json.loads(js), 16 + padded

def find(header, parts):
    node = header
    for p in parts:
        node = node['files'][p]
    return node

def extract(parts, out_path, header=None, base=None):
    if header is None:
        header, base = read_header()
    node = find(header, parts)
    if 'files' in node:
        os.makedirs(out_path, exist_ok=True)
        for name in node['files']:
            extract(parts + [name], os.path.join(out_path, name), header, base)
        return
    off = int(node['offset'])
    size = node['size']
    with open(ASAR, 'rb') as f:
        f.seek(base + off)
        data = f.read(size)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'wb') as f:
        f.write(data)
    print('OK', out_path, size)

if __name__ == '__main__':
    src = sys.argv[1].strip('/').split('/')
    dst = sys.argv[2]
    extract(src, dst)
