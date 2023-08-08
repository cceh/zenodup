"""Zenodup Application

This application was developed to upload the abstracts of the DHd conferences to Zenodo. 
It is integrated in a workflow in order to collect, structure and publish the abstracts and the associated metadata. 
The use case for the application is on the one hand to create a valid bundle structure and on the other hand to interact with the Zenodo API. 
This script is the main script of the application.

Please see README.md for more detailed documentation.
"""

import argparse

import api
import bundles


def __create_bundles(args):
    del args["func"]
    conference = bundles.Conference(**args)
    conference.create_bundles()

    # update metadata for conference (not part of regular workflow)
    # conference.update_metadata()

def __api_interact(args):
    del args["func"]
    action = args.pop("action")
    con = api.Connection(**args)
    func = {"upload": con.upload,"publish": con.publish, "update": con.update, "delete": con.delete, "get_metadata": con.get_metadata, "write_identifier": con.write_identifier()}
    func[action]()

def __set_parser() -> argparse.ArgumentParser:

    zenodup_parser = argparse.ArgumentParser(description="This application was developed to upload the abstracts of the DHd conferences to Zenodo. \
                                                          It is integrated in a workflow in order to collect, structure and publish the abstracts and the associated metadata. \
                                                          The use case for the application is on the one hand to create a valid bundle structure and on the other hand to interact with the Zenodo API.\n\n \
                                                          Please see README.md for more detailed documentation.")
    
    subparsers = zenodup_parser.add_subparsers()
    subparsers.required = True

    # BUNDLE SUBPARSER
    bundle_parser = subparsers.add_parser('bundle', description='Create bundle structure for conference data. Please see README.md for more detailed documentation.')
    bundle_parser.add_argument('name')
    bundle_parser.add_argument('metadata')
    bundle_parser.add_argument('-sequenced', nargs='?', type=bool, default=False, const=True)
    bundle_parser.add_argument('-pdf', nargs='?', type=str, default='pdf', const='pdf')
    bundle_parser.add_argument('-xml', nargs='?', type=str, default=None, const='xml')
    bundle_parser.set_defaults(func=__create_bundles)
    
    # ZENODO API PARSER
    api_parser = subparsers.add_parser('api', description='Interact with zenodo api. Please see README.md for more detailed documentation.')
    api_parser.add_argument('action', choices=["upload", "publish", "update", "delete", "get_metadata", "write_identifier"])
    api_parser.add_argument('name')
    api_parser.add_argument('token')
    api_parser.add_argument('-productive', nargs='?', type=bool, default=False, const=True)
    api_parser.set_defaults(func=__api_interact)

    return zenodup_parser

if __name__ == "__main__":

    # set application parser
    parser = __set_parser()
    arguments = parser.parse_args()
    input_args = vars(arguments)

    # call function based on input arguments
    arguments.func(input_args)
    