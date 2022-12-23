import sys
import os
import time
import argparse

from os.path import exists
from twitter import *
from datetime import datetime, timedelta

TWITTER_KEY=os.environ['TWITTER_KEY']
TWITTER_SECRET=os.environ['TWITTER_SECRET']
TWITTER_APP_NAME=os.environ['TWITTER_APP_NAME']

MY_TWITTER_CREDENTIALS = os.path.expanduser('~/.my_app_credentials')
if not os.path.exists(MY_TWITTER_CREDENTIALS):
    oauth_dance(TWITTER_APP_NAME, TWITTER_KEY, TWITTER_SECRET, MY_TWITTER_CREDENTIALS)
    
oauth_token, oauth_secret = read_token_file(MY_TWITTER_CREDENTIALS)

t = Twitter2(auth=OAuth(oauth_token, oauth_secret, TWITTER_KEY, TWITTER_SECRET), retry=True)

def process_tweet(tweet, is_reply, op_tweet_id = None):
    fields = []
    
    if is_reply:
        file_path = replies_path
        fields.append(op_tweet_id)
    else:
        file_path = op_path
    
    tweet_id = str(tweet["id"])
    fields.append(tweet_id)
    fields.append(tweet["created_at"])
    fields.append(tweet["author_id"])
    
    metrics = tweet["public_metrics"]
    fields.append(str(metrics["like_count"]))
    fields.append(str(metrics["reply_count"]))
    fields.append(str(metrics["quote_count"]))
        
    tweet_text =  '"' + tweet["text"].replace('"', '""').replace("\n", "{NEWLINE}") + '"'
    
    fields.append(tweet_text)
    
    new_line = ",".join(fields) + "\n"
    
    with open(file_path, 'a+', encoding="utf-8") as op_writer:
        op_writer.write(new_line)
        
def process_reply_tweet(tweet):
    referenced_tweets = tweet.get("referenced_tweets")

    if referenced_tweets == None:
        return

    op_tweet_id = referenced_tweets[0].get("id")
    process_tweet(tweet, True, op_tweet_id)
    
    return op_tweet_id

def get_replies_tweets(pagination_token = None):
    query = "(the OR i OR to OR a OR is OR in OR it OR you OR of) lang:en is:reply"
    max_results = 100
    params = {
        "tweet.fields": "public_metrics,referenced_tweets,created_at,author_id,lang"
    }
    sort_order = "relevancy" # Will generally return well liked or relevant tweets

    # Optional args
    cond_args = {"pagination_token": pagination_token } if pagination_token != None else {}

    return t.tweets.search.recent(query=query, max_results=max_results, params=params, sort_order=sort_order, **cond_args)
    

def process_op_tweets(op_tweet_ids):
    op_tweets = t.tweets(ids=",".join(op_tweet_ids),
        params = {
            "tweet.fields": "public_metrics,created_at,author_id,lang"
        }).get("data")
    
    for tweet in op_tweets:
        if tweet["lang"] == "en":  #Only save eng tweets
            process_tweet(tweet, False)
        
# INIT FILES

current_dir = os.getcwd()
op_path = os.path.join(current_dir, "op.csv")
base_labels = "created_at,author_id,like_count,reply_count,quote_count,text" + "\n"

if not exists(op_path):
    with open(op_path, 'w+', encoding="utf-8") as op_writer:
        op_writer.write("op_id," + base_labels)
        
replies_path = os.path.join(current_dir, "replies.csv")
if not exists(replies_path):
    with open(replies_path, 'w+', encoding="utf-8") as op_writer:
        op_writer.write("op_id,reply_id," + base_labels)        

is_first_loop = True
next_token = None
total_replies = 0
total_processed_replies = 0

while next_token != None or is_first_loop:
    is_first_loop = False

    tweets_replies_result = get_replies_tweets(next_token)
    replies = tweets_replies_result.get("data")
    op_tweet_ids = []
    
    for tweet in replies:
        op_tweet_id = process_reply_tweet(tweet)
        
        if op_tweet_id != None:
            op_tweet_ids.append(op_tweet_id)
            total_processed_replies += 1
    
    if len(op_tweet_ids) > 0:
        process_op_tweets(op_tweet_ids)
    
    next_token = tweets_replies_result.get("meta").get("next_token") 
    total_replies += len(replies)
    
    print("Total replies : " + str(total_replies) + ", Total processed replies : " + str(total_processed_replies) + ", Time : " + datetime.utcnow().isoformat())
    
print("Done")        