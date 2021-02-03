"""Script for assigning conference papers to bundles based on metadata file

Put conference folder in /conferences. The conference folder is expected in the following strucutre:

- CONFERENCE: Folder containing all relevant files of conference
    - METADATA_FILE: Name of metadata file for conference containing all relevant information of conference publications
    - XML: Folder to xml files of conference pubclications
    - PDF: Folder to pdf files of conference publications

To run this script the following arguments need to be modified:
    * CONFERENCE: Name of conference folder
    * METADATA_FILE: Name of metadata file (expected format: xml) for conference publications
    * XML (Optional): Name of folder of conference publication xmls. If no name is given,
      script expects folder name "xml"
    * PDF (Optional): Name of folder of conference publication pdfs. If no name is given,
      script expects folder name "pdf"

The created bundle structure will be created in /bundle_structure/[CONFERENCE].
"""

# ## Imports
import getopt
import logging
import os
from pathlib import Path
import sys
from xml.etree import ElementTree as ET
from shutil import copyfile
import json
import re
import pandas as pd

import general_functions

def main(argv):

    # set working paths based on command line arguments
    conference, metadata_file, xml, pdf = set_paths(argv[1:])

    # set logging
    conference_name = os.path.basename(conference)
    logging.basicConfig(filename='support/' + conference_name+'_bundle.log', filemode='w', level=logging.INFO)

    # parse metadata file of conference
    tree = ET.parse(metadata_file)
    publications_metadata = tree.findall("metadata")

    # get publications with creator names
    publications = get_publications(publications_metadata)

    # Get all possible names of pdf and xml files based on publication creaotors and titles in metadata file of
    # conference
    publication_names = get_possible_publication_names(tree, publications)
    logging.debug(len(publication_names))

    # get publication pdfs
    publication_pdfs = get_publication_files(publication_names, pdf)

    # get publication xmls
    publication_xmls = get_publication_files(publication_names, xml)

    # create bundle directories for publications
    publication_bundles = create_bundles(conference, publication_pdfs, publication_xmls)
    
    # create json metadata file for each bundle based on metadata for publication
    general_functions.create_bundles_metadata(publications_metadata, publication_bundles)

    create_csv(os.path.basename(conference))
    logging.info(f"Bundle structure for conference {conference_name} has been created under "
                 f"'bundle_structures/{conference_name}'.")


# set working paths
def set_paths(argv: list) -> (Path, Path, Path, Path):
    conference = ''
    metadata_file = ''
    xml = ''
    pdf = ''
    try:
        opts, args = getopt.getopt(argv, "hc:m:x:p:", ["conference=", "metadata_file=", "xml=", "pdf="])
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('create_bundles.py -c <conference_folder> -m <metadata_file> -x <xml_folder> -p <pdf_folder>')
            sys.exit()
        elif opt in ("-c", "--conference"):
            conference = os.path.join("conferences", arg)
            xml = os.path.join(conference, "xml")
            pdf = os.path.join(conference, "pdf")
        elif opt in ("-m", "--metadata"):
            metadata_file = os.path.join(conference, arg)
        elif opt in ("-x", "--xml"):
            xml = os.path.join(conference, arg)
        elif opt in ("-p", "--pdf"):
            pdf = os.path.join(conference, arg)
    return general_functions.readable_dir(conference), general_functions.readable_file(metadata_file), general_functions.readable_dir(xml), general_functions.readable_dir(pdf)

def get_publications(metadata: ET.Element) -> dict:

    logging.debug(f"Number of publications in metadata file: {len(metadata)}")

    # get titles and creator names of publications
    publications = {}
    for publication in metadata:
        title = publication.find("title").text
        if not title:
            logging.warning(f"The publication with index {metadata.index(publication)} does not contain a title")
        creator_names = [parse_creator(creator.find("name").text) for creator in publication.findall(".//creator")]
        if len(creator_names) == 0:
            logging.warning(f"The publication with title {publication.find('title').text} "
                            f"(index {metadata.index(publication)}) does not contain creators.")
        publications.update({title: creator_names})

    return publications

def ascii_rename(name: str) -> str:
    try:
        elements_to_be_replaced = [".", "-", ":", ",", "?", "!", " ", "(", ")", "&", "@"]
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

def parse_creator(name: str) -> list:
    name = [ascii_rename(elem.strip()) for elem in name.split(",")]
    return name

def get_possible_publication_names(metadata: list, publications: dict) -> dict:

    publication_names = {}
    title = ''
    for (publication, creators) in publications.items():
        # logging.info((publication, creators))
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

