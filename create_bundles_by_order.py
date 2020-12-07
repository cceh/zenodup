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
from pdfreader import SimplePDFViewer
import pandas as pd
from lxml import etree

XMLParser = etree.XMLParser()
ET.register_namespace('', "http://www.tei-c.org/ns/1.0")
namespace = {'TEI': "http://www.tei-c.org/ns/1.0"}

pdf_only = False
conference = ''
metadata_file = ''
xml = ''
pdf = ''


def main(argv):
    # set working paths based on command line arguments
    set_paths(argv[1:])

    print(pdf_only)
    # set logging
    conference_name = os.path.basename(conference)
    logging.basicConfig(filename='support/' + conference_name + '_bundle.log', filemode='w', level=logging.INFO)

    # parse metadata file of conference
    tree = ET.parse(metadata_file)
    publications_metadata = tree.findall("metadata")

    # get list of publications
    publications = get_publications(publications_metadata)

    if not pdf_only:
        # get publication pdfs
        publication_pdfs = get_publication_files(pdf)
        # get publication xmls
        publication_xmls = get_publication_files(xml)
        # safe ordered files and titles in csv file
        df = pd.DataFrame({"title": publications, 'title from pdf': publication_pdfs.values(),
                           'title from xml': publication_xmls.values(),
                           'pdf file': publication_pdfs.keys(), 'xml file': publication_xmls.keys()})

        df.to_csv('support/' + conference_name + ".csv", header=True)

        create_bundles(conference, publications_metadata, list(publication_pdfs.keys()), list(publication_xmls.keys()))

        logging.info(f"Bundle structure for conference {conference_name} has been created under "
                     f"'bundle_structures/{conference_name}'.")
    else:
        # get file names
        pdf_files = [file for file in os.listdir(pdf) if file != ".DS_Store"]
        pdf_files.sort()
        print(pdf_files)
        # safe ordered files and titles in csv file
        while len(publications) < len(pdf_files):
            publications.append('')

        df = pd.DataFrame({"title": publications, 'pdf file': pdf_files})
        df.to_csv('support/' + conference_name + ".csv", header=True)

        # create_bundles(conference, publications_metadata, list(publication_pdfs.keys()), list(publication_xmls.keys()))

        logging.info(f"Bundle structure for conference {conference_name} has been created under "
                     f"'bundle_structures/{conference_name}'.")


# set working paths
def set_paths(argv: list):
    global pdf_only
    global conference
    global metadata_file
    global xml
    global pdf

    try:
        opts, args = getopt.getopt(argv, "h:c:m:x:p:", ["conference=", "metadata_file=", "xml=", "pdf="])
    except getopt.GetoptError:
        sys.exit(2)

    print(opts)
    for opt in opts:
        print(opt[0])

    if any('-x' in opt[0] for opt in opts):
        for opt, arg in opts:
            if opt == '-h':
                print('create_bundles.py -c <conference_folder> -m <metadata_file> -x <xml_folder> -p <pdf_folder>')
                sys.exit()
            elif opt in ("-c", "--conference"):
                conference = readable_dir(os.path.join("conferences", arg))
                pdf = os.path.join(conference, "pdf")
                xml = os.path.join(conference, "xml")
            elif opt in ("-m", "--metadata"):
                metadata_file = readable_file(os.path.join(conference, arg))
            elif opt in ("-x", "--xml"):
                xml = readable_dir(os.path.join(conference, arg))
            elif opt in ("-p", "--pdf"):
                pdf = readable_dir(os.path.join(conference, arg))
    else:
        pdf_only = True
        for opt, arg in opts:
            if opt == '-h':
                print('create_bundles.py -c <conference_folder> -m <metadata_file> -x <xml_folder> -p <pdf_folder>')
                sys.exit()
            elif opt in ("-c", "--conference"):
                conference = readable_dir(os.path.join("conferences", arg))
                pdf = os.path.join(conference, "pdf")
            elif opt in ("-m", "--metadata"):
                metadata_file = readable_file(os.path.join(conference, arg))
            elif opt in ("-p", "--pdf"):
                pdf = readable_dir(os.path.join(conference, arg))
        return readable_dir(conference), readable_file(metadata_file), readable_dir(pdf)


# check if unchecked path references is readable directory
def readable_dir(prospective_dir: str) -> str:
    if not os.path.isdir(prospective_dir):
        raise Exception("readable_dir:{0} is not a valid path".format(prospective_dir))
    if not os.access(prospective_dir, os.R_OK):
        raise Exception("readable_dir:{0} is not a readable dir".format(prospective_dir))
    return prospective_dir


def readable_file(prospective_file: str) -> str:
    if not os.path.isfile(prospective_file):
        raise Exception("readable_dir:{0} is not a valid path".format(prospective_file))
    if not os.access(prospective_file, os.R_OK):
        raise Exception("readable_dir:{0} is not a readable dir".format(prospective_file))
    return prospective_file


def get_publications(metadata: ET.Element) -> list:
    logging.debug(f"Number of publications in metadata file: {len(metadata)}")

    # get titles and creator names of publications
    publications = []
    for publication in metadata:
        title = publication.find("title").text
        if not title:
            logging.warning(f"The publication with index {metadata.index(publication)} does not contain a title")
        publications.append(title)

    return publications


