import os

# Adapted from https://stackoverflow.com/a/59950703
def get_commit_hash():
    git_head = os.path.join('.git', 'HEAD')
    
    # Open .git\HEAD file:
    with open(git_head, 'r') as git_head_file:
        # Contains e.g. ref: ref/heads/master if on "master"
        git_head_data = str(git_head_file.read())
    
    # Open the correct file in .git\ref\heads\[branch]
    git_head_ref = os.path.join('.git', *[item.strip() for item in git_head_data.split(' ')[1].split('/')])
    
    # Get the commit hash ([:7] used to get "--short")
    with open(git_head_ref, 'r') as git_head_ref_file:
        commit_id = git_head_ref_file.read().strip()[:7]
        
    return commit_id