def get_publication_files(publication_names: dict, file_dir) -> dict:

    # get types of files in given directory
    file_types = set([os.path.splitext(file_name)[1] for file_name in os.listdir(file_dir) if file_name != ".DS_Store"])
    if len(file_types) > 1:
        logging.error(f"The given directory {file_dir} contains files with multipe formats: {file_types}")
        raise Exception("The given directory contains files with multiple formats")
    else:
        file_type = list(file_types)[0]

    # get file names
    file_names = [os.path.splitext(file_name)[0] for file_name in os.listdir(file_dir) if file_name != ".DS_Store"]
    file_names.sort()
    file_names_to_compare = {re.sub(r'[0-9]{3}_final-', '', name): name for name in file_names}
    # print(file_names_to_compare)
    publication_files = {}
    last_elem = ()
    counter = 0

    for elem in publication_names:
        if any(possible_name.find(name) != -1 for possible_name in publication_names.get(elem) for name in
               file_names_to_compare.keys()):
            for possible_name in publication_names.get(elem):
                for name in file_names_to_compare.keys():
                    if possible_name.find(name) != -1:
                        logging.debug("----")
                        logging.debug(name)
                        logging.debug("----")
                        publication_files.update({elem: general_functions.readable_file(
                                                os.path.join(file_dir, file_names_to_compare.get(name) + file_type))})
                        last_elem = (elem, name)
            counter = counter + 1
        elif any(possible_name.find(name[:-1]) != -1 for possible_name in publication_names.get(elem) for name in
                 file_names_to_compare.keys()):
            for possible_name in publication_names.get(elem):
                for name in file_names_to_compare.keys():
                    if possible_name.find(name[:-1]) != -1:
                        logging.debug("----")
                        logging.debug(name)
                        logging.debug("----")
                        publication_files.update({elem: general_functions.readable_file(
                                                os.path.join(file_dir, file_names_to_compare.get(name) + file_type))})
                        last_elem = (elem, name)
                        # print(last_elem)
            counter = counter + 1
        else:
            try: 
                logging.info(f"Last element: {last_elem[1]}")
                if all(key != last_elem[1] for key in file_names_to_compare.keys()):
                    current_file = file_names[counter]
                    # logging.info(f"Current file: {current_file}")
                    last_elem = (elem, current_file)
                    # logging.info(f"Updated last element: {last_elem}")
                else:
                    temp = iter(file_names_to_compare)
                    for key in temp:
                        # print(key)
                        if key == last_elem[1]:
                            current_file = file_names_to_compare.get(next(temp))
                            # logging.info(f"Current file: {current_file}")
                            last_elem = (elem, current_file)
                            # logging.info(f"Updated last element: {last_elem}")
            except IndexError:
                last_elem = (elem, file_names[counter])
                # logging.info(f"Last element: {last_elem}")
                current_file = file_names[counter]
                # logging.info(f"Current file: {current_file}")

            logging.warning("***")
            logging.warning(f"For the publication {elem} exists no matching file. Get publication by previous file. "
                            f"Assigned \n {current_file} \n {elem}")
            publication_files.update({elem: general_functions.readable_file(os.path.join(file_dir, current_file + file_type))})
            logging.warning("***")
            counter = counter + 1

    return publication_files

def create_bundles(conference, publication_pdfs: dict, publication_xmls: dict) -> dict:
    
    # create directory for conference in bundle structure
    bundle_path = os.path.join("bundle_structures", os.path.basename(conference))
    try:
        os.mkdir(bundle_path)
    except OSError:
        logging.warning("Directory already exists. Continue..")

    publication_paths = {publication: os.path.join(bundle_path, os.path.basename(file_path)[:-4]) for
                         (publication, file_path) in publication_pdfs.items()}
    # create_csv(os.path.basename(conference), publication_paths)
    logging.info(len(publication_paths))
    # create directory for each publication and copy pdfs / xmls to directory
    for (publication, path) in publication_paths.items():
        try:
            os.mkdir(os.path.join(path))
            os.mkdir(os.path.join(path, "bundle_publications"))
        except FileExistsError:
            logging.warning(f"Bundle directories {os.path.join(path)} already exists. Continue..")

        publications_folder = os.path.join(path, "bundle_publications")
        copyfile(publication_pdfs.get(publication), os.path.join(publications_folder,
                                                                 os.path.basename(publication_pdfs.get(publication))))
        copyfile(publication_xmls.get(publication), os.path.join(publications_folder,
                                                                 os.path.basename(publication_xmls.get(publication))))

    list_of_defective_dirs = [dirpath for (dirpath, dirs, files) in os.walk(bundle_path)
                              if len(dirs) == 0 and len(files) != 2]
    if len(list_of_defective_dirs) != 0:
        logging.warning(f"The following directories do not contain two files: {list_of_defective_dirs}")
    else:
        logging.info("All directories have been created and contain two files. Continue..")
    return publication_paths

def create_csv(conference:str):
    # safe ordered files and titles in csv file
    bundles_overview = []
    for bundle in os.listdir(os.path.join("bundle_structures", conference)):
        bundle_publications = os.listdir(os.path.join("bundle_structures", conference, bundle, "bundle_publications"))
        data = [bundle] + bundle_publications
        bundles_overview.append(data)

    df = pd.DataFrame(data=bundles_overview, index = None, columns=["Bundle Name", "Pdf file", "XML file"])
    df.to_csv('support/' + conference + ".csv", header=True)


if __name__ == "__main__":

    # call main function
    main(sys.argv)
