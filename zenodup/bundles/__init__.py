"""Package to handle creation of bundle structure

Contains a python module to parse filenames and 
abstract titles from conferences metadata files 
as well as a module to check sanity of given paths.
"""

import csv
import json
import logging
from lxml import etree
import os
from shutil import copyfile
from xml.etree import ElementTree as ET
import yaml

from bundles import parsing
from bundles import sanity


# set base paths for working diretories
with open(r'config.yml') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

# register TEI namespace for abstracts xml files
XMLParser = etree.XMLParser()
ET.register_namespace('', "http://www.tei-c.org/ns/1.0")
namespace = {'TEI': "http://www.tei-c.org/ns/1.0"}  


class Conference:
    """Conference class 

    Contains all information in order to create bundle structure for given 
    Conference directory.

    Methods
    -------
    create bundles
        Created bundle structure for conference
    update metadata
        Updates metadata file of conference. 
        This method is not part of the regular workflow and was used once.
    """

    def __init__(self, name: str, metadata: str, sequenced: bool, pdf: str, xml: str):
        """Constructor of class Conference
        
        Checks if given parameters are valid in order to create bundle structure and 
        sets paths.

        Parameters
        ----------
        name : str
            Name of conference (directory) to be processed
        source : str
            Path to conference directory ("input_base/name")
        metadata : str
            Name of conference metadata file
        sequenced : bool
            If parameter is passed, the order of files is assumed to 
            be the same as appearances of metadata tags in metadata file. 
            If not passed, the files will be assigned by name scheme
        pdf : str
            Name of conferences directory containing all pdf files
        xml : str
            Name of conferences directory containing all xml files
        abstracts : list
            List of metadata elements from conference's metadata file
        titles : list
            List of titles from conference's metadata file
        """

        # set parameters of Conference instance
        self.name = name
        self.source = sanity.readable_dir(os.path.join(config['input_base'], name))
        self.output = self.__create_output_dir()
        self.metadata = sanity.readable_file(os.path.join(self.source, metadata))
        self.sequenced = sequenced
        self.pdf = sanity.readable_dir(os.path.join(self.source, pdf))
        if xml:
            self.xml = sanity.readable_dir(os.path.join(self.source, xml))
        else:
            self.xml = None
        self.abstracts = self.__get_abstracts()
        self.titles = self.__get_titles()

        # set logging
        logging.basicConfig(filename=config['logging_dir'] + self.name +'_bundle.log', filemode='w+', level=logging.INFO)

        # check sanity of pdf and xml directories
        sanity.directory(self.pdf)
        if self.xml:
            sanity.directory(self.xml)
            sanity.filenames(self)
        
    def create_bundles(self) -> None:
        """Creates bundle structure

        Creates bundle structure for conference in 
        configured output_base directory (see config.yml file). 
        For more information please see README.md
        """
        
        counter = 1

        # assign xmls and pdfs to publications
        assignments = self.__assign_files()

        # create bundle structure
        for bundle in assignments:
            try:

                # create bundle directory
                if self.xml:
                    bundle_dir = os.path.join(self.output, bundle['name'])
                else:
                    bundle_dir = os.path.join(self.output, 'bundle_'+ '{:03d}'.format(counter))

                # create bundle directories
                os.mkdir(bundle_dir)
                os.mkdir(os.path.join(bundle_dir, 'bundle_publications'))

                # copy pdf file
                pdf_path = os.path.join(self.pdf, bundle['pdf'])
                copyfile(pdf_path, os.path.join(bundle_dir,'bundle_publications', bundle['pdf']))
                
                # copy xml file
                if self.xml:
                    xml_path = os.path.join(self.xml, bundle['xml'])
                    copyfile(xml_path, os.path.join(bundle_dir,'bundle_publications', bundle['xml']))
                
                # create json metadata file
                for elem in self.abstracts:
                    if elem.find("title").text == bundle["title"]:
                        create_metadata(elem, bundle_dir)
                    else:
                        continue

            except OSError:
                logging.warning(f"Directory {bundle_dir} already exists. Continue..")
            finally:
                counter = counter + 1

        # check if created bundle structure is complete
        self.__quality_check()
        # create csv file with assigned files to bundles
        self.__create_csv()

        # finish
        logging.info(f"Bundle structure for conference {self.name} has been created under "
                    f"'bundle_structures/{self.name}'.")

    def update_metadata(self):
        """Updates conference's metadata
        
        Adds notes and references to metadata elements in conference's metadata file.
        This method is not part of the regular workflow and was used once.
        """

        # set notes
        note = "Sofern eine editorische Arbeit an dieser Publikation stattgefunden hat, dann bestand diese aus der Eliminierung von Bindestrichen in Überschriften, die aufgrund fehlerhafter Silbentrennung entstanden sind, der Vereinheitlichung von Namen der Autor*innen in das Schema „Nachname, Vorname“ und/oder der Trennung von Überschrift und Unterüberschrift durch die Setzung eines Punktes, sofern notwendig."

        # set reference based on conference (year)
        if self.name == "DHd2014":
            ref = ""
        elif self.name == "DHd2015":
            ref = "http://gams.uni-graz.at/o:dhd2015.abstracts-gesamt"
        elif self.name == "DHd2016":
            ref = "https://doi.org/10.5281/zenodo.3679331"
        elif self.name == "DHd2017":
            ref = "https://doi.org/10.5281/zenodo.3684825"
        elif self.name == "DHd2018":
            ref = "https://doi.org/10.5281/zenodo.3684897"
        elif self.name == "DHd2019":
            ref = "https://doi.org/10.5281/zenodo.2600812"
        elif self.name == "DHd2020":
            ref = "https://doi.org/10.5281/zenodo.3666690"
        else:
            ref = ""

        # add notes and references
        tree = ET.parse(self.metadata)
        root = tree.getroot()

        references = ET.Element('references')
        references.text = ref
        notes = ET.Element('notes')
        notes.text = note

        for abstract in root.findall("metadata"):
            abstract.append(references)
            abstract.append(notes)

        ET.indent(tree, space="   ")

        # save file in configured directory for updated metadata files
        tree.write(config["update_dir"] + self.name + ".xml", encoding="utf-8")

    # get pdf files of conference
    def __get_pdfs(self) -> dict:
        files = [f for f in os.listdir(self.pdf) if f != ".DS_Store"]
        files.sort()
        if len(files) != len(self.abstracts):
            raise Exception(f"Number of pdf files in conference pdf directory {self.pdf} does not match number of metadata tags in conference metadata file {self.metadata}. \n Files ({len(files)} - Element-Tags ({len(self.abstracts)}).")
        return files

    # get xml files of conference
    def __get_xmls(self) -> dict:
        xmls = [f for f in os.listdir(self.xml) if f != ".DS_Store"]
        xmls.sort()
        if len(xmls) != len(self.abstracts):
            raise Exception(f"Number of xml files in conference xml directory {self.xml} does not match number of metadata tags in conference metadata file {self.metadata}. \n Files ({len(xmls)} - Element-Tags ({len(self.abstracts)}).")        
        return xmls

    # parse metadata file of conference end return abstracts metadata
    def __get_abstracts(self) -> list:
        tree = ET.parse(self.metadata)
        abstracts = tree.findall("metadata")
        return abstracts

    # get titles of conference's abstracts from metadata file
    def __get_titles(self) -> list:
        titles = []
        for abstract in self.abstracts:
            title = abstract.find("title").text
            if not title:
                raise Exception(f"The publication with index {self.abstracts.index(abstract)} does not contain a title")
            titles.append(title)
        return titles
    
    # assign files to abstracts metadata from metadata file
    def __assign_files(self) -> list:
        assignments = []
        if self.sequenced:
            # assign files by indexes
            for index, title in enumerate(self.titles):
                bundle = {}
                bundle.update({"title": title})
                pdf = self.__get_pdfs()[index]
                bundle.update({"pdf": pdf})
                if self.xml:
                    xml = self.__get_xmls()[index]
                    bundle.update({"xml": xml})
                bundle_name = os.path.splitext(pdf)[0]
                bundle.update({"name": bundle_name})
                assignments.append(bundle)
        else:
            # assign files by name scheme
            for index, abstract in enumerate(self.abstracts):
                bundle = {}
                bundle.update({"title": abstract.find("title").text})

                # get pdfs
                pdfs = self.__get_pdfs()
                file_names_to_compare = parsing.get_comparable_filenames(pdfs)

                # get possible bundle names
                names = parsing.get_bundle_names(abstract)

                # assign pdf file to abstract
                assigned_pdf = parsing.get_abstract_file(names, file_names_to_compare, index) + ".pdf"
                bundle.update({"pdf": assigned_pdf})

                # file name
                bundle_name = os.path.splitext(assigned_pdf)[0]

                # assign xml file to abstract
                if self.xml:
                    # Check sanity of filenames in pdf and xml directory
                    sanity.filenames(self)
                    xmls = self.__get_xmls()
                    xml = xmls[xmls.index(bundle_name + ".xml")]
                    bundle.update({"xml": xml})
                bundle.update({"name": bundle_name})

                assignments.append(bundle)

        return assignments

    # creates output directory for bundle structure of conference
    def __create_output_dir(self) -> str:
        output_dir = os.path.join(config['output_base'], os.path.basename(self.name))
        try:
            os.mkdir(output_dir)
        except OSError:
            logging.warning('Directory already exists. Continue..')
        return output_dir

    # checks if files und bundles contain the corresponding numbers of files
    def __quality_check(self) -> None:
        if not self.xml:
            defective_dirs = [bundle_dir for bundle_dir in os.listdir(self.output) if len(os.listdir(os.path.join(self.output, bundle_dir, "bundle_publications"))) != 1]
            logging.info(f"The following directories do not contain the pdf file: {defective_dirs}")
        else:
            defective_dirs = [bundle_dir for bundle_dir in os.listdir(self.output) if len(os.listdir(os.path.join(self.output, bundle_dir, "bundle_publications"))) != 2]
            logging.info(f"The following directories do not contain two files: {defective_dirs}")

    # create csv file with overview of assigned files to bundles
    def __create_csv(self) -> None:

        with open(config['assignments_dir'] + self.name + ".csv", 'w', encoding='utf-8', newline='') as csv_file:
            if self.xml:
                fieldnames = ["Bundle", "Title", "Title from xml", "PDF", "XML"]
            else:
                fieldnames = ["Bundle", "Title", "PDF"]

            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for bundle in os.listdir(self.output):
                bundle_path = os.path.join(self.output, bundle)
                publications = os.path.join(bundle_path, "bundle_publications")

                # get title from json metadata
                with open (os.path.join(bundle_path, 'bundle_metadata.json'), 'r') as f:
                    metadata = json.load(f)["metadata"]
                title = metadata["title"]
                
                # get file names            
                for f in os.listdir(publications):
                    if f.endswith('.pdf'):
                        pdf = f
                    elif f.endswith('.xml'):
                        xml = f
                    else:
                        raise Exception("The publication files do not have the correct format. Please check if all files are either pdf or xml files.")

                if self.xml:
                    # get title from xml
                    for f in os.listdir(publications):
                        if f.endswith(".xml"):
                            xml_title = get_xml_title(os.path.join(publications, f))
                    from_xml = xml_title
                    
                    bundle_data = {'Bundle': bundle, 'Title': title, 'Title from xml': from_xml, 'PDF': pdf, 'XML': xml}
                else:
                    bundle_data = {'Bundle': bundle, 'Title': title, 'PDF': pdf}
            
                # write bundle data in csv file
                writer.writerow(bundle_data)
                
