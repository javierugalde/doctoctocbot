#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, configparser, tweepy, inspect, hashlib

path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# friends file
friendsfile = os.path.join(path, "friends")                                            
print "friends file:", friendsfile

# read config
config = configparser.SafeConfigParser()
config.read(os.path.join(path, "config"))

# your hashtag or search query and tweet language (empty = all languages)
hashtag = config.get("settings", "search_query")
tweetLanguage = config.get("settings", "tweet_language")

# Number retweets per time
num = int(config.get("settings","number_of_rt"))
print "number of rt: ", num

# whitelisted users and words
# eg: ["medecinelibre", "freemedsoft"]
#userWhitelist = ["medecinelibre", "freemedsoft", "LibreHealthCare"]
with open(friendsfile, 'r') as f:
    userIdWhiteList = [line.rstrip('\n') for line in f]

print "Number of friends:", len(userIdWhiteList)
for userId in userIdWhiteList:
    print userId

wordBlacklist = ["RT", u"♺"]

# build savepoint path + file
hashedHashtag = hashlib.md5(hashtag.encode('ascii')).hexdigest()
last_id_filename = "last_id_hashtag_%s" % hashedHashtag
rt_bot_path = os.path.dirname(os.path.abspath(__file__))
last_id_file = os.path.join(rt_bot_path, last_id_filename)

# create bot
auth = tweepy.OAuthHandler(config.get("twitter", "consumer_key"), config.get("twitter", "consumer_secret"))
auth.set_access_token(config.get("twitter", "access_token"), config.get("twitter", "access_token_secret"))
api = tweepy.API(auth)

# retrieve last savepoint if available
try:
    with open(last_id_file, "r") as file:
        savepoint = file.read()
except IOError:
    savepoint = ""
    print("No savepoint found. Bot is now searching for results")

# search query
timelineIterator = tweepy.Cursor(api.search, q=hashtag, since_id=savepoint, lang=tweetLanguage).items(num)

# put everything into a list to be able to sort/filter

oklist = []

for tweet in timelineIterator:
    user = tweet.user
    screenname = user.screen_name
    userid = user.id
    print "userid: ", userid
    print "screen name: ", screenname
    useridstring = str(userid)
    if useridstring in userIdWhiteList:
        print useridstring, screenname, "is in the whitelist"
        oklist.append(tweet)

try:
    last_tweet_id = oklist[0].id
except IndexError:
    last_tweet_id = savepoint

# filter @replies/blacklisted words & users out and reverse timeline
# remove all tweets with an @mention
# oklist = filter(lambda status: status.text[0] == "@", oklist)

#timeline = filter(lambda status: not any(word in status.text.split() for word in wordBlacklist), timeline)

timeline = filter(lambda status: status.author.id_str in userIdWhiteList, oklist)
oklist = list(oklist)
oklist.reverse()

tw_counter = 0
err_counter = 0

# iterate the timeline and retweet
for status in oklist:
    try:
        print("(%(date)s) %(name)s: %(message)s\n" % \
              {"date": status.created_at,
               "name": status.author.screen_name.encode('utf-8'),
               "message": status.text.encode('utf-8')})

        #api.retweet(status.id)
        tw_counter += 1
    except tweepy.error.TweepError as e:
        # just in case tweet got deleted in the meantime or already retweeted
        err_counter += 1
        # print e
        continue

print("Finished. %d Tweets retweeted, %d errors occured." % (tw_counter, err_counter))

# write last retweeted tweet id to file
with open(last_id_file, "w") as file:
    file.write(str(last_tweet_id))
