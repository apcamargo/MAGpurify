#!/usr/bin/env python

import sys
import magfly
from magfly.utility import *

def fetch_args():
	import argparse
	parser = argparse.ArgumentParser(
		formatter_class=argparse.RawTextHelpFormatter
	)
	parser.add_argument('fna_path', type=str,
		help="""Path to input genome in FASTA format""")
	parser.add_argument('out_dir', type=str,
		help="""Output directory to store results and intermediate files""")
	parser.add_argument('-t', dest='threads', type=int, default=1,
		help="""Number of CPUs to use (default=1)""")
	parser.add_argument('-d', dest='db', type=str,
		help="""Path to reference database
By default, the magflyEN_DB environmental variable is used""")
	parser.add_argument('-m', dest='modules', type=str,
		help="""Comma-separated list of modules to run (default=all)
Choices; each uses a different pipeling to predict whether a contig is contamination:
   uscmg - discordant taxonomy based on universal-single-copy marker-genes
   csmg - discordant taxonomy based on clade-specific marker-genes
   contdb - hits to database of known contaminants
   tnf - outlier tetranucleotide frequency
   gcc - outlier gc content
   depth - outlier read depth
   """)
	parser.add_argument('-s', dest='sens', type=str,
		help="""Sensitivity/specificity (default=very-specific)
Choices: very-specific, specific, sensitive, very-sensitive""")

	args = vars(parser.parse_args())
	if (not args['db']
			and 'magfly_DB' in os.environ):
		args['db'] = os.environ['magfly_DB']
	if args['modules']:
		args['modules'] = args['modules'].split(',')
	return args

class Contig:
	def __init__(self):
		pass

if __name__ == "__main__":
	
	args = fetch_args()

	check_input(args)
	check_output(args)
	check_dependencies(['blastn'])
	check_database(args)

	contigs = {}
	for rec in parse_fasta(args['fna_path']):
		contig = Contig()
		contig.id = rec.id
		contig.seq = str(rec.seq)
		contig.length = len(rec.seq)
		contig.flags = []
		contigs[rec.id] = contig
	
	if args['modules'] and 'uscmg' in args['modules']:
		sys.stdout.write("discordant taxonomy based on universal-single-copy marker-genes\n")
		from magfly import uscmg
		flagged = uscmg.main(args)
		for id in flagged:
			contigs[id].flags.append('uscmg')
		sys.stdout.write("   %s contigs flagged\n" % len(flagged))

	if args['modules'] and 'csmg' in args['modules']:
		sys.stdout.write("discordant taxonomy based on clade-specific marker-genes\n")
		from magfly import csmg
		flagged = csmg.main(args)
		for id in flagged:
			contigs[id].flags.append('csmg')
		sys.stdout.write("   %s contigs flagged\n" % len(flagged))

	if args['modules'] and 'contdb' in args['modules']:
		sys.stdout.write("hits to database of contaminants\n")
		from magfly import contam
		flagged = contam.main(args)
		for id in flagged:
			contigs[id].flags.append('contdb')
		sys.stdout.write("   %s contigs flagged\n" % len(flagged))

	if args['modules'] and 'tnf' in args['modules']:
		sys.stdout.write("outlier tetranucleotide frequency\n")
		from magfly import tetra
		flagged = tetra.main(args)
		for id in flagged:
			contigs[id].flags.append('tnf')
		sys.stdout.write("   %s contigs flagged\n" % len(flagged))

	if args['modules'] and 'gcc' in args['modules']:
		sys.stdout.write("outlier gc content\n")
		from magfly import gc
		flagged = gc.main(args)
		for id in flagged:
			contigs[id].flags.append('gcc')
		sys.stdout.write("   %s contigs flagged\n" % len(flagged))

	with open('%s/cleaned.fa' % args['out_dir'], 'w') as f:
		for contig in contigs.values():
			if len(contig.flags) > 0:
				continue
			f.write('>'+contig.id+'\n'+contig.seq+'\n')

	with open('%s/summary.tsv' % args['out_dir'], 'w') as f:
		fields = ['contig_id', 'length', 'flags']
		f.write('\t'.join(fields)+'\n')
		for contig in contigs.values():
			values = [contig.id, str(contig.length), ','.join(contig.flags)]
			f.write('\t'.join(values)+'\n')



