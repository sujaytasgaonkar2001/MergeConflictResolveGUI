import os
import re
from git import Repo, InvalidGitRepositoryError

def detect_conflicts_in_file(file_path):
    conflicts = []
    file_content_lines = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.readlines()
        file_content_lines = [l.rstrip('\n') for l in content]

    current = None
    conflict_id = 0

    for idx, line in enumerate(content):
        if line.startswith('<<<<<<<'):
            current = {
                'id': conflict_id,
                'start': idx,
                'end': None,
                'ours': [],
                'theirs': [],
                'state': 'ours',
                'raw': [line]
            }
            conflict_id += 1

        elif line.startswith('======='):
            current['state'] = 'theirs'
            current['raw'].append(line)

        elif line.startswith('>>>>>>>'):
            current['end'] = idx
            current['raw'].append(line)
            conflicts.append(current)
            current = None

        elif current:
            if current['state'] == 'ours':
                current['ours'].append(line.rstrip('\n'))
            else:
                current['theirs'].append(line.rstrip('\n'))
            current['raw'].append(line)

    return file_content_lines, conflicts


def find_conflicting_files(repo_path):
    files = []
    try:
        repo = Repo(repo_path)
        for path in repo.index.unmerged_blobs().keys():
            files.append(path)
    except InvalidGitRepositoryError:
        pass
    return files


def resolve_single_conflict(repo_path, file_path, conflict_id, side, manual_text=None):
    full_path = os.path.join(repo_path, file_path)
    lines = open(full_path, 'r', encoding='utf-8').readlines()
    _, conflicts = detect_conflicts_in_file(full_path)

    target = next((c for c in conflicts if c['id'] == conflict_id), None)
    if not target:
        return False

    resolved = []
    idx = 0

    while idx < len(lines):
        if idx == target['start']:
            if side == 'ours':
                resolved.extend([l + '\n' for l in target['ours']])
            elif side == 'theirs':
                resolved.extend([l + '\n' for l in target['theirs']])
            elif side == 'manual':
                resolved.extend(manual_text.splitlines(keepends=True))
            idx = target['end'] + 1
        else:
            resolved.append(lines[idx])
            idx += 1

    with open(full_path, 'w', encoding='utf-8') as f:
        f.writelines(resolved)

    Repo(repo_path).index.add([file_path])
    return True
