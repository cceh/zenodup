"""Module for parsing filenames and titles of abstracts
"""

import logging
import os
import re
from xml.etree import ElementTree as ET

from bundles import sanity


def get_bundle_names(abstract: ET.Element) -> dict:
    """Returns a dictionary with possible bundle names

    Parses title and creators of the abstract's metadata tag. 

    Parameters
    ----------
    abstract : ET.Element
        Metadata element of conference's metadata file

    Returns
    -------
    bundle_names : dict
        Returns a dictionary with the title of metadata tag as key and a 
        list of possible filenames for corresponding abstract pdf file as value.
    """

    bundle_names = {}
    creator_names = [__parse_creator(creator.find("name").text) for creator in abstract.findall(".//creator")]
    if len(creator_names) == 0:
        logging.warning(f"The abstract with title {abstract.find('title').text} "
                        f"(index) does not contain creators.")
    try:
        title = __ascii_rename(abstract.find("title").text)
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
    """Returns a dictionary with the conference's files without prefixes and extensions

    Parameters
    ----------
    files: list
        List of files to assign to corresponding metadata

    Returns
    -------
    names_to_compare: dict
        Returns a dictionary with modified filenames as keys and filenames as values 

    """
    # get file names
    names = [os.path.splitext(f)[0] for f in files]
    names.sort()
    names_to_compare = {re.sub(r'[0-9]{3}_final-', '', name): name for name in names}

    return names_to_compare

def get_abstract_file(publication_names: dict, comparable_files: dict, index : int) -> str:
    """Assigns file to abstract and returns filename

    Parameters
    ----------
    publication_names: dict
        Dictionary with all possible names for one abstract
    comparable_files: dict
        Dictionary with modified filenames as keys and filenames as values
    index: int
        Index of metadata element to be assigned. If no file could be assigned to metadata by name 
        comparison, the file with given index in list will be matched with metadata element.

    Returns
    -------
    abstract_file: str
        Returns filename of matched file
    """

    # find matching filename
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
    # if matching filename has been found return file
    try:
        return abstract_file
    # else return file with metadata elements index
    except UnboundLocalError:
        return list(comparable_files.values())[index]

# return string representation of creator
def __parse_creator(name: str) -> list:
    name = [__ascii_rename(elem.strip()) for elem in name.split(",")]
    return name

# get ascii representation of string
def __ascii_rename(name: str) -> str:
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
