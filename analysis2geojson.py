# -*- coding: utf-8 -*-
import sys
import json
import xml.etree.ElementTree as et
from collections import defaultdict
import datetime

namespaces = {
    'jmx_ib': 'http://xml.kishou.go.jp/jmaxml1/informationBasis1/',
    'jmx_eb': 'http://xml.kishou.go.jp/jmaxml1/elementBasis1/',
    'jmx_ml': 'http://xml.kishou.go.jp/jmaxml1/body/meteorology1/'
    }

def tag(namespace, element):
    return '{' + namespaces[namespace]+ '}'+ element

class metinfo:
    def __init__(self, tree):
        self.tree = tree
        self.parse()

    def parse(self):
        root = self.tree.getroot()

        head = root.find('.//jmx_ib:Head', namespaces)
        self.headTitle = head.find('.//jmx_ib:Title', namespaces).text
        self.headReportDateTime = head.find('.//jmx_ib:ReportDateTime', namespaces).text
        self.headTargetDateTime = head.find('.//jmx_ib:TargetDateTime', namespaces).text
        self.headEventID = head.find('.//jmx_ib:EventID', namespaces).text
        self.headInfoType = head.find('.//jmx_ib:InfoType', namespaces).text
        self.headSerial = head.find('.//jmx_ib:Serial', namespaces).text
        self.headInfoKind = head.find('.//jmx_ib:InfoKind', namespaces).text
        self.headInfoKindVersion = head.find('.//jmx_ib:InfoKindVersion', namespaces).text
        headline = head.find('.//jmx_ib:Headline', namespaces)
        self.headlineText = headline.find('.//jmx_ib:Text', namespaces).text

        features = []
        metinfos = root.findall('.//jmx_ml:MeteorologicalInfos', namespaces)

        for metinfo in metinfos:
            aType = metinfo.get("type")
            for item in metinfo.findall('.//jmx_ml:Item', namespaces):
                for kind in item.find('.//jmx_ml:Kind', namespaces):
                    if kind.tag == tag('jmx_ml', 'Name'):
                        kName = kind.text
                    elif kind.tag == tag('jmx_ml', 'Property'):
                        geometry = []
                        geometryType = ""
                        properties = {}
                        for property_ in kind:
                            if property_.tag == tag('jmx_ml', 'Type'):
                                properties.update({"type": property_.text})
                            elif property_.tag == tag('jmx_ml', 'IsobarPart'):
                                for p in property_:
                                    if p.tag == tag('jmx_eb', 'Line'):
                                        geometryType = "LineString"
                                        for combined_coordinates in p.text.split("/"):
                                            if combined_coordinates:
                                                divided_coordinates = combined_coordinates.split("+")
                                                coordinates = [float(divided_coordinates[2]), float(divided_coordinates[1])]
                                                geometry.append(coordinates)
                                    elif p.tag == tag('jmx_eb', 'Pressure'):
                                        properties.update({"pressure": p.text})
                            elif property_.tag == tag('jmx_ml', 'CenterPart'):
                                for p in property_:
                                    if p.tag == tag('jmx_eb', 'Coordinate'):
                                        geometryType = "Point"
                                        for combined_coordinates in p.text.split("/"):
                                            if combined_coordinates:
                                                divided_coordinates = combined_coordinates.split("+")
                                                coordinates = [float(divided_coordinates[2]), float(divided_coordinates[1])]
                                                geometry = coordinates
                                    elif p.tag == tag('jmx_eb', 'Pressure'):
                                        properties.update({"pressure": p.text})
                                    elif p.tag == tag('jmx_eb', 'Direction') and p.text:
                                        properties.update({"direction": p.text})
                                    elif p.tag == tag('jmx_eb', 'Speed') and p.get("unit") == "km/h":
                                        properties.update({"speed_kmh": p.text})
                                        properties.update({"speed_kmh_description": p.get("description")})
                                    elif p.tag == tag('jmx_eb', 'Speed') and p.get("unit") == "ノット":
                                        properties.update({"speed_kt": p.text})
                                        properties.update({"speed_kt_description": p.get("description")})
                            elif property_.tag == tag('jmx_ml', 'CoordinatePart'):
                                for p in property_:
                                    if p.tag == tag('jmx_eb', 'Line'):
                                        geometryType = "LineString"
                                        for combined_coordinates in p.text.split("/"):
                                            if combined_coordinates:
                                                divided_coordinates = combined_coordinates.split("+")
                                                coordinates = [float(divided_coordinates[2]), float(divided_coordinates[1])]
                                                geometry.append(coordinates)
                
                        feature = {
                            "geometry": {
                                "type": geometryType,
                                "coordinates": geometry
                            },
                            "type": "Feature",
                            "properties": properties
                        }
                        features.append(feature)
        self.featurecollection = {"type":"FeatureCollection","features":features}
        self.geojson = json.dumps(self.featurecollection, ensure_ascii=False)

if __name__ == '__main__':
    argvs = sys.argv
    argc = len(argvs)
    if (argc != 2):
        print('Usage: # python %s uuid.xml ' % argvs[0])
        quit()
    else:
        tree = et.parse(argvs[1])
        metinfo = metinfo(tree)
        print(metinfo.headTitle)
        targetDateTime = datetime.datetime.fromisoformat(metinfo.headTargetDateTime)
        f = open(targetDateTime.strftime("%Y%m%d_%H%M") + ".json", "w")
        f.write(metinfo.geojson)
        f.close()
        print("save json")