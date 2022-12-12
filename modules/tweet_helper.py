import re

def remove_links(text):
    reg = "(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w\.-]*)( *)"
    return re.sub(reg,"", text)

def remove_leading_mentions(text):
    reg = "^([@]([a-zA-Z0-9_]+|$)( *)(,*)( *))+"
    return re.sub(reg,"", text)

# Remove the (x/y) at the beginning or end of a tweet
def remove_part_number(text):
    reg_part = "( *)((\(?\[?[0-9][0-9]?\/([0-9][0-9]?|n)\]?\)?))( *)"
    reg = "^" + reg_part + "|" + reg_part + "$"
    return re.sub(reg, "", text)

def replace_text(text):
    return text.replace('"', '""').replace("{NEWLINE}", "\n").replace("&amp;","&").replace("&gt;",">").replace("&lt;","<")

def fix_tweet_text(text):
    return remove_part_number(remove_links(remove_leading_mentions(replace_text(text))))

# Filter mentions or hashtag that contains certain words
def filter_hashtags_mentions(text):
    reg = "(?i)[#|@][a-zA-Z0-9_]*(ETH|CEX|USHI|TOKEN|BSC|crypto|NFT)[a-zA-Z0-9_]*"
    return re.search(reg, text)

# Remove tweets with spam or text that won't be processed correctly (empty space = tweet might be meant to be read vertically)
    # Also filter out words that start or end with $
def filter_spam(text):
	reg = "(?i)(NFT|altcoin|bnb|busd|usdt|kripto|bobainu|🚀|giveaway|livebet|your prize|nsfw|     )|([$]([a-zA-Z]+|$))"
	return re.search(reg, text)

def filter_tweet(text):
    return filter_spam(text) != None or filter_hashtags_mentions(text) != None