import requests
import time
import os
import json
import config
import tweepy
import datetime

# GitHub configuration
SEARCH_QUERY_TERMS = ['fuck', 'fucking', 'bullshit', 'shit', 'idiot', 'damn', 'hell', 'ass', 'crap', 'bitch', 'bastard', 'wtf', 'lmao', 'rofl']  # Keywords to search for

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
        current_datetime = datetime.datetime.now(datetime.UTC).isoformat() + 'Z'
        all_commits = []
        seen_shas_in_current_cycle = set()

        # Split search terms into chunks of 6 (5 OR operators)
        for i in range(0, len(SEARCH_QUERY_TERMS), 6):
            chunk = SEARCH_QUERY_TERMS[i:i+6]
            query_chunk = ' OR '.join(chunk)
            full_query = f"{query_chunk} committer-date:<={current_datetime}"
            
            # Fetch commits for the current chunk
            results = search_commits(full_query)
            commits_for_chunk = results.get('items', [])
            
            for commit in commits_for_chunk:
                commit_sha = commit['sha']
                if commit_sha not in seen_shas_in_current_cycle:
                    all_commits.append(commit)
                    seen_shas_in_current_cycle.add(commit_sha)

        if not all_commits:
            print("No new commits found.")
            time.sleep(43200)  # Sleep for 12 hours
            continue
        
        # Process the first unseen commit from the merged results
        for commit in all_commits:
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