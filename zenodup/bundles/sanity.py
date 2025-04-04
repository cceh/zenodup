"""Sanity checks for given bundle structure
"""

import logging
import os

import bundles

def directory(d: str) -> None:
    """Checks if directory contains multiple file types

    Ignores .DS_Store.

    Parameters
    ----------
    d : str
        Path to directory checking file types

    Raises
    ------
    Exception
        If the given directory contains multiple file types.
    """

    types = set([os.path.splitext(f)[1] for f in os.listdir(d) if f != ".DS_Store"])
    if len(types) > 1:
        logging.warning(f"The given directory {d} contains files with multiple formats: {types}")
        raise Exception("The given directory contains files with multiple formats.")

def filenames(conf: 'bundles.Conference') -> None:
    """Compares filenames in pdf and xml directories 

    Compares filenames without extensions. 
    Ignores .DS_Store files.

    Parameters
    ----------
    conf : bundles.Conference
        Conference from which the filenames are to be compared.

    Raises
    ------
    Exception
        If directories contain different filenames.
    """

    pdf_names = [os.path.splitext(f)[0] for f in os.listdir(conf.pdf) if f != ".DS_Store"]
    xml_names = [os.path.splitext(f)[0]  for f in os.listdir(conf.xml) if f != ".DS_Store"]

    missing_xmls = [f for f in pdf_names if f not in xml_names]
    missing_pdfs = [f for f in xml_names if f not in pdf_names]

    if len(missing_xmls) != 0 or len(missing_pdfs) != 0:
        logging.warning(f"For the following pdf files exists no matching xml file: {missing_xmls}. For the following xml files exists no matching pdf file: {missing_pdfs}. Please check.")
        raise Exception(f"For the following pdf files exists no matching xml file: {missing_xmls}. For the following xml files exists no matching pdf file: {missing_pdfs}. Please check.")

def readable_dir(prospective_dir: str) -> str:
    """Check if unchecked path references is readable directory

    Parameters
    ----------
    prospective_dir: str
        String representation of path to directory to be checked.

    Returns
    -------
    prospective_dir: str
        String representation of path if readable directory.

    Raises
    ------
    Exception
        If path is not a readable directory or if access to directory is not granted.
    """

    if not os.path.isdir(prospective_dir):
        raise Exception("readable_dir:{0} is not a valid path".format(prospective_dir))
    if not os.access(prospective_dir, os.R_OK):
        raise Exception("readable_dir:{0} is not a readable dir".format(prospective_dir))
    return prospective_dir

def readable_file(prospective_file: str) -> str:
    """Check if unchecked path references is readable file

    Parameters
    ----------
    prospective_file: str
        String representation of path to file to be checked.

    Returns
    -------
    prospective_file: str
        String representation of path if readable file.

    Raises
    ------
    Exception
        If path is not a readable file or if access to file is not granted.
    """
    
    if not os.path.isfile(prospective_file):
        raise Exception("readable_dir:{0} is not a valid path".format(prospective_file))
    if not os.access(prospective_file, os.R_OK):
        raise Exception("readable_dir:{0} is not a readable dir".format(prospective_file))
    return prospective_file