#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from __future__ import print_function
import re

import sys

reload(sys)
sys.setdefaultencoding("utf-8")


def getNameAndSemester(text):
    headerpattern = re.compile(r"(?<=\<h1\>)(.*)\((.*?\d{4})\)(?=\</h1\>)")
    headerfind = re.search(headerpattern, text)
    nameofLV = headerfind.group(1).strip()
    semester = prettyPrintSemester(headerfind.group(2).strip())
    return nameofLV, semester


def prettyPrintSemester(verboseName):
    name = verboseName.lower() \
        .replace("wintersemester", "WS") \
        .replace("sommersemester", "SS") \
        .replace("summersemester", "SS")

    semesterRegex = r"(?i)(WS|SS) ?((?:20)?\d{2}(?:/(?:20)?\d{2})?)(?!.*\d)"
    semesterMatch = re.search(semesterRegex, name)

    if semesterMatch is None:
        print("Cannot prettify semester: " + verboseName)
        return verboseName

    ws_ss = semesterMatch.group(1).upper()
    shortNum = semesterMatch.group(2).split("/")[0][-2:]

    return ws_ss + shortNum


def getCP(text):
    ectsRegex = r"<li>(?:Credits|ECTS) ?: ?(\d+)</li>"
    ectsMatch = re.search(ectsRegex, text)
    if ectsMatch is None:
        return 0
    return int(ectsMatch.group(1))


lehrformAliases = {
    "Blockseminar": ["BS"],
    "Bachelorprojekt": ["BP"],
    "Klubsprecher": ['K'],
    "Projekt": ['P'],
    "Seminar": ['S'],
    "Übung": ['U', u'Ü'],
    "Vorlesung": ['V']
}


def getLehrform(text):
    text = text.replace("Projektseminar", "Projekt/Seminar")
    lehrformRegex = r"(?is)<li>(?:Teaching Form|Lehrform) ?: ?(.*?)</li>"
    lehrformMatch = re.search(lehrformRegex, text)
    lehrform = []
    if lehrformMatch is not None:
        lehrformString = lehrformMatch.group(1).strip().decode('utf-8')
        if lehrformString.endswith(' (Block)'):
            lehrformString = lehrformString[:-len(' (Block)')]
        for teilLehrformString in map(unicode.strip, lehrformString.split("/")):
            if teilLehrformString in lehrformAliases:
                lehrform.append(teilLehrformString)
            else:
                matched = False
                for lehrformName, aliases in lehrformAliases.iteritems():
                    for alias in aliases:
                        if teilLehrformString == alias:
                            lehrform.append(lehrformName)
                            matched = True
                        if matched:
                            break
                    if matched:
                        break
                if not matched:
                    for charIndex in range(len(teilLehrformString)):
                        currentCharMatched = False
                        char = teilLehrformString[charIndex]
                        for lehrformName, aliases in lehrformAliases.iteritems():
                            for alias in aliases:
                                if alias == char:
                                    lehrform.append(lehrformName)
                                    currentCharMatched = True
                                    break
                        matched = matched or currentCharMatched
                if not matched:
                    print("Unknown LV type, continue parsing: " + char)
                    lehrform.append(teilLehrFormString)
    lehrform.sort()
    return lehrform


def getDozenten(text):
    dataBlockRegex = re.compile(r"(?s)(?:Dozent|Lecturer): (.*?)(<br|<p)")
    dataBlockMatch = re.search(dataBlockRegex, text)
    dataBlock = dataBlockMatch.group(1)
    subBlocks = dataBlock.split(", ")

    result = []
    dozentRegex = re.compile(r"(?<=>).[^<>\n]+?(?=<)")
    for subBlock in subBlocks:
        subBlockStrip = subBlock.strip()
        if subBlockStrip.startswith("<"):
            dozentMatch = re.search(dozentRegex, subBlockStrip)
            if dozentMatch is not None:
                result.append(dozentMatch.group().strip())
        else:
            result.append(subBlockStrip)
    result.sort()
    return result


def getVertiefungAndModules(text):
    # Module extrahieren - ergibt zB die Vertiefungsgebiete
    moduleBlockRegex = r"<h2>(Studiengänge \& Module|Programs \& Modules)</h2>([\s\S]+?)</ul>"
    moduleBlockMatch = re.search(moduleBlockRegex, text)
    vertiefung = set()
    modules = set()
    if moduleBlockMatch is not None:
        moduleBlock = moduleBlockMatch.group(2)
        moduleRegex = r"<li>([\s\S]+?)</li>"
        moduleMatches = re.finditer(moduleRegex, moduleBlock)
        for match in moduleMatches:
            moduleName = match.group(1)
            vertiefung.add(extractVertiefung(moduleName))
            modules.add(extractModule(moduleName))

    vertiefung.discard("")
    modules.discard("")
    return sorted(list(vertiefung)), sorted(list(modules))


