import os
import os.path

for dirpath, dirnames, filenames in os.walk('earwax'):
    for filename in filenames:
        if not filename.endswith('.py'):
            continue
        path = os.path.join(dirpath, filename)
        with open(path, 'r') as f:
            for i, line in enumerate(f.readlines()):
                line = line.strip()
                if line.endswith('"""'):
                    if not line.startswith('"""') and "'''" not in line:
                        print(f'{path}: {i + 1}: {line}')
