#!/usr/bin/env python2.7

import re

def preprocess(data):
    return [datum.strip() for datum in data.strip().split('\n')]

def get_morphemes_and_standard(mlist, slist):
    morphemes = []
    standard = []

    EOS = '^EOS'
    DEF = '^Def'

    # regexes for extracting gold standard morphs/TAGS
    MORPH = re.compile(r'(?<![^\+])\S+?/[A-Z]+(?![^\+])')
    SPLIT = re.compile(r'^(.+)/(.+)$')
    
    # regexes for handling + sequences in morpheme sequences
    PLUSR = re.compile(r'\+\+$')
    PLUSL = re.compile(r'^\+\+')
    PLUSM = re.compile(r'\+\+')

    # loop through lines of both files, aligned properly
    for mline, sline in zip(mlist, slist):
        # skip ill-formed lines with ^Def
        if DEF in mline or DEF in sline:
            continue
        if sline == EOS and mline == EOS:
            standard.append(sline)
            morphemes.append(mline)
        else:
            word, tagged = sline.split()
            morphs = []
            tags = []
            pairs = MORPH.findall(tagged)
            if not pairs:
                continue
            else:
                # extract gold standard morphs/TAGS
                for pair in pairs:
                    match = SPLIT.match(pair)
                    if match:
                        m, t = match.groups()
                        morphs.append(m)
                        tags.append(t)
                    else:
                        continue
                standard.append((tuple(morphs), tuple(tags)))

                # extract test morphemes
                if mline == '+':
                    morphemes.append(mline)
                else:
                    # guard against sequences of contiguous pluses
                    mline = PLUSM.sub('+<p>', PLUSR.sub('+<p>', PLUSL.sub('<p>+', mline)))
                    mtokens = mline.split('+')
                    mtokens = [mtoken.replace('<p>', '+') for mtoken in mtokens]
                    morphemes.extend(mtokens)

    # package results and return
    return (morphemes, standard)

def extract_morphemes(wordlist):
    morphemes = []
    i = 0
    for word in wordlist:
        if i == 1568:
            i += 1
            continue
        if "^Def" not in word:
            if word == '+':
                morphemes.append(word)
            else:
                PLUSR = re.compile(r'\+\+$')
                PLUSL = re.compile(r'^\+\+')
                PLUSM = re.compile(r'\+\+')
                tokens = word.split('+')
                tokens = [token.replace('<p>', '+') for token in tokens]
                morphemes.extend(tokens)
        i += 1
        
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

    try:
        gold_f = sys.argv[1]
    except IndexError:
        exit("No filename argument provided")

    with open(gold_f, 'r') as gold_in:
        standard = gold_in.read()

    test_morphemes = sys.stdin.read()

    standard = preprocess(standard)
    test_morphemes = preprocess(test_morphemes)

    test_morphemes, standard = get_morphemes_and_standard(test_morphemes, standard)

    test_sentences = [sent.strip() for sent in
                      ' '.join(test_morphemes).split(EOS) if sent]

    # tag sentences

    v = Viterbi()

    test_output = []
    for sentence in test_sentences:
        s_morphemes = tuple(sentence.split(' '))
        tagged = v.tag(sentence).split(' ')
        test_output.extend(zip(s_morphemes, tagged))

    test_report = []
    errors = 0
    possible = 0

    output_index = 0
    for line in standard:
        if line == EOS:
            test_report.append(EOS)
        else:
            morphemes, tags = line
            incr = len(morphemes)

            if output_index + incr > len(test_output):
                break

            out_tags = [t for m, t in test_output[output_index:output_index+incr]]
            for i in range(len(out_tags)):
                my = out_tags[i]
                gold = tags[i]
                if my != gold:
                    out_tags[i] = '**{0}**'.format(my)
                    errors += 1

            test_report.append('+'.join(['/'.join(pair) for pair in zip(morphemes, out_tags)]))
            possible += incr
            output_index += incr

    print '\n'.join(test_report)
    print output_index
    print errors
    print '{0:.2f}% accuracy'.format(float(possible - errors)/possible*100)

    # feed sentences from test file to viterbi to tag them
    # results will be in space-separated string form
    # you're going to need to reconstitute the viterbi output back into words for comparison with the gold standard
