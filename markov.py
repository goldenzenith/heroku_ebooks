import re
import random
import logging

logging.basicConfig(filename = 'output.log')

class MarkovChainer(object):
    def __init__(self, order):
        self.order = order
        self.beginnings = []
        self.freq = {}

    # pass a string with a terminator to add it to the Markov chains
    def add_sentence(self, string, terminator):
        words = "".join(string).split()
        buf = []

        if len(words) > self.order:
            words.append(terminator)
            self.beginnings.append(words[:self.order])

        for word in words:
            buf.append(word)

            if len(buf) == self.order + 1:
                mykey = (buf[0], buf[-2])

                if mykey in self.freq:
                    self.freq[mykey].append(buf[-1])
                else:
                    self.freq[mykey] = [buf[-1]]

                buf.pop(0)


    def add_text(self, text):
        text = re.sub(r'\n\s*\n/m', ".", text)
        separators = '([.!?;:])'
        pieces = re.split(separators, text)
        sentence = ""

        for piece in pieces:
            if piece:
                if re.search(separators, piece):
                    self.add_sentence(sentence, piece)
                    sentence = ""
                else:
                    sentence = piece


    def generate_sentence(self):
        res = random.choice(self.beginnings)
        sentence = None

        if len(res) == self.order:
            nw = True

            while nw != None:
                restup = (res[-2], res[-1])

                try:
                    nw = self.next_word_for(restup)

                    if nw != None:
                        res.append(nw)
                except:
                    nw = False

            new_res = res[0:-2]

            if not(new_res[0].istitle() or new_res[0].isupper()):
                new_res[0] = new_res[0].capitalize()

            sentence = ""

            for word in new_res:
                sentence += word + " "

            sentence += res[-2] + res[-1]

        return sentence


    def next_word_for(self, words):
        try:
            arr = self.freq[words]
            return random.choice(arr)
        except:
            return None


if __name__ == "__main__":
    logging.info("Try running ebooks.py first")
