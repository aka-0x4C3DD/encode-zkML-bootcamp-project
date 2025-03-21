from atproto import Client
import logging
from src.api.keyword_extractor import KeywordExtractor

class BlueskyAPI:
    def __init__(self, username=None, password=None):
        self.client = Client()
        self.is_authenticated = False
        self.keyword_extractor = KeywordExtractor()
        if username and password:
            self.login(username, password)

    def login(self, username, password):
        try:
            self.client.login(username, password)
            self.is_authenticated = True
            logging.info("Successfully logged in to Bluesky")
        except Exception as e:
            logging.error(f"Failed to login to Bluesky: {e}")
            self.is_authenticated = False

    def fetch_posts_by_keyword(self, keyword, limit=10):
        """Fetch posts containing the given keyword."""
        try:
            response = self.client.app.bsky.feed.search_posts({"q": keyword, "limit": limit})
            return [post.text for post in response.posts]
        except Exception as e:
            logging.error(f"Error fetching posts by keyword: {e}")
            return []

    def fetch_posts_by_hashtag(self, hashtag, limit=10):
        """Fetch posts with the given hashtag."""
        # Remove # if present
        if hashtag.startswith("#"):
            hashtag = hashtag[1:]
        return self.fetch_posts_by_keyword(f"#{hashtag}", limit)
    
    def fetch_recent_posts(self, limit=10):
        """Fetch recent posts from the timeline."""
        try:
            if not self.is_authenticated:
                logging.warning("Authentication required to fetch timeline")
                return []
            
            response = self.client.app.bsky.feed.get_timeline({"limit": limit})
            return [post.post.record.text for post in response.feed]
        except Exception as e:
            logging.error(f"Error fetching recent posts: {e}")
            return []

    def fetch_posts_for_question(self, question, limit=20):
        """
        Strategy to fetch relevant posts for a question using advanced NLP:
        1. Extract keywords using spaCy NLP
        2. Search for each keyword
        3. Combine and deduplicate results
        """
        # Use advanced keyword extraction
        keywords = self.keyword_extractor.extract_keywords_from_question(question)
        
        if not keywords:
            # Fallback to simple extraction if NLP fails
            keywords = [word.lower() for word in question.split() 
                     if len(word) > 4 and word.lower() not in ['about', 'what', 'where', 'when', 'which', 'who', 'why', 'how']]
        
        logging.info(f"Extracted keywords: {keywords}")
        
        all_posts = []
        posts_per_keyword = limit // len(keywords) if keywords else limit
        
        for keyword in keywords:
            posts = self.fetch_posts_by_keyword(keyword, limit=posts_per_keyword)
            all_posts.extend(posts)
        
        # Deduplicate
        return list(set(all_posts))
