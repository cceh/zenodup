"""Script for Zenodo API interaction. 

Interaction with Zenodo API works through instances of the Connection class of this module. 
For further documentation and usage please see README.md.
"""

# Imports

# ## external imports
import json
from lxml import etree
import os
import pandas as pd
import requests
import shutil
from xml.etree import ElementTree as ET
import yaml

# # ## internal imports
import bundles
from bundles import sanity

# set base paths for working diretories
with open(r'config.yml') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

# register TEI namespace for abstracts xml files
XMLParser = etree.XMLParser()
ET.register_namespace('', "http://www.tei-c.org/ns/1.0")
namespace = {'TEI': "http://www.tei-c.org/ns/1.0"}  

class Connection:
    """Connection class for interaction with zenodo 
    
    The class methods are based on zenodo api documentation. 
    For further information see also https://developers.zenodo.org/#introduction

    Attributes
    ----------
    conference : str
        Name of conference. Based on the name of the conference all necessary paths and information is determined. 
        For further information please see README.md.

    token : str
        Zenodo API access token. For further documentation please see README.md.

    url : str
        Url used to connect to Zenodo api (Sandbox/Production)

    headers : dict
        Header for Zenodo API connection

    params : dict
        Parameters for Zenodo API connection

    Methods
    -------
    upload
        Uploads the abstracts of given conference

    delete
        Deletes drafts from zenodo for given conference

    update
        Adds missing notes and references to drafts for conference

    publish
        Publishes drafts in zenodo of given conference

    get_metadata
        Gets final metadata from abstracts of conference
    """

    def __init__(self, name:str, token:str, productive: bool) -> None:
        """Constructor of Connection class

        Parameters
        ----------
        name : str
            Name of conference. Based on the name of the conference all necessary paths and information is determined. 
            For further information please see README.md.

        token : str
            Zenodo API access token. For further documentation please see README.md. 

        productive : bool
            Determines to interact with Zenodo API for testing (Zenodo sandbox) or production purposes.
        """
        # set conference name
        self.conference = name
        # set zenodo api access token
        self.token = token
        # set url based on testing (zenodo sandbox) or productive
        if productive:
            self.url = 'https://zenodo.org/api/deposit/depositions'
        else:
            self.url = 'https://sandbox.zenodo.org/api/deposit/depositions'

        # set header and parameters for zenodo api request
        self.headers = {"Content-Type": "application/json"}
        self.params = {'access_token': self.token}

    def upload(self) -> None:
        """Uploads the abstracts of given conference

        Uploads the abstracts of given conference to zenodo sandbox or productive system (based on given url).
        In order to upload the abstracts of a conference the files have to be in required bundle structure.
        For further information see README.md.
        """

        print("Upload bundles..")

        # create file to store zenodo deposition ids fur uploaded bundles
        dep_file = open(config['depositions_dir'] + self.conference + ".txt", "w+")

        # upload bundles
        bundle_base = sanity.readable_dir(os.path.join(config['output_base'], self.conference))
        print(f"Bundle base directory based on given conference {self.conference}: {bundle_base}")
        conference_bundles = [os.path.join(bundle_base, bundle) for bundle in os.listdir(bundle_base)]

        for bundle in conference_bundles:
            # get bucket url and deposition id for upload
            bucket_url, deposition_id = self.__get_upload_params()
            # write deposition id for bundle in textfile
            dep_file.write(str(deposition_id)+ "\n")
            # get bundle files for upload
            bundle_json, bundle_publications = bundles.get_bundle_files(bundle)
            # upload bundle files
            for publication in bundle_publications:
                with open(publication, "rb") as pub:
                    r = requests.put(
                        "%s/%s" % (bucket_url, os.path.basename(publication)),
                        data=pub,
                        params=self.params)
                    print(f"Put publication file {publication}: {r.status_code}")
            # upload bundle metadata
            with open(bundle_json) as json_file:
                data = json.load(json_file)
            r = requests.put( self.url+'/%s' % deposition_id,
                            params=self.params, data=json.dumps(data), headers=self.headers)
            if r.status_code in [400, 401, 403, 404, 409, 415, 429]:
                print(f"Upload for bundle {bundle} didn't go through. Please check resource.")
                print(f"Status code: {r.status_code}.")
                print(r.json())
        print("..finished")
    
    def delete(self) -> None:
        """Deletes drafts from zenodo for given conference

        Deletes all uploaded drafts of conference from zenodo (sandbox or productive system).  
        In order to delete drafts from multiple conferences at once please collect the corresponding deposition ids in a deposition textfile. 
        In order to call this method the given conference name needs to match the filename with the deposition ids.
        For further information see README.md.
        """

        print("Delete drafts..")

        # get deposition ids to be deleted
        dep_file = open(config['depositions_dir'] + self.conference + ".txt", "r")
        dep_ids = [line.replace("\n", "") for line in dep_file]

        # delete drafts with given deposition ids
        for deposition_id in dep_ids:
            dep_url = self.url + '/' + deposition_id
            r = requests.delete(dep_url, params= self.params )
            if r.status_code in [400, 401, 403, 404, 409, 415, 429]:
                print(f"Draft with deposition id {deposition_id} didn't go through. Please check resource.")
                print(f"Status code: {r.status_code}.")
                print(r.json())
        print("..finished")

    def update(self) -> None:
        """Adds missing notes and references to drafts for conference

        CAUTION: This method has been written for a specific use case. 
        It is hardcoded and shouldn't be used in a generic way.  
        """

        print("Update metadata of depositions that have not been submitted yet..")

        # set metadata (notes/references) to be updated
        notes = "Sofern eine editorische Arbeit an dieser Publikation stattgefunden hat, dann bestand diese aus der Eliminierung von Bindestrichen in Überschriften, die aufgrund fehlerhafter Silbentrennung entstanden sind, der Vereinheitlichung von Namen der Autor*innen in das Schema „Nachname, Vorname“ und/oder der Trennung von Überschrift und Unterüberschrift durch die Setzung eines Punktes, sofern notwendig."

        if self.conference == "DHd2014":
            references = [""]
        elif self.conference == "DHd2015":
            references = ["http://gams.uni-graz.at/o:dhd2015.abstracts-gesamt"]
        elif self.conference == "DHd2016":
            references = ["https://doi.org/10.5281/zenodo.3679331"]
        elif self.conference == "DHd2017":
            references = ["https://doi.org/10.5281/zenodo.3684825"]
        elif self.conference == "DHd2018":
            references = ["https://doi.org/10.5281/zenodo.3684897"]
        elif self.conference == "DHd2019":
            references = ["https://doi.org/10.5281/zenodo.2600812"]
        elif self.conference == "DHd2020":
            references = ["https://doi.org/10.5281/zenodo.3666690"]
        else:
            references = [""]

        # get deposition ids of drafts to be updated
        dep_file = open(config['depositions_dir'] + self.conference + ".txt", "r")
        dep_ids = [line.replace("\n", "") for line in dep_file]

        # update metadata of drafts
        for deposition_id in dep_ids:
            dep_url = self.url+ '/' + deposition_id
            r = requests.get(dep_url, params=self.params )

            metadata = r.json()["metadata"]
            json_metadata = {"metadata": {"upload_type": metadata["upload_type"],
                                        "publication_type": metadata["publication_type"],
                                        "publication_date": metadata["publication_date"],
                                        "title": metadata["title"],
                                        "creators": metadata["creators"],
                                        "description": metadata["description"],
                                        "access_right": metadata["access_right"],
                                        "license": metadata["license"],
                                        "doi": metadata["doi"],
                                        "keywords": metadata["keywords"],
                                        "contributors": metadata["contributors"],
                                        "communities": metadata["communities"],
                                        "conference_title": metadata["conference_title"],
                                        "conference_acronym": metadata["conference_acronym"],
                                        "conference_dates": metadata["conference_dates"],
                                        "conference_place": metadata["conference_place"],
                                        "conference_url": metadata["conference_url"],
                                        "notes": notes,
                                        "references": references
                                        }
                            }
            r = requests.put(self.url+'/%s' % deposition_id,
                            params=self.params, data=json.dumps(json_metadata), headers=self.headers)
            if r.status_code in [400, 401, 403, 404, 409, 415, 429]:
                print(f"Upload for deposition id {deposition_id} didn't go through. Please check resource.")
                print(f"Status code: {r.status_code}.")

        print("finished")

    def publish(self) -> None:
        """Publishes drafts in zenodo of given conference

        Publishes drafts in zenodo of givien conference. 
        In order to publish the drafts the deposition ids have to be stored 
        in a textfile with conference name in depositions dir. 
        For further information see README.md.
        """

        print("Publish conference papers..")

        # get deposition ids of drafts to be published
        dep_file = open(config['depositions_dir'] + self.conference + ".txt", "r")
        dep_ids = [line.replace("\n", "") for line in dep_file]

        # publish drafts for given deposition ids
        for deposition_id in dep_ids:
            dep_url = self.url + '/' + deposition_id + '/actions/publish'
            r = requests.post(dep_url, params=self.params )
            if r.status_code in [400, 401, 403, 404, 409, 415, 429]:
                print(f"Publishing for deposition id {deposition_id} didn't go through. Please check deposition.")
                print(f"Status code: {r.status_code}.")

        print("..finished")

    def get_metadata(self):
        """Gets final metadata from abstracts of conference

        This method is used to create an csv file containing all final abstracts metadata of conference.
        In order to add publication category (e.g. poster, panel, ...) to csv file the conferences files 
        conference the files have to be in required bundle structure.
        For further information see README.md.
        """

        print("Get metadata from (published) abstracts of conference..")

        # get depositions ids of conference
        dep_file = open(config['depositions_dir'] + self.conference + ".txt", "r")
        dep_ids = [line.replace("\n", "") for line in dep_file]

        conference_info = []
        for index, deposition_id in enumerate(dep_ids):

            dep_url = self.url+ '/' + deposition_id
            # get request for bundle metadata
            r = requests.get(dep_url, params=self.params )
            # get request for bundle files
            r_files = requests.get(dep_url + '/files', params=self.params )

            if r.status_code == 200:
                
                # get deposition metadata
                bundle_info = r.json()["metadata"]
                # clean description tag
                bundle_info["description"] = bundle_info["description"].replace("<p>","").replace("</p>", "")
                # add filenames of deposition files to bundle_info
                bundle_info["files"] = [elem["filename"] for elem in r_files.json()]

                # get publication category (e.g. poster, panel, ...)
                # iterate through files in bundle structure and get xml file
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

                                            # TODO generic?
                                            if self.conference in ["DHd2014", "DHd2015", "DHd2016", "DHd2017"]:
                                                for elem in key_tags:
                                                    if elem.attrib["n"]=="category":
                                                        pub_format = elem.find("TEI:term", namespace).text
                                            elif self.conference in ["DHd2018", "DHd2019", "DHd2020"]:
                                                for elem in key_tags:
                                                    if elem.attrib["n"]=="subcategory":
                                                        pub_format = elem.find("TEI:term", namespace).text

                                            bundle_info["xml_id"] = xml_id
                                            bundle_info["format"] = pub_format
            
                                        except KeyError:
                                            print(f"Could not find correct category tag for file {file_name}. Please check.")
                conference_info.append(bundle_info)
            else:
                print(f"Status code for deposition with id {deposition_id} is not 200. Please check deposition on zenodo.")

        # save conference info in csv file
        df = pd.DataFrame(conference_info)
        df.to_csv(config['packages_dir'] + self.conference + ".csv", header = True, encoding = "utf-8")

        print('... finished')

    # empty post to zenodo in order to get bucket url and deposition id
    def __get_upload_params(self):
        r = requests.post(self.url,
            params= self.params,
            json={},
            headers= self.headers)

        print(f"Empty post to {self.url} with given access token: {r.status_code}")
        bucket_url = r.json()["links"]["bucket"]
        print(f"Using the following bucket url: {bucket_url}")
        deposition_id = r.json()['id']
        print(f"Using the following deposition id: {deposition_id}")

        return bucket_url, deposition_id
