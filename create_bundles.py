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
from shutil import copyfile
import json



def main(argv):

    # set working paths based on command line arguments
    conference, metadata_file, xml, pdf = set_paths(argv[1:])

    # set logging
    conference_name = os.path.basename(conference)
    logging.basicConfig(filename=conference_name+'_bundle.log', filemode='w', encoding='utf-8', level=logging.INFO)

    # parse metadata file of conference
    tree = ET.parse(metadata_file)
    publications_metadata = tree.findall("metadata")

    # get publications with creator names
    publications = get_publications(publications_metadata)

    # Get all possible names of pdf and xml files based on publication creaotors and titles in metadata file of conference
    publication_names = get_possible_publication_names(tree, publications)
    logging.debug(len(publication_names))

    # get publication pdfs
    publication_pdfs = get_publication_files(publication_names, pdf)

    # get publication xmls
    publication_xmls = get_publication_files(publication_names, xml)

    # create bundle directories for publications
    publication_bundles = create_bundles(conference, publication_pdfs, publication_xmls)
    
    # create json metadata file for each bundle based on metadata for publication
    create_bundles_metadata(publications_metadata, publication_bundles)

    logging.info(f"Bundle structure for conference {conference_name} has been created under 'bundle_structures/{conference_name}'.")

# set working paths
def set_paths(argv:list) -> (Path, Path, Path, Path):
    conference = ''
    metadata_file = ''
    xml = ''
    pdf = ''
    try:
        opts, args = getopt.getopt(argv,"hc:m:x:p:",["conference=","metadata_file=","xml=","pdf="])
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('create_bundles.py -c <conference_folder> -m <metadata_file> -x <xml_folder> -p <pdf_folder>')
            sys.exit()
        elif opt in ("-c", "--conference"):
            conference = os.path.join("conferences", arg)
            xml = os.path.join(conference,"xml")
            pdf = os.path.join(conference,"pdf")
        elif opt in ("-m", "--metadata"):
            metadata_file = os.path.join(conference, arg)
        elif opt in ("-x", "--xml"):
            xml = os.path.join(conference, arg)
        elif opt in ("-p", "--pdf"):
            pdf = os.path.join(conference, arg)
    return readable_dir(conference), readable_file(metadata_file), readable_dir(xml), readable_dir(pdf)

# check if unchecked path references is readable directory
def readable_dir(prospective_dir:str) -> Path:
    if not os.path.isdir(prospective_dir):
        raise Exception("readable_dir:{0} is not a valid path".format(prospective_dir))
    if not os.access(prospective_dir, os.R_OK):
        raise Exception("readable_dir:{0} is not a readable dir".format(prospective_dir))
    return Path(prospective_dir)

def readable_file(prospective_file:str) -> Path:
    if not os.path.isfile(prospective_file):
        raise Exception("readable_dir:{0} is not a valid path".format(prospective_file))
    if not os.access(prospective_file, os.R_OK):
        raise Exception("readable_dir:{0} is not a readable dir".format(prospective_file))
    return Path(prospective_file)

def get_publications(metadata:ET.Element) -> dict:

    logging.debug(f"Number of publications in metadata file: {len(metadata)}")

    # get titles and creator names of publications
    publications = {}
    for publication in metadata:
        title = publication.find("title").text
        if not title:
            logging.warning(f"The publication with index {metadata.index(publication)} does not contain a title")
        creator_names = [parse_creator(creator.find("name").text) for creator in publication.findall(".//creator")]
        if len(creator_names) == 0:
            logging.warning(f"The publication with index {metadata.index(publication)} does not contain creators")
        publications.update({title: creator_names})

    return publications

def ascii_rename(name:str) -> str:
    try:
        elements_to_be_replaced = [".", "-", ":", ",", "?", "!" ," ", "(", ")", "&", "@"]
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

def get_possible_publication_names(metadata:list, publications:dict) -> dict:

    publication_names = {}
    for (publication, creators) in publications.items():
        try:
            title = ascii_rename(publication)
        except TypeError:
            logging.warning(f"The following publication does not contain a title: {metadata.index(publication)}")
        prefixes = [creator[0].upper()+'_'+creator[1]+'_' for creator in creators]
        possible_names = [prefix + title for prefix in prefixes]

        # if '_em_' in title replace by '_' and add prefix + modified name to possible names 
        try:
            if title.find("_em_") != -1:
                for prefix in prefixes:
                    possible_names.append(prefix + title.replace("_em_", "_"))
            if title.find("ss") != -1:
                for prefix in prefixes:
                    possible_names.append(prefix + title.replace("ss", "_"))
        except AttributeError:
            pass

        # add double '_' at the end of prefix and add all combinations to possible names
        for prefix in prefixes:
            possible_names.append(prefix + '_' + title)

        publication_names.update({publication: possible_names})
    return publication_names

