# Zenodup

This application was developed to upload the abstracts of the [DHd-Conferences](https://dig-hum.de/) to [Zenodo](https://zenodo.org/).
It is integrated in a workflow in order to collect, structure and publish the abstracts and the associated metadata.
The use case for the application is on the one hand to create a valid bundle structure and on the other hand to interact with the Zenodo API.

## Overview

- ``legacy/``: Legacy python scripts which are not integrated in generic workflow
- ``zenodup/``: Zenodup application source code
  - ``bundles/``: Python package to handle creation of bundle structure
  - ``INPUT/``: Default input directory for data of conferences
  - ``OUTPUT/``: Default output directory for data of conferences
  - ``support/``: Default support directory

## Requirements

Python 3.8 or higher

## Installation

Download Zenodup repository. If package manager [pip](https://pip.pypa.io/en/stable/) is installed, navigate to project folder and run:

```bash
pip install -r requirements.txt
```

## Usage

Two different tasks can be executed by running the application's main script ``zenodup/zenodup.py``:

- Creating a bundle strucutre for conference's data
- Interacting with [Zenodo's REST API](https://developers.zenodo.org/):
  - Upload abstracts
  - Publish drafts
  - Delete drafts
  - Update local metadata files
  - Get zenodo metadata of conferences for annual packages

It is also possible to run all actions on the [Zenodo Sandbox](https://sandbox.zenodo.org/) for testing purposes.

### Configurations

In ``zenodup/config.yml`` the working directories such as desired input or output directory for the conferences' bundle structures can be set.

- ``input_base``: Input directory for conference in order to create bundle structure. (Default: ``zenodup/support/INPUT/``)
- ``output_base``: Output directory for bundle structure. Bundle structure needs to be in output_base directory for Zenodo API interaction. (Default: ``zenodup/support/OUTPUT/``)
- ``depositions_dir``: Directory to save and load deposition files of conferences (Default: ``zenodup/support/depositions/``)
- ``logging_dir``: Directory to save logging files (Default: ``zenodup/support/logging/``)
- ``assignments_dir``: Directory for csv files to check final assignments of bundle creation (Default:``zenodup/support/assignments/``)
- ``packages_dir``: Directory for csv files containing Zenodo metadata of all published abstracts (Default:``zenodup/support/package/``)
- ``update_dir``: Directoy for updated metadata files (not part of regular workflow)(Default: ``zenodup/support/updated_metadata/``)

### Create Bundles for Upload

In order to interact with zenodo api via this application, the conferences have to be restructured in a certain bundle structure. Run script ``zenodup.py`` (cwd: ``/zenodup/zenodup/``) for assigning conference papers to bundles based on metadata file. Put conference folder in configured input directory (Default:``/support/INPUT/``). The conference folder is expected in the following structure:

- **CONFERENCE**: Folder containing all relevant files of conference
  - **METADATA_FILE**: Metadata file for conference containing all relevant information of conference publications
  - **XML**: Folder to xml files of conference pubclications
  - **PDF**: Folder to pdf files of conference publications (optional)

> Remark: You can find an example dataset of a conference folder under ``/INPUT/example/``.

To create the bundle structure for a conference, the following arguments need to be passed:

- **name**: Name of conference's folder to be restructured
- **metadata**: Name of the conference's metadata file
- **-sequenced** (optional): If parameter is passed, the order of files is assumed to be the same as appearances of metadata tags in metadata file. If not passed, the files will be assigned by name scheme.
- **-pdf** (optional): Parameter for name of directory containing conference's pdf files. If neither passed nor name is given the default is 'pdf'.
- **-xml** (optional): Parameter for name of directory containing conference's xml files. If not passed, there will be no abstract's xml files taken into account. If passed and no name is given the default is 'xml'.

Example:

```bash
python zenodup.py bundle example example_metadata.xml -pdf -xml
```

The created bundle structure will be created in configured output directory (Default:``/bundle_structure/[CONFERENCE]``).

Logging file with name ``[CONFERENCE]_bundle.log`` will be created under configured loggin directory (Default: ``support/logging``).

## TODO hier weiter

### Interact with Zenodo API

Run script ``zenodoup.py`` (cwd: zenodup/zenodup/) to upload bundle structure to Zenodo. If bundle structure hasn't been created automatically with this application, this script expects the following bundle structure for CONFERENCE under configured ``output_base`` (Default: "OUTPUT").

- CONFERENCE/: Folder containing all bundles to be uploaded as single publications
    - BUNDLE_1/:
        - bundle_metadata.json
        - bundle_publications/
            - file_1
            - ...
    - BUNDLE_2/:
        - ...
    - ..

> Remark: This bundle structure is automatically generated by creating bundle structure with this application.

For more information to structure file ``bundle_metadata.json`` please see [Zenodo REST API Documentation](https://developers.zenodo.org/).

To run this script the following arguments need to be passed:

    * - c CONFERENCE: Name of conference folder
    * - a ACCESS_TOKEN: Generated Access Token to use Zenodo API
    * - p (Optional): If argument is given, the bundles will be uploaded to productive system. Otherwise they will be uploaded to the [zenodo sandbox](https://sandbox.zenodo.org/).

Personal access Token need to be either created for [sandbox](https://sandbox.zenodo.org/account/settings/applications/tokens/new/) oder [productive system](https://zenodo.org/account/settings/applications/tokens/new/):

1. Register for a Zenodo account if you don’t already have one.
2. Go to your Applications, to create a new token.
3. Select the OAuth scopes you need (for the quick start tutorial you need deposit:write and deposit:actions).

```bash
# Upload to sandbox
python zenodo_up.py -c [CONFERENCE] -a [ACCESS_TOKEN] 

# Upload to productive system
python zenodo_up.py -p -c [CONFERENCE] -a [ACCESS_TOKEN] 
```
Logging file with name ``[CONFERENCE]_upload.log`` will be created in project folder.

## License
[MIT](LICENSE)


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

Personal access Token need to be either created for sandbox (https://sandbox.zenodo.org/account/settings/applications/tokens/new/) or productive system (https://zenodo.org/account/settings/applications/tokens/new/):

1. Register for a Zenodo account if you don’t have one.
2. Go to your Applications, to create a new token.
3. Select the OAuth scopes you need (for the quick start tutorial you need deposit:write and deposit:actions).

## Authors and Acknowledgment
## License
## Project status

 Tests
 Assign by title from xml files