def extractVertiefung(moduleName):
    simpleAbbrevRegex = r"(.{3,4})-Vertiefung"
    simpleAbbrevMatch = re.search(simpleAbbrevRegex, moduleName)
    if simpleAbbrevMatch is not None:
        result = simpleAbbrevMatch.group(1)
        if result == "IST":
            return "ISAE"
        return result
    if moduleName == "Human Computer Interaction &amp; Computer Graphics Technology":
        return "HCGT"
    if moduleName == "Software Architecture &amp; Modeling Technology":
        return "SAMT"
    if moduleName == "Operating Systems &amp; Information Systems Technology":
        return "OSIS"
    if moduleName == "Internet &amp; Security Technology":
        return "ISAE"
    if moduleName == "Business Process &amp; Enterprise Technologies":
        return "BPET"

    return ""


def extractModule(moduleName):
    if extractVertiefung(moduleName) != "":
        return "Vertiefungsgebiete"

    if moduleName == "Rechtliche Grundlagen" or \
            moduleName == "Wirtschaftliche Grundlagen" or \
            moduleName == "Rechtliche und wirtschaftliche Grundlagen":
        return "Rechtliche und wirtschaftliche Grundlagen"

    if moduleName == "Softskills" or \
            moduleName == "Design Thinking" or \
            moduleName == "Klubsprecher" or \
            moduleName == "Schlüsselkompetenzen" or \
            moduleName.startswith("Design Thinking") or \
            moduleName == "Projektentwicklung und -management":
        return "Softskills"

    if moduleName.startswith("Mathematik") or \
            moduleName.startswith("Theoretische Informatik"):
        return "Mathematische und theoretische Grundlagen"

    if moduleName == "Betriebssysteme":
        return "BS"
    if moduleName == "Computergrafische Systeme":
        return "SB1"
    if moduleName == "Datenbanksysteme":
        return "SB2"
    if moduleName == "Prozessorientierte Informationssysteme":
        return "SB3"
    if moduleName == "Interactive Systeme" or \
            moduleName == "User-Interface-Systeme":
        return "SB4"
    if moduleName == "Web- und Internet-Technologien":
        return "SB5"

    if moduleName.startswith("Programmiertechnik") or \
            moduleName == "Software-Architektur" or \
            moduleName == "Digitale Systeme":
        return "Grundlagen IT-Systems Engineering"

    if moduleName == "Softwaretechnik" or \
            moduleName.startswith("Modellierung"):
        return "Softwaretechnik und Modellierung"

    return ""


ShortenLV = [
    # Grundlagen IT-Systems Engineering
    ("Einführung in die Programmiertechnik", "PT"),
    ("Grundlagen digitaler Systeme", "GdS"),
    ("Softwarearchitektur", "SWA"),
    # Softwaretechnik und Modellierung
    ("Modellierung", "Mod"),
    ("Softwaretechnik", "SWT"),
    # Mathematische und TheoretischeGrundlagen
    ("Theoretische Informatik", "TI"),
    # Softwarebasissysteme
    ("Betriebssysteme 1", "BS"),
    ("Betriebssysteme", "BS"),
    ("3D-Computergrafik", "CG"),
    ("Datenbanksysteme", "DBS"),
    ("POIS (Prozessorientierte Informationssysteme)", "POIS"),
    ("Prozessorientierte Informationssysteme", "POIS"),
    ("Designing Interactive Systems", "HCI I"),
    ("HCI: Building Interactive Devices and Computer Vision", "HCI II"),
    ("Building Interactive Devices", "HCI II"),
    ("Internet- und WWW-Technologien", "WWW"),
    # Rechtliche und wirtschaftliche Grundlagen
    ("Recht für Ingenieure", "Recht"),
    ("Wirtschaftliche Grundlagen", "Wirtschaft"),
    ("Wirtschaft I", "Wirtschaft"),
    # Vertiefungsgebiete
    ("Algorithmic Problem Solving", "AlgoRiddles"),
    ("Competitive Programming", "CompProg"),
    ("Big Data", "BD"),
    ("Bildverarbeitungsalgorithmen", "BVA"),
    ("Internet-Security", "ISec"),
    ("Internet Security", "ISec"),
    ("Entwurf und Implementierung digitaler Schaltungen mit VHDL", "VHDL"),
    ("Softwarequalität", "SWQualität"),

    ("Studienbegleitendes Seminar", "StubS"),

    ("HCI Project Seminar: ", "[HCI PS] "),
    ("HCI Project Seminar on ", "[HCI PS] "),
    ("HCI Project Seminar ", "[HCI PS] "),

    ("Projektentwicklung und- Management", "PEM"),
    ("Projektentwicklung und - management", "PEM"),
    ("Projektentwicklung und -management", "PEM")
]
ShortenWords = {
    ("Qualitätssicherung", "Qualität"),
    ("Applikationen", "Apps"),
    ("&quot;", "\""),
    ("&amp;", "and")
}
RemovableWords = {
    "\\",
    "zur Prüfungsvorbereitung",
    "Fachspezifisches ",
    "Best Practices",
    "Praktische Anwendung von",
    "Entwicklung von",
    "A Platform for",
    "für ",
    "development of ",
    "Industrieseminar"
}
IDReplace = {
    "professionalisiertelerntechniken": "lerntechnikenundstrategien"
}
MaxLVIDLength = 50


