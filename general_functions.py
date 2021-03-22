from xml.etree import ElementTree as ET
import os
import json

# check if unchecked path references is readable directory
def readable_dir(prospective_dir: str) -> str:
    if not os.path.isdir(prospective_dir):
        raise Exception("readable_dir:{0} is not a valid path".format(prospective_dir))
    if not os.access(prospective_dir, os.R_OK):
        raise Exception("readable_dir:{0} is not a readable dir".format(prospective_dir))
    return prospective_dir


def readable_file(prospective_file: str) -> str:
    if not os.path.isfile(prospective_file):
        raise Exception("readable_dir:{0} is not a valid path".format(prospective_file))
    if not os.access(prospective_file, os.R_OK):
        raise Exception("readable_dir:{0} is not a readable dir".format(prospective_file))
    return prospective_file


def create_bundles_metadata(pub: ET.Element, bundle_path: str, conf:str) -> None:
    print(f"Create bundle for publication: {pub.find('title').text}")
    data = {}

    if pub.find("doi").text:
        doi = pub.find("doi").text
    else:
        doi = ""
    data = {"metadata": {"upload_type": pub.find("upload_type").text,
                        "publication_type": pub.find("publication_type").text,
                        "publication_date": pub.find("publication_date").text,
                        "title": pub.find("title").text,
                        "creators": [{"name": creator.find("name").text,
                                    "affiliation": creator.find("affiliation").text
                                    } for creator in pub.findall("creators/creator")],
                        "description": pub.find("description").text,
                        "access_right": pub.find("access_right").text,
                        "license": pub.find("license").text,
                        "doi": doi,
                        "keywords": pub.find("keywords").text.split(", "),
                        "contributors": [{"name": contributor.find("name").text,
                                        "affiliation": contributor.find("affiliation").text,
                                        "type": contributor.find("type").text
                                        } for contributor in pub.findall("contributors/contributor")],
                        "communities": [{"identifier": "dhd"}],
                        "conference_title": pub.find("conference_title").text,
                        "conference_acronym": pub.find("conference_acronym").text,
                        "conference_dates": pub.find("conference_dates").text,
                        "conference_place": pub.find("conference_place").text,
                        "conference_url": pub.find("conference_url").text
                        }
            }
   
    with open(os.path.join(bundle_path, 'bundle_metadata.json'), 'w') as outfile:
              json.dump(data, outfile)
