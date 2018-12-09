from flask import Flask, render_template, url_for, redirect, request
from flask_sqlalchemy import SQLAlchemy
from twitter_listener import get_tweets

app = Flask(__name__)
app.config["debug"] = True

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(username="rtflynn", password="herpaderp", hostname="rtflynn.mysql.pythonanywhere-services.com", databasename="rtflynn$twitter_data")
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Tweet(db.Model):
    __tablename__ = "tweets"
    id = db.Column(db.Integer, primary_key = True)
    tweet_text = db.Column(db.String(4096))
    tweet_language = db.Column(db.String(128))
    num_retweets = db.Column(db.Integer)


def convert_TweetSpreadsheet_to_Tweet_list(spreadsheet):
    list = []
    for i in range(len(spreadsheet)):
        tweet = Tweet(tweet_text = spreadsheet.tweet_texts[i], tweet_language = spreadsheet.languages[i], num_retweets = spreadsheet.num_retweets[i])
        list.append(tweet)
    return list


def get_tweet_text(some_tweet):
    if some_tweet.tweet_text:
        return some_tweet.tweet_text
    else:
        return ""


def sort_tweets_by_tweet_text(tweet_list):
    tweet_list.sort(key = get_tweet_text)


def remove_duplicates_by_tweet_text(sorted_tweet_list):
    list_length = len(sorted_tweet_list)
    if list_length <= 1:
        return
    cursor_location = 0
    while cursor_location < list_length - 1:
        if sorted_tweet_list[cursor_location].tweet_text == sorted_tweet_list[cursor_location + 1].tweet_text:
            del sorted_tweet_list[cursor_location + 1]
            list_length -=1
        else:
            cursor_location += 1


def get_distinct_tweets(num_tweets_to_grab = 30, search_text = ""):
    mySpreadsheet = get_tweets(num_tweets_to_grab = num_tweets_to_grab, search_text=[search_text])
    tweet_list = convert_TweetSpreadsheet_to_Tweet_list(mySpreadsheet)
    sort_tweets_by_tweet_text(tweet_list)
    remove_duplicates_by_tweet_text(tweet_list)
    return tweet_list


def parse_search_text(search_text):
    """ Given a string like 'cats, dogs', returns the list ['cats', 'dogs']. """
    search_terms = search_text.split(",")
    temp_list = []
    for i in range(len(search_terms)):
        term = search_terms[i].strip()
        temp_list.append(term)
    return temp_list


def collect_tweets_with_our_term(term, tweet_list):
    match_list = []
    match_count = 0
    for tweet in tweet_list:
        if term in tweet.tweet_text:
            match_list.append(tweet)
            match_count += 1
    return match_list, match_count


def concatenate_all_tweets(match_list, num_tweets_to_save = 50):
    long_tweet_string = ""
    counter = 0
    num_tweets_to_concat = min(num_tweets_to_save, len(match_list))
    while counter < num_tweets_to_concat:
        current_tweet = match_list[counter].tweet_text
        current_tweet = '{message: <160}'.format(message=current_tweet)
        long_tweet_string += current_tweet
        counter += 1
    return long_tweet_string


def un_concatenate_long_string(long_string):
    tweet_size = 160
    num_strings = int(len(long_string)/tweet_size)
    tweet_texts = []
    for i in range(num_strings):
        tweet_text = long_string[160*i : 160*(i+1)]
        tweet_text = tweet_text.replace("\n","")                #newlines can reeeeally screw up the javascript because of how jinja2 works.
        tweet_text = tweet_text.rstrip()
        tweet_texts.append(tweet_text)
    return tweet_texts


class Twitter_Graph(db.Model):
    num_tweets_to_save = 50
    __tablename__  = "Twitter_Graph_Stats"
    id = db.Column(db.Integer, primary_key = True)
    all_tweet_search_terms = db.Column(db.String(280))
    tweet_search_term = db.Column(db.String(280))
    tweet_texts_glued_together = db.Column(db.String(280*num_tweets_to_save))
    number_of_distinct_tweets = db.Column(db.Integer)


