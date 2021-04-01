"""Script to upload bundle structure to Zenodo. 

If bundle structure hasn't been created with script create_bundles.py, this script expects the following bundle structure for CONFERENCE under bundle_structures/:

- CONFERENCE/: Folder containing all bundles to be uploaded as single publications
    - BUNDLE_1/:
        - bundle_metadata.json
        - bundle_publications/
            - file_1
            - ...
    - BUNDLE_2/:
        - ...
    - ..

For more information to structure file bundle_metadata.json please see Zenodo REST API Documentation(https://developers.zenodo.org/).

To run this script the following arguments need to be passed:
    * - c CONFERENCE: Name of conference folder
    * - a ACCESS_TOKEN: Generated Access Token to use Zenodo API
    * - p (Optional): If argument is given, the bundles will be uploaded to productive system. Otherwise they will be uploaded to the  zenodo sandbox (https://sandbox.zenodo.org/).

Personal access Token need to be either created for sandbox (https://sandbox.zenodo.org/account/settings/applications/tokens/new/) or productive system (https://zenodo.org/account/settings/applications/tokens/new/):

1. Register for a Zenodo account if you don’t already have one.
2. Go to your Applications, to create a new token.
3. Select the OAuth scopes you need (for the quick start tutorial you need deposit:write and deposit:actions).

"""

import argparse
import logging
import os
from pathlib import Path
import shutil
import requests
import json
from xml.etree import ElementTree as ET

# import getopt
# import sys

def upload(conference: str, url: str, headers:dict, params:dict) -> None:
    print("Upload bundles")
    # create upload for each bundle
    dep_file = open("support/depositions_" + conference + ".txt", "w+")

    # upload bundle content
    bundle_base = readable_dir(os.path.join("bundle_structures",conference))
    print(f"Bundle base directory based on given conference {conference}: {bundle_base}")
    bundles = [os.path.join(bundle_base, bundle) for bundle in os.listdir(bundle_base)]

    for bundle in bundles:
        # get bucket url and deposition id for upload
        bucket_url, deposition_id = get_upload_params(url, params, headers)
        # write deposition id in textfile for publishing
        dep_file.write(str(deposition_id)+ "\n")
        # get bundle files for upload
        bundle_json, bundle_publications = get_bundle_files(bundle)
        # upload bundle publications
        for publication in bundle_publications:
            with open(publication, "rb") as pub:
                r = requests.put(
                    "%s/%s" % (bucket_url, os.path.basename(publication)),
                    data=pub,
                    params=params)
                print(f"Put publication file {publication}: {r.status_code}")
        # upload bundle metadata
        with open(bundle_json) as json_file:
            data = json.load(json_file)
        # print(bundle_json)
        # print(data)
        r = requests.put( url+'/%s' % deposition_id,
                        params=params, data=json.dumps(data), headers=headers)
        if r.status_code in [400, 401, 403, 404, 409, 415, 429]:
            print(f"Upload for bundle {bundle} didn't go through. Please check resource.")
            print(f"Status code: {r.status_code}.")
            print(r.json())
    print("finished")

def delete(conference: str, url: str, headers:dict, params:dict) -> None:
    print("Delete drafts..")
    dep_file = open("support/depositions_" + conference + ".txt", "r")
    dep_ids = [line.replace("\n", "") for line in dep_file]

    for deposition_id in dep_ids:
        dep_url = url+ '/' + deposition_id
        print(dep_url)
        r = requests.delete(url+ '/' + deposition_id,
                            params=params )
        print(r.status_code)
    print("finished")

