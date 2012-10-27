#!/usr/bin/env python2.7

from HMM import HMM
import sys

# initialize HMM object, write resulting
# probability matrices to proper files

try:
    training_file = sys.argv[1]
except IndexError:
    exit("No file provided")

model = HMM(training_file)

with open('hw3b.a-matrix.txt', 'w') as tp_out:
    tp_out.write(HMM.format_matrix(model.tmatrix))
with open('hw3b.emission.txt', 'w') as ep_out:
    ep_out.write(HMM.format_matrix(model.ematrix))
