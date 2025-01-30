import requests
import time
import os
import json
import config
import tweepy

# GitHub configuration
SEARCH_QUERY = 'fuck OR fucking OR bullshit OR shit OR idiot'  # Change this to your desired keyword

# Twitter configuration

# Set up Twitter API

# File to save state
STATE_FILE = 'bot_state.json'

client = tweepy.Client(
    consumer_key=config.TWITTER_API_KEY,
    consumer_secret=config.TWITTER_API_SECRET,
    access_token=config.TWITTER_ACCESS_TOKEN,
    access_token_secret=config.TWITTER_ACCESS_TOKEN_SECRET,
    bearer_token=config.BEARER_TOKEN
)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"seen_commits": [], "last_posted_index": 0}

def save_state(seen_commits, last_posted_index):
    with open(STATE_FILE, 'w') as f:
        json.dump({"seen_commits": list(seen_commits), "last_posted_index": last_posted_index}, f)

def search_commits(query):
    url = f'https://api.github.com/search/commits?q=sort:committer-date+{query}'
    headers = {  # Add your GitHub token here
        'Accept': 'application/vnd.github+json'  # Required for commit search
    }
    response = requests.get(url, headers=headers)
    return response.json()


def main():
    # Load the previous state
    state = load_state()
    seen_commits = set(state['seen_commits'])
    last_posted_index = state['last_posted_index']
    
    while True:
        results = search_commits(SEARCH_QUERY)
        commits = results.get('items', [])
        
        if not commits:
            print("No new commits found.")
            time.sleep(43200)  # Wait for the next interval
            continue
        
        # Iterate through the commits starting from the last posted index
        for i in range(last_posted_index, len(commits)):
            commit_message = commits[i]['commit']['message']
            commit_message = f"""'{commits[i]['commit']['message']}'
URL: {commits[i]['html_url']}"""
            commit_sha = commits[i]['sha']
            
            if commit_sha not in seen_commits:
                try:
                    client.create_tweet(text=commit_message)
                    print('Tweet successfully sent!')
                except Exception as e:
                    print('Error:', e)
                print(commit_message)
                seen_commits.add(commit_sha)
                last_posted_index = i + 1  # Update the last posted index
                save_state(seen_commits, last_posted_index)  # Save state after posting
                break
        else:
            # If we reach here, it means we have posted all new commits
            print("All new commits have been posted.")
            last_posted_index = 0  # Reset the index to start from the beginning next time

        time.sleep(43200)  # Comply to X's API limits (100/posts a month = 3 posts a day)

if __name__ == '__main__':
    main()
