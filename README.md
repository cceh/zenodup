# zenodup

Zenodup is a Python (3.9) application for uploading publications to [Zenodo](https://zenodo.org/).

## Installation

Download/Clone Zenodup repository. If package manager [pip](https://pip.pypa.io/en/stable/) is installed, navigate to project folder and run: 

```bash
pip install -r requirements.txt
```

## Usage

This application is divided in 2 different tasks which can be executed by running the scripts ``create_bundles.py`` and ``zenodo_up.py``. 

### Create Bundles for Upload

Run script ``create_bundles.py`` (cwd: projectfolder) for assigning conference papers to bundles based on metadata file. Put conference folder in /conferences. The conference folder is expected in the following strucutre:

- CONFERENCE: Folder containing all relevant files of conference
    - METADATA_FILE: Name of metadata file for conference containing all relevant information of conference publications
    - XML: Folder to xml files of conference pubclications
    - PDF: Folder to pdf files of conference publications

To run this script the following arguments need to be passed:

    * - c CONFERENCE: Name of conference folder
    * - m METADATA_FILE: Name of metadata file (expected format: xml) for conference publications
    * - x XML (Optional): Name of folder of conference publication xmls. If no name is given, script expects folder name "xml"
    * - p PDF (Optional): Name of folder of conference publication pdfs. If no name is given, script expects folder name "pdf"

```bash
python create_bundles.py -c [CONFERENCE] -m [METADATA_FILE] -p [FOLDER_TO_PDF] -x [FOLDER_TO_XML]
```

The created bundle structure will be created in ``/bundle_structure/[CONFERENCE]``. 

Logging file with name ``[CONFERENCE]_bundle.log`` will be created in project folder.

### Upload Bundles to Zenodo

Run script ``zenodo_up.py`` (cwd: projectfolder) to upload bundle structure to Zenodo. If bundle structure hasn't been created with script ``create_bundles.py``, this script expects the following bundle structure for CONFERENCE under ``bundle_structures/``:

- CONFERENCE/: Folder containing all bundles to be uploaded as single publications
    - BUNDLE_1/:
        - bundle_metadata.json
        - bundle_publications/
            - file_1
            - ...
    - BUNDLE_2/:
        - ...
    - ..

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