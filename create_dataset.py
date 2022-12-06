import sys
import os
import time
import argparse
from os.path import exists

import csv
import modules.tweet_helper as tweet_helper

current_dir = os.getcwd()
op_path = os.path.join(current_dir, "op_liked.csv")
reply_path = os.path.join(current_dir, "replies_liked.csv")
final_path = os.path.join(current_dir, "final_liked_gpt.csv")

op_dict = {}

# LOAD OP DICT
with open(op_path, 'r', encoding="utf-8") as op_file:
    
    reader = csv.DictReader(op_file)
    row_idx = 1
    
    for row in reader:
    
        # Don't resave to dicitonnary if op already exists
        if row["id"] not in op_dict:
            op_dict[row["id"]] = row["text"]
        
        row_idx += 1
        
        if row_idx % 1000 == 0:
            print("Current op index = " + str(row_idx))
    
# CREATE final.csv
with open(reply_path, 'r', encoding="utf-8") as reply_file:
    with open(final_path, 'w+', encoding="utf-8") as final_file:
        
        final_file.write(",".join(["op_id", "reply_id", "op_text", "reply_text"]) + "\n")
        
        reader = csv.DictReader(reply_file)
        row_idx = 1
        
        for row in reader:
            
            op_id = row["in_reply_to_tweet_id"]
            reply_id = row["id"]
            
            # Skip if op tweet is missing (has been deleted)
            if int(row["like_count"]) >= 10 and op_id in op_dict:
                
                op_text = tweet_helper.fix_tweet_text(op_dict[op_id]) 
                reply_text = tweet_helper.fix_tweet_text(row["text"])
                
                # In case the texts are now empty
                if op_text != "" and reply_text != "" and tweet_helper.filter_tweet(op_text) == None and tweet_helper.filter_tweet(reply_text) == None: 
                    
                    op_text = '"' + op_text + '"'
                    reply_text = '"' + reply_text + '"'
                    
                    #op_with_reply_text =  '"' + op_text + "{REPLY}" + reply_text + '"'
                    
                    final_text = ",".join([op_id, reply_id, op_text, reply_text]) + "\n"
                    
                    final_file.write(final_text)
                    
                    row_idx += 1
                    
                    if row_idx % 1000 == 0:
                        print("Current text index = " + str(row_idx))
        
        print("Final text index :" + str(row_idx))