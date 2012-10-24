#!/usr/bin/env python2.7

import re

def preprocess(data):
    return [datum.strip() for datum in data.strip().split('\n')]

def extract_morphemes(wordlist):
    morphemes = []
    for word in wordlist:
        word = word.replace('++', '<plus-tok>+')
        tokens = word.split('+')
        tokens = [token.replace('<plus-tok>', '+') for token in tokens]
        morphemes.extend(tokens)
    return morphemes

def frequencies(lst):
    freqs = {}
    for item in lst:
        freqs[item] = freqs.get(item, 0) + 1
    return freqs

if __name__ == "__main__":

    import sys
    from Viterbi import Viterbi

    EOS = '^EOS'

    try:
        gold_f = sys.argv[1]
    except IndexError:
        exit("No filename argument provided")

    with open(gold_f, 'r') as gold_in:
        standard = gold_in.read()

    test = sys.stdin.read()

    standard = preprocess(standard)
    test = preprocess(test)

    test_morphemes = extract_morphemes(test)
    morpheme_freqs = frequencies(test_morphemes)
    test_morphemes = ['UNK' if morpheme_freqs[m] == 1 else m for m in test_morphemes]

    test_sentences = [sent.strip() for sent in
                      ' '.join(test_morphemes).split(EOS) if sent]

    v = Viterbi()

    s_wrap = '<s>{0}<s>'
    print v.tag(s_wrap.format(test_sentences[0]))
    print v.tag(s_wrap.format(test_sentences[1]))

    # determine morpheme frequencies and replace singleton morphemes with "UNK"
    # chunk the morpheme list by sentence boundary
    # feed sentences from test file to viterbi to tag them
    # results will be in space-separated string form
    # you're going to need to reconstitute the viterbi output back into words for comparison with the gold standard
