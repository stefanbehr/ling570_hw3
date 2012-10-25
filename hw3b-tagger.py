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
            result.append((tuple(morphs), tuple(tags)))
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
    test_morphemes = ['<s>' if m.strip() == EOS else m.strip() for m in test_morphemes if m]
    if test_morphemes[-1] == '<s>':
        test_morphemes = test_morphemes[:-1]
    test_glob = ' '.join(test_morphemes)

    standard = process_standard(standard, EOS)

    # tag sentences

    v = Viterbi()

    tagged = v.tag(test_glob)
    tagged = [x for x in tagged.split(' ') if x]
    if len(tagged) == len(test_morphemes):
        test_output = zip(test_morphemes, tagged)

    test_report = []
    error = 0
    possible = 0

    output_index = 0
    for line in standard:
        if line == EOS:
            test_report.append(EOS)
            output_index += 1
        else:
            morphemes, tags = line
            incr = len(morphemes)

            if output_index + incr > len(test_output):
                break
            
            in_morphs = tuple([m for m, t in test_output[output_index:output_index+incr]])
            out_tags = [t for m, t in test_output[output_index:output_index+incr]]

            for i in range(len(out_tags)):
                my = out_tags[i]
                gold = tags[i]
                if my != gold:
                    out_tags[i] = '**{0}**'.format(my)
                    error += 1

            test_report.append('+'.join(['/'.join(pair) for pair in zip(morphemes, out_tags)]))
            possible += incr
            output_index += incr

    print '\n'.join(test_report)
    print '\n' + '{} morphemes tagged: (possible)'
    print '\n{0:.2f}% accuracy'.format(float(possible - error)/possible*100)

    # feed sentences from test file to viterbi to tag them
    # results will be in space-separated string form
    # you're going to need to reconstitute the viterbi output back into words for comparison with the gold standard