def create_twitter_graphs(num_tweets_to_grab = 300, num_tweets_to_save = 50, search_text = ""):
    twitter_graphs = []
    search_terms = parse_search_text(search_text)
    tweet_list = get_distinct_tweets(num_tweets_to_grab = num_tweets_to_grab, search_text = search_text)
    for term in search_terms:
        match_list, match_count = collect_tweets_with_our_term(term = term, tweet_list = tweet_list)
        long_tweet_string = concatenate_all_tweets(match_list = match_list, num_tweets_to_save = num_tweets_to_save)
        graph = Twitter_Graph(all_tweet_search_terms = search_text, tweet_search_term = term, tweet_texts_glued_together = long_tweet_string, number_of_distinct_tweets = match_count)
        twitter_graphs.append(graph)
    return twitter_graphs


def create_title(title_terms):
    title = title_terms[0]
    for i in range(len(title_terms) - 1):
        title += " vs "
        title += title_terms[i+1]
    return title


def convert_from_twitter_graph_to_google_graph(twitter_graphs_from_same_search):
    search_term_to_tweets_dict = {}
    google_graph_data = []
    title_terms = []

    for tgraph in twitter_graphs_from_same_search:

        all_tweet_search_terms = tgraph.all_tweet_search_terms              # a string, like "cat, dog, panda"
        particular_search_term = tgraph.tweet_search_term                   # a string like "cat"
        num_distinct_tweets = tgraph.number_of_distinct_tweets              # counts number of tweets containing 'cat'
        concatenated_tweet_texts = tgraph.tweet_texts_glued_together        # all tweets containing 'cat' concatenated together
        text_list = un_concatenate_long_string(concatenated_tweet_texts)    # all tweets containing 'cat' unpacked into a list
        search_terms = parse_search_text(all_tweet_search_terms)            # list of search terms, ['cat', 'dog']

        graph_contribution = [particular_search_term, num_distinct_tweets]  # ['cat', 56]  if there were 56 tweets containing 'cat'
        google_graph_data.append(graph_contribution)                        # [['cat', 56], ['dog', 35]]

        search_term_to_tweets_dict[particular_search_term] = text_list      # this_dict['cat'] = list of tweets containing cat

        title_terms = search_terms                                          # ['cat', 'dog', 'panda']
        title = create_title(title_terms)                                   # string 'cat vs dog vs panda' for use in chart title

        unique_id = ""
        for i in range(len(title_terms)):
            unique_id += title_terms[i]                                     # each Google Chart needs a unique name, or the tooltip events won't work properly.
                                                                            # this implementation is not great, but works for now.
    return google_graph_data, text_list, title_terms, title, unique_id, search_term_to_tweets_dict


def collect_twitter_graphs_with_same_search(twitter_graphs):
    tgraph_collections = []
    tgraph_temp_dict = {}
    index = 0
    for tgraph in twitter_graphs:
        our_search_terms = tgraph.all_tweet_search_terms
        if our_search_terms in tgraph_temp_dict:
            tgraph_collections[tgraph_temp_dict[our_search_terms]].append(tgraph)
        else:
            tgraph_collections.append([tgraph])
            tgraph_temp_dict[our_search_terms] = index
            index += 1
    return tgraph_collections


def convert_all_from_twitter_graphs_to_google_graphs(twitter_graphs):
    google_graphs = []
    tgraphs_collected_according_to_search = collect_twitter_graphs_with_same_search(twitter_graphs)
    for i in range(len(tgraphs_collected_according_to_search)):
        g_graph, term_dict, title_terms, title, unique_id, search_term_to_tweets_dict = convert_from_twitter_graph_to_google_graph(tgraphs_collected_according_to_search[i])
        google_graphs.append([g_graph, term_dict, title_terms, title, unique_id, search_term_to_tweets_dict])
    return google_graphs


def get_all_google_graphs():
    twitter_graphs = Twitter_Graph.query.all()
    return convert_all_from_twitter_graphs_to_google_graphs(twitter_graphs)



@app.route('/', methods = ["GET", "POST"])
def index():
    if request.method == "GET":
        twitter_graphs = get_all_google_graphs()
        return render_template("google_charts.html", twitter_graphs = twitter_graphs)
    else:
        search_text = request.form["search_form_entry"]
        tweet_list = get_distinct_tweets(num_tweets_to_grab = 100, search_text = search_text)
        for i in range(len(tweet_list)):
            tweet = tweet_list[i]
            db.session.add(tweet)
        db.session.commit()

        twitter_graphs = create_twitter_graphs(num_tweets_to_grab = 100, num_tweets_to_save = 50, search_text = search_text)
        for i in range(len(twitter_graphs)):
            graph = twitter_graphs[i]
            db.session.add(graph)
        db.session.commit()

        return redirect(url_for("index"))


