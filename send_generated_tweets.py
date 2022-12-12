#Tweet import
import sys
import os
import time
import argparse

from os.path import exists
from twitter import *
from datetime import datetime, timedelta

import modules.tweet_helper as tweet_helper

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Setup twitter

TWITTER_KEY=os.environ['TWITTER_KEY']
TWITTER_SECRET=os.environ['TWITTER_SECRET']
TWITTER_APP_NAME=os.environ['TWITTER_APP_NAME']

MY_TWITTER_CREDENTIALS = os.path.expanduser('~/.my_app_credentials')
if not os.path.exists(MY_TWITTER_CREDENTIALS):
    oauth_dance(TWITTER_APP_NAME, TWITTER_KEY, TWITTER_SECRET, MY_TWITTER_CREDENTIALS)
    
oauth_token, oauth_secret = read_token_file(MY_TWITTER_CREDENTIALS)
t = Twitter2(auth=OAuth(oauth_token, oauth_secret, TWITTER_KEY, TWITTER_SECRET), retry=True)

# Create model
print("start loading model")
tokenizer = AutoTokenizer.from_pretrained("marca116/twitter_reply_generator")
model = AutoModelForCausalLM.from_pretrained("marca116/twitter_reply_generator")
model.cuda()
print("model loaded")

device = torch.device("cuda")
max_token_length = 180 # About 100 per tweets, better if this number is a little less than the true max (250)

def generate_outputs(input_text, nb_seq):
    text_to_generate = input_text + "{REPLY}"
    
    encoded_input = tokenizer.encode(text_to_generate)
    generated_output = torch.tensor(encoded_input).unsqueeze(0).to(device)
    
    new_max_length = (max_token_length / 2) + len(encoded_input) # Limit the generated tweet to about 280 characters max
    
    outputs = model.generate(
            generated_output, 
            do_sample=True,   
            top_k=50, 
            max_length = new_max_length,
            top_p=0.95, 
            num_return_sequences=nb_seq
        )
    return [tokenizer.decode(o, skip_special_tokens=True).split('{REPLY}')[1]  for o in outputs] 

def get_replies_tweets():
    query = "(the OR i OR to OR a OR is OR in OR it OR you OR of) lang:en is:reply"
    max_results = 10
    params = {
        "tweet.fields": "public_metrics,referenced_tweets,created_at,author_id,lang"
    }
    sort_order = "relevancy"
    
    return t.tweets.search.recent(query=query, max_results=max_results, params=params, sort_order=sort_order)

print("Start sending tweets")

tweets_replies_result = get_replies_tweets()
replies = tweets_replies_result.get("data")
op_tweet_ids = []

for tweet in replies:
    tweet_text = tweet_helper.fix_tweet_text(tweet["text"])
    if tweet_text != "" and not tweet_helper.filter_tweet(tweet_text):
        output = generate_outputs(tweet_text, 1)[0]
        output = output if len(output) <= 280 else output[0:280] #Truncate at 280 characters
        
        print("")
        print("original tweet :" + tweet_text)
        print("reply tweet : " + output)
        
        tweet_to_send = { "text": output, "reply": {"in_reply_to_tweet_id": tweet["id"]}}
        t.tweets(_json=tweet_to_send)
print("Done")