def shortenName(longName):
    """take the name of a LV and return the shorter display-version of the name"""
    name = longName

    for toReplace, replacement in ShortenLV:
        name = name.replace(toReplace, replacement)
    for toReplace, replacement in ShortenWords:
        name = name.replace(toReplace, replacement)
    for toRemove in RemovableWords:
        name = name.replace(toRemove, "")
    if name == "BS I":
        name = "BS"

    name = name.split(":")[0]
    name = name.split(" - ")[0]
    name = name.split(" mit ")[0]
    name = name.split(" with ")[0]
    name = name.split(" for ")[0]
    name = name.strip()

    if len(name) > MaxLVIDLength:
        name = name[:(MaxLVIDLength - 3)] + "..."

    if len(name) > 25 and name.count(' ') > 0:
        # add a br in the middlest space
        middleIndex = len(name) / 2
        middlestSpace = middleIndex
        spaceStep = 0

        while name[middlestSpace] != ' ':
            spaceStep += 1
            if name[middleIndex - spaceStep] == ' ':
                middlestSpace = middleIndex - spaceStep
            elif name[middleIndex + spaceStep] == ' ':
                middlestSpace = middleIndex + spaceStep

        name = name[:middlestSpace] + '<br />' + name[middlestSpace + 1:]

    return name


def shortNameToID(shortName):
    """take a short name and return an id string to use in json"""
    lvID = shortName \
        .replace('<br />', ' ') \
        .replace("III", "3") \
        .replace("II", "2") \
        .replace("\"", "") \
        .replace("&quot;", "") \
        .replace("(", "") \
        .replace(")", "") \
        .replace("[", "") \
        .replace("]", "") \
        .replace("{", "") \
        .replace("}", "") \
        .replace(".", "") \
        .replace(",", "") \
        .replace("\\", "") \
        .replace("-", "") \
        .replace("&", "") \
        .replace(";", "")

    if lvID.endswith(' I'):
        lvID = lvID[:-1] + "1"

    lvID = lvID \
        .replace("ü", "ue") \
        .replace("ä", "ae") \
        .replace("ö", "oe") \
        .replace("Ü", "Ue") \
        .replace("Ä", "Ae") \
        .replace("Ö", "Oe") \
        .replace(" ", "")

    while lvID[0].isdigit():
        lvID = lvID[1:]
    lvID = lvID.lower()

    return IDReplace.get(lvID, lvID)


def isPflicht(lv):
    return lv['id'] == 'bs' or \
           lv['id'] == 'gds' or \
           lv['id'] == 'pem' or \
           lv['id'] == 'wirtschaft' or \
           lv['kurz'].startswith("Mathe") or \
           lv['kurz'].startswith("TI ") or \
           lv['kurz'].startswith("PT ") or \
           lv['kurz'].startswith("Mod") or \
           lv['kurz'].startswith("Recht")


def getEmpfohlen(lv):
    """return the suggested semester number, or an empty string"""
    return {
        'gds': 1,
        'mathematik1': 1,
        'mod1': 1,
        'pt1': 1,
        'wirtschaft': 1,

        'mathematik2': 2,
        'mod2': 2,
        'pt2': 2,
        'recht1': 2,

        'recht2': 3,
        'swa': 3,
        'ti1': 3,
        'bs': 3,

        'ti2': 4,
        'swt1': 4
    }.get(lv['id'], '')


def cleanUp(lv):
    """take a finished lv-object and perform additional cleanup steps if needed"""
    if lv['id'] == 'pem':
        lv['modul'] = ['PEM']
        lv['cp'] = 6
