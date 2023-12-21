import time
from dotenv import load_dotenv
import pandas as pd
import subprocess
import os
import re

# Load github token from environment variable
load_dotenv()  
TOKEN = os.environ.get('GITHUB_TOKEN')

if TOKEN is None:
    raise ValueError("Please set the GITHUB_TOKEN in the .env file.")


def get_commit_history_as_csv(repo_owner, repo_name):
  """
  Collects and saves the commit history of a GitHub repository as a CSV file.
  
  This function clones the specified repository to the local machine, extracts commit information using 
  the 'git log' command, and then saves this information in a CSV file in the current working directory.
  It requires the GitHub username or organization (repo_owner) and the repository name (repo_name).

  :param str repo_owner: The GitHub username or organization of the repository. Example: 'microsoft'
  :param str repo_name: The name of the repository. Example: 'vscode'
  
  The function does not return any value. It saves the commit history to a CSV file named 
  '{repo_name}_commit_history.csv' in the current working directory.

  Example usage: 
  get_commit_history_as_csv('microsoft','vscode')
  """
  print(f"\n##### Collecting Data for {repo_name} Repository #####") # add text to make console output more readable
  # Check if repo has already been processed
  if repo_already_existing(repo_owner, repo_name, repos):
    print(f"Repo has already been processed -> Exit function")
    return

  start_time = time.time()  # Capture the start time

  # Create a temporary folder that will store the repo
  temp_dir = "temp_repo"
  # Clone repo and collect commits
  clone_repo(repo_owner, repo_name, temp_dir)
  complete_commit_history = collect_commits(temp_dir)

  # Convert commit history to data frame and export CSV file
  commit_history_df = pd.DataFrame(complete_commit_history)
  commit_history_df.to_csv(f'./data/{repo_name}_commit_history.csv', index=False)

  # Cleanup: Remove the cloned repo
  subprocess.run(['rm', '-rf', temp_dir], check=True)

  end_time = time.time()  # Capture the end time
  elapsed_time = end_time - start_time  # Calculate elapsed time
  print(f"##### Collecting data from {repo_name} took {elapsed_time:.2f} seconds. #####")



def repo_already_existing(owner, repo_name, repo_list):
  for repo in repo_list:
    if repo["owner"] == owner and repo["repo_name"] == repo_name:
      return True
    elif repo["repo_name"] == repo_name:
      print("Project name already exists")
      
  return False



def clone_repo(repo_owner, repo_name, temp_dir):
  # Check if folder already exists
  if os.path.exists(temp_dir):
      raise FileExistsError(f"'{temp_dir}' already exists. Please provide a different path or remove the directory.")
  else:
    os.makedirs(temp_dir)

  # Clone the repository with all branches
  repo_url = f"https://{TOKEN}@github.com/{repo_owner}/{repo_name}"
  subprocess.run(['git', 'clone', '--mirror', repo_url, temp_dir], check=True)
  
  return

