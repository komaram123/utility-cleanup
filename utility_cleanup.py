import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

GITHUB_TOKEN = os.getenv('SECRET_KEY')


# Constants
REPO_LIST_FILE = 'masterRepoList.txt'
TW = timedelta(days=365)  # Time Window of 1 year

# Function to get repo's branches
def get_branches(repo):
    url = f'https://api.github.com/repos/{repo}/branches'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else []

# Function to check the last commit of a branch
def get_last_commit(repo, branch):
    url = f'https://api.github.com/repos/{repo}/commits/{branch}'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        commit_data = response.json()
        return commit_data['commit']['committer']['date']
    return None

# Function to check if a branch is stale
def is_stale(last_commit_date):
    last_commit_datetime = datetime.strptime(last_commit_date, '%Y-%m-%dT%H:%M:%SZ')
    return datetime.utcnow() - last_commit_datetime > TW

# Function to delete a branch
def delete_branch(repo, branch):
    url = f'https://api.github.com/repos/{repo}/git/refs/heads/{branch}'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.delete(url, headers=headers)
    return response.status_code == 204

# Main function to process repositories and branches
def clean_repos():
    with open(REPO_LIST_FILE, 'r') as f:
        repos = f.readlines()

    for repo in repos:
        repo = repo.strip()
        print(f"Processing repository: {repo}")
        branches = get_branches(repo)

        if not branches:
            print(f"No branches found in {repo}. Skipping.")
            continue

        stale_branches = []
        for branch in branches:
            branch_name = branch['name']
            last_commit_date = get_last_commit(repo, branch_name)
            if last_commit_date and is_stale(last_commit_date):
                stale_branches.append(branch_name)

        if stale_branches:
            print(f"Stale branches in {repo}: {stale_branches}")
            confirm = input("Do you want to delete these branches? (y/n): ")
            if confirm.lower() == 'y':
                for branch in stale_branches:
                    if delete_branch(repo, branch):
                        print(f"Deleted branch: {branch}")
                    else:
                        print(f"Failed to delete branch: {branch}")
            else:
                print("No branches deleted.")
        else:
            print(f"No stale branches found in {repo}.")

        # Recommend repo deletion if all branches are stale
        if len(stale_branches) == len(branches):
            print(f"Recommendation: Delete repository {repo} as all branches are stale.")

if _name_ == "_main_":
    clean_repos()