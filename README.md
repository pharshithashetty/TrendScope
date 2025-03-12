# TrendScope

TrendScope is a Flask-based web application that curates trending social media topics in real-time, featuring a responsive UI and secure API integration.

## Overview

TrendScope empowers users to stay updated with the latest trends by aggregating posts from social media platforms. It uses OAuth 2.0 for secure authentication, calculates trending scores for posts, and provides a sleek, interactive frontend for an engaging user experience.

## Features

- Real-time aggregation of trending topics from social media.
- Secure OAuth 2.0 authentication for API access.
- Custom trending score algorithm based on likes and shares.
- Interactive frontend with search suggestions and dynamic post cards.
- Robust backend with RSS fallback for content retrieval.

## Prerequisites

- Python 3.6 or higher
- Git
- A social media account and app credentials (e.g., Client ID and Secret)

## Setup

Follow these steps to set up TrendScope locally:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/pharshithashetty/TrendScope.git
   cd TrendScope
Create and Activate a Virtual Environment:
# Windows
python -m venv .venv
.venv\Scripts\activate
# Unix/Linux/Mac
python -m venv .venv
source .venv/bin/activate

Install Dependencies:
pip install -r requirements.txt
Set Up Environment Variables:

Create a .env file in the project root:
MASTODON_CLIENT_ID=your_client_id_here
MASTODON_CLIENT_SECRET=your_client_secret_here
MASTODON_REDIRECT_URI=http://localhost:5000/callback
Replace the values with your app credentials.

Run the Application:
python app.py

Access the App:
Open your browser and go to http://localhost:5000.

Usage
Search Trends: Use the search bar to find trending topics by keyword.
Explore Posts: View curated posts with trending scores, likes, and shares.
Read More: Click "Read More" to visit the original post on the social media platform.

Project Structure
TrendScope/
├── app.py             # Main Flask application
├── index.html         # Frontend HTML template
├── requirements.txt   # Python dependencies
├── .env               # Environment variables (not tracked)
├── .gitignore         # Git ignore file
└── README.md          # Project documentation

Contributing
Contributions are welcome! Please fork the repository, create a new branch, and submit a pull request with your changes.

License
This project is licensed under the MIT License.

Contact
For questions or feedback, reach out to pharshithashetty.
