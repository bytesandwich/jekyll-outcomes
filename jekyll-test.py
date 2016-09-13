#!/usr/bin/python
from __future__ import print_function
import errno
import filecmp
import glob
import os
import re
import shutil
import subprocess


JEKYLL_ROOT = "test"
DIRS = [
    "",
    "_posts",
    "_drafts",
    "_data",
    "_my_output_collection",
    "_my_non_output_collection",
    "_underscore_dir",
    "regular_dir",
]

JEKYLL_IN_DIRS = [ "{}/{}".format(JEKYLL_ROOT, dir) for dir in DIRS ]
JEKYLL_OUT_DIRS = [ "{}/_site/{}".format(JEKYLL_ROOT, re.sub(r'^_', '', dir)) for dir in DIRS ]

subprocess.call(["jekyll", "new", JEKYLL_ROOT])

os.mkdir("{}/_layouts".format(JEKYLL_ROOT))

with open(JEKYLL_ROOT + '/_config.yml', 'a') as config:
    config_add = """
collections:
  my_non_output_collection:
    output: false
  my_output_collection:
    output: true
    """
    config.write(config_add)

with open(JEKYLL_ROOT + '/_layouts/special.html', 'w+') as special_layout:
    special_layout_content = """
    <div>
      <span>special file:</span>
      <div>{{content}}</div>
    </div>
    """
    special_layout.write(special_layout_content)

def append_dir_suffix(file_path, out_path):
    """
    outputs a filename in dir_path with file_path's base, with dir_path's base as a suffix
    if the suffix would begin with '_' the '_' is stripped
    """

    file_name = os.path.basename(file_path)
    out_name = re.sub(r'^_', '', os.path.basename(out_path))
    if out_path.endswith('/'):
        return out_path + file_name
    else:
        return out_path + '/' + file_name.replace(".", "-{}.".format(out_name))

assert append_dir_suffix('/bar/foo.txt', 'a/_b') == 'a/_b/foo-b.txt'
assert append_dir_suffix('/bar/foo.txt', 'a/b') == 'a/b/foo-b.txt'
assert append_dir_suffix('/bar/foo.txt', 'a/b/') == 'a/b/foo.txt'

# copy files into DIRS, adding the dir to the filename
for copy_dir in JEKYLL_IN_DIRS:
    try:
        os.makedirs(copy_dir)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(copy_dir):
            pass
        else:
            raise
    for file_name in os.listdir('/files/'):
        shutil.copy("/files/" + file_name,  append_dir_suffix(file_name, copy_dir))

# run jekyll build from the new jekyll site
p = subprocess.Popen(['jekyll', 'build', '-D'], cwd=JEKYLL_ROOT)
p.wait()

def file_outcome(in_file_name, out_dir):
    expect_file_path = append_dir_suffix(in_file_name, out_dir)
    expect_file_name = os.path.basename(expect_file_path)
    match_pattern = re.sub(r'.[^.]+$', '', expect_file_name)
    match_pattern = re.sub(r'\d+-\d+-\d+-','', match_pattern)
    found_file_path_glob = subprocess.check_output(['find', '{}/_site/'.format(JEKYLL_ROOT), '-name', '*{}.*'.format(match_pattern)]).split('\n')[0:-1]
    if len(found_file_path_glob) == 0:
        return "omitted"

    if len(found_file_path_glob) > 1:
        raise Exception(found_file_path_glob)

    found_file_path = found_file_path_glob[0]

    irregular_move = found_file_path.count('/') > expect_file_path.count('/')
    kept_contents = filecmp.cmp('/files/' + in_file_name, found_file_path)

    if kept_contents and not irregular_move:
        return "copied"
    elif not kept_contents and not irregular_move:
        return "transformed"
    elif not kept_contents and irregular_move:
        return "post transformed"

assert file_outcome('2020-02-02-post-future.md', 'test/_site/') == 'transformed'
assert file_outcome('text.txt', 'test/_site/') == 'copied'
assert file_outcome('2016-05-05-post-normal.md', 'test/_site/posts') == 'post transformed'
assert file_outcome('yaml.yml', 'test/_site/data') == 'omitted'

# header
print("| | " + " | ".join(os.listdir('/files/')) + " |")

# table_body
for out_dir in JEKYLL_OUT_DIRS:
    print("| {} | ".format(out_dir), end="")

    for in_file_name in os.listdir('/files/'):
        print("{} | ".format(file_outcome(in_file_name, out_dir)), end="")
    print("")
