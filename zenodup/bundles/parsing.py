import logging
from xml.etree import ElementTree as ET
import os
import re

from bundles import sanity

def ascii_rename(name: str) -> str:
    try:
        elements_to_be_replaced = [".", "-", ":", ",", "?", "!", " ", "(", ")", "&", "@"]
        name = name.replace("ß", "ss")
        name = name.replace("\"", "_em_")
        name = name.replace("\'", "_em_")
        for char in elements_to_be_replaced:
            name = name.replace(char, "_")
        try:
            name.encode("ascii")
        except:
            # if name contains non ascii
            name = ''.join([i if ord(i) < 128 else '_' for i in name])
        return name
    except AttributeError:
        pass

def parse_creator(name: str) -> list:
    name = [ascii_rename(elem.strip()) for elem in name.split(",")]
    return name

def get_bundle_names(abstract: ET.Element) -> dict:
    bundle_names = {}

    
    creator_names = [parse_creator(creator.find("name").text) for creator in abstract.findall(".//creator")]
    if len(creator_names) == 0:
        logging.warning(f"The abstract with title {abstract.find('title').text} "
                        f"(index) does not contain creators.")
    try:
        title = ascii_rename(abstract.find("title").text)
    except TypeError:
        logging.warning(f"The following abstract does not contain a title:")

    prefixes = [creator[0].upper()+'_'+creator[1]+'_' for creator in creator_names]
    possible_names = [prefix + title for prefix in prefixes]
    # if '_em_' in title replace by '_' and add prefix + modified name to possible names 
    try:
        if title.find("_em_") != -1:
            for prefix in prefixes:
                possible_names.append(prefix + title.replace("_em_", "_"))
        if title.find("ss") != -1:
            for prefix in prefixes:
                possible_names.append(prefix + title.replace("ss", "_"))
    except AttributeError:
        pass

    # add double '_' at the end of prefix and add all combinations to possible names
    for prefix in prefixes:
        possible_names.append(prefix + '_' + title)

    bundle_names.update({title: possible_names})

    return bundle_names

def get_comparable_filenames(files: list)-> dict:
    # get file names
    names = [os.path.splitext(f)[0] for f in files]
    names.sort()
    names_to_compare = {re.sub(r'[0-9]{3}_final-', '', name): name for name in names}

    return names_to_compare

def get_abstract_file(publication_names: dict, comparable_files: list, index : int) -> dict:

    for elem in publication_names:
        if any(possible_name.find(name) != -1 for possible_name in publication_names.get(elem) for name in
               comparable_files.keys()):
            for possible_name in publication_names.get(elem):
                for name in comparable_files.keys():
                    if possible_name.find(name) != -1:
                        abstract_file = comparable_files.get(name) 
        elif any(possible_name.find(name[:-1]) != -1 for possible_name in publication_names.get(elem) for name in
                 comparable_files.keys()):
            for possible_name in publication_names.get(elem):
                for name in comparable_files.keys():
                    if possible_name.find(name[:-1]) != -1:
                        abstract_file = comparable_files.get(name)
    try:
        return abstract_file
    except UnboundLocalError:
        return list(comparable_files.values())[index]

