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
            if not username or not password:
                logging.warning("No Bluesky credentials provided, operating in unauthenticated mode")
                self.is_authenticated = False
                return False
                
            # Try to login
            logging.info(f"Attempting to login with username: {username}")
            session = self.client.login(username, password)
            self.is_authenticated = True
            logging.info("Successfully logged in to Bluesky")
            return True
        except Exception as e:
            logging.error(f"Failed to login to Bluesky: {e}")
            self.is_authenticated = False
            return False

    def fetch_posts_by_keyword(self, keyword, limit=10):
        """Fetch posts containing the given keyword."""
        try:
            response = self.client.app.bsky.feed.search_posts({"q": keyword, "limit": limit})
            
            # Debug full response structure
            logging.debug(f"Response structure: {response}")
            
            posts = []
            for post in response.posts:
                try:
                    # Extract text based on current API structure
                    if hasattr(post, 'record') and hasattr(post.record, 'text'):
                        posts.append(post.record.text)
                    elif hasattr(post, 'post') and hasattr(post.post, 'record') and hasattr(post.post.record, 'text'):
                        posts.append(post.post.record.text)
                    elif hasattr(post, 'value') and hasattr(post.value, 'text'):
                        posts.append(post.value.text)
                    # New structure handling for current API
                    else:
                        # Get all available attributes to find the text
                        attrs = dir(post)
                        logging.debug(f"Post attributes: {attrs}")
                        
                        # Try to find text in various locations
                        if 'text' in attrs:
                            posts.append(post.text)
                        elif hasattr(post, 'reply') and hasattr(post.reply, 'root') and hasattr(post.reply.root, 'record'):
                            posts.append(post.reply.root.record.text)
                        elif hasattr(post, 'params') and hasattr(post.params, 'text'):
                            posts.append(post.params.text)
                        # Attempt to extract from nested objects
                        else:
                            # Convert to dictionary for easier exploration
                            post_dict = post.dict() if hasattr(post, 'dict') else vars(post)
                            logging.debug(f"Post dictionary: {post_dict}")
                            
                            # Extract text from the dictionary (check common paths)
                            if 'record' in post_dict and isinstance(post_dict['record'], dict) and 'text' in post_dict['record']:
                                posts.append(post_dict['record']['text'])
                            elif 'text' in post_dict:
                                posts.append(post_dict['text'])

                except Exception as e:
                    logging.warning(f"Could not extract text from post: {e}")
            
            return posts
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
