import re
import random
import sys
import twitter
import markov

from htmlentitydefs import name2codepoint as n2c
from local_settings import *

import logging
logging.basicConfig(filename = 'output.log')


def connect():
    return twitter.Api(consumer_key = MY_CONSUMER_KEY,
                      consumer_secret = MY_CONSUMER_SECRET,
                      access_token_key = MY_ACCESS_TOKEN_KEY,
                      access_token_secret = MY_ACCESS_TOKEN_SECRET)


def entity(text):
    if text[:2] == "&#":
        try:
            if text[:3] == "&#x" and text[3:-1] != "":
                return unichr(int(text[3:-1], 16))
            else:
                return unichr(int(text[2:-1]))
        except ValueError:
            pass
    else:
        # obtain the middle portion, e.g. word in "&word;"
        guess = text[1:-1]

        # maps HTML entity names to Unicode codepoints
        numero = n2c[guess]

        try:
            text = unichr(numero)
        except KeyError:
            pass

    return text


def filter_tweet(tweet):
    # remove anything after a retweet or modified tweet
    tweet.text = re.sub(r'\b(RT|MT) .+', '', tweet.text)

    # remove URLs, hashtags, http(s), etc.
    tweet.text = re.sub(r'(\#|@|(h\/t)|(http))\S+', '', tweet.text)

    # remove newlines
    tweet.text = re.sub(r'\n', '', tweet.text)

    # remove quotes
    tweet.text = re.sub(r'\"|\(|\)', '', tweet.text)

    # match against words like "&word;"
    htmlsents = re.findall(r'&\w+;', tweet.text)
    for item in htmlsents:
        tweet.text = re.sub(item, entity(item), tweet.text)

    # remove accented e's
    tweet.text = re.sub(r'\xe9', 'e', tweet.text)

    return tweet.text


def grab_tweets(api, max_id=None):
    source_tweets = []

    user_tweets = api.GetUserTimeline(screen_name = user, count = 200, max_id = max_id, \
                                      include_rts = True, trim_user = True, exclude_replies = True)

    max_id = user_tweets[len(user_tweets)-1].id - 1

    for tweet in user_tweets:
        tweet.text = filter_tweet(tweet)

        if tweet.text:
            source_tweets.append(tweet.text)

    return source_tweets, max_id


if __name__ == "__main__":
    order = MARKOV_INDEX
    guess = 0 if DEBUG else random.choice(range(ODDS))
    source_tweets = []

    if guess == 0:
        if STATIC_TEST:
            logging.info("Generating from %s ...", TEST_SOURCE)

            string_list = open(TEST_SOURCE).readlines()
            source_tweets = map(lambda x: x.split("\n")[0], string_list)
        else:
            for handle in SOURCE_ACCOUNTS:
                user = handle
                api = connect()
                max_id = None
                max_tweets = 17

                for x in range(1, max_tweets):
                    user_tweets, max_id = grab_tweets(api, max_id)
                    source_tweets += user_tweets

                if source_tweets:
                    logging.info("%d tweets found in %s", len(source_tweets), handle)
                else:
                    logging.info("Error fetching tweets. Seems like there's none... aborting!")
                    sys.exit()

        mine = markov.MarkovChainer(order)
        max_sentences = 10
        sentence_length_cutoff = 40
        secondary_cutoff = 110

        for tweet in source_tweets:
            tweet += "" if re.search('([\.\!\?\"\']$)', tweet) else "."
            mine.add_text(tweet)

        for x in range(max_sentences):
            generated_tweet = mine.generate_sentence()

        # randomly drop the last word, like Horse_ebooks does!
        words_to_ignore = r'(in|to|from|for|with|by|our|of|your|around|under|beyond)\s\w+$'

        if not random.randint(0, 4) and re.search(words_to_ignore, generated_tweet):
            logging.info("Losing last word randomly... now the tweet is:")
            generated_tweet = re.sub(r'\s\w+.$', '', generated_tweet)
            logging.info(generated_tweet)

        # if a tweet is very short, this will randomly add a second sentence to it.
        if generated_tweet and len(generated_tweet) < sentence_length_cutoff:
            randnum = random.randint(0, 10)

            if randnum == 0 or randnum == 7:
                logging.info("Short tweet. Adding another sentence randomly")
                newer_tweet = None

                while not newer_tweet:
                    newer_tweet = mine.generate_sentence()

                generated_tweet += " " + newer_tweet
            elif randnum == 1:
                # say something crazy/prophetic in all caps because why not
                logging.info("ALL THE THINGS")
                generated_tweet = generated_tweet.upper()

        # discard tweets that match anything from the source account
        if generated_tweet and len(generated_tweet) < secondary_cutoff:
            for tweet in source_tweets:
                if generated_tweet[:-1] in tweet:
                    logging.info("TOO SIMILAR: %s", generated_tweet)
                    sys.exit()

            if not DEBUG:
                status = api.PostUpdate(generated_tweet)
                logging.info(status.text.encode('utf-8'))
            else:
                logging.info(generated_tweet)

        elif not generated_tweet:
            logging.info("Tweet is empty, try again!")
        else:
            logging.info("TOO LONG: %s", generated_tweet)
    else:
        logging.info("Guess didn't match: %s", str(guess))
