#!/usr/bin/python3.6
from tweepy_setup import auth
from tweepy.streaming import StreamListener
from tweepy import Stream
from twitter_code_dicts import langs
import json


class TweetSpreadsheet:
    """
    Keeps track of the language, number of retweets, anc content of tweets grabbed by our TweetGrabber
    """
    def __init__(self):
        self.languages = []
        self.num_retweets = []
        self.tweet_texts = []

    def __len__(self):
        if len(self.languages) == len(self.num_retweets) == len(self.tweet_texts):
            return len(self.languages)
        else:
            return 0

    def add_language(self, lang):
        if lang:
            self.languages.append(lang)
        else:
            self.languages.append("NONE")

    def add_num_retweets(self, num):
        self.num_retweets.append(num)

    def add_tweet_text(self, text):
        self.tweet_texts.append(text)

    def get_all_lists(self):
        return self.languages, self.num_retweets, self.tweet_texts


class Listener(StreamListener):
    """
    Listener(num_tweets_to_grab=1000, min_num_retweets=0, spreadsheet=TweetSpreadSheet())
    Sets up a StreamListener which streams tweets.  Filters out tweets with fewer than
    min_num_retweets retweets.  Among those which have more than that number of retweets,
    stores the number of retweets, the tweet text, and the language of the tweet into the
    spreadsheet.  Closes the Stream once it's stored the contents of num_tweets_to_grab
    tweets.  Returns nothing, so the spreadsheet needs to exist outside of this method and
    be passed in if we want to retain any of this.
    """
    def __init__(self, num_tweets_to_grab=1000, min_num_retweets=0, spreadsheet=TweetSpreadsheet()):
        StreamListener.__init__(self)
        self.counter = 0
        self.num_tweets_to_grab = num_tweets_to_grab
        self.spreadsheet = spreadsheet
        self.min_num_retweets = min_num_retweets

    def on_data(self, data):
        unpacked_tweet = json.loads(data)
        if "retweeted_status" in unpacked_tweet:
            num_retweets = unpacked_tweet["retweeted_status"]["retweet_count"]
        else:
            num_retweets = 0

        if num_retweets < self.min_num_retweets:
            return True

        self.spreadsheet.add_num_retweets(num_retweets)
        if "text" in unpacked_tweet:
            self.spreadsheet.add_tweet_text(unpacked_tweet["text"])
        if "lang" in unpacked_tweet:
            if unpacked_tweet["lang"] in langs:
                self.spreadsheet.add_language(langs[unpacked_tweet["lang"]])
            else:
                self.spreadsheet.add_language("NONE")


        self.counter += 1
        if self.counter == self.num_tweets_to_grab:
            return False
        return True

    def on_error(self, status):
        print("on_error occurred with error code:")
        print(status)
        return False



def get_tweets(num_tweets_to_grab=1000, min_num_retweets=0, spreadsheet=TweetSpreadsheet(), search_text=["Hello"]):
    twitter_stream = Stream(auth=auth, listener=Listener(num_tweets_to_grab=num_tweets_to_grab, min_num_retweets=min_num_retweets, spreadsheet=spreadsheet))
    twitter_stream.filter(track=search_text)
    return spreadsheet
