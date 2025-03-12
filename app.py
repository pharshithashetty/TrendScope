from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import random
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder='.')
CORS(app)

# Mastodon instance
MASTODON_INSTANCE = "https://mastodon.social"

# Load secrets from environment variables
CLIENT_ID = os.getenv("MASTODON_CLIENT_ID")
CLIENT_SECRET = os.getenv("MASTODON_CLIENT_SECRET")
REDIRECT_URI = os.getenv("MASTODON_REDIRECT_URI")

# Placeholder for access token (will be fetched)
MASTODON_API_TOKEN = os.getenv("MASTODON_API_TOKEN")

def get_access_token():
    global MASTODON_API_TOKEN
    if not MASTODON_API_TOKEN:
        # Simplified token fetch for client credentials (you may need to use authorization_code flow)
        token_url = f"{MASTODON_INSTANCE}/oauth/token"
        payload = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'client_credentials',  # Use 'authorization_code' if you have a code
            'scope': 'read',
            'redirect_uri': REDIRECT_URI
        }
        response = requests.post(token_url, data=payload)
        if response.status_code == 200:
            MASTODON_API_TOKEN = response.json().get('access_token')
            print(f"Access token obtained: {MASTODON_API_TOKEN}")
        else:
            print(f"Failed to get token: {response.text}")
    return MASTODON_API_TOKEN

def clean_query(query):
    cleaned = query.replace('#', '').strip()
    keywords = cleaned.split()
    if len(keywords) > 1:
        return " ".join(keywords[:3])
    return cleaned

def calculate_trending_score(likes, shares, timestamp):
    hours_ago = (datetime.now(timezone.utc).timestamp() - timestamp) / 3600
    score = (likes + shares * 2) / (hours_ago + 1)
    return round(score, 2)

# Fetch posts from Mastodon with authentication
def fetch_mastodon_posts(query):
    try:
        print(f"Fetching Mastodon posts for query: {query}")
        cleaned_query = clean_query(query)
        access_token = get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
        if not access_token:
            print("No access token; falling back to public timeline.")
            response = requests.get(
                f"{MASTODON_INSTANCE}/api/v1/timelines/public?limit=10&q={cleaned_query}",
                timeout=10
            )
        else:
            # Use search API for authenticated, more relevant results
            response = requests.get(
                f"{MASTODON_INSTANCE}/api/v2/search?type=statuses&q={cleaned_query}&limit=10&resolve=true",
                headers=headers,
                timeout=10
            )
        response.raise_for_status()
        data = response.json()

        post_data = []
        posts = data.get('statuses', data)  # 'statuses' key for search API, direct list for public timeline
        for post in posts:
            # Determine the instance for the post (if not on MASTODON_INSTANCE)
            account = post.get('account', {})
            username = account.get('username', 'Unknown')
            post_id = post.get('id')
            
            # Get the instance domain from the post's URL or account
            post_url = post.get('url')  # The full URL of the post (e.g., https://mastodon.social/@username/123)
            if post_url:
                # Use the post's URL directly
                post_instance_url = post_url
            else:
                # Fallback: Construct the URL using the account's instance
                acct = account.get('acct', username)  # acct is "username@instance" for remote users
                if '@' in acct:
                    instance_domain = acct.split('@')[1]
                    post_instance_url = f"https://{instance_domain}/@{username}/{post_id}"
                else:
                    post_instance_url = f"{MASTODON_INSTANCE}/@{username}/{post_id}"

            image_url = post.get("media_attachments", [{}])[0].get("url") if post.get("media_attachments") else None
            timestamp = datetime.strptime(post.get("created_at"), "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc).timestamp()
            post_data.append({
                "title": f"Toot by @{username}",
                "text": BeautifulSoup(post.get("content", "No text available."), "html.parser").get_text()[:150],
                "id": post_id,
                "url": post_instance_url,  # Use the correct post URL
                "source": "Mastodon",
                "image_url": image_url,
                "likes": post.get("favourites_count", 0),
                "shares": post.get("reblogs_count", 0),
                "timestamp": timestamp,
                "username": username
            })

        for post in post_data:
            post["trending_score"] = calculate_trending_score(post["likes"], post["shares"], post["timestamp"])

        print(f"Fetched {len(post_data)} Mastodon posts.")
        post_data.sort(key=lambda x: x['trending_score'], reverse=True)
        return post_data[:10]
    except Exception as e:
        print(f"Mastodon API error: {str(e)}")
        return []

# Fallback: Scrape public movie-related RSS feeds
def fetch_rss_fallback(query):
    try:
        print(f"Fetching RSS fallback for query: {query}")
        rss_url = "https://www.feedspot.com/inf/1711279"  # Example; replace with a valid movie RSS feed
        response = requests.get(rss_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item")

        post_data = []
        for item in items[:10]:
            title = item.title.text if item.title else "No title"
            if clean_query(query).lower() not in title.lower():
                continue
            description = BeautifulSoup(item.description.text, "html.parser").get_text()[:150] if item.description else "No description"
            link = item.link.text if item.link else "#"
            pub_date = datetime.strptime(item.pubDate.text, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc).timestamp() if item.pubDate else datetime.now(timezone.utc).timestamp()
            post_data.append({
                "title": title,
                "text": description,
                "id": item.guid.text if item.guid else link,
                "url": link,
                "source": "RSS Feed",
                "image_url": None,
                "likes": 0,
                "shares": 0,
                "timestamp": pub_date,
                "username": "FeedSource"
            })

        for post in post_data:
            post["trending_score"] = calculate_trending_score(post["likes"], post["shares"], post["timestamp"])

        print(f"Fetched {len(post_data)} RSS posts.")
        post_data.sort(key=lambda x: x['trending_score'], reverse=True)
        return post_data[:10]
    except Exception as e:
        print(f"RSS fetch error: {str(e)}")
        return []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if code:
        token_url = f"{MASTODON_INSTANCE}/oauth/token"
        payload = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI
        }
        response = requests.post(token_url, data=payload)
        if response.status_code == 200:
            global MASTODON_API_TOKEN
            MASTODON_API_TOKEN = response.json().get('access_token')
            return f"Access token obtained. You can close this window and use the app. Token: {MASTODON_API_TOKEN}"
        return f"Failed to get token: {response.text}"
    return "No authorization code provided."

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query', 'trending')
    print(f"Received search query: {query}")
    try:
        # Try Mastodon first
        posts = fetch_mastodon_posts(query)
        if not posts:
            # Fallback to RSS scraping
            posts = fetch_rss_fallback(query)
            if not posts:
                return jsonify({"error": f"No posts found for '{query}'. Try a different query or check your connection.", "status": "error"})
        
        response = {
            "posts": posts,
            "status": "success"
        }
        return jsonify(response)
    except Exception as e:
        print(f"Error fetching posts: {str(e)}")
        return jsonify({"error": f"Failed to fetch posts: {str(e)}.", "status": "error"})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)