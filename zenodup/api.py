"""Module for interaction with Zenodo API

Module for interaction with Zenodo API using instances of the Connection class.
Please see README.md for more detailed documentation.
"""

import csv
import json
import logging
from lxml import etree
import os
import requests
from xml.etree import ElementTree as ET
import yaml
import time

import bundles
from bundles import sanity

# set base paths for working directories
with open(r'config.yml') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

# register TEI namespace for abstracts xml files
XMLParser = etree.XMLParser()
ET.register_namespace('', "http://www.tei-c.org/ns/1.0")
namespace = {'TEI': "http://www.tei-c.org/ns/1.0"}  

class Connection:
    """Connection class for interaction with Zenodo API 
    
    The class methods are based on Zenodo API documentation. 
    See also: https://developers.zenodo.org/#introduction.

    Attributes
    ----------
    conference : str
        Name of conference. Based on the name of the conference all necessary paths and information is determined. 
        The name must correspond to the folder for the respective conference.
        Please see README.md for more detailed documentation.

    token : str
        Zenodo API access token.

    url : str
        URL used to connect to Zenodo API (Sandbox/Production).

    headers : dict
        Header for Zenodo API connection.

    params : dict
        Parameters for Zenodo API connection.

    Methods
    -------
    upload
        Uploads the abstracts of given conference to Zenodo.

    delete
        Deletes drafts of conference from Zenodo.

    update
        Adds missing notes and references to drafts of conference.

    publish
        Publishes uploaded drafts of conference.

    get_metadata
        Saves the abstracts' metadata of conference for annual package.
    """

    def __init__(self, name:str, token:str, productive: bool) -> None:
        """Constructor of Connection class

        Parameters
        ----------
        name : str
            Name of conference. The name must correspond to the folder for the respective conference.

        token : str
            Zenodo API access token.

        productive : bool
            Determines whether the productive system or the Zenodo sandbox (for testing purposes) is used.
        """

        self.conference = name
        self.token = token
        
        # set url based on testing (zenodo sandbox) or productive
        if productive:
            self.url = 'https://zenodo.org/api/deposit/depositions'
        else:
            self.url = 'https://sandbox.zenodo.org/api/deposit/depositions'

        # set header and parameters for zenodo api request
        self.headers = {"Content-Type": "application/json"}
        self.params = {'access_token': self.token}

        logging.basicConfig(filename=config['logging_dir'] + self.conference +'_api.log', filemode='w+', level=logging.INFO)

    def upload(self) -> None:
        """Upload of abstracts

        Upload of abstracts to Zenodo.
        In order to upload the abstracts the files must be available in the required bundle structure.
        """

        logging.info("Upload bundles..")

        # create textfile to store deposition ids
        dep_file = open(config['depositions_dir'] + 'depositions_' + self.conference + ".txt", "w+")

        # upload bundles
        bundle_base = sanity.readable_dir(os.path.join(config['output_base'], self.conference))
        logging.info(f"Bundle base directory for conference {self.conference}: {bundle_base}")
        conference_bundles = [os.path.join(bundle_base, bundle) for bundle in os.listdir(bundle_base)]

        for bundle in conference_bundles:
            # get bucket url and deposition id
            bucket_url, deposition_id = self.__get_upload_params()
            # write deposition id for bundle in textfile
            dep_file.write(str(deposition_id) + "\n")
            # get bundle files for upload
            bundle_json, bundle_publications = bundles.get_bundle_files(bundle)
            # upload bundle files
            for publication in bundle_publications:
                with open(publication, "rb") as pub:
                    r = requests.put(
                        "%s/%s" % (bucket_url, os.path.basename(publication)),
                        data=pub,
                        params=self.params)
                    logging.info(f"Put publication file {publication}: {r.status_code}")
            # upload bundle metadata
            with open(bundle_json) as json_file:
                data = json.load(json_file)
            r = requests.put(self.url+'/%s' % deposition_id,
                            params=self.params, data=json.dumps(data), headers=self.headers)
            if r.status_code in [400, 401, 403, 404, 409, 415, 429]:
                logging.info(f"Upload for bundle {bundle} didn't go through. Please check resource.")
                logging.info(f"Status code: {r.status_code}.")
                logging.info(r.json())
            time.sleep(1)
        logging.info("..finished")
    
    def delete(self) -> None:
        """Deletes drafts of given conference from Zenodo
        """

        logging.info("Delete drafts..")

        # get deposition ids
        dep_file = open(config['depositions_dir'] + 'depositions_' + self.conference + ".txt", "r")
        dep_ids = [line.replace("\n", "") for line in dep_file]

        # delete drafts with given deposition ids
        for deposition_id in dep_ids:
            dep_url = self.url + '/' + deposition_id
            r = requests.delete(dep_url, params= self.params )
            if r.status_code in [400, 401, 403, 404, 409, 415, 429]:
                logging.info(f"Could not delete draft with deposition id {deposition_id}. Please check resource.")
                logging.info(f"Status code: {r.status_code}.")
                logging.info(r.json())
            time.sleep(1)
        logging.info("..finished")

    def update(self) -> None:
        """Adds missing notes and references

        CAUTION: This method has been written for a specific use case. 
        It is hardcoded and shouldn't be used in a generic way.  
        """

        logging.info("Update metadata of depositions..")

        # set metadata (notes/references) to be updated
        notes = "Sofern eine editorische Arbeit an dieser Publikation stattgefunden hat, dann bestand diese aus der Eliminierung von Bindestrichen in Überschriften, die aufgrund fehlerhafter Silbentrennung entstanden sind, der Vereinheitlichung von Namen der Autor*innen in das Schema „Nachname, Vorname“ und/oder der Trennung von Überschrift und Unterüberschrift durch die Setzung eines Punktes, sofern notwendig."

        references = {"DHd2014": ["https://github.com/DHd-Verband/DHd-Abstracts-2014"], 
                      "DHd2015":["http://gams.uni-graz.at/o:dhd2015.abstracts-gesamt", "https://github.com/DHd-Verband/DHd-Abstracts-2015"], 
                      "DHd2016":["https://doi.org/10.5281/zenodo.3679331", "https://github.com/DHd-Verband/DHd-Abstracts-2016"],
                      "DHd2017":["https://doi.org/10.5281/zenodo.3684825","https://github.com/DHd-Verband/DHd-Abstracts-2017"], 
                      "DHd2018":["https://doi.org/10.5281/zenodo.3684897", "https://github.com/DHd-Verband/DHd-Abstracts-2018"], 
                      "DHd2019":["https://doi.org/10.5281/zenodo.2600812","https://github.com/DHd-Verband/DHd-Abstracts-2019"], 
                      "DHd2020":["https://doi.org/10.5281/zenodo.3666690", "https://github.com/DHd-Verband/DHd-Abstracts-2020"],
                      "patrick":["https://doi.org/10.5281/zenodo.3666690", "https://github.com/DHd-Verband/DHd-Abstracts-2020"]}

        # get deposition ids
        dep_file = open(config['depositions_dir'] + 'depositions_' + self.conference + ".txt", "r")
        dep_ids = [line.replace("\n", "") for line in dep_file]

        for deposition_id in dep_ids:
            logging.info(deposition_id)
            # unlock already submitted deposition for editing
            r = requests.post(self.url + '/' + deposition_id + '/actions/edit', params=self.params)
            time.sleep(1)

            # update metadata
            dep_url = self.url+ '/' + deposition_id
            r = requests.get(dep_url, params=self.params)

            # add related identifiers for each poster
            logging.info(r.json())
            metadata = r.json()["metadata"]
            logging.info(f"Metadata: {metadata}")
            metadata["notes"] = notes
            metadata["references"] = references[self.conference]
            logging.info(f"Updated metadata: {metadata}")

            r = requests.put(self.url+'/%s' % deposition_id,
                            params=self.params, data=json.dumps(metadata), headers=self.headers)
            if r.status_code in [400, 401, 403, 404, 409, 415, 429]:
                logging.info(f"Update for draft with deposition id {deposition_id} didn't go through. Please check resource.")
                logging.info(f"Status code: {r.status_code}.")
                logging.info(f"Error Message: {r}")

        logging.info("finished")

    def publish(self) -> None:
        """Publishes drafts of given conference in Zenodo. 
        """

        logging.info("Publish..")

        # get deposition ids
        dep_file = open(config['depositions_dir'] + 'depositions_' + self.conference + ".txt", "r")
        dep_ids = [line.replace("\n", "") for line in dep_file]

        # publish drafts
        for deposition_id in dep_ids:
            logging.info(deposition_id)
            dep_url = self.url + '/' + deposition_id + '/actions/publish'
            r = requests.post(dep_url, params=self.params )
            if r.status_code in [400, 401, 403, 404, 409, 415, 429]:
                logging.warning(f"Publishing for draft with deposition id {deposition_id} didn't go through. Please check deposition.")
                logging.warning(f"Status code: {r.status_code}.")
            time.sleep(1)

        logging.info("..finished")

    def get_metadata(self):
        """Saves the abstracts' metadata for annual package

        This method is used to create an csv file containing all final abstracts metadata of conference.
        In order to add publication category (e.g. poster, panel, ...) to csv file the conferences' files must be available in the required bundle structure.
        """

        logging.info("Get the abstracts' metadata for annual package..")

        # get depositions ids of conference
        dep_file = open(config['depositions_dir'] + 'depositions_' + self.conference + ".txt", "r")
        dep_ids = [line.replace("\n", "") for line in dep_file]

        # create root element for conference's final metadata file
        metadata_tree = ET.ElementTree()
        root = ET.Element('root')
        metadata_tree._setroot(root)

        with open(config['packages_dir'] + self.conference + ".csv", 'w', encoding='utf-8', newline='') as csv_file:

            fieldnames = ['access_right', 'communities', 'conference_acronym', 'conference_dates',
                          'conference_place', 'conference_title', 'conference_url', 'contributors', 'creators',
                          'description', 'doi', 'keywords', 'license', 'notes', 'prereserve_doi',
                          'publication_date', 'related_identifiers', 'publication_type', 'references', 'title',
                          'upload_type', 'conceptdoi', 'files', 'format', 'xml_id']

            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for index, deposition_id in enumerate(dep_ids):

                dep_url = self.url+ '/' + deposition_id
                # get request for bundle metadata
                r = requests.get(dep_url, params=self.params )
                # get request for bundle files
                r_files = requests.get(dep_url + '/files', params=self.params )

                if r.status_code in [200, 201, 202]:
                    
                    if self.conference == "FORGE":
                        bundle_info = {"title": r.json()["title"],"conceptdoi": r.json()["conceptdoi"]}
                        
                    else: 
                        # get deposition metadata
                        bundle_info = r.json()["metadata"]

                        # get conceptdoi
                        bundle_info.update({"conceptdoi": r.json()["conceptdoi"]})
                        bundle_info.update({"doi": r.json()["doi"]})
                        # remove html-tag from description
                        bundle_info["description"] = ' '.join(bundle_info["description"].replace("<p>","").replace("</p>", "").replace("\n"," ").split(" "))
                        bundle_info["title"] = bundle_info["title"].replace("\\n","")
                        bundle_info["conference_title"] = bundle_info["conference_title"].replace("\n","")

                        # add filenames of deposition files
                        bundle_info["files"] = [elem["filename"] for elem in r_files.json()]

                        # get publication category (e.g. poster, panel, ...) from TEI-file
                        if any(elem["filename"].endswith(".xml") for elem in r_files.json()):
                            for elem in r_files.json():
                                if elem["filename"].endswith(".xml"):
                                    file_name = elem["filename"]
                                    for root, dirs, files in os.walk(os.path.join(config['output_base'], self.conference)):
                                        for f in files:
                                            if f == file_name:
                                                xml_path = os.path.join(root, f)
                                                try:
                                                    # parse xml file
                                                    tree = ET.parse(xml_path)
                                                    # get xml id
                                                    root = tree.getroot()
                                                    xml_id = root.attrib["{http://www.w3.org/XML/1998/namespace}id"]
                                                    key_tags = tree.findall(".//TEI:keywords", namespace)
                                                    # TODO generic
                                                    if self.conference in ["DHd2014", "DHd2015", "DHd2016", "DHd2017"]:
                                                        for elem in key_tags:
                                                            if elem.attrib["n"]=="category":
                                                                pub_format = elem.find("TEI:term", namespace).text
                                                    elif self.conference in ["DHd2018", "DHd2019", "DHd2020", "DHd2022"]:
                                                        for elem in key_tags:
                                                            if elem.attrib["n"]=="subcategory":
                                                                pub_format = elem.find("TEI:term", namespace).text

                                                    bundle_info["xml_id"] = xml_id
                                                    bundle_info["format"] = pub_format
                    
                                                except KeyError:
                                                    logging.info(f"Couldn't find correct category tag for file {file_name}. Please check.")
                        
                        # self.__create_metadata_element(bundle_info, root)

                        time.sleep(1)                        
                else:
                    logging.info(r.status_code)
                    logging.info(f"Status code for deposition with id {deposition_id} is not 200. Please check the deposition.")

                # write bundle data in csv file
                logging.info(bundle_info)
                logging.info(fieldnames)
                writer.writerow(bundle_info)
                time.sleep(1)

        # write in xml file
        metadata_tree.write(config['update_dir'] + self.conference + "_updated.xml", encoding="utf-8", xml_declaration=True, method="xml")

        logging.info('... finished')

    def write_identifiers_for_posters(self):
        """Writes the abstract's doi as related identifier.

        Find the related abstract by matching titles. Changes relation, identifier and resource_type of first
        related_identifier for each publication (metadata entry). Relation changes from 'isPartOf' to 'isSupplementTo'
        , identifier will be overwritten by the abstract's concept doi and the resource_type changes from
        'publication-book' to 'publication-conferencepaper'."""

        logging.info("Write abstract's doi as related identifier..")

        # get metadata file
        metadata_file = sanity.readable_file(os.path.join(config['input_base'], self.conference + '_posters', self.conference + '_posters.xml'))
        logging.info(f"Metadatafile for posters: {metadata_file}")

        #instantiate list depositions_info
        depositions_info = []


        # get list of titles from depositions

        # get depositions ids of conference
        dep_file = open(config['depositions_dir'] + 'depositions_' + self.conference + ".txt", "r")
        dep_ids = [line.replace("\n", "") for line in dep_file]

        # get doi and title from each deposition
        for index, deposition_id in enumerate(dep_ids):

            dep_url = self.url + '/' + deposition_id
            # get request for bundle metadata
            r = requests.get(dep_url, params=self.params)

            if r.status_code in [200, 201, 202]:
                # get deposition metadata
                depositions_info.append([r.json()["title"].replace("\n",""), r.json()["conceptdoi"]])
                time.sleep(0.500)
            else:
                logging.info(r.status_code)
                logging.info(
                    f"Status code for deposition with id {deposition_id} is not 200. Please check the deposition.")
        logging.info(f"Information from Depositions: {depositions_info}")

        titles = [dep[0] for dep in depositions_info]


        # modify related identifiers for all poster publications

        # create root element for conference's final metadata file
        tree = ET.parse(metadata_file)
        root = tree.getroot()
        dates = root.findall('metadata')

        counter = 0
        for i, date in enumerate(dates):
            logging.info(f"Processing entry {i} with title {date.find('title').text}..")
            if date.find("title").text.replace("\n", "") in titles:
                logging.info(f"Title: {date.find('title').text}")
                rel_identifier = date.find("related_identifiers")[0]
                rel_identifier.find("relation").text = "isSupplementTo"
                rel_identifier.find("resource_type").text = "publication-conferencepaper"
                # ersetze related identifier
                rel_identifier.find("identifier").text = depositions_info[titles.index(date.find("title").text)][1]
                counter = counter + 1
            else:
                logging.warning(f"Identifier for publication with title {date.find('title').text} could not be modified. Please check manually.")

        # write in xml file
        tree.write(os.path.join(config['input_base'], self.conference + '_posters', self.conference + '_posters_related_ids.xml'))
        logging.info(f"{counter} related identifiers have been modified.")
        logging.info('... finished')

    # empty post to zenodo in order to get bucket url and deposition id
    def __get_upload_params(self):
        r = requests.post(self.url,
            params= self.params,
            json={},
            headers= self.headers)

        logging.info(f"Empty post to {self.url} with given access token: {r.status_code}")
        bucket_url = r.json()["links"]["bucket"]
        logging.info(f"Using the following bucket url: {bucket_url}")
        deposition_id = r.json()['id']
        logging.info(f"Using the following deposition id: {deposition_id}")

        return bucket_url, deposition_id

    # create metadata element in xml format
    def __create_metadata_element(self, bundle_info, root):

        metadata = ET.SubElement(root, 'metadata')
                        
        upload_type = ET.SubElement(metadata, 'upload_type')
        upload_type.text = bundle_info['upload_type']

        publication_type = ET.SubElement(metadata, 'publication_type')
        publication_type.text = bundle_info['publication_type']

        publication_date = ET.SubElement(metadata, 'publication_date')
        publication_date.text = bundle_info['publication_date']

        title = ET.SubElement(metadata, 'title')
        title.text = bundle_info['title']
        
        creators = ET.SubElement(metadata, 'creators')
        for elem in bundle_info['creators']:
            creator = ET.SubElement(creators, 'creator')
            name = ET.SubElement(creator, 'name')
            name.text = elem.get('name')
            affiliation = ET.SubElement(creator, 'affiliation')
            affiliation.text = elem.get('affiliation')
        ET.indent(creators, space="   ", level=0)
  
        description = ET.SubElement(metadata, 'description')
        description.text = bundle_info['description']

        access_right = ET.SubElement(metadata, 'access_right')
        access_right.text = bundle_info['access_right']

        license = ET.SubElement(metadata, 'license')
        license.text = bundle_info['license']

        doi = ET.SubElement(metadata, 'doi')
        doi.text = bundle_info['conceptdoi']

        keywords = ET.SubElement(metadata, 'keywords')
        keywords.text = ', '.join(bundle_info['keywords'])

        contributors = ET.SubElement(metadata, 'contributors')
        for elem in bundle_info['contributors']:
            contributor = ET.SubElement(contributors, 'contributor')
            name = ET.SubElement(contributor, 'name')
            name.text = elem.get('name')
            affiliation = ET.SubElement(contributor, 'affiliation')
            affiliation.text = elem.get('affiliation')
            c_type = ET.SubElement(contributor, 'type')
            c_type.text = elem.get('type')
        ET.indent(contributors, space="    ", level=0)

        conference_title = ET.SubElement(metadata, 'conference_title')
        conference_title.text = bundle_info['conference_title']

        conference_acronym = ET.SubElement(metadata, 'conference_acronym')
        conference_acronym.text = bundle_info['conference_acronym']

        conference_dates = ET.SubElement(metadata, 'conference_dates')
        conference_dates.text = bundle_info['conference_dates']

        conference_place = ET.SubElement(metadata, 'conference_place')
        conference_place.text = bundle_info['conference_place']

        conference_url = ET.SubElement(metadata, 'conference_url')
        conference_url.text = bundle_info['conference_url']

        ET.indent(root, space="    ", level=0)