def update(conference: str, url: str, headers:dict, params:dict) -> None:

    print("Update metadata of depositions that have not been submitted yet..")
    # print("This function has not been implemented yet.")
    notes = "Sofern eine editorische Arbeit an dieser Publikation stattgefunden hat, dann bestand diese aus der Eliminierung von Bindestrichen in Überschriften, die aufgrund fehlerhafter Silbentrennung entstanden sind, der Vereinheitlichung von Namen der Autor*innen in das Schema „Nachname, Vorname“ und/oder der Trennung von Überschrift und Unterüberschrift durch die Setzung eines Punktes, sofern notwendig."

    if conference == "DHd2014":
        references = [""]
    elif conference == "DHd2015":
        references = ["http://gams.uni-graz.at/o:dhd2015.abstracts-gesamt"]
    elif conference == "DHd2016_alt":
        references = ["https://doi.org/10.5281/zenodo.3679331"]
    elif conference == "DHd2016_neu":
        references = ["https://doi.org/10.5281/zenodo.3679331"]
    elif conference == "DHd2017":
        references = ["https://doi.org/10.5281/zenodo.3684825"]
    elif conference == "DHd2018":
        references = ["https://doi.org/10.5281/zenodo.3684897"]
    elif conference == "DHd2019":
        references = ["https://doi.org/10.5281/zenodo.2600812"]
    elif conference == "DHd2020":
        references = ["https://doi.org/10.5281/zenodo.3666690"]
    elif conference == "patrick":
        references = ["https://doi.org/10.5281/zenodo.3666690"]
    else:
        references = [""]

    dep_file = open("support/depositions_" + conference + ".txt", "r")
    dep_ids = [line.replace("\n", "") for line in dep_file]
    counter = 0
    for deposition_id in dep_ids:
        counter = counter + 1
        print(counter)
        dep_url = url+ '/' + deposition_id
        print(dep_url)
        r = requests.get(url+ '/' + deposition_id,
                            params=params )
        print(r.status_code)

        # print(r.json())
        # print(r.json()["prereserve_doi"])
        # print(r.json()["metadata"])
        metadata = r.json()["metadata"]
        # print(metadata)
        print(metadata["title"])

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
        # print(json_metadata)
        r = requests.put(url+'/%s' % deposition_id,
                         params=params, data=json.dumps(json_metadata), headers=headers)
        if r.status_code in [400, 401, 403, 404, 409, 415, 429]:
            print(f"Upload for deposition id {deposition_id} didn't go through. Please check resource.")
            print(f"Status code: {r.status_code}.")

    print("finished")

    """edit_url = url + '/' + dep_id + '/actions/edit'
        # post empty request to set deposition back to editing mode
        print(edit_url)
        r = requests.post(edit_url,
                            params=params,
                            json={},
                            headers=headers)
        # print(f"Empty Request has been postet: {r.status_code}")
        # print(r.json())
        # # post empty request
        p = requests.get(new_url, params=params, headers=headers)
        for f in p.json()['files']:
            old_file = f['id']
            print(f['filename'] + " " + old_file)
            deleting_url = new_url + '/files/' + f['id']
            r = requests.delete(deleting_url, params=params)
            print(f"DELETE: {r.status_code}")

        create_url = new_url + '/files'

        data = {'file_name': 'updated.txt'}
        files = {'file': open('bundle_structures/TEST_UPDATE/bundle/bundle_publications/new.txt', 'rb')}
        r = requests.post(create_url, data=data, files=files, params = params)
        print(f"CREATE FILE: {r.status_code}")

        data = updated_data
        r = requests.put(new_url, data=json.dumps(data), headers=headers, params = params)
        print(f"METADATA UPDATE: {r.status_code}")"""
    
def publish(conference: str, url: str, headers:dict, params:dict) -> None:

    print("Publish conference papers..")
    dep_file = open("support/depositions_" + conference + ".txt", "r")
    dep_ids = [line.replace("\n", "") for line in dep_file]

    counter = 0

    for deposition_id in dep_ids:
        counter = counter + 1
        print(counter)
        print(deposition_id)
        dep_url = url+ '/' + deposition_id + '/actions/publish'
        print(dep_url)
        r = requests.post(url+ '/' + deposition_id + '/actions/publish',
                                params=params )
        print(r.status_code)
        # print(r.json())
        if r.status_code in [400, 401, 403, 404, 409, 415, 429]:
            print(f"Publishing for deposition id {deposition_id} didn't go through. Please check deposition.")
            print(f"Status code: {r.status_code}.")
    print(f"Submitted {counter} depositions.")
    print("finished")

