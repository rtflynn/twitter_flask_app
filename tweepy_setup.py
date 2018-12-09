import tweepy

consumer_key = "INSERT CONSUMER KEY HERE"
consumer_secret = "INSERT CONSUMER SECRET KEY HERE"
access_token = "INSERT ACCESS TOKEN HERE"
access_token_secret = "INSERT ACCESS TOKEN SECRET HERE"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
tweepy_api = tweepy.API(auth)