def get_publication_files(file_dir) -> dict:
    # get types of files in given directory
    file_types = set([os.path.splitext(file_name)[1] for file_name in os.listdir(file_dir) if file_name != ".DS_Store"])
    if len(file_types) > 1:
        logging.error(f"The given directory {file_dir} contains files with multipe formats: {file_types}")
        raise Exception("The given directory contains files with multiple formats")
    else:
        file_type = list(file_types)[0]
        # print(file_type)

    # get file names
    files = [os.path.join(file_dir, file) for file in os.listdir(file_dir) if file != ".DS_Store"]
    files.sort()

    file_titles = {}
    # get title from file

    # get titles and creator names of publications
    if file_type == ".xml":
        for file in files:
            tree = ET.parse(file)
            try:
                title = tree.find(".//TEI:title", namespace).text
            except AttributeError:
                logging.warning(f"Couldn't extract title from file {file}")
                title = ""
            file_titles.update({file: title})
            # print(title)

    elif file_type == ".pdf":
        for file in files:
            fd = open(file, "rb")
            viewer = SimplePDFViewer(fd)
            viewer.navigate(1)
            viewer.render()
            plain_text = "".join(viewer.canvas.strings)
            new_text = plain_text.replace(
                        "Book of Abstracts zur Konferenz Digital Humanities im deutschsprachigen Raum 2018", "")
            new_text = new_text[:100]
            file_titles.update({file: new_text})
            # print(new_text)
    return file_titles


def create_bundles(conference, publications: list, publication_pdfs: list, publication_xmls: list):
    # create directory for conference in bundle structure
    bundle_path = os.path.join("bundle_structures", os.path.basename(conference))
    try:
        os.mkdir(bundle_path)
    except OSError:
        logging.warning("Directory already exists. Continue..")

    for file in publication_pdfs:
        index = publication_pdfs.index(file)
        file_name = os.path.splitext(os.path.basename(file))[0]
        bundle_dir = os.path.join(bundle_path, file_name)
        try:
            os.mkdir(bundle_dir)
        except OSError:
            logging.warning("Directory already exists. Continue..")

        copyfile(file, os.path.join(bundle_dir, os.path.basename(file)))
        copyfile(publication_xmls[index], os.path.join(bundle_dir, os.path.basename(publication_xmls[index])))

        create_bundles_metadata(bundle_dir, publications[index])

    list_of_defective_dirs = [dirpath for (dirpath, dirs, files) in os.walk(bundle_path)
                              if len(dirs) == 1 and len(files) != 2]
    if len(list_of_defective_dirs) != 0:
        logging.warning(f"The following directories do not contain two files: {list_of_defective_dirs}")
    else:
        logging.info("All directories have been created and contain two files. Continue..")


def create_bundles_metadata(bundle_dir: str, pub: ET.Element) -> None:
    if pub.find("doi").text:
        data = {"metadata": {"upload_type": pub.find("upload_type").text,
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
                             "keywords": [keyword.replace("\"", "") for keyword in
                                          pub.find("keywords").text.split(", ")],
                             "contributors": [{"name": contributor.find("name").text,
                                               "affiliation": contributor.find("affiliation").text,
                                               "type": contributor.find("type").text
                                               } for contributor in
                                              pub.findall("contributors/contributor")],
                             "communities": [{"identifier": community.text
                                              } for community in pub.findall("communities/identifier")],
                             "conference_title": pub.find("conference_title").text,
                             "conference_acronym": pub.find("conference_acronym").text,
                             "conference_dates": pub.find("conference_dates").text,
                             "conference_place": pub.find("conference_place").text,
                             "conference_url": pub.find("conference_url").text
                             }
                }
    else:
        data = {"metadata": {"upload_type": pub.find("upload_type").text,
                             "publication_type": pub.find("publication_type").text,
                             "publication_date": pub.find("publication_date").text,
                             "title": pub.find("title").text,
                             "creators": [{"name": creator.find("name").text,
                                           "affiliation": creator.find("affiliation").text
                                           } for creator in pub.findall("creators/creator")],
                             "description": pub.find("description").text,
                             "access_right": pub.find("access_right").text,
                             "license": pub.find("license").text,
                             "keywords": [keyword.replace("\"", "") for keyword
                                          in pub.find("keywords").text.split(", ")],
                             "contributors": [{"name": contributor.find("name").text,
                                               "affiliation": contributor.find("affiliation").text,
                                               "type": contributor.find("type").text
                                               } for contributor in
                                              pub.findall("contributors/contributor")],
                             # "communities":[{"identifier": community.text
                             #  } for community in pub.findall("communities/identifier")],
                             "conference_title": pub.find("conference_title").text,
                             "conference_acronym": pub.find("conference_acronym").text,
                             "conference_dates": pub.find("conference_dates").text,
                             "conference_place": pub.find("conference_place").text,
                             "conference_url": pub.find("conference_url").text
                             }
                }
    with open(os.path.join(bundle_dir, 'bundle_metadata.json'), 'w') as outfile:
        json.dump(data, outfile)


if __name__ == "__main__":
    # call main function
    main(sys.argv)