def collect_zenodo_metadata(conference: str, url: str, headers:dict, params:dict) -> None:

    print("Get zenodo metadata and save new json files in bundles. Update conference metadata file")
    print("This function has not been implemented yet.")
    dep_file = open("support/depositions_" + conference + ".txt", "r")
    dep_ids = [line.replace("\n", "") for line in dep_file]

    notes = "Sofern eine editorische Arbeit an dieser Publikation stattgefunden hat, dann bestand diese aus der Eliminierung von Bindestrichen in Überschriften, die aufgrund fehlerhafter Silbentrennung entstanden sind, der Vereinheitlichung von Namen der Autor*innen in das Schema „Nachname, Vorname“ und/oder der Trennung von Überschrift und Unterüberschrift durch die Setzung eines Punktes, sofern notwendig."

    if conference == "DHd2014":
        references = ""
        conf_metadata_file = "2014metadata_v2.xml"
    elif conference == "DHd2015":
        references = "http://gams.uni-graz.at/o:dhd2015.abstracts-gesamt"
        conf_metadata_file = "2015metadata.xml"
    elif conference == "DHd2016":
        references = "https://doi.org/10.5281/zenodo.3679331"
        conf_metadata_file = "2016metadata.xml"
    elif conference == "DHd2017":
        references = "https://doi.org/10.5281/zenodo.3684825"
        conf_metadata_file = "2017metadata.xml"
    elif conference == "DHd2018":
        references = "https://doi.org/10.5281/zenodo.3684897"
        conf_metadata_file = "2018metadata.xml"
    elif conference == "DHd2019":
        references = "https://doi.org/10.5281/zenodo.2600812"
        conf_metadata_file = "2019metadata.xml"
    elif conference == "DHd2020":
        references = "https://doi.org/10.5281/zenodo.3666690"
        conf_metadata_file = "2020metadata.xml"
    elif conference == "patrick":
        references = "https://doi.org/10.5281/zenodo.3666690"
        conf_metadata_file = "2020metadata.xml"
        conference = "DHd2020"
    else:
        references = ""


    conf_path = os.path.join("bundle_structures", conference)
    print(conf_metadata_file)
    name = conf_metadata_file.split(".")[0] 
    print(name)
    path_to_conf_metadata_file = os.path.join("conferences", conference, conf_metadata_file)
    print(path_to_conf_metadata_file)
    path_to_metadata_copy = os.path.join("conferences", conference, name + "_updated.xml")
    shutil.copyfile(path_to_conf_metadata_file, path_to_metadata_copy)

    tree = ET.parse(path_to_metadata_copy)
    pub_metadata = tree.findall("metadata")
    counter = 0
    counter_no_title = 0

    for deposition_id in dep_ids:
        dep_url = url+ '/' + deposition_id
        print(dep_url)
        r = requests.get(url+ '/' + deposition_id,
                            params=params )
        print(r.status_code)

        # print(r.json())
        # print(r.json()["prereserve_doi"])
        # print(r.json()["metadata"])
        metadata = r.json()["metadata"]
        # print(metadata)
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

        for bundle in os.listdir(conf_path):
            bundle_path = os.path.join(conf_path, bundle)
            bundle_json = os.path.join(bundle_path, "bundle_metadata.json")
            with open(bundle_json, "r") as f:
                bundle_data = json.load(f)
                if bundle_data["metadata"]["title"] == json_metadata["metadata"]["title"]:
                    with open(os.path.join(bundle_path, "bundle_metadata_update.json"), "w") as outfile:
                        json.dump(json_metadata, outfile)
        if not any(elem.find("title").text.replace("-","").replace(" ","").replace(".","") == json_metadata["metadata"]["title"].replace("-","").replace(" ","").replace(".","") for elem in pub_metadata):
            print(json_metadata["metadata"]["title"])

        for elem in pub_metadata:
            # print(elem.find("title").text)

            if elem.find("title").text == json_metadata["metadata"]["title"]:
                counter = counter + 1
                elem.find("upload_type").text = json_metadata["metadata"]["upload_type"]
                elem.find("publication_type").text = json_metadata["metadata"]["publication_type"]
                elem.find("publication_date").text = json_metadata["metadata"]["publication_date"]
                elem.find("title").text = json_metadata["metadata"]["title"]

                creators = elem.find("creators")
                for creator in list(creators):
                    creators.remove(creator)
                for creator in json_metadata["metadata"]["creators"]:
                    new_creator = ET.Element("creator")
                    new_name = ET.SubElement(new_creator, "name")
                    new_name.text = creator["name"]
                    new_affiliation = ET.SubElement(new_creator, "affiliation")
                    new_affiliation.text = creator["affiliation"]
                    creators.append(new_creator)

                elem.find("description").text = json_metadata["metadata"]["description"]
                elem.find("access_right").text = json_metadata["metadata"]["access_right"]
                elem.find("license").text = json_metadata["metadata"]["license"]

                elem.find("doi").text = json_metadata["metadata"]["doi"]
                
                elem.find("keywords").text = ", ".join(json_metadata["metadata"]["keywords"])

                contributors = elem.find("contributors")
                for contributor in list(contributors):
                    contributors.remove(contributor)

                for contrib in json_metadata["metadata"]["contributors"]:
                    new_contrib = ET.Element("contributor")
                    new_name = ET.SubElement(new_contrib, "name")
                    new_name.text = contrib["name"]
                    new_affiliation = ET.SubElement(new_contrib, "affiliation")
                    new_affiliation.text = contrib["affiliation"]
                    new_type = ET.SubElement(new_contrib, "type")
                    new_type.text = contrib["type"]
                    contributors.append(new_contrib)

                elem.find("conference_title").text = json_metadata["metadata"]["conference_title"]
                elem.find("conference_acronym").text = json_metadata["metadata"]["conference_acronym"]
                elem.find("conference_dates").text = json_metadata["metadata"]["conference_dates"]
                elem.find("conference_place").text = json_metadata["metadata"]["conference_place"]
                elem.find("conference_url").text = json_metadata["metadata"]["conference_url"]

                """elem_communities = ET.Element("communities")
                elem_communities.text = ("dhd")
                elem.append(elem_communities)"""

                elem_reference = ET.Element("references")
                elem_reference.text = references
                elem.append(elem_reference)

                elem_notes = ET.Element("notes") 
                elem_notes.text = notes   
                elem.append(elem_notes)

    tree.write(path_to_metadata_copy)
    print(counter)
    print(counter_no_title)
    print("finished")


