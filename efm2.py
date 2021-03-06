####################################################
## EVOLUTIOINARY FAILURE MODE CALCULATOR
## COMMAND LINE DRIVER
## Version 1.0.1
####################################################


import subprocess
import csv
import sys
from .efm2_helper import *
from Bio import SeqIO

def process_file(filepath, organism):
    """Process a single file given by the user on the command line."""

    fasta_filepath = filepath

    # Determine file type
    spstring = re.split('/', filepath)
    fname = spstring[-1].lower()
    fnamesplit = re.split('\.', fname)
    ftype = fnamesplit[-1]
    if ftype == 'gb':
        ftype = 'genbank'
    check_features = (ftype == 'genbank')

    # Open the file and get metadata
    obj_file = SeqIO.read(filepath, ftype)
    features = get_genbank_features(obj_file)
    my_seq = str(obj_file.seq)

    # Create FASTA file if necessary
    if ftype != 'fasta':
        fasta_filepath = "/tmp/" + fnamesplit[0] + ".fasta"
        with open(fasta_filepath, 'w') as handle:
            SeqIO.convert(filepath, "genbank", handle, "fasta")

    # Process the file
    output_dict = process_efm_cli(fasta_filepath, features, my_seq, organism, check_features, fname)
    return output_dict

def process_dir(dirpath, organism):
    """Process several files all contained within a directory specified
    on the command line."""

    flist = list() # list of files
    metadata_lst = list() # list of dictionaries containing sequence metadata

    for dirName, subDirList, fileList in os.walk(dirpath):
        flist = fileList

    # Gather metadata on all files and store in a list
    for f in flist:
        metadata_lst.append(process_file(dirpath + f, organism))

    return metadata_lst

def print_output(data, output_dir):
    """
    Export data from MUMmer into CSV/table format.
    :param data: dictionary output from process_file()
    :param output_dir: directory to store output
    """

    """The following is documentation to help me, Tyler, write this program.

    :key rate: dictionary of rates. Key is sum, value is rate
    :key version: version of efm calc (string)
    :key features: list of dictionaries of features
    :key title: useless string (but could be used later for stuff)
    :key repeats: list of dictionaries of repeats
    :key organism: the organism (string)
    :key seq_length: length of sequence (numeric)
    """

    # Field names for CSV writer (i.e., keys for the header rows)
    rate_fieldnames = ['rip', 'rmd_sum', 'ssr_sum', 'bps_sum']
    feature_fieldnames = ['startpos', 'type', 'length', 'title']
    repeats_fieldnames = ['count', 'raw_rate', 'sequence', 'overlap', 'length', 'location', 'type']

    with open(output_dir + data['title'] + ".csv", "wb") as f:
        writer = csv.writer(f)

        # Write metadata
        writer.writerow(['Title', 'Organism', 'Sequence_length', 'EFM_Version'])
        writer.writerow([data['title'], data['organism'], data['seq_length'], data['version']])

        # Write the mutation rates and RIP score
        writer = csv.DictWriter(f, rate_fieldnames)
        writer.writeheader()
        writer.writerow(data['rate'])

        # Write the repeats
        writer = csv.DictWriter(f, repeats_fieldnames)
        writer.writeheader()
        for repeat in data['repeats']:
            writer.writerow(repeat)

        # Write the features
        writer = csv.DictWriter(f, feature_fieldnames)
        writer.writeheader()
        for feat in data['features']:
            writer.writerow(feat)

    return


def process_efm_cli(fasta_filepath, features, my_seq, org, check_features, title):
    """
    Takes command line arguments and finds potentially hypermutable sites in a submitted sequence(s).
    :param fasta_filepath: the path of the FASTA file
    :param features: dictionary of features
    :param org: the organism to which the sequence belongs
    :param check_features: boolean determining to check for features
    :param title: title of the CSV obtained from file name
    :return: A dictionary to be processed into a CSV
    """
   
    return process_helper(fasta_filepath, features, my_seq, org, check_features, title)


def main():
    """Driver for command line version of EFM calculator."""

    """Get the input from the user via the command line. The user may
    specify (currently) either GenBank or FASTA files. GenBank files
    must be converted into FASTA format for use with repeat-match in
    MUMmer."""

    # Define temporary directory
    tmp_path = "/tmp/"
    default_output = "output/"
    # Define error strings
    ERR_NO_FILE = "No file(s) specified."
    ERR_NO_ACCESS = "Cannot access path:"
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str, help="file or path containing sequence(s) to analyze")
    parser.add_argument('-g', '--organism', choices=['ecoli', 'reca', 'yeast'], help="specify organism")
    parser.add_argument('-o', '--output', type=str, help="directory to store output in")
    args = parser.parse_args()

    # Enforce constraints on input
    organism = ""
    output_dir = default_output

    if not args.input:
        print "ERROR:", ERR_NO_FILE
        return

    if not(os.access(args.input, os.R_OK)):
        print "ERROR:", ERR_NO_ACCESS, args.input
        return

    if not args.organism:
        organism = 'ecoli'
    else:
        organism = args.organism

    if args.output:
        if not(os.access(args.output, os.R_OK)):
            print "ERROR:", ERR_NO_ACCESS, args.output
        output_dir = args.output

    if not(os.access(output_dir, os.F_OK)):
        os.mkdir(output_dir)

    # Process a single file
    if not (os.path.isdir(args.input)):
        d = process_file(args.input, organism)
        print_output(d, output_dir)

    else:
        d = process_dir(args.input, organism)
        for item in d:
            print_output(item, output_dir)

if __name__ == "__main__":
    main()
