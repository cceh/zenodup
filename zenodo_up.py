"""
Creating a personal access token

    Register for a Zenodo account if you don’t already have one.
    Go to your Applications, to create a new token.
    Select the OAuth scopes you need (for the quick start tutorial you need deposit:write and deposit:actions).

https://zenodo.org/account/settings/applications/tokens/new/
"""

import getopt
import requests
import sys
import logging
import os
from pathlib import Path
import shutil
import json


def main(argv):

    # set params based on command line arguments
    productive, access_token, conference = set_params(argv[1:])
    # set logging
    logging.basicConfig(filename=conference + '_upload.log', filemode='w', encoding='utf-8', level=logging.DEBUG)
    # set parameters for zenodo request
    headers = {"Content-Type": "application/json"}
    params = {'access_token': access_token}
    if productive:
        url = 'https://zenodo.org/api/deposit/depositions'
    else:
        url = 'https://sandbox.zenodo.org/api/deposit/depositions'
    logging.info(f"Send requests to url: {url}")

    # upload bundle content
    bundle_base = readable_dir(os.path.join("bundle_structures",conference))
    logging.info(f"Bundle base directory based on given conference {conference}: {bundle_base}")
    bundles = [os.path.join(bundle_base, bundle) for bundle in os.listdir(bundle_base)]

    # create upload for each bundle
    for bundle in bundles:
        # get bucket url and deposition id for upload
        bucket_url, deposition_id = get_upload_params(url, params, headers)
        # get bundle files for upload
        bundle_json, bundle_publications = get_bundle_files(bundle)
        # upload bundle publications
        for publication in bundle_publications:
            with open(publication, "rb") as pub:
                r = requests.put(
                    "%s/%s" % (bucket_url, os.path.basename(publication)),
                    data=pub,
                    params=params)
                logging.info(f"Put publication file {publication}: {r.status_code}")
        # upload bundle metadata
        with open(bundle_json) as json_file:
            data = json.load(json_file)
        r = requests.put( url+'/%s' % deposition_id,
                         params=params, data=json.dumps(data), headers=headers)
        logging.info(f"Put publication metadata {bundle_json}: {r.status_code}")

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
    logging.info(f"Empty post to {url} with given access token: {r.status_code}")
    bucket_url = r.json()["links"]["bucket"]
    logging.info(f"Using the following bucket url: {bucket_url}")
    deposition_id = r.json()['id']
    logging.info(f"Using the following deposition id: {deposition_id}")
    return bucket_url, deposition_id

def set_params(argv:list) -> (bool, str, str):
    productive = bool
    access_token = ''
    conference = ''
    try:
        opts, args = getopt.getopt(argv,"hp:a:c:",["productive=","access_token=","conference="])
    except getopt.GetoptError:
        sys.exit(2)
    # if option -p is given, upload publications to zenodo productive system else upload to sandbox.
    if any(opt=='-p' for opt in opts):
        logging.info("Upload publications to zenodo productive system.")
        productive = True
    else:
        logging.info("Upload publications to zenodo sandbox.")
        productive = False
    for opt, arg in opts:
        if opt == '-h':
            print('zenodo_up.py -p <productive> -a <access_token> -c <conference>')
            sys.exit()
        elif opt in ("-a", "--access_token"):
            access_token = arg
        elif opt in ("-c", "--conference"):
            conference = arg
    return productive, access_token, conference

# check if unchecked path references is readable directory
def readable_dir(prospective_dir:str) -> Path:
    if not os.path.isdir(prospective_dir):
        raise Exception("readable_dir:{0} is not a valid path".format(prospective_dir))
    if not os.access(prospective_dir, os.R_OK):
        raise Exception("readable_dir:{0} is not a readable dir".format(prospective_dir))
    return Path(prospective_dir)

if __name__ == "__main__":

    # call main function
    main(sys.argv)