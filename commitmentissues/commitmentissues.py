import requests
import time
import os
import json
import config
import tweepy
import datetime

# GitHub configuration
SEARCH_QUERY = 'fuck OR fucking OR bullshit OR shit OR idiot OR damn OR hell OR ass OR crap OR bitch OR bastard OR wtf OR lmao OR rofl'  # Keywords to search for

# File to save state
STATE_FILE = os.path.join(os.path.dirname(__file__), 'bot_state.json')

# Set up Twitter API client
client = tweepy.Client(
    consumer_key=config.TWITTER_API_KEY,
    consumer_secret=config.TWITTER_API_SECRET,
    access_token=config.TWITTER_ACCESS_TOKEN,
    access_token_secret=config.TWITTER_ACCESS_TOKEN_SECRET,
    bearer_token=config.BEARER_TOKEN
)

def load_state():
    """Load the state from the state file, or initialize if it doesn't exist."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"seen_commits": []}

def save_state(seen_commits):
    """Save the seen_commits set to the state file."""
    with open(STATE_FILE, 'w') as f:
        json.dump({"seen_commits": list(seen_commits)}, f)

def search_commits(query):
    """Search GitHub commits with the given query, sorted by committer date descending."""
    url = 'https://api.github.com/search/commits'
    params = {
        'q': query,
        'sort': 'committer-date',  # Sort by committer date
        'order': 'desc'           # Newest first
    }
    headers = {
        'Accept': 'application/vnd.github+json'
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.RequestException as e:
        print(f"GitHub API error: {e}")
        return {"items": []}

def main():
    # Load initial state
    state = load_state()
    seen_commits = set(state['seen_commits'])
    
    while True:
        # Get current UTC date and time in ISO 8601 format (e.g., '2023-10-06T12:34:56Z')
        current_datetime = datetime.datetime.now(datetime.UTC).isoformat() + 'Z'
        # Construct query to include only commits up to the current date/time
        full_query = f"{SEARCH_QUERY} committer-date:<={current_datetime}"
        
        # Fetch commits
        results = search_commits(full_query)
        commits = results.get('items', [])
        
        if not commits:
            print("No new commits found.")
            time.sleep(43200)  # Sleep for 12 hours
            continue
        
        # Process the first unseen commit
        for commit in commits:
            commit_sha = commit['sha']
            if commit_sha not in seen_commits:
                commit_message = f"\"{commit['commit']['message']}\" - {commit['commit']['author']['name']}\n{commit['html_url']}"
                
                # Truncate tweet if too long (Twitter limit is 280 characters)
                max_tweet_length = 280
                if len(commit_message) > max_tweet_length:
                    # Leave space for '... URL: ' and the URL itself
                    # Assuming URL is around 50 chars after t.co shortening
                    # This is a rough estimate, actual shortened URL length can vary
                    truncation_length = max_tweet_length - len(commit['html_url']) - len('... URL: ')
                    commit_message = f"'{commit['commit']['message'][:truncation_length].strip()}...\nURL: {commit['html_url']}"

                try:
                    client.create_tweet(text=commit_message)
                    print('Tweet successfully sent!')
                    seen_commits.add(commit_sha)
                    save_state(seen_commits)
                    break  # Exit loop after tweeting one commit
                except tweepy.TweepyException as e:
                    print(f"Twitter API error: {e}")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
        else:
            print("All new commits have been posted.")
        
        time.sleep(43200)  # Sleep for 12 hours

if __name__ == '__main__':
    main()