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
    # TODO
    print("Update conference papers..")
    print("This function has not been implemented yet.")
    """dep_file = open("support/depositions_" + conference + ".txt", "r")
    dep_ids = [line.replace("\n", "") for line in dep_file]
    updated_data = {
            "metadata": {
            "title": "My first VERSION update",
            "upload_type": "poster",
            "description": "This is my first upload",
            "creators": [
                        {"name": "Doe, John", "affiliation": "Zenodo"}
                        ]
                        }
            }
    for dep_id in dep_ids:
        edit_url = url + '/' + dep_id + '/actions/edit'
        # post empty request to set deposition back to editing mode
        print(edit_url)
        r = requests.post(edit_url,
                            params=params,
                            json={},
                            headers=headers)
        # print(f"Empty Request has been postet: {r.status_code}")
        # print(r.json())

        # create new version
        version_url = url + '/' + dep_id + '/actions/newversion'
        r = requests.post(version_url, params=params)
        print(f"Created new version of deposition: {r.status_code}")
        print(r.json())
        new_url = r.json()['links']['latest_draft']
        new_deposition = r.json()['links']['latest_draft'].split('/')[-1]
        print(new_url)
        print(new_deposition)
        for f in r.json()['files']:
            old_file = f['id']
            print(f['filename'] + " " + old_file)
        # post empty request
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
        print(f"METADATA UPDATE: {r.status_code}")
    print("finished")"""
    
def publish(conference: str, url: str, headers:dict, params:dict) -> None:

    print("Publish conference papers..")
    dep_file = open("support/depositions_" + conference + ".txt", "r")
    dep_ids = [line.replace("\n", "") for line in dep_file]

    for deposition_id in dep_ids:
        print(deposition_id)
        dep_url = url+ '/' + deposition_id + '/actions/publish'
        print(dep_url)
        r = requests.post(url+ '/' + deposition_id + '/actions/publish',
                                params=params )
        print(r.status_code)
        print(r.json())
    print("finished")

def collect_dois(conference: str, url: str, headers:dict, params:dict) -> None:

    # TODO
    print("Get list of dois..")
    print("This function has not been implemented yet.")
    dep_file = open("support/depositions_" + conference + ".txt", "r")
    dep_ids = [line.replace("\n", "") for line in dep_file]

    for deposition_id in dep_ids:
        dep_url = url+ '/' + deposition_id
        print(dep_url)
        r = requests.get(url+ '/' + deposition_id,
                            params=params )
        print(r.status_code)
        print(r.json())

        print(r.json()["title"])
        print(r.json()["doi"])
        print(r.json()["doi_url"])
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

    # subparser 'collect dois'
    collect_parser = subparsers.add_parser('collect_dois', description='')
    collect_parser.add_argument('conference')
    collect_parser.add_argument('token')
    collect_parser.add_argument('-productive', nargs='?', type=bool, default=False, const=True)
    collect_parser.set_defaults(func=collect_dois)

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