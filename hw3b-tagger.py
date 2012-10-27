#!/usr/bin/env python2.7

import re

def preprocess(data):
    """
    Pull in and clean up data. Returns list of whitespace-stripped
    lines from the data blob given.
    """
    return [datum.strip() for datum in data.strip().split('\n')]

def get_morphemes_and_standard(mlist, slist):
    """
    Given two lists of strings, one corresponding to a test
    input file and the other corresponding to the tagged gold
    standard of the test input file, returns a tuple containing
    processed version of the two input lists.
    """
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
            # this case indicates ill-formed gold standard
            # input, so we skip to the next iteration to 
            # avoid getting well-formed test input that corresponds
            # to ill-formed gold standard input. it happens.
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

if __name__ == "__main__":

    import sys
    from Viterbi import Viterbi

    EOS = '^EOS'

    # get gold standard file path
    try:
        gold_f = sys.argv[1]
    except IndexError:
        exit("No filename argument provided")

    with open(gold_f, 'r') as gold_in:
        standard = gold_in.read()

    # test file is redirected to stdin
    test_morphemes = sys.stdin.read()

    # clean up test file and gold standard data for 
    # further processing
    standard = preprocess(standard)
    test_morphemes = preprocess(test_morphemes)

    # extract morphemes from test file and morpheme-tag pairs from gold standard
    test_morphemes, standard = get_morphemes_and_standard(test_morphemes, standard)

    # partition morpheme list into sentence strings
    test_sentences = [sent.strip() for sent in
                      ' '.join(test_morphemes).split(EOS) if sent]


    # tag sentences!
    v = Viterbi()

    # get output, storing each tag with the morpheme
    # that generated it
    test_output = []
    for sentence in test_sentences:
        s_morphemes = tuple(sentence.split(' '))
        tagged = v.tag(sentence).split(' ')
        test_output.extend(zip(s_morphemes, tagged))

    test_report = []
    errors = 0
    possible = 0

    # iterate through gold standard (a list containing sublists
    # of variable lengths corresponding to lines in the original
    # gold standard file), checking each tagged morpheme against 
    # that morpheme's tag in the gold standard in the appropriate
    # location
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
            for i in range(incr):
                my_tag = out_tags[i]
                gold_tag = tags[i]
                if my_tag != gold_tag:
                    out_tags[i] = '**{0}**'.format(my_tag)
                    errors += 1

            test_report.append('+'.join(['/'.join(pair) for pair in zip(morphemes, out_tags)]))
            possible += incr
            output_index += incr

    # print tagger results with incorrect tags marked, 
    # total morphemes evaluated, and accuracy score
    print '\n'.join(test_report)

    tot = 'Total # of morphemes evaluated:'
    acc = '{0:{1}s}'.format('Accuracy:', len(tot))

    tot = '\n{0}\t{1}'.format(tot, possible)
    acc = '\n{0}\t{1:.2f}%'.format(acc, float(possible-errors)/possible*100)

    print tot
    print acc
