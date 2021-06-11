import os
import json
from xml.etree import ElementTree as ET

ns = {"tei": "http://www.tei-c.org/ns/1.0"}

for elem in os.listdir("bundle_structures"):
    if elem in ["DHd2016","DHd2017", "DHd2018", "DHd2019", "DHd2020"]:
        year = elem.replace("DHd", "")
        print(elem)
        conf_metadata = os.path.join("conferences", elem)
        conference_path = os.path.join("bundle_structures", elem)
        bundle_paths = [os.path.join(conference_path, bundle) for bundle in os.listdir(conference_path)]

        for bundle in bundle_paths:
            
            # read title from json
            json_file = os.path.join(bundle, "bundle_metadata.json")
            with open(json_file, 'r') as f:
                data = json.load(f)
            title = data["metadata"]["title"]

            # put keywords in conference metadata
            metadata_file = "conferences/" + elem + "/" + year + "metadata.xml"
            metadata_tree = ET.parse(metadata_file)
            
            # read keywords from xml
            for pub in os.listdir(os.path.join(bundle, "bundle_publications")):
                if pub.endswith(".xml"):
                    xml_file = os.path.join(bundle, "bundle_publications", pub)
                    # parse metadata file of conference
                    tree = ET.parse(xml_file)
                    keywords = tree.findall(".//tei:keywords", ns)
                    for keyword in keywords:
                        if keyword.attrib.get("n") == "keywords":
                            terms = [term.text for term in keyword.findall("tei:term", ns)]

            if terms != [None]:
                for pub in metadata_tree.findall("metadata"):
                    if pub.find("title").text == title:
                        keyword = pub.find("keywords").text
                        new_keywords = keyword + ", " + ", ".join(terms)
                        pub.find("keywords").text = new_keywords
                        print(new_keywords)

            metadata_tree.write(metadata_file)
        

