#!/usr/bin/env python2.7

import re

def preprocess(data):
    return [datum.strip() for datum in data.strip().split('\n')]

def extract_morphemes(wordlist):
    morphemes = []
    for word in wordlist:
        if "^Def" not in word:
            word = word.replace('++', '<plus-tok>+')
            tokens = word.split('+')
            tokens = [token.replace('<plus-tok>', '+') for token in tokens]
            morphemes.extend(tokens)
    return morphemes

def process_standard(wordlist, EOS):
    result = []
    MORPH = re.compile(r'(?<![^\+])\S+?/[A-Z]+(?![^\+])')
    SPLIT = re.compile(r'^(.+)/(.+)$')
    for line in wordlist:
        if line == EOS:
            result.append(line)
        elif "^Def" in line:
            continue
        else:
            w, tagged = line.split()
            morphs = []
            tags = []
            for pair in MORPH.findall(tagged):
                match = SPLIT.match(pair)
                if match:
                    m, t = match.groups()
                    morphs.append(m)
                    tags.append(t)
                else:
                    continue
            result.extend(zip(tuple(morphs), tuple(tags)))
    return result

def frequencies(lst):
    freqs = {}
    for item in lst:
        freqs[item] = freqs.get(item, 0) + 1
    return freqs

if __name__ == "__main__":

    import sys
    from Viterbi import Viterbi

    EOS = '^EOS'
    HEAD = 10 # limit on lines of input for testings purposes (because viterbi is slow)

    try:
        gold_f = sys.argv[1]
    except IndexError:
        exit("No filename argument provided")

    try:
        HEAD = int(sys.argv[2])
    except IndexError:
        HEAD = 10

    with open(gold_f, 'r') as gold_in:
        standard = gold_in.read()

    test = sys.stdin.read()

    standard = preprocess(standard)
    test = preprocess(test)

    test_morphemes = extract_morphemes(test)
    test_morphemes = ['<s>' if m == EOS else m for m in test_morphemes if m]
    if test_morphemes[-1] == '<s>':
        test_morphemes = test_morphemes[:-1]
    test_glob = ' '.join(test_morphemes)

    standard = process_standard(standard, EOS)

    # tag sentences

    v = Viterbi()

    tagged = v.tag(test_glob)
    tagged = [x for x in tagged.split(' ')]

    test_report = []
    error = 0
    possible = 0

    index = 0
    for line in standard:
        if line == EOS:
            test_report.append(EOS)
        else:
            morpheme, tag = line
            tm = test_morphemes[index]
            out_tag = tagged[index]
            
            if morpheme != tm:
                print "bad morpheme!"
                print 'input: {}'.format(tm)
                print 'gold: {}'.format(morpheme)

            if out_tag != tag:
                out_tag = '**{0}**'.format(out_tag)
                error += 1

            possible += 1
            test_report.append('/'.join((tm, out_tag)))
        index += 1

    print '\n'.join(test_report)
    print '\n' + 'Number of morphemes tagged: {0}'.format(possible)
    print '\n{0:.2f}% accuracy'.format(float(possible - error)/possible*100)

    # feed sentences from test file to viterbi to tag them
    # results will be in space-separated string form
    # you're going to need to reconstitute the viterbi output back into words for comparison with the gold standard
