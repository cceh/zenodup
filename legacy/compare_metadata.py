""" Use-case for DHd2022

Script to compare metadata of abstracts and posters:
Check if all poster publications do have 2 related identifiers
"""

from lxml import etree
from xml.etree import ElementTree as ET

XMLParser = etree.XMLParser()

# set filepaths
abstracts_file = "../zenodup/INPUT/DHd2022/DHd2022_Gesamtmetadaten.xml"
posters_file = "../zenodup/INPUT/DHd2022_poster/DHd2022_poster.xml"

# read in abstracts' metadata file
abstracts_tree = ET.parse(abstracts_file)
abstracts_root = abstracts_tree.getroot()
# read in posters' metadata file
posters_tree = ET.parse(posters_file)
posters_root = posters_tree.getroot()

abstracts_titles = [' '.join(abstract.find("title").text.replace("\n", "").split()) for abstract in abstracts_root.findall("metadata")] 
posters_titles = [' '.join(poster.find("title").text.replace("\n", "").split()) for poster in posters_root.findall("metadata")] 

posters_in_abstracts = [title for title in abstracts_titles if title in posters_titles]
abstracts_in_posters = [title for title in posters_titles if title in abstracts_titles]

if len(posters_in_abstracts) == len(abstracts_in_posters):
    for pub in abstracts_root.findall("metadata"):
        if ' '.join(pub.find("title").text.replace("\n", "").split()) in posters_titles:
            if len(pub.findall("related_identifiers/related_identifier")) == 2:
                print("OK")
            else:
                print(pub.findall("related_identifiers/related_identifier"))
                print(pub.find("title").text + " is a poster but does not contain 2 related identifiers.")
        else:
            if len(pub.findall("related_identifiers/related_identifier")) == 1:
                print("OK")
            else:
                print(pub.find("title").text + " is NOT a poster but does contain 2 related identifiers.")
