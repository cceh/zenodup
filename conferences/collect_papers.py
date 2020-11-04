"""Script for assigning conference papers based on metadata file

This script needs to be put next to the folder containing all files of the dhd conference that need to be collected in order to upload these publication pairs as single objects to zenodo.
The following folder structure is expected:

- collect_papers.py
- CONFERENCE: Folder containing all relevant files of conference
    - METADATA_FILE: Name of metadata file for conference containing all relevant information of conference publications
    - XML: Folder to xml files of conference pubclications
    - PDF: Folder to pdf files of conference publications

To run this scirpt the following arguments need to be modified:
    * CONFERENCE: Name of conference folder
    * METADATA_FILE: Name of metadata file (expected format: xml) for conference publications
    * XML (Optional): Name of folder of conference publication xmls. If no name is given, script expects folder name "xml"
    * PDF (Optional): Name of folder of conference publication pdfs. If no name is given, script expects folder name "pdf"
"""

# ## Imports
import getopt
import logging
import lxml
from lxml import etree
import os
from pathlib import Path
import sys
from xml.etree import ElementTree as ET



def main(argv):

    # set working paths based on command line arguments
    conference, metadata_file, xml, pdf = set_paths(argv[1:])

    # parse metadata file of conference
    tree = ET.parse(metadata_file)
    publications = get_publications(tree)

    # get pdf files
    pdf_files = [os.path.join(pdf,file_name) for file_name in os.listdir(pdf) if file_name != ".DS_Store"]
    pdf_names = [os.path.splitext(file_name)[0] for file_name in os.listdir(pdf) if file_name != ".DS_Store"]
    # print(pdf_names)
    # shortened_pdf_names = [name[-15:] for name in pdf_names]

    logging.debug(f"Names of pdf files: {pdf_names}")

    publication_names = {}
    for (publication, creators) in publications.items():
        try:
            title = ascii_rename(publication)
        except TypeError:
            logging.warning(f"The following publication does not contain a title: {metadata.index(publication)}")
        prefixes = [creator[0].upper()+'_'+creator[1]+'_' for creator in creators]
        possible_names = [prefix + title for prefix in prefixes]

        try:
            if title.find("_em_") != -1:
                # print(title)
                for prefix in prefixes:
                    possible_names.append(prefix + title.replace("_em_", "_"))
                    # logging.debug(possible_names)
        except AttributeError:
            pass
        
        publication_names.update({publication: possible_names})

    logging.debug(len(publication_names))

    publication_pdfs = {}
    for elem in publication_names:
        if any(possible_name.find(name)!= -1 for possible_name in publication_names.get(elem) for name in pdf_names):
            for possible_name in publication_names.get(elem):
                for name in pdf_names:
                    if possible_name.find(name) != -1:
                        logging.info("----")
                        logging.info(name)
                        logging.info("----")
                        publication_pdfs.update({elem:name+'.pdf'})
        else:
            logging.warning("***")
            logging.warning(f"For the publication {elem} exists no matching file.")
            logging.warning(publication_names.get(elem))
            logging.warning("***")
        
    print(publication_pdfs)
    print(len(publication_pdfs))
    

    # get xml files
    xml_files = [os.path.join(xml, file_name) for file_name in os.listdir(xml) if file_name != ".DS_Store"]
    xml_names = [os.path.splitext(file_name)[0] for file_name in os.listdir(xml) if file_name != ".DS_Store"]
    # print(xml_names)
    # TODO check if elements of 'metadata' nodes in metadata file of conference matches files in xml and pdf

# set working paths
def set_paths(argv:list) -> (Path, Path, Path, Path):
    conference = ''
    metadata_file = ''
    xml = ''
    pdf = ''
    print(argv)
    try:
        opts, args = getopt.getopt(argv,"hc:m:x:p:",["conference=","metadata_file=","xml=","pdf="])
        print(opts, args)
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('collect_papers.py -c <conference_folder> -m <metadata_file> -x <xml_folder> -p <pdf_folder>')
            sys.exit()
        elif opt in ("-c", "--conference"):
            conference = arg
            xml = os.path.join(conference,'xml')
            pdf = os.path.join(conference,'pdf')
        elif opt in ("-m", "--metadata"):
            metadata_file = os.path.join(conference, arg)
        elif opt in ("-x", "--xml"):
            xml = os.path.join(conference, arg)
        elif opt in ("-p", "--pdf"):
            pdf = os.path.join(conference, arg)
    return readable_dir(conference), readable_file(metadata_file), readable_dir(xml), readable_dir(pdf)

# check if unchecked path references is readable directory
def readable_dir(prospective_dir: str) -> Path:
    if not os.path.isdir(prospective_dir):
        raise Exception("readable_dir:{0} is not a valid path".format(prospective_dir))
    if not os.access(prospective_dir, os.R_OK):
        raise Exception("readable_dir:{0} is not a readable dir".format(prospective_dir))
    return Path(prospective_dir)

def readable_file(prospective_file: str) -> Path:
    if not os.path.isfile(prospective_file):
        raise Exception("readable_dir:{0} is not a valid path".format(prospective_file))
    if not os.access(prospective_file, os.R_OK):
        raise Exception("readable_dir:{0} is not a readable dir".format(prospective_file))
    return Path(prospective_file)

def get_publications(tree) -> dict:

    metadata = tree.findall("metadata")
    logging.debug(f"Number of publications in metadata file: {len(metadata)}")

    # get titles and creator names of publications
    publications = {}
    for publication in metadata:
        title = publication.find("title").text
        creator_names = [parse_creator(creator.find("name").text) for creator in publication.findall(".//creator")]
        if len(creator_names) == 0:
            logging.warning(f"The following publication does not contain creators: {metadata.index(publication)}")
        publications.update({title: creator_names})

    return publications

def ascii_rename(name:str) -> str:
    try:
        elements_to_be_replaced = [".", "-", ":", ",", "?", "!" ," "]
        name = name.replace("ß", "ss")
        name = name.replace("\"", "_em_")
        name = name.replace("\'", "_em_")
        for char in elements_to_be_replaced:
            name = name.replace(char, "_")
        try:
            name.encode("ascii")
        except:
            # if name contains non ascii
            name = ''.join([i if ord(i) < 128 else '_' for i in name])
        return name
    except AttributeError:
        pass

def parse_creator(name:str) -> list:
    name=[ascii_rename(elem.strip()) for elem in name.split(",")]
    return name

if __name__ == "__main__":

    # set logging
    logging.basicConfig(filename='collection.log', filemode='w', encoding='utf-8', level=logging.DEBUG)

    # call main function
    main(sys.argv)
