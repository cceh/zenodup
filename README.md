# Zenodup

This application was developed to upload the abstracts of the [DHd-Conferences](https://dig-hum.de/) to [Zenodo](https://zenodo.org/).
It is integrated in a workflow in order to collect, structure and publish the abstracts and the associated metadata.
The use case for the application is on the one hand to create a valid bundle structure and on the other hand to interact with the Zenodo API.

## Overview

- ``legacy/``: Legacy python scripts which are not integrated in generic workflow
- ``resources/``: png resources for README.md
- ``zenodup/``: Zenodup application source code
  - ``bundles/``: Python package to handle creation of bundle structure
  - ``INPUT/``: Default input directory
  - ``OUTPUT/``: Default output directory
  - ``support/``: Default support directory

## Requirements/Installation

Python 3.9 is required to run this application. Download Zenodup repository. If package manager [pip](https://pip.pypa.io/en/stable/) is installed, navigate to project folder and run:

```bash
pip install -r requirements.txt
```

## Usage

Two different tasks can be executed by running the application's main script ``zenodup/zenodup.py``:

1. Creating a bundle strucutre for conference's data
2. Interacting with [Zenodo's REST API](https://developers.zenodo.org/):
   - Upload abstracts
   - Publish drafts
   - Delete drafts
   - Update local metadata files
   - Get zenodo metadata of conferences for annual packages

It is also possible to run all actions on the [Zenodo Sandbox](https://sandbox.zenodo.org/) for testing purposes.

### Overview of workflow

### Configurations

In ``zenodup/config.yml`` the working directories such as desired input or output directory for the conferences' bundle structures are set.

- ``input_base``: Input directory for conference in order to create bundle structure. (Default: ``zenodup/INPUT/``)
- ``output_base``: Output directory for bundle structure. Bundle structure needs to be in output_base directory for Zenodo API interaction. (Default: ``zenodup/OUTPUT/``)
- ``depositions_dir``: Directory to save and load deposition files of conferences (Default: ``zenodup/support/depositions/``)
- ``logging_dir``: Directory to save logging files (Default: ``zenodup/support/logging/``)
- ``assignments_dir``: Directory for csv files to check final assignments of bundle creation (Default:``zenodup/support/assignments/``)
- ``packages_dir``: Directory for csv files containing Zenodo metadata of all published abstracts (Default:``zenodup/support/package/``)
- ``update_dir``: Directoy for updated metadata files (not part of regular workflow)(Default: ``zenodup/support/updated_metadata/``)

### Create Bundles for Upload

Change current working directory to ``/zenodup/zenodup/``. In order to interact with Zenodo's REST API via this application, the conferences have to be restructured in a certain bundle structure. Run script ``zenodup.py`` with argument ``bundle`` for assigning conference papers to bundles based on metadata file. Put folder with conference files in configured input directory (Default:``/support/INPUT/``). The conference folder is expected in the following structure:

```bash
  CONFERENCE
    ├── metadata.xml                   # Metadata file for conference containing all relevant information of the conference's publications
    ├── xml                            # Folder to xml files of the conference's pubclications
    │   ├── abstract1.xml                    
    │   └── ...                       
    └── pdf                            # Folder to pdf files of the conference's publications (optional)
        ├── abstract1.pdf                   
        └── ...   
```

> Remark: You can find an example dataset of a conference under ``/INPUT/example/``.

__Workflow to create bundle structure:__

![Workflow to create bundle structure](/resources/bundleworkflow_english.png)

To create the bundle structure for a conference, the following arguments need to be taken into account:

- **name**: Name of conference's folder to be restructured
- **metadata**: Name of the conference's metadata file
- **-sequenced** (optional): If parameter is passed, the order of files is assumed to be the same as appearances of metadata tags in metadata file. If not passed, the files will be assigned by name scheme.
- **-pdf** (optional): Name of directory containing conference's pdf files. If neither passed nor name is given the default is 'pdf'.
- **-xml** (optional): Name of directory containing conference's xml files. If not passed, there will be no xml files taken into account for the single abstracts of the conerence. If passed and no name is given the default is 'xml'.

Example usage:

```bash
# create bundle structure for conference "example" by name scheme
python zenodup.py bundle example example_metadata.xml -pdf -xml
```

The bundle structure will be created in the configured output directory (Default:``/OUTPUT/[CONFERENCE]``).

Logging file with name ``[CONFERENCE]_bundle.log`` will be created under configured logging directory (Default: ``support/logging``).

### Interact with Zenodo API

Change current working directory to ``/zenodup/zenodup/``. Run script ``zenodoup.py`` with argument ``api`` to run tasks with Zenodo API. If the bundle structure hasn't been created automatically with this application, this script expects the following bundle structure under configured ``output_base`` (Default: "``/OUTPUT``"):

```bash
  CONFERENCE                        # folder containing all bundles to be uploaded as single publications
    ├── abstract1                   # bundle folder for abstract1                
    │   ├── bundle_metadata.json    # abstract's metadata in json format
    │   └── bundle_publications
    │       ├── abstract1.pdf       # abstract's pdf file         
    │       └── abstract1.xml       # abstract's xml file (optional)                   
    └── ...                           
```

> Remark: This bundle structure is automatically generated by creating the bundle structure with this application.

__Workflow to publish abstract's on Zenodo:__

![Workflow to publish abstract's on Zenodo](/resources/publicationworkflow_english.png)

For more information about file ``bundle_metadata.json`` please see [Zenodo REST API Documentation](https://developers.zenodo.org/).

To interact with Zenodo API the following arguments need to be taken into account:

- **action**
  - _upload_: Upload of abstracts to Zenodo. In order to upload the abstracts the files must be available in the required bundle structure under the configured output directory.
  - _publish_: Publishes drafts of given conference in Zenodo.
  - _update_: Adds missing notes and references to the drafts' metadata.
    > CAUTION: This method contains hardcoded elements.
  - _delete_: Deletes drafts of given conference from Zenodo
  - _get_metadata_: Saves the abstracts' metadata for conference's annual package. This method is used to create an csv file containing all final abstracts metadata of conference. In order to add publication category (e.g. poster, panel, ...) to csv file the conferences' files must be available in the required bundle structure under the configured output directory.
    > CAUTION: This method contains hardcoded elements.
  - _write_identifier_: Writes the abstract's concept doi as related identifier. This method is used to add the abstract's concept doi to the affiliated poster publication. For this method the posters have to be stored in a subdirectory of the INPUT directory. It is necessary for each conference that the poster directory is called [CONFERENCE NAME]_poster containing the respective metadata file for the posters named [CONFERENCE NAME]_poster.xml (the final path is therefore ```/INPUT/[CONFERENCE NAME]_poster/[CONFERENCE NAME]_poster.xml```).


- **name**: Name of conference's folder with bundle structure
- **token**: Generated access token to use Zenodo API.
- **-productive** (optional): If argument is given, the bundles will be uploaded to productive system. Otherwise they will be uploaded to the [zenodo sandbox](https://sandbox.zenodo.org/).

Personal access token needs to be either created for [sandbox](https://sandbox.zenodo.org/account/settings/applications/tokens/new/) or [productive system](https://zenodo.org/account/settings/applications/tokens/new/):

1. Register for a Zenodo account if you don’t already have one.
2. Go to your Applications, to create a new token.
3. Select the OAuth scopes you need (for the quick start tutorial you need deposit:write and deposit:actions).

Example usage:

```bash
# Upload conference's abstracts to sandbox
python zenodup.py api upload [CONFERENCE] [ACCESS_TOKEN]

# Upload conference's abstracts to productive system
python zenodup.py api upload [CONFERENCE] [ACCESS_TOKEN] -productive
```

Logging file with name ``[CONFERENCE]_upload.log`` will be created under ``support/logging/``.

## Project related links

- Published abstracts can be found under [DHd Community on Zenodo](https://zenodo.org/search?page=1&size=20&q=dhd)
- Data for the conferences of 2014-2020 can be accessed here: https://github.com/DHd-Verband

## Authors and Acknowledgment

### Digital Humanities im deutschsprachigen Raum

- GitHub: https://github.com/DHd-Verband
- Website: https://dig-hum.de

### Patrick Helling

- GitHub: https://github.com/PatrickHelling
- Email: patrick.helling@uni-koeln.de

### Anke Debbeler

- GitHub: https://github.com/AnkeDe, https://github.com/Baenki
- Email: adebbel1@uni-koeln.de

## License

[MIT](LICENSE)

## Project status

 This application is designed for specific use cases. It should be adjusted in case for generic usage:

- integrate tests
- if xml files of abstracts are available assign abstracts by title from xml files and not by name scheme
- in case of versioning of publications a new workflow to maintain the abstracts deposition ids has to be created
- functions ``update`` and ``get_metadata`` in script ``zenodup/api.py`` contain hardcoded elements
