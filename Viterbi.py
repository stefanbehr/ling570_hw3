#!/usr/bin/env python2.7

from subprocess import Popen, PIPE;
import os

class Viterbi:
	def __init__(self, extraArgs = ""):
		self.process = Popen(
			['perl', 'viterbi.pl',
                         '-transition', 'hw3b.a-matrix.txt',
                         '-emission', 'hw3b.emission.txt'],
			cwd = os.getcwd(),
			shell=0,
			stdin=PIPE, stdout=PIPE)

	def tag(self, input):
		self.process.stdin.write(input + '\n')
		self.process.stdin.flush()
		return self.process.stdout.readline().strip()

if __name__ == '__main__':
        v = Viterbi()
        print v.tag('this is a test .'),
        print v.tag('that is a test .'),
