"""Zenodup application

This application hat been built to upload abstracts of DHd Conferences to Zenodo. 
It is an integrated task in the workflow for collecting, structuring and publishing the conferences metadata. 
The use cases for this application are creating a valid bundle structure and interacting with the zenodo api. 
This script is used as the main script to navigate the different tasks based on input arguments.
For further usage, information and references see README.md.
"""

# Imports

# ## external python packages
import argparse

# ## project internal python packages/modules
import api
import bundles


def __create_bundles(args):
    # create instance of bundles conference class based on input arguments
    del args["func"]
    conference = bundles.Conference(**args)
    # create bundles for conference
    conference.create_bundles()

    # update metadata for conference
    # ## not integrated in usual workflow, was used once
    # conference.update_metadata()

def __api_interact(args):
    # create instance of api connection class based on input arguments
    del args["func"]
    action = args.pop("action")
    con = api.Connection(**args)
    func = {"upload": con.upload,"publish": con.publish, "update": con.update, "delete": con.delete, "get_metadata": con.get_metadata}
    func[action]()

def __set_parser() -> argparse.ArgumentParser:

    # ## create application parser
    zenodup_parser = argparse.ArgumentParser(description="Zenodup is an python application integrated in a workflow to publish DHd Conference abstracts. It can be used for two different tasks. Creating required bundle structure (subparser bundle) and interacting with zenodo api (subparser api). For further information please see README.md.")
    
    # ## create subparsers
    subparsers = zenodup_parser.add_subparsers()
    subparsers.required = True

    # ## BUNDLE SUBPARSER
    bundle_parser = subparsers.add_parser('bundle', description='Create bundle structure for conference. For further documentation please see README.md.')
    bundle_parser.add_argument('name')
    bundle_parser.add_argument('metadata')
    bundle_parser.add_argument('-sequenced', nargs='?', type=bool, default=False, const=True)
    bundle_parser.add_argument('-pdf', nargs='?', type=str, default='pdf', const='pdf')
    bundle_parser.add_argument('-xml', nargs='?', type=str, default=None, const='xml')
    bundle_parser.set_defaults(func=__create_bundles)
    
    # ## ZENODO API INTERACTION PARSER
    api_parser = subparsers.add_parser('api', description='Interact with zenodo api. For further Information pleas see README.md.')
    api_parser.add_argument('action', choices=["upload","publish", "update", "delete", "get_metadata"])
    api_parser.add_argument('name')
    api_parser.add_argument('token')
    api_parser.add_argument('-productive', nargs='?', type=bool, default=False, const=True)
    api_parser.set_defaults(func=__api_interact)

    return zenodup_parser

if __name__ == "__main__":

    # get application parser and run function based on system arguments
    parser = __set_parser()
    arguments = parser.parse_args()
    input_args = vars(arguments)

    # call function based on input arguments
    arguments.func(input_args)
    