import json, struct, sys, os

ASAR = r"D:\其他\DeepSeekHarness\resources\app.asar"

def read_header(path=ASAR):
    with open(path, 'rb') as f:
        data = f.read(16)
        # asar: uint32 size of the pickle header (4), uint32 header string size, uint32 header json size, uint32 header json string size
        _, _, c, json_size = struct.unpack('<4I', data)
        f.seek(16)
        js = f.read(json_size).decode('utf-8')
    return json.loads(js)

def walk(node, prefix='', depth=0, maxdepth=3, out=None):
    if out is None:
        out = []
    for name, child in node.get('files', {}).items():
        p = prefix + '/' + name
        if 'files' in child:
            out.append((p + '/', None, child.get('unpacked')))
            if depth < maxdepth:
                walk(child, p, depth + 1, maxdepth, out)
        else:
            out.append((p, child.get('size'), child.get('unpacked')))
    return out

if __name__ == '__main__':
    h = read_header()
    maxdepth = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    for p, size, unpacked in walk(h, maxdepth=maxdepth):
        print(f"{p}\t{size}\t{unpacked}")
