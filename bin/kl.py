import splunk.Intersplunk
import collections
import profile

# compute a,b,c,d per http://www.pdl.cmu.edu/PDL-FTP/ProblemDiagnosis/draco-dsn.pdf
# for each compute node, based on job pass/fail in slurm joblogs, eg
# sourcetype=joblog index=hpc_redsky  | lookup hostlist short AS NodeList OUTPUT long AS host | makemv delim="," host | mvexpand host | fields + host,JobState
# can also run on cli as: `splunk cmd python abcd.py < ~/dataFromAboveQuery.csv`
# then put the resulting csv into R and compute KL like this:
#   kl<-lbeta(a,b)-lbeta(c,d)-(a-c)*digamma(c)-(b-d)*digamma(d)+(a-c+b-d)*digamma(c+d)

inData = splunk.Intersplunk.readResults( None, None, False )
outData = []

nodes = collections.defaultdict( lambda: 4*[1] )

passedJobCount = 0
failedJobCount = 0;

for jobIter in inData:
	if jobIter[ 'JobState' ] == 'COMPLETED':
		passedJobCount = 1 + passedJobCount
		for nodeIter in jobIter[ 'host' ].split( ',' ):
			nodes[ nodeIter ][ 0 ] = 1 + nodes[ nodeIter ][ 0 ]	# ++a
	if jobIter[ 'JobState' ] == 'FAILED':
		failedJobCount = 1 + failedJobCount
		for nodeIter in jobIter[ 'host' ].split( ',' ):
			nodes[ nodeIter ][ 2 ] = 1 + nodes[ nodeIter ][ 2 ]	# ++c

for nodeIter in nodes.iterkeys():
	if nodeIter.__len__() > 0:
		nodes[ nodeIter ][ 1 ] = 1 + passedJobCount - nodes[ nodeIter ][ 0 ]	# find b
		nodes[ nodeIter ][ 3 ] = 1 + failedJobCount - nodes[ nodeIter ][ 2 ]	# find d
		newOutDataRow = {}
		newOutDataRow[ 'host' ] = nodeIter
		newOutDataRow[ 'a' ] = nodes[ nodeIter ][ 0 ]
		newOutDataRow[ 'b' ] = nodes[ nodeIter ][ 1 ]
		newOutDataRow[ 'c' ] = nodes[ nodeIter ][ 2 ]
		newOutDataRow[ 'd' ] = nodes[ nodeIter ][ 3 ]
		outData.append( newOutDataRow )

splunk.Intersplunk.outputResults( outData )