def collect_commits(temp_dir):
  """
  This function uses the git log command to collect the complete commit history of a specified repository.
  The data then gets stored in a file centric way so in the end we get a df with changed files as rows (commits might 
  get split into multiple lines). This makes the data processing step easier.
  """
  # Run git log with --numstat and split output into lines
  # Increase rate limit to collect all files from bigger repos
  log_output = subprocess.getoutput(
      f"git -C {temp_dir} -c diff.renameLimit=10000 log --all --pretty=format:'%H | %an | %ad | %s' --numstat --date=format:'%Y-%m-%d %H:%M:%S'"
      .replace('\n', '\\n') # replace newline character in commit messages
  ).split('\n')

  # Initialize an empty list for storing file changes
  file_changes = []

  # Regular expression pattern to match commit metadata, allowing for empty messages and missing authors
  commit_pattern = re.compile(r'^([0-9a-fA-F]{40}) \| (.*?) \| (.+?) \| (.*)$')
  # Regular expression pattern to match numstat data
  numstat_pattern = re.compile(r'^(\d+|-)\s+(\d+|-)\s+(.+)$')

  # Variables to hold current commit information
  current_hash = None
  current_author = None
  current_date = None
  current_message = None

  # Iterate over each line in log output
  for line in log_output:
    commit_match = commit_pattern.match(line)
    numstat_match = numstat_pattern.match(line)
    if commit_match:
      # When a new commit is found, update current commit information
      current_hash, author, current_date, current_message = commit_match.groups()
      # Set default author if missing
      current_author = author if author else "Unknown Author"  
    elif numstat_match and current_hash is not None:
      # This line contains numstat data (number of lines added and removed, and file name)
      additions, deletions, file_name = numstat_match.groups()
      file_changes.append({
        "hash": current_hash,
        "author": current_author,
        "date": current_date,
        "message": current_message,
        "file": file_name,
        "additions": additions,
        "deletions": deletions
      })
    elif line.strip():
      # If the line is not empty and does not match the expected patterns, it's unexpected
      print(f"Unexpected format in line: {line}")  # Debugging information

  print(len(file_changes), "file changes were collected...")
  return file_changes

#####################################
# Collect commits from repositories #
#####################################

# List of repositories that were already processed
repos = [
    {"owner": "tensorflow", "repo_name": "tensorflow"},
    {"owner": "keras-team", "repo_name": "keras"},
    {"owner": "pytorch", "repo_name": "pytorch"},
    {"owner": "microsoft", "repo_name": "vscode"},
    {"owner": "microsoft", "repo_name": "PowerToys"},
    {"owner": "facebook", "repo_name": "react"},
    {"owner": "facebook", "repo_name": "react-native"},
    {"owner": "facebook", "repo_name": "create-react-app"},
    {"owner": "home-assistant", "repo_name": "core"},
    {"owner": "flutter", "repo_name": "flutter"},
    {"owner": "microsoftdocs", "repo_name": "azure-docs"},
    {"owner": "automatic1111", "repo_name": "stable-diffusion-webui"},
    {"owner": "vercel", "repo_name": "next.js"},
    {"owner": "langchain-ai", "repo_name": "langchain"},
]

# tensorflow/tensorflow | 179k stars
get_commit_history_as_csv('tensorflow','tensorflow') # 1'039'558 file changes | 374s
# keras-team/keras | 59.8k stars
get_commit_history_as_csv('keras-team','keras') # 91'281 file changes | 46s
# pytorch/pytorch | 72.8k stars
get_commit_history_as_csv('pytorch','pytorch') #  1'797'750 file changes | 581s
# microsoft/vscode | 153k stars
get_commit_history_as_csv('microsoft','vscode') #  651'090 file changes | 190s
# microsoft/PowerToys | 98.9k stars
get_commit_history_as_csv('microsoft','PowerToys') #  154'312 file changes | 57s
# facebook/react | 216k stars
get_commit_history_as_csv('facebook','react') #  266'857 file changes | 135s
# facebook/react-native | 113k stars
get_commit_history_as_csv('facebook','react-native') #  1'570'920 file changes | 451s
# facebook/create-react-app | 101k stars
get_commit_history_as_csv('facebook','create-react-app') #  46'197 file changes | 17s
# home-assistant/core | 64.9k
get_commit_history_as_csv('home-assistant','core') # 1'451'416 file changes | 253s
# flutter/flutter | 159k
get_commit_history_as_csv('flutter','flutter') # 918'396 file changes | 212s
# microsoftdocs/azure-docs | 9.6k
get_commit_history_as_csv('microsoftdocs','azure-docs') # 2'459'682 file changes | 2572s
# automatic1111/stable-diffusion-webui | 114k
get_commit_history_as_csv('automatic1111','stable-diffusion-webui') # 30'459 file changes | 21s
# vercel/next.js | 116k
get_commit_history_as_csv('vercel','next.js') # 405'327 file changes | 414s
# langchain-ai/langchain | 71.2k
get_commit_history_as_csv('langchain-ai','langchain') # 189790 file changes | 51s