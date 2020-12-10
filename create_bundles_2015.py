import logging
import os
from xml.etree import ElementTree as ET
import re
import pandas as pd
from shutil import copyfile
import shutil
from pathlib import Path

conference = "DHd2015"

# set logging
logging.basicConfig(filename='support/' + conference +'_bundle.log', filemode='w', level=logging.INFO)

def main():
    base_path = readable_dir(os.path.join("conferences", conference))
    metadata_file = readable_file(os.path.join(base_path, "Metadaten_2015.xml"))
    pdf = readable_dir(os.path.join(base_path, "dhd2015_gesamt"))

    # parse metadata file of conference
    tree = ET.parse(metadata_file)
    publications_metadata = tree.findall("metadata")
    pub = get_publications(publications_metadata)

    # get pdf files
    files = [f for f in os.listdir(pdf) if f != ".DS_Store"]
    renamed = {f:f.replace("\xa0", "") for f in files}
    # print(renamed)
    for f in renamed.keys():
        os.rename(os.path.join(pdf,f), os.path.join(pdf, renamed.get(f)))
    files = [f.replace("\xa0", "") for f in files]
    if len(publications_metadata) != len(files):
        logging.warning(f"Number of publications in metadata file ({len(publications_metadata)}) does not match the number of files in directory ({len(files)}).")

    # clean file names
    # cleaned = [re.sub(r'[0-9]{6}_[a-zA-Z]*_', '',name) if name[0].isdigit() else name for name in file_names]

    assigned_files = {}

    for title in pub.keys():
        creators = pub.get(title)
        parsed_title = title.split(" ")
    
        for creator in creators:
            creator_files = find_matching_files(creator, files)
            if len(creator_files)!=0:
                if any(parsed_title[0].lower() in f.lower() for f in creator_files):
                    for f in creator_files:
                        if parsed_title[0].lower() in f.lower():
                            assigned_files.update({title:f})

    # safe ordered files and titles in csv file
    df = pd.DataFrame({"title": list(assigned_files.keys()),
                    'file name': [os.path.basename(elem) for elem in list(assigned_files.values())]})
    df.to_csv('support/' + conference + ".csv", header=True)

    # check not assigned titles
    not_assigned = []
    for title in pub.keys():
        if title not in assigned_files.keys():
            not_assigned.append(title)
    # print(not_assigned)
    print(len(not_assigned))

    # check not assigned files
    single_files = []
    for name in files:
        if name not in assigned_files.values():
            single_files.append(name)
    # print(single_files)
    print(len(single_files))

    create_bundles(conference, pdf, assigned_files)


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

def parse_creator(name: str) -> list:
    name = [elem.strip() for elem in name.split(",")]
    return name[0]

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

def find_matching_files(creator, file_names):
    possible_files = [f for f in file_names if creator.lower() in f.lower()]
    non_ascii = [f for f in file_names if ascii_rename(creator.lower()) in ascii_rename(f.lower())] 
    return possible_files + non_ascii

def create_bundles(conference, pdf, assigned_files: dict) -> dict:
    
    # create directory for conference in bundle structure
    bundle_path = os.path.join("bundle_structures", os.path.basename(conference))
    print(bundle_path)
    try:
        os.mkdir(bundle_path)
    except OSError:
        logging.warning("Directory already exists. Continue..")

    # create directory for each publication and copy pdfs / xmls to directory
    for (title, f) in assigned_files.items():
        file_name = ascii_rename(f[:-4])
        try:
            os.mkdir(os.path.join(bundle_path, file_name))
            os.mkdir(os.path.join(bundle_path, file_name, "bundle_publications"))
        except FileExistsError:
            logging.warning(f"Bundle directories {os.path.join(bundle_path, ascii_rename(f[:-4]))} already exists. Continue..")

        publications_folder = readable_dir(os.path.join(bundle_path, file_name, "bundle_publications"))
        path_to_pdf = readable_file(os.path.join(pdf,f))
        # print(publications_folder)
        print(path_to_pdf)
        print(os.path.join(publications_folder, f))
        shutil.copy(path_to_pdf, publications_folder)

    list_of_defective_dirs = [dirpath for (dirpath, dirs, files) in os.walk(bundle_path)
                              if len(dirs) == 0 and len(files) != 2]
    if len(list_of_defective_dirs) != 0:
        logging.warning(f"The following directories do not contain two files: {list_of_defective_dirs}")
    else:
        logging.info("All directories have been created and contain two files. Continue..")

if __name__ == "__main__":
    main()
