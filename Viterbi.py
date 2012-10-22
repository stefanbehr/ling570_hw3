from subprocess import Popen, PIPE;
class Viterbi:
	def __init__(self, extraArgs = ""):
		self.process = Popen(
			['perl', 'viterbi.pl'],
			cwd='/opt/dropbox/12-13/570/hw3',
			shell=0,
			stdin=PIPE, stdout=PIPE)

	def tag(self, input):
		self.process.stdin.write(input)
		self.process.stdin.flush()
		return self.process.stdout.readline()

if __name__ == '__main__':
        v = Viterbi()
        print v.tag('this is a test .')