def get_publication_files(publication_names:dict, file_dir:Path) -> dict:

    # get types of files in given directory
    file_types = set([os.path.splitext(file_name)[1] for file_name in os.listdir(file_dir) if file_name != ".DS_Store"])
    if len(file_types) > 1:
        logging.error(f"The given directory {file_dir} contains files with multipe formats: {file_types}")
        raise Exception("The given directory contains files with multipe formats")
    else:
        file_type = list(file_types)[0]

    # get file names
    file_names = [os.path.splitext(file_name)[0] for file_name in os.listdir(file_dir) if file_name != ".DS_Store"]

    publication_files = {}
    last_elem = tuple

    for elem in publication_names:
        if any(possible_name.find(name)!= -1 for possible_name in publication_names.get(elem) for name in file_names):
            for possible_name in publication_names.get(elem):
                for name in file_names:
                    if possible_name.find(name) != -1:
                        logging.debug("----")
                        logging.debug(name)
                        logging.debug("----")
                        publication_files.update({elem:readable_file(os.path.join(file_dir, name + file_type))})
                        last_elem = (elem, name)
        elif any(possible_name.find(name[:-1])!= -1 for possible_name in publication_names.get(elem) for name in file_names):
            for possible_name in publication_names.get(elem):
                for name in file_names:
                    if possible_name.find(name[:-1]) != -1:
                        logging.debug("----")
                        logging.debug(name)
                        logging.debug("----")
                        publication_files.update({elem:readable_file(os.path.join(file_dir,name + file_type))})
                        last_elem = (elem, name)
        else:
            logging.warning("***")
            logging.warning(f"For the publication {elem} exists no matching file. Get publication by previous file.")
            current_file = file_names[file_names.index(last_elem[1]) + 1]
            logging.warning(f"Assigned file {current_file} to publication {elem}")
            publication_files.update({elem:readable_file(os.path.join(file_dir,current_file + file_type))})
            logging.warning("***")

    return publication_files

def create_bundles(conference: Path, publication_pdfs: dict, publication_xmls: dict) -> dict:
    
    # create directory for conference in bundle structure
    bundle_path = os.path.join("bundle_structures", os.path.basename(conference))
    try:
        os.mkdir(bundle_path)
    except OSError:
        logging.warning("Directory already exists. Continue..")

    publication_paths = {publication:os.path.join(bundle_path, os.path.basename(file_path)[:-4]) for (publication,file_path) in publication_pdfs.items()}
    # create directory for each publication and copy pdfs / xmls to directory
    for (publication, path) in publication_paths.items():
        os.mkdir(os.path.join(path))
        os.mkdir(os.path.join(path, "bundle_publications"))
        publications_folder = os.path.join(path, "bundle_publications")
        copyfile(publication_pdfs.get(publication), os.path.join(publications_folder, os.path.basename(publication_pdfs.get(publication))))
        copyfile(publication_xmls.get(publication), os.path.join(publications_folder, os.path.basename(publication_xmls.get(publication))))

    list_of_defective_dirs = [dirpath for (dirpath, dirs, files) in os.walk(bundle_path) if len(dirs) == 0 and len(files) != 2]
    if len(list_of_defective_dirs) != 0:
        logging.warning(f"The following directories do not contain two files: {list_of_defective_dirs}")
    else:
        logging.info("All directories have been created and contain two files. Continue..")
    return publication_paths

def create_bundles_metadata(publications_metadata: ET.Element, publication_bundles: dict) -> None:

    for (publication, bundle_path) in publication_bundles.items():
        for pub in publications_metadata:
            if pub.find("title").text == publication:
                if pub.find("doi").text:
                    data = {"metadata":{"upload_type": pub.find("upload_type").text,
                                        "publication_type": pub.find("publication_type").text,
                                        "publication_date": pub.find("publication_date").text,
                                        "title": pub.find("title").text,
                                        "creators": [{"name": creator.find("name").text,
                                                    "affiliation": creator.find("affiliation").text
                                                    } for creator in pub.findall("creators/creator")],                       
                                        "description": pub.find("description").text,
                                        "access_right": pub.find("access_right").text,
                                        "license": pub.find("license").text,
                                        "doi": pub.find("doi").text,
                                        "keywords": [keyword.replace("\"", "") for keyword in pub.find("keywords").text.split(", ")],
                                        "contributors": [{"name":contributor.find("name").text,
                                                        "affiliation":contributor.find("affiliation").text,
                                                        "type":contributor.find("type").text
                                                        } for contributor in pub.findall("contributors/contributor")],
                                        "communities":[{"identifier": community.text
                                                        } for community in pub.findall("communities/identifier")],
                                        "conference_title": pub.find("conference_title").text,
                                        "conference_acronym": pub.find("conference_acronym").text,
                                        "conference_dates": pub.find("conference_dates").text,
                                        "conference_place": pub.find("conference_place").text,
                                        "conference_url": pub.find("conference_url").text
                                        }
                            }
                else: 
                    data = {"metadata":{"upload_type": pub.find("upload_type").text,
                                        "publication_type": pub.find("publication_type").text,
                                        "publication_date": pub.find("publication_date").text,
                                        "title": pub.find("title").text,
                                        "creators": [{"name": creator.find("name").text,
                                                    "affiliation": creator.find("affiliation").text
                                                    } for creator in pub.findall("creators/creator")],                       
                                        "description": pub.find("description").text,
                                        "access_right": pub.find("access_right").text,
                                        "license": pub.find("license").text,
                                        "keywords": [keyword.replace("\"", "") for keyword in pub.find("keywords").text.split(", ")],
                                        "contributors": [{"name":contributor.find("name").text,
                                                        "affiliation":contributor.find("affiliation").text,
                                                        "type":contributor.find("type").text
                                                        } for contributor in pub.findall("contributors/contributor")],
                                        # "communities":[{"identifier": community.text
                                                       #  } for community in pub.findall("communities/identifier")],
                                        "conference_title": pub.find("conference_title").text,
                                        "conference_acronym": pub.find("conference_acronym").text,
                                        "conference_dates": pub.find("conference_dates").text,
                                        "conference_place": pub.find("conference_place").text,
                                        "conference_url": pub.find("conference_url").text
                                        }
                            }
        with open(os.path.join(bundle_path, 'bundle_metadata.json'), 'w') as outfile:
            json.dump(data, outfile)


if __name__ == "__main__":

    # call main function
    main(sys.argv)
