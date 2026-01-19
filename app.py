import os
from flask import Flask, render_template, request, redirect, url_for
from urllib.parse import unquote

from git_utils import (
    find_conflicting_files,
    detect_conflicts_in_file,
    resolve_single_conflict
)

app = Flask(__name__)

REPO_PATH = os.environ.get(
    "GIT_REPO_PATH",
    "/var/fpwork/stasgaon/perf4/perftests-fuzzy"
)

@app.route('/')
def index():
    conflicting_files = find_conflicting_files(REPO_PATH)
    return render_template('index.html', conflicting_files=conflicting_files)

@app.route('/resolve/<path:file_path>')
def resolve_file(file_path):
    decoded_file_path = unquote(file_path)
    full_file_path = os.path.join(REPO_PATH, decoded_file_path)

    file_content_lines, conflicts = detect_conflicts_in_file(full_file_path)

    return render_template(
        'resolve.html',
        file_path=decoded_file_path,
        file_content_lines=file_content_lines,
        conflicts=conflicts
    )

@app.route('/action/resolve', methods=['POST'])
def perform_resolution():
    file_path = request.form['file_path']
    conflict_id = int(request.form['conflict_id'])
    side = request.form['side']
    manual_text = request.form.get('manual_text')

    success = resolve_single_conflict(
        REPO_PATH,
        file_path,
        conflict_id,
        side,
        manual_text
    )

    if success:
        return redirect(url_for('resolve_file', file_path=file_path))
    else:
        return "Error resolving conflict", 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
