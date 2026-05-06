import sys, re

def strip_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    def docstring_replacer(m):
        doc = m.group(1).strip()
        first_line = doc.split('\n')[0]
        return f'# {first_line}'

    content = re.sub(r'\"\"\"(.*?)\"\"\"', docstring_replacer, content, flags=re.DOTALL)
    
    content = re.sub(r'\s*->\s*[^:]+:', ':', content)

    content = re.sub(r'(?<=[a-zA-Z0-9_])\s*:\s*[a-zA-Z_][a-zA-Z0-9_\[\]\| ]*(?=[,\)])', '', content)

    content = re.sub(r'^from models\.exceptions import.*$\n?', '', content, flags=re.MULTILINE)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

for p in ['gui/admin_view.py', 'gui/dashboard.py']:
    try:
        strip_file(p)
        print(f'Processed {p}')
    except Exception as e:
        print(f'Error on {p}: {e}')