def get_bundle_files(bundle: Path) -> (Path, list):
    bundle_content = os.listdir(bundle)
    for element in bundle_content: 
        if os.path.isdir(os.path.join(bundle,element)) and element == "bundle_publications":
            bundle_publications = [os.path.join(bundle, element, publication_file) for publication_file in os.listdir(os.path.join(bundle, element)) ]
        elif element.endswith(".json"):
            bundle_json = os.path.join(bundle,element)
    return bundle_json, bundle_publications

def get_upload_params(url:str, params:dict, headers:dict)-> (str, str):
    # empty post to zenodo in order to get bucket url and deposition id
    r = requests.post(url,
        params=params,
        json={},
        headers=headers)

    print(r.json())

    print(f"Empty post to {url} with given access token: {r.status_code}")
    bucket_url = r.json()["links"]["bucket"]
    print(f"Using the following bucket url: {bucket_url}")
    deposition_id = r.json()['id']
    print(f"Using the following deposition id: {deposition_id}")
    return bucket_url, deposition_id

# check if unchecked path references is readable directory
def readable_dir(prospective_dir:str) -> Path:
    if not os.path.isdir(prospective_dir):
        raise Exception("readable_dir:{0} is not a valid path".format(prospective_dir))
    if not os.access(prospective_dir, os.R_OK):
        raise Exception("readable_dir:{0} is not a readable dir".format(prospective_dir))
    return Path(prospective_dir)

def set_parser() -> argparse.ArgumentParser:

    # ## create parser
    zenodup_parser = argparse.ArgumentParser(description="Zenodup is an python application using Zenodo API to upload, publish, update and delete publications on Zenodo or Zenodo Sandbox. For further information see https://developers.zenodo.org/.")

    # ## create subparsers
    subparsers = zenodup_parser.add_subparsers()
    subparsers.required = True

    # subparser 'upload'
    upload_parser = subparsers.add_parser('upload', description='')
    upload_parser.add_argument('conference')
    upload_parser.add_argument('token')
    upload_parser.add_argument('-productive', nargs='?', type=bool, default=False, const=True)
    upload_parser.set_defaults(func=upload)

    # subparser 'publish'
    publish_parser = subparsers.add_parser('publish', description='')
    publish_parser.add_argument('conference')
    publish_parser.add_argument('token')
    publish_parser.add_argument('-productive', nargs='?', type=bool, default=False, const=True)
    publish_parser.set_defaults(func=publish)

    # subparser 'update'
    update_parser = subparsers.add_parser('update', description='')
    update_parser.add_argument('conference')
    update_parser.add_argument('token')
    update_parser.add_argument('-productive', nargs='?', type=bool, default=False, const=True)
    update_parser.set_defaults(func=update)

    # subparser 'delete'
    delete_parser = subparsers.add_parser('delete', description='')
    delete_parser.add_argument('conference')
    delete_parser.add_argument('token')
    delete_parser.add_argument('-productive', nargs='?', type=bool, default=False, const=True)
    delete_parser.set_defaults(func=delete)

    # subparser 'collect_zenodo_metadata'
    collect_parser = subparsers.add_parser('collect_zenodo_metadata', description='')
    collect_parser.add_argument('conference')
    collect_parser.add_argument('token')
    collect_parser.add_argument('-productive', nargs='?', type=bool, default=False, const=True)
    collect_parser.set_defaults(func=collect_zenodo_metadata)

    return zenodup_parser

if __name__ == "__main__":

    # get application parser and run function based on system arguments
    parser = set_parser()
    arguments = parser.parse_args()
    print(vars(arguments))

    args_dict = vars(arguments)
    conference = args_dict['conference']
    access_token = args_dict['token']
    if args_dict['productive']:
        url = 'https://zenodo.org/api/deposit/depositions'
    else:
        url = 'https://sandbox.zenodo.org/api/deposit/depositions'

    # set logging
    # logging.basicConfig(level=logging.DEBUG)
    # set parameters for zenodo request
    headers = {"Content-Type": "application/json"}
    params = {'access_token': access_token}

    arguments.func(conference, url, headers, params)