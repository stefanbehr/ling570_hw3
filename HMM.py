#!/usr/bin/env python2.7

import re, types
from math import log

class HMM:
    def __init__(self, corpus_path):
        self.process_corpus(corpus_path)
        self.tp_matrix()
        self.ep_matrix()

    @staticmethod
    def make_ngrams(lst, n):
        """
        Given a list of items, returns a list of tuples
        representing the bigrams in the list.
        """
        ngrams = []
        if n <= len(lst):
            for i in range(len(lst) - n + 1):
                ngrams.append(tuple(lst[i:i+n]))
        return ngrams

    @staticmethod
    def frequencies(lst):
        """
        Given a list, outputs a dict containing the
        items of the list as keys, with the value of each
        key representing the frequency of the key in the
        original list.
        """
        freqs = {}
        for item in lst:
            freqs[item] = freqs.get(item, 0) + 1
        return freqs

    @staticmethod
    def format_matrix(matrix):
        """
        Given a matrix in nested dict form,
        creates a nicely formatted string
        representation of it.
        """
        row_labels = sorted(matrix.keys())
        col_labels = sorted(matrix[row_labels[0]].keys())
        rows = ['\t'.join([''] + col_labels)]
        for row_label in row_labels:
            row = matrix[row_label]
            row = ['{0:.6f}'.format(cell) if type(cell) == types.FloatType else cell
                   for cell in map(row.get, col_labels)]
            row.insert(0, row_label)
            rows.append('\t'.join(row))
        return '\n'.join(rows)

    def tp_matrix(self):
        """
        Produces a probability matrix for transitions between
        morpheme tags.
        """
        # make taglist into set, get tag bigrams, get bigram frequencies
        self.tagset = list(set(self.tags))
        self.tag_bigrams = self.make_ngrams(self.tags, 2)
        self.tag_bigram_frequencies = self.frequencies(self.tag_bigrams)

        matrix = {}
        # for add one smoothing
        T = len(self.tagset)

        # calculate and store probabilities row by row, column by colum
        for row_tag in self.tagset:
            row = {}
            row_count = T + sum(self.tag_bigram_frequencies[bigram] for bigram
                                in self.tag_bigram_frequencies.keys()
                                if bigram[0] == row_tag) # number of bigrams with col_tag as first unigram
            for col_tag in self.tagset:
                pair = (row_tag, col_tag)
                bigram_count = 1 + self.tag_bigram_frequencies.get(pair, 0) # add one smoothing
                t_prob = log(float(bigram_count)/row_count, 2)
                row[col_tag] = t_prob
            matrix[row_tag] = row

        self.tmatrix = matrix
        
    def ep_matrix(self):
        """
        Given a list of morphemes and corresponding list
        of tags, generate an emission probability matrix for
        emissions of morphemes from tags.
        """

        # replace morphemes occurring once with 'UNK' token
        self.morpheme_frequencies = self.frequencies(self.morphemes)        
        self.morphemes = ['UNK' if self.morpheme_frequencies[morpheme] == 1 else morpheme
                          for morpheme in self.morphemes]
        self.morpheme_frequencies = self.frequencies(self.morphemes)
        self.morpheme_set = list(set(self.morphemes))

        # remove <s> tag from tags to allow proper alignment
        # of tag and morpheme lists
        self.tags = [t for t in self.tags if t != '<s>']
        self.tagset = list(set(self.tags))

        self.pairs = zip(self.morphemes, self.tags)
        self.pair_frequencies = self.frequencies(self.pairs)

        self.tag_frequencies = self.frequencies(self.tags)

        # calculate and store emission probabilities,
        # row by row, column by column
        matrix = {}
        for morpheme in sorted(self.morpheme_set):
            row = {}
            for tag in sorted(self.tagset):
                pair = (morpheme, tag)
                this_pair_count = self.pair_frequencies.get(pair, 0)
                tag_pair_count = self.tag_frequencies[tag]
                e_prob = float(this_pair_count)/tag_pair_count
                e_prob = log(e_prob, 2) if e_prob != 0 else "-inf"
                row[tag] = e_prob
            matrix[morpheme] = row

        self.ematrix = matrix

    def process_corpus(self, corpus_path):
        """
        Given a path to a file, stores a list of all
        morpheme-tag pairs found in the file.
        """
        with open(corpus_path, 'r') as infile:
            blob = infile.read()
        
        lines = blob.strip().split('\n')

        self.errors = [] # for storing tagging errors
        self.morphemes = [] # morphemes
        self.tags = [] # morpheme tags

        # patterns and regular expressions for capturing morpheme-tag pairs
        pair = r'[^\s/]+?/[^\+]+'
        TAGGEDSEQ = re.compile(r'^{0}(?:(?:\+){0})*$'.format(pair)) # matches a valid tagged morpheme sequence
        PAIR = re.compile(r'(?<![^\+]){0}(?![^\+])'.format(pair)) # matches a valid morpheme-tag pair in the proper context

        # end of sentence tags
        EOS_THEM = '^EOS'
        EOS_ME = '<s>'

        # iterate through data lines, dumping morphemes
        # and tags into two separate flat lists (which are 
        # stored as attributes of the self object)
        for line in lines:
            line = line.strip()
            cols = line.split()
            if len(cols) != 2:
                if line == EOS_THEM: # sentence boundary
                    self.tags.append(EOS_ME)
            else:
                word, tagged = cols
                match = TAGGEDSEQ.match(tagged)
                if match: # well-formed morpheme-tag sequence
                    pairs = PAIR.findall(tagged)
                    for pair in pairs:
                        morpheme, tag = pair.split('/')
                        self.morphemes.append(morpheme)
                        if tag != tag.upper():
                            tag = re.sub(r'[a-z]', '', tag)
                        self.tags.append(tag)
                else:
                    self.errors.append(tagged) # ill-formed morpheme-tag sequence, save for inspection
        self.tags.insert(0, EOS_ME)

    # various printing methods for testing
    def print_morphemes_and_tags(self):
        print '\n'.join('{0}\t{1}'.format(morpheme, tag) for morpheme, tag in self.pairs)

    def print_errors(self):
        print '\n'.join(self.errors)