def get_xml_title(xml_file: str) -> str:
    """Returns title of (abstract's) xml file (TEI)

    Parameters
    ----------
    xml_file : str
        Path to xml file
    
    Returns
    -------
    title : str
        Text of title tag
    """

    tree = ET.parse(xml_file)
    try:
        title_tags = tree.findall(".//TEI:title", namespace)
        # if xml file contains only one title tag get text from this tag
        if len(title_tags) == 1:
            title = title_tags[0].text
        # else get content of title tag with attribute 'type'='main'
        else:
            try:
                title =" ".join([elem.text for elem in title_tags if elem.attrib['type'] in ["main", "sub"]])
            except TypeError:
                for elem in title_tags:
                    if elem.attrib["type"]=="main":
                        title = elem.text
    # return empty string if no title tag could be found in xml file
    except AttributeError:
        logging.warning(f"Couldn't extract title from file {xml_file}")
        title = ""
    return title

def create_metadata(pub: ET.Element, bundle_path: str) -> None:
    """Create bundle's json metadata file (for zenodo metadata)

    Parameters
    ----------
    pub: ET.Element
        Metadata element of given bundle from conference's metadata file
    bundle_path: str
        Path to bundle
    """

    # get bundle information and translate into json format
    logging.info(f"Create bundle for publication: {pub.find('title').text}")
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
                        "doi": "",
                        "keywords": pub.find("keywords").text.split(", "),
                        "contributors": [{"name": contributor.find("name").text,
                                        "affiliation": contributor.find("affiliation").text,
                                        "type": contributor.find("type").text
                                        } for contributor in pub.findall("contributors/contributor")],
                        "communities": [{"identifier": "dhd"}],
                        "conference_title": pub.find("conference_title").text,
                        "conference_acronym": pub.find("conference_acronym").text,
                        "conference_dates": pub.find("conference_dates").text,
                        "conference_place": pub.find("conference_place").text,
                        "conference_url": pub.find("conference_url").text
                        }
            }
    # save json metadata file in bundle path
    with open(os.path.join(bundle_path, 'bundle_metadata.json'), 'w') as outfile:
        json.dump(data, outfile)

def get_bundle_files(bundle: str):
    """Returns files assigned to bundle

    Parameters
    ----------
    bundle: str
        Path to bundle

    Returns
    -------
    bundle_json: str
        Path to json metadata file of bundle
    bundle_publications: list
        List with assigned bundle publication files. 
        Contains path to pdf file if xml files have not been taken into account for bundle creation. 
    """
    
    bundle_content = os.listdir(bundle)
    for element in bundle_content: 
        if os.path.isdir(os.path.join(bundle,element)) and element == "bundle_publications":
            bundle_publications = [os.path.join(bundle, element, publication_file) for publication_file in os.listdir(os.path.join(bundle, element)) ]
        elif element.endswith(".json"):
            bundle_json = os.path.join(bundle,element)
    return bundle_json, bundle_publications
