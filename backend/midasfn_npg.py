import math as mt
import matplotlib.pyplot as plt
from scipy.interpolate import CubicHermiteSpline
import requests
section_ids = []    #Global list of section IDs
#1 Class to enter the MAPI key in user python file
class MAPI_KEY:
    """MAPI key from Civil NX.  Sample MAPI_Key("eadsfjaksldfjaklsdvkalsdnvlkasndvklasdf.asdjkflasdkjlkajrt09342568ajkgj345")"""
    data = []
    
    def __init__(self, mapi_key):
        MAPI_KEY.data = []
        self.KEY = mapi_key
        MAPI_KEY.data.append(self.KEY)
        
    @classmethod
    def get_key(cls):
        my_key = MAPI_KEY.data[-1]
        return my_key
#---------------------------------------------------------------------------------------------------------------

#2 midas API link code:
def MidasAPI(method, command, body=None):
    """Method, Command, Body.  Sample: MidasAPI("PUT","/db/NODE",{"Assign":{1{'X':0, 'Y':0, 'Z':0}}})"""
    global base_url
    mapi_key = MAPI_KEY.get_key()

    url = base_url + command
    headers = {
        "Content-Type": "application/json",
        "MAPI-Key": mapi_key
    }

    if method == "POST":
        response = requests.post(url=url, headers=headers, json=body)
    elif method == "PUT":
        response = requests.put(url=url, headers=headers, json=body)
    elif method == "GET":
        response = requests.get(url=url, headers=headers)
    elif method == "DELETE":
        response = requests.delete(url=url, headers=headers)

    if response.status_code == 404: print(f"Civil NX model is not connected.  Click on 'Apps> Connect' in Civil NX. \nMake sure the MAPI Key in python code is matching with the MAPI key in Civil NX.")

    if response.status_code != 200: print(method, command, response.status_code)

    return response.json()
#---------------------------------------------------------------------------------------------------------------

#3 Function to define units
def units(force = "KN",length = "M", heat = "BTU", temp = "C"):
    """force --> KN, N, KFG, TONF, LFB, KIPS ||  
    \ndist --> M, CM, MM, FT, IN ||  
    \nheat --> CAL, KCAL, J, KJ, BTU ||  
    \ntemp --> C, F
    \nDefault --> KN, M, BTU, C"""
    if temp not in ["C","F"]:
        temp="C"
    if force not in ["KN", "N", "KGF", "TONF", "LBF", "KIPS"]:
        force = "KN"
    if length not in ["M", "CM", "MM", "FT", "IN"]:
        dist = "M"
    if heat not in ["CAL", "KCAL", "J", "KJ", "BTU"]:
        heat = "BTU"
    unit={"Assign":{
        1:{
            "FORCE":force,
            "DIST":length,
            "HEAT":heat,
            "TEMPER":temp
        }
    }}
    MidasAPI("PUT","/db/UNIT",unit)
#---------------------------------------------------------------------------------------------------------------

#4 Function to check analysis status & perform analysis if not analyzed
def analyze():
    """Checkes whether a model is analyzed or not and then performs analysis if required."""
    r = (MidasAPI("POST","/post/TABLE",{"Argument": {"TABLE_NAME": "Reaction(Global)","TABLE_TYPE": "REACTIONG",}}))
    if 'error' in r.keys():
        MidasAPI("POST","/doc/SAVE",{"Argument":{}})
        MidasAPI("POST","/doc/ANAL",{"Assign":{}})
#---------------------------------------------------------------------------------------------------------------

#5 Class to create nodes
class Node:
    """X ordinate, Y ordinate, Z ordinate, Node ID (optional). \nSample: Node(1,0,5)"""
    nodes = []
    ids = []
    def __init__(self,x,y,z,id=0):
        if Node.ids == []: 
            node_count = 1
        else:
            node_count = max(Node.ids)+1
        self.X = x
        self.Y = y
        self.Z = z
        if id == 0 or id in Node.ids: self.ID = node_count
        if id != 0 and id not in Node.ids: self.ID = id
        Node.nodes.append(self)
        Node.ids.append(self.ID)
    
    @classmethod
    def make_json(cls):
        json = {"Assign":{}}
        for i in cls.nodes:
            json["Assign"][i.ID]={"X":i.X,"Y":i.Y,"Z":i.Z}
        return json
    
    @classmethod
    def create(cls):
        MidasAPI("PUT","/db/NODE",Node.make_json())
        
    @classmethod
    def call_json(cls):
        return MidasAPI("GET","/db/NODE")
    
    @classmethod
    def update_class(cls):
        a = Node.call_json()
        if a != {'message': ''}:
            if list(a['NODE'].keys()) != []:
                Node.nodes = []
                for j in a['NODE'].keys():
                    Node(round(a['NODE'][j]['X'],6), round(a['NODE'][j]['Y'],6), round(a['NODE'][j]['Z'],6),int(j))
#---------------------------------------------------------------------------------------------------------------

#6 Class to create elements
class Element:
    """i Node ID, j Node ID, Mat ID, Sect ID, TYPE [Optional]("BEAM" or "TRUSS"), B_ANGLE [Optional], id[Optional].
    \nSample: Element(1,2)"""
    elements = []
    ids = []
    def __init__(self,i, j, mID = 1, sID = 1, TYPE = "BEAM", B_ANGLE = 0,id = 0):
        if i>0 and j>0 and i!=j and mID>0 and sID>0 and id>=0:
            if Element.ids == []: 
                element_count = 1
            else:
                element_count = max(Element.ids)+1
            self.I = i
            self.J = j
            self.MAT = mID
            self.SECT = sID
            self.TYPE = TYPE
            self.B_ANGLE = B_ANGLE
            if id == 0 or id in Element.ids: self.ID = element_count
            if id!= 0 and id not in Element.ids: self.ID = id
            Element.elements.append(self)
            Element.ids.append(self.ID)
    
    @classmethod
    def make_json(cls):
        json = {"Assign":{}}
        for k in cls.elements:
            json["Assign"][k.ID]={"TYPE": k.TYPE,
            "MATL":k.MAT,
            "SECT":k.SECT,
            "NODE":[k.I,k.J],
            "ANGLE":k.B_ANGLE}
        return json
    
    @classmethod
    def create(cls):
        MidasAPI("PUT","/db/ELEM",Element.make_json())
        
    @classmethod
    def call_json(cls):
        return MidasAPI("GET","/db/ELEM")
    
    @classmethod
    def update_class(cls):
        a = Element.call_json()
        if a != {'message': ''}:
            if list(a['ELEM'].keys()) != []:
                Element.elements = []
                for j in a['ELEM'].keys():
                    Element(a['ELEM'][j]['NODE'][0], a['ELEM'][j]['NODE'][1], mID = a['ELEM'][j]['MATL'], sID = a['ELEM'][j]['SECT'], TYPE = a['ELEM'][j]['TYPE'], B_ANGLE = a['ELEM'][j]['ANGLE'], id = int(j))
#---------------------------------------------------------------------------------------------------------------

#7 Class to define supports
class Support:
    """Node ID, Constraint, Boundary Group.  Sample: Support(3, "1110000") or Support(3, "pin").  \nValid inputs for DOF are 1s and 0s or "pin", "fix", "free" (no capital letters).  
    \nIf more than 7 characters are entered, then only first 7 characters will be considered to define constraint."""
    sups = []
    def __init__(self, node, constraint, group = ""):
        if not isinstance(constraint, str): constraint = str(constraint)
        if constraint == "pin": constraint = "111"
        if constraint == "fix": constraint = "1111111"
        if constraint == "free": constraint = "001"
        if len(constraint) < 7: constraint = constraint + '0' * (7-len(constraint))
        if len(constraint) > 7: constraint = constraint[:7]
        string = ''.join(['1' if char != '0' else '0' for char in constraint])
        self.NODE = node
        self.CONST = string
        self.GROUP = group
        self.ID = len(Support.sups) + 1
        Support.sups.append(self)
    
    @classmethod
    def make_json(cls):
        json = {"Assign":{}}
        ng = []
        for i in Support.sups:
            if i.NODE in Node.ids:
                json["Assign"][i.NODE] = {"ITEMS":
                        [{"ID": i.ID,
                        "CONSTRAINT":i.CONST,
                        "GROUP_NAME": i.GROUP}]
                        }
            if i.NODE not in Node.ids: ng.append(i.NODE)
        if len(ng) > 0: print("These nodes are not defined: ", ng)
        return json
    
    @classmethod
    def create(cls):
        MidasAPI("PUT","/db/cons",Support.make_json())
        
    @classmethod
    def call_json(cls):
        return MidasAPI("GET","/db/cons")
    
    @classmethod
    def update_class(cls):
        a = Support.call_json()
        if a != {'message': ''}:
            if list(a['CONS'].keys()) != []:
                Support.sups = []
                for j in a['CONS'].keys():
                    Support(int(j),a['CONS'][j]['ITEMS'][0]['CONSTRAINT'])
#---------------------------------------------------------------------------------------------------------------

#8 Function to define beam
def Beam(length = 20, x = 0, y = 0, z = 0, h_angle = 0, v_angle = 0, mID = 1, sID = 1, elen = 1, elen_type = "max", b_angle = 0):
    """Length, X, Y, Z ordinates from start of beam, angle to X axis, angle to XY plane, \nmaterial ID, section ID, unit element length, unit elment length type (max or min), beta angle.
    \nSample: Beam(15)"""
    if length > 0 and mID > 0 and sID > 0 and elen > 0:
        a = int(length/elen)
        beam_nodes = []
        if length/a > elen and elen_type == "max": a += 1
        single_elem = length/a
        for i in range(a+1):
            Node(round(x + i * single_elem * mt.cos(mt.radians(h_angle)) * mt.cos(mt.radians(v_angle)),8),
                round(y + i * single_elem * mt.sin(mt.radians(h_angle))* mt.cos(mt.radians(v_angle)),8),
                round(z + i * single_elem * mt.sin(mt.radians(v_angle)),8))
            beam_nodes.append(Node.nodes[-1].ID)
        for i in range(len(beam_nodes)-1):
            Element(beam_nodes[i], beam_nodes[i+1], mID, sID, "BEAM", b_angle)
#---------------------------------------------------------------------------------------------------------------

#9 Function to remove duplicate nodes and elements from Node & Element classes
def remove_duplicate(node_dict="", elem_dict="", tolerance = 0):
    """This functions removes duplicate nodes defined in the Node Class and modifies Element class accordingly.  \nSample: remove_duplicate()"""
    a=[]
    b=[]
    node_json = Node.make_json()
    elem_json = Element.make_json()
    node_di = node_json["Assign"]
    elem_di = elem_json["Assign"]
    if node_dict != "NA":
        for i in list(node_di.keys()):
            for j in list(node_di.keys()):
                if list(node_di.keys()).index(j) > list(node_di.keys()).index(i):
                    if (node_di[i]["X"] >= node_di[j]["X"] - tolerance and node_di[i]["X"] <= node_di[j]["X"] + tolerance):
                        if (node_di[i]["Y"] >= node_di[j]["Y"] - tolerance and node_di[i]["Y"] <= node_di[j]["Y"] + tolerance):
                            if (node_di[i]["Z"] >= node_di[j]["Z"] - tolerance and node_di[i]["Z"] <= node_di[j]["Z"] + tolerance):
                                a.append(i)
                                b.append(j)
        for i in range(len(a)):
            for j in range(len(b)):
                if a[i] == b[j]: 
                    a[i] = a[j]
                    for k in elem_di.keys():
                        for i in range(len(a)):
                            if elem_di[k]['NODE'][0] == b[i]: elem_di[k]['NODE'][0] = a[i]
                            if elem_di[k]['NODE'][1] == b[i]: elem_di[k]['NODE'][1] = a[i]
        if len(b)>0:
            for i in range(len(b)):
                if b[i] in node_di: del node_di[b[i]]
            Node.nodes = []
            Node.ids = []
            for i in node_di.keys():
                Node(node_di[i]['X'], node_di[i]['Y'], node_di[i]['Z'], i)
            Element.elements = []
            Element.ids = []
            for i in elem_di.keys():
                Element(elem_di[i]['NODE'][0], elem_di[i]['NODE'][1], elem_di[i]['MATL'], elem_di[i]['SECT'], elem_di[i]['TYPE'], elem_di[i]['ANGLE'], i)
    if elem_di!="" and elem_dict != "NA": 
        for i in b:
            if len(b)>0:
                for j in list(elem_di.keys()):
                    if elem_di[j]['NODE'][0]==i:
                        elem_di[j]['NODE'][0]=a[b.index(i)]
                    if elem_di[j]['NODE'][1]==i:
                        elem_di[j]['NODE'][1]=a[b.index(i)]
        c=[]
        for i in list(elem_di.keys()):
            for j in list(elem_di.keys()):
                if list(elem_di.keys()).index(j) > list(elem_di.keys()).index(i):
                    if ((elem_di[i]['NODE'][0] == elem_di[j]['NODE'][0] and elem_di[i]['NODE'][1] == elem_di[j]['NODE'][1]) or (elem_di[i]['NODE'][0] == elem_di[j]['NODE'][1] and elem_di[i]['NODE'][1] == elem_di[j]['NODE'][0])):
                        c.append(j)
        if len(c)>0:
            for i in c:
                del elem_di[i]
            Element.elements = []
            Element.ids = []
            for i in elem_di.keys():
                Element(elem_di[i]['NODE'][0], elem_di[i]['NODE'][1], elem_di[i]['MATL'], elem_di[i]['SECT'], elem_di[i]['TYPE'], elem_di[i]['ANGLE'], i)
#---------------------------------------------------------------------------------------------------------------

#10 Class to define DB/User section
class DBSec:
    """Name, d1, d2 to d10 [Optional], Offset[Optional], Shape[Optional], id[Optional].  \nSample DBSec("Rectangle",1,0.5)"""
    sections = []   #List of objects with DB/User section info
    
    def __init__(self, name, d1, d2=0, d3=0, d4=0, d5=0, d6=0, d7=0, d8=0, d9=0, d10=0, shape = "SB", sect = "", db = "", 
                id = 0, offset="CC", center_loc = 0, uor = 0, ho = 0, vo = 0, ho_i = 0, vo_i = 0, cf = [0] * 10, n1 = 0, n2 = 0, ccs = "", sd = True, we = True):
        
        #Assigning the right section ID, considering already defined sections
        if id == 0: section_count = 1
        if len(section_ids) != 0: section_count = max(section_ids) + 1
        if id != 0:
            if id in section_ids and id in [i.ID for i in DBSec.sections]:
                print(f"Section ID {id}, already exists and is now updated with new input.")
                section_count = id
            elif id in section_ids and id not in [i.ID for i in DBSec.sections]:
                section_count = max(section_ids) + 1
                print(f"Section ID {id} already exists.  New ID {section_count} is assigned to the section {name}.")
            else:
                section_count = id
        
        self.NAME = name
        self.D1 = d1
        self.D2 = d2
        self.D3 = d3
        self.D4 = d4
        self.D5 = d5
        self.D6 = d6
        self.D7 = d7
        self.D8 = d8
        self.D9 = d9
        self.D10 = d10
        self.OFFSET = offset
        self.CL = center_loc
        self.SHAPE = shape
        self.SEC = sect
        self.DB = db
        self.ID = section_count
        self.UOR = uor
        self.HO = ho
        self.VO = vo
        self.HOI = ho_i
        self.VOI = vo_i
        self.CF = cf
        self.N1 = n1
        self.N2 = n2
        self.CCS = ccs
        self.SD = sd
        self.WE = we
        DBSec.sections.append(self)             #Adding this section info object to the list
        section_ids.append(int(section_count))       #Adding this section ID to the global list
        
    @classmethod
    def make_json(cls):
        json = {"Assign":{}}
        for k in cls.sections:
            json["Assign"][k.ID] = {
                "SECTTYPE": "DBUSER",
                "SECT_NAME": k.NAME,
                "SECT_BEFORE": {
                "OFFSET_PT": k.OFFSET,
                "OFFSET_CENTER": k.CL,
                "USER_OFFSET_REF": k.UOR,
                "HORZ_OFFSET_OPT": k.HO,
                "USERDEF_OFFSET_YI": k.HOI,
                "VERT_OFFSET_OPT": k.VO,
                "USERDEF_OFFSET_ZI": k.VOI,
                "USE_SHEAR_DEFORM": k.SD,
                "USE_WARPING_EFFECT": k.WE,
                "SHAPE": k.SHAPE}}
            if k.SEC != "" and k.DB != "":      #Use Section ID and DB data if defined
                json["Assign"][k.ID]["SECT_BEFORE"]["DATATYPE"] = 1
                json["Assign"][k.ID]["SECT_BEFORE"]["SECT_I"] = {
                    "DB_NAME": k.DB,
                    "SECT_NAME": k.SEC
                }
            else:                               #Generic definition if section ID & DB are not defined.
                json["Assign"][k.ID]["SECT_BEFORE"]["DATATYPE"] = 2
                json["Assign"][k.ID]["SECT_BEFORE"]["SECT_I"] = {
                "vSIZE": [k.D1, k.D2, k.D3, k.D4, k.D5, k.D6, k.D7, k.D8, k.D9, k.D10]
                    }
            if k.SHAPE == "CC" or k.SHAPE == "Z" or k.SHAPE == "UP":    #Additional info for Cold Formed sections
                json["Assign"][k.ID]["SECT_BEFORE"]["SECT_I"]["CF_STIFF_ULS"] = {
                    "A_EFF": k.CF[0],
                    "A_NET": k.CF[1],
                    "LY_EFF": k.CF[2],
                    "LZ_EFF": k.CF[3],
                    "WY_EFF": k.CF[4],
                    "WZ_EFF": k.CF[5],
                    "LT_EFF": k.CF[6],
                    "LW_EFF": k.CF[7],
                    "RY_EFF": k.CF[8],
                    "RZ_EFF": k.CF[9]
                }
            if k.SHAPE == "CC": json["Assign"][k.ID]["SECT_BEFORE"]["SECT_I"]['SHAPE'] = k.CCS  #Additional infor for cold formed Channels
            if k.SHAPE == "BSTF":       #Additional info for box with stiffener
                json["Assign"][k.ID]["SECT_BEFORE"]["CELL_SHAPE"] = k.N1
                json["Assign"][k.ID]["SECT_BEFORE"]["CELL_TYPE"] = k.N2
            elif k.SHAPE == "PSTF":     #Additional info for pipe with stiffener
                json["Assign"][k.ID]["SECT_BEFORE"]["CELL_SHAPE"] = k.N1
        return json
    
    @classmethod
    def create(cls):
        MidasAPI("PUT","/db/sect",DBSec.make_json())
        
    @classmethod
    def call_json(cls):
        return MidasAPI("GET","/db/sect")
    
    @classmethod
    def update_class(cls):
        a = DBSec.call_json()
        if a != {'message': ''}:
            b = []
            for i in list(a['SECT'].keys()):
                if a['SECT'][i]['SECTTYPE'] == 'DBUSER': b.append(int(i))
            global section_ids
            section_ids = [i for i in section_ids if i not in [int(j) for j in b]]
            DBSec.sections = []
            cfsh = ["CC", "Z", "UP"]
            stfsh = ["BSTF", "PSTF"]
            for k, v in a['SECT'].items():
                if v["SECTTYPE"] == "DBUSER":
                    shp = v['SECT_BEFORE']['SHAPE']
                    if shp not in cfsh and shp not in stfsh:
                        if v['SECT_BEFORE']['DATATYPE'] == 2:
                            DBSec(v['SECT_NAME'], v['SECT_BEFORE']['SECT_I']['vSIZE'][0], v['SECT_BEFORE']['SECT_I']['vSIZE'][1],
                                v['SECT_BEFORE']['SECT_I']['vSIZE'][2], v['SECT_BEFORE']['SECT_I']['vSIZE'][3],
                                v['SECT_BEFORE']['SECT_I']['vSIZE'][4], v['SECT_BEFORE']['SECT_I']['vSIZE'][5],
                                v['SECT_BEFORE']['SECT_I']['vSIZE'][6], v['SECT_BEFORE']['SECT_I']['vSIZE'][7],
                                v['SECT_BEFORE']['SECT_I']['vSIZE'][8], v['SECT_BEFORE']['SECT_I']['vSIZE'][9],
                                v['SECT_BEFORE']['SHAPE'], "", "", k, v['SECT_BEFORE']['OFFSET_PT'], v['SECT_BEFORE']['OFFSET_CENTER'],
                                v['SECT_BEFORE']['USER_OFFSET_REF'], v['SECT_BEFORE']['HORZ_OFFSET_OPT'], v['SECT_BEFORE']['VERT_OFFSET_OPT'],
                                v['SECT_BEFORE']['USERDEF_OFFSET_YI'], v['SECT_BEFORE']['USERDEF_OFFSET_ZI'],
                                sd = v['SECT_BEFORE']['USE_SHEAR_DEFORM'], we = v['SECT_BEFORE']['USE_WARPING_EFFECT'])
                        elif v['SECT_BEFORE']['DATATYPE'] == 1:
                            DBSec(v['SECT_NAME'], 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, v['SECT_BEFORE']['SHAPE'], 
                                v['SECT_BEFORE']['SECT_I']['SECT_NAME'], v['SECT_BEFORE']['SECT_I']['DB_NAME'], 
                                k, v['SECT_BEFORE']['OFFSET_PT'], v['SECT_BEFORE']['OFFSET_CENTER'], v['SECT_BEFORE']['USER_OFFSET_REF'], 
                                v['SECT_BEFORE']['HORZ_OFFSET_OPT'], v['SECT_BEFORE']['VERT_OFFSET_OPT'],
                                v['SECT_BEFORE']['USERDEF_OFFSET_YI'], v['SECT_BEFORE']['USERDEF_OFFSET_ZI'],
                                sd = v['SECT_BEFORE']['USE_SHEAR_DEFORM'], we = v['SECT_BEFORE']['USE_WARPING_EFFECT'])
                    elif shp in cfsh and shp != "CC":
                        if v['SECT_BEFORE']['DATATYPE'] == 2:
                            DBSec(v['SECT_NAME'], v['SECT_BEFORE']['SECT_I']['vSIZE'][0], v['SECT_BEFORE']['SECT_I']['vSIZE'][1],
                                v['SECT_BEFORE']['SECT_I']['vSIZE'][2], v['SECT_BEFORE']['SECT_I']['vSIZE'][3],
                                v['SECT_BEFORE']['SECT_I']['vSIZE'][4], v['SECT_BEFORE']['SECT_I']['vSIZE'][5],
                                v['SECT_BEFORE']['SECT_I']['vSIZE'][6], v['SECT_BEFORE']['SECT_I']['vSIZE'][7],
                                v['SECT_BEFORE']['SECT_I']['vSIZE'][8], v['SECT_BEFORE']['SECT_I']['vSIZE'][9],
                                v['SECT_BEFORE']['SHAPE'], "", "", k, v['SECT_BEFORE']['OFFSET_PT'], v['SECT_BEFORE']['OFFSET_CENTER'], 
                                v['SECT_BEFORE']['USER_OFFSET_REF'], v['SECT_BEFORE']['HORZ_OFFSET_OPT'], v['SECT_BEFORE']['VERT_OFFSET_OPT'],
                                v['SECT_BEFORE']['USERDEF_OFFSET_YI'], v['SECT_BEFORE']['USERDEF_OFFSET_ZI'],
                                [v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['A_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['A_NET'],
                                v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['LY_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['LZ_EFF'],
                                v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['WY_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['WZ_EFF'],
                                v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['LT_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['LW_EFF'],
                                v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['RY_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['RZ_EFF']],
                                sd = v['SECT_BEFORE']['USE_SHEAR_DEFORM'], we = v['SECT_BEFORE']['USE_WARPING_EFFECT'])
                        elif v['SECT_BEFORE']['DATATYPE'] == 1:
                            DBSec(v['SECT_NAME'], 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                v['SECT_BEFORE']['SHAPE'], v['SECT_BEFORE']['SECT_I']['SECT_NAME'], v['SECT_BEFORE']['SECT_I']['DB_NAME'],
                                k, v['SECT_BEFORE']['OFFSET_PT'], v['SECT_BEFORE']['OFFSET_CENTER'], v['SECT_BEFORE']['USER_OFFSET_REF'], 
                                v['SECT_BEFORE']['HORZ_OFFSET_OPT'], v['SECT_BEFORE']['VERT_OFFSET_OPT'],
                                v['SECT_BEFORE']['USERDEF_OFFSET_YI'], v['SECT_BEFORE']['USERDEF_OFFSET_ZI'],
                                [v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['A_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['A_NET'],
                                v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['LY_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['LZ_EFF'],
                                v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['WY_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['WZ_EFF'],
                                v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['LT_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['LW_EFF'],
                                v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['RY_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['RZ_EFF']],
                                sd = v['SECT_BEFORE']['USE_SHEAR_DEFORM'], we = v['SECT_BEFORE']['USE_WARPING_EFFECT'])
                    elif shp in cfsh and shp == "CC":
                        if v['SECT_BEFORE']['DATATYPE'] == 2:
                            DBSec(v['SECT_NAME'], v['SECT_BEFORE']['SECT_I']['vSIZE'][0], v['SECT_BEFORE']['SECT_I']['vSIZE'][1],
                                v['SECT_BEFORE']['SECT_I']['vSIZE'][2], v['SECT_BEFORE']['SECT_I']['vSIZE'][3],
                                v['SECT_BEFORE']['SECT_I']['vSIZE'][4], v['SECT_BEFORE']['SECT_I']['vSIZE'][5],
                                v['SECT_BEFORE']['SECT_I']['vSIZE'][6], v['SECT_BEFORE']['SECT_I']['vSIZE'][7],
                                v['SECT_BEFORE']['SECT_I']['vSIZE'][8], v['SECT_BEFORE']['SECT_I']['vSIZE'][9],
                                v['SECT_BEFORE']['SHAPE'], "", "", k, v['SECT_BEFORE']['OFFSET_PT'], v['SECT_BEFORE']['OFFSET_CENTER'], 
                                v['SECT_BEFORE']['USER_OFFSET_REF'], v['SECT_BEFORE']['HORZ_OFFSET_OPT'], v['SECT_BEFORE']['VERT_OFFSET_OPT'],
                                v['SECT_BEFORE']['USERDEF_OFFSET_YI'], v['SECT_BEFORE']['USERDEF_OFFSET_ZI'],
                                [v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['A_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['A_NET'],
                                v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['LY_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['LZ_EFF'],
                                v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['WY_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['WZ_EFF'],
                                v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['LT_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['LW_EFF'],
                                v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['RY_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['RZ_EFF']],
                                0, 0, v['SECT_BEFORE']['SECT_I']['SHAPE'], sd = v['SECT_BEFORE']['USE_SHEAR_DEFORM'], we = v['SECT_BEFORE']['USE_WARPING_EFFECT'])
                        elif v['SECT_BEFORE']['DATATYPE'] == 1:
                            DBSec(v['SECT_NAME'], 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, v['SECT_BEFORE']['SHAPE'], 
                                v['SECT_BEFORE']['SECT_I']['SECT_NAME'], v['SECT_BEFORE']['SECT_I']['DB_NAME'], 
                                k, v['SECT_BEFORE']['OFFSET_PT'], v['SECT_BEFORE']['OFFSET_CENTER'], v['SECT_BEFORE']['USER_OFFSET_REF'], 
                                v['SECT_BEFORE']['HORZ_OFFSET_OPT'], v['SECT_BEFORE']['VERT_OFFSET_OPT'],
                                v['SECT_BEFORE']['USERDEF_OFFSET_YI'], v['SECT_BEFORE']['USERDEF_OFFSET_ZI'],
                                [v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['A_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['A_NET'],
                                v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['LY_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['LZ_EFF'],
                                v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['WY_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['WZ_EFF'],
                                v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['LT_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['LW_EFF'],
                                v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['RY_EFF'], v['SECT_BEFORE']['SECT_I']['CF_STIFF_ULS']['RZ_EFF']],
                                0, 0, v['SECT_BEFORE']['SECT_I']['SHAPE'], sd = v['SECT_BEFORE']['USE_SHEAR_DEFORM'], we = v['SECT_BEFORE']['USE_WARPING_EFFECT'])
                    elif shp == "BSTF":
                        DBSec(v['SECT_NAME'], v['SECT_BEFORE']['SECT_I']['vSIZE'][0], v['SECT_BEFORE']['SECT_I']['vSIZE'][1],
                            v['SECT_BEFORE']['SECT_I']['vSIZE'][2], v['SECT_BEFORE']['SECT_I']['vSIZE'][3],
                            v['SECT_BEFORE']['SECT_I']['vSIZE'][4], v['SECT_BEFORE']['SECT_I']['vSIZE'][5],
                            v['SECT_BEFORE']['SECT_I']['vSIZE'][6], v['SECT_BEFORE']['SECT_I']['vSIZE'][7],
                            v['SECT_BEFORE']['SECT_I']['vSIZE'][8], v['SECT_BEFORE']['SECT_I']['vSIZE'][9],
                            v['SECT_BEFORE']['SHAPE'], "", "", k, v['SECT_BEFORE']['OFFSET_PT'], v['SECT_BEFORE']['OFFSET_CENTER'], 
                            v['SECT_BEFORE']['USER_OFFSET_REF'], v['SECT_BEFORE']['HORZ_OFFSET_OPT'], v['SECT_BEFORE']['VERT_OFFSET_OPT'],
                            v['SECT_BEFORE']['USERDEF_OFFSET_YI'], v['SECT_BEFORE']['USERDEF_OFFSET_ZI'], [0]*10,
                            v['SECT_BEFORE']['CELL_SHAPE'], v['SECT_BEFORE']['CELL_TYPE'],
                            sd = v['SECT_BEFORE']['USE_SHEAR_DEFORM'], we = v['SECT_BEFORE']['USE_WARPING_EFFECT'])
                    elif shp == "PSTF":
                        DBSec(v['SECT_NAME'], v['SECT_BEFORE']['SECT_I']['vSIZE'][0], v['SECT_BEFORE']['SECT_I']['vSIZE'][1],
                            v['SECT_BEFORE']['SECT_I']['vSIZE'][2], v['SECT_BEFORE']['SECT_I']['vSIZE'][3],
                            v['SECT_BEFORE']['SECT_I']['vSIZE'][4], v['SECT_BEFORE']['SECT_I']['vSIZE'][5],
                            v['SECT_BEFORE']['SECT_I']['vSIZE'][6], v['SECT_BEFORE']['SECT_I']['vSIZE'][7],
                            v['SECT_BEFORE']['SECT_I']['vSIZE'][8], v['SECT_BEFORE']['SECT_I']['vSIZE'][9],
                            v['SECT_BEFORE']['SHAPE'], "", "", k, v['SECT_BEFORE']['OFFSET_PT'], v['SECT_BEFORE']['OFFSET_CENTER'], 
                            v['SECT_BEFORE']['USER_OFFSET_REF'], v['SECT_BEFORE']['HORZ_OFFSET_OPT'], v['SECT_BEFORE']['VERT_OFFSET_OPT'],
                            v['SECT_BEFORE']['USERDEF_OFFSET_YI'], v['SECT_BEFORE']['USERDEF_OFFSET_ZI'], [0]*10,
                            v['SECT_BEFORE']['CELL_SHAPE'], sd = v['SECT_BEFORE']['USE_SHEAR_DEFORM'], we = v['SECT_BEFORE']['USE_WARPING_EFFECT'])
#---------------------------------------------------------------------------------------------------------------

#11 Class to define Load Cases:
class Load_Case:
    """Type symbol (Refer Static Load Case section in the Onine API Manual, Load Case names.  
    \nSample: Load_Case("USER", "Case 1", "Case 2", ..., "Case n")"""
    cases = []
    types = ["USER", "D", "DC", "DW", "DD", "EP", "EANN", "EANC", "EAMN", "EAMC", "EPNN", "EPNC", "EPMN", "EPMC", "EH", "EV", "ES", "EL", "LS", "LSC", 
            "L", "LC", "LP", "IL", "ILP", "CF", "BRK", "BK", "CRL", "PS", "B", "WP", "FP", "SF", "WPR", "W", "WL", "STL", "CR", "SH", "T", "TPG", "CO",
            "CT", "CV", "E", "FR", "IP", "CS", "ER", "RS", "GE", "LR", "S", "R", "LF", "RF", "GD", "SHV", "DRL", "WA", "WT", "EVT", "EEP", "EX", "I", "EE"]
    def __init__(self, type, *name):
        self.TYPE = type
        self.NAME = name
        self.ID = []
        for i in range(len(self.NAME)):
            if Load_Case.cases == []: self.ID.append(i+1)
            if Load_Case.cases != []: self.ID.append(max(Load_Case.cases[-1].ID) + i + 1)
        Load_Case.cases.append(self)
    
    @classmethod
    def make_json(cls):
        ng = []
        json = {"Assign":{}}
        for i in Load_Case.cases:
            if i.TYPE in Load_Case.types:
                for j in i.ID:
                    json['Assign'][j] = {
                        "NAME": i.NAME[i.ID.index(j)],
                        "TYPE": i.TYPE}
            else:
                ng.append(i.TYPE)
        if ng != []: print(f"These load case types are incorrect: {ng}.\nPlease check API Manual.")
        return json
    
    @classmethod
    def create(cls):
        MidasAPI("PUT","/db/stld",Load_Case.make_json())
        
    @classmethod
    def call_json(cls):
        return MidasAPI("GET","/db/stld")
    
    @classmethod
    def update_class(cls):
        a = Load_Case.call_json()
        if a != {'message': ''}:
            if list(a['STLD'].keys()) != []:
                Load_Case.cases = []
                for j in a['STLD'].keys():
                    Load_Case(a['STLD'][j]['TYPE'], a['STLD'][j]['NAME'])
#---------------------------------------------------------------------------------------------------------------

#12 Class to define & update Structure Groups, Boundary Groups, Load Groups & Tendon Groups:
class Group:
    groups = []
    def __init__(self, type = "S", *name, **kwargs):
        """Type ("S" for structure, "B" for boundary, "L" for load & "T" for tendon), name, \nelement list (if applicable), node list (if applicable), autotype (if applicable)\n
        Sample:  Group("S", "Girder", "Slab", elist=[[1,2,...50],[51, 52,....100]], nlist = [[1,2,....,51],[]])"""
        if type == "S" or type == "B" or type == "L" or type == "T":
            self.TYPE = type
            self.NAME = name
            self.ID = []
            for i in range(len(self.NAME)):
                if Group.groups == []: self.ID.append(i+1)
                if Group.groups != []: self.ID.append(max(Group.groups[-1].ID) + i + 1)
            if type == "S":
                self.ELIST = kwargs.get('elist', [[]])
                self.NLIST = kwargs.get('nlist', [[]])
            if type == "B":
                self.AUTOTYPE = kwargs.get('autotype', 0)
            Group.groups.append(self)
    
    @classmethod
    def update_SG(cls, name, elist = [[]], nlist = [[]], operation = "add"):
        """Group name, element list, node list, operation ("add" or "replace").\n
        Sample:  update_SG("Girder", [1,2,...20],[],"replace")"""
        up = 0
        for i in Group.groups:
            if i.TYPE == "S":
                for j in range(len(i.NAME)):
                    if name == i.NAME[j]:
                        up = 1
                        if operation == "replace":
                            i.ELIST[j] = elist
                            i.NLIST[j] = nlist
                        if operation == "add":
                            for k in range(len(elist[0])):
                                if elist[0][k] not in i.ELIST[j]: i.ELIST[j].append(elist[0][k])
                            if nlist != [[]]:
                                for l in range(len(nlist)):
                                    if nlist[0][l] not in i.NLIST[j]: i.NLIST[j].append(nlist[0][l])
        if up == 0: print(f"Structure group {name} is not defined!")
    
    @classmethod
    def make_json_SG(cls):
        "Generates the json file for all defined structure groups."
        json = {"Assign":{}}
        for i in Group.groups:
            if i.TYPE == "S":
                for j in range(len(i.NAME)):
                    json["Assign"][i.ID[j]] = {
                        "NAME": i.NAME[j],
                        "P_TYPE": 0,
                        "N_LIST": i.NLIST[j],
                        "E_LIST": i.ELIST[j]
                    }
        return json
    
    @classmethod
    def create_SG(cls):
        MidasAPI("PUT","/db/GRUP",Group.make_json_SG())
        
    @classmethod
    def call_json_SG(cls):
        return MidasAPI("GET","/db/GRUP")
    
    @classmethod
    def update_BG(cls, name, autotype = 0):
        """Update the Auto Type of boundary group."""
        up = 0
        for i in Group.groups:
            if i.TYPE == "B":
                for j in range(len(i.NAME)):
                    if name == i.NAME[j]:
                        up = 1
                        i.AUTOTYPE = autotype
        if up == 0: print(f"Boundary group {name} is not defined!")
    
    @classmethod
    def make_json_BG(cls):
        "Generate the json file for all defined boundary groups."
        json = {"Assign":{}}
        for i in Group.groups:
            if i.TYPE == "B":
                for j in range(len(i.NAME)):
                    json["Assign"][i.ID[j]] = {
                        "NAME": i.NAME[j],
                        "AUTOTYPE": i.AUTOTYPE
                    }
        return json
    
    @classmethod
    def create_BG(cls):
        MidasAPI("PUT","/db/BNGR",Group.make_json_BG())
        
    @classmethod
    def call_json_BG(cls):
        return MidasAPI("GET","/db/BNGR")
    
    @classmethod
    def make_json_LG(cls, gr = "L"):
        """Generate the json file for all defined load groups."""
        json = {"Assign":{}}
        for i in Group.groups:
            if i.TYPE == gr:
                for j in range(len(i.NAME)):
                    json["Assign"][i.ID[j]] = {
                        "NAME": i.NAME[j]
                    }
        return json
    
    @classmethod
    def create_LG(cls):
        MidasAPI("PUT","/db/LDGR",Group.make_json_LG())
        
    @classmethod
    def call_json_LG(cls):
        return MidasAPI("GET","/db/LDGR")
    
    @classmethod
    def make_json_TG(cls):
        """Generate the json file for all defined tendon groups."""
        return(Group.make_json_LG(gr = "T"))
    
    @classmethod
    def create_TG(cls):
        MidasAPI("PUT","/db/TDGR",Group.make_json_TG())
        
    @classmethod
    def call_json_TG(cls):
        return MidasAPI("GET","/db/TDGR")
    
    @classmethod
    def update_class(cls):
        a = Group.call_json_SG()
        b = Group.call_json_BG()
        c = Group.call_json_LG()
        d = Group.call_json_TG()
        if a != {'message': ''} or b != {'message': ''} or c != {'message': ''} or d != {'message': ''}:
            Group.groups = []
            if 'GRUP' in list(a.keys()):
                if list(a['GRUP'].keys()) != []:
                    for j in a['GRUP'].keys():
                        if 'E_LIST' in list(a['GRUP'][j].keys()) and 'N_LIST' in list(a['GRUP'][j].keys()):
                            Group("S", a['GRUP'][j]['NAME'],elist = [a['GRUP'][j]['E_LIST']], nlist = [a['GRUP'][j]['N_LIST']])
                        elif 'E_LIST' in list(a['GRUP'][j].keys()):
                            Group("S", a['GRUP'][j]['NAME'],elist = [a['GRUP'][j]['E_LIST']], nlist = [[]])
                        elif 'N_LIST' in list(a['GRUP'][j].keys()):
                            Group("S", a['GRUP'][j]['NAME'],elist = [[]], nlist = [a['GRUP'][j]['N_LIST']])
                        else:
                            Group("S", a['GRUP'][j]['NAME'],elist = [[]], nlist = [[]])
            if 'BNGR' in list(b.keys()):
                if list(b['BNGR'].keys()) != []:
                    for j in b['BNGR'].keys():
                        Group("B", b['BNGR'][j]['NAME'], autotype = b['BNGR'][j]['AUTOTYPE'])
            if 'LDGR' in list(c.keys()):
                if list(c['LDGR'].keys()) != []:
                    for j in c['LDGR'].keys():
                        Group("L", c['LDGR'][j]['NAME'])
            if 'TDGR' in list(d.keys()):
                if list(d['TDGR'].keys()) != []:
                    for j in d['TDGR'].keys():
                        Group("T", d['TDGR'][j]['NAME'])
#---------------------------------------------------------------------------------------------------------------

#13 Function to create/call model:
def create_model(request = "update", set = 1, force = "KN", length = "M", heat = "BTU", temp = "C"):
    """request["update" to update a model, "call" to get details of existing model], \nforce[Optional], length[Optional], heat[Optional], temp[Optional].  
    \nSample: model() to update/create model. model("call") to get details of existing model and update classes.\n
    set = 1 => Functions that don't need to call data from connected model file.\n
    set = 2 => Functions that may need to call data from connected model file."""
    units(force, length, heat, temp)
    if MAPI_KEY.data == []:  print(f"Enter the MAPI key using the MAPI_KEY command.")
    if MAPI_KEY.data != []:
        if set == 1:
            if request == "update" or request == "create" or request == "PUT":
                if Node.make_json() != {"Assign":{}}: Node.create()
                if Element.make_json() != {"Assign":{}}: Element.create()
                if DBSec.make_json() != {"Assign":{}}: DBSec.create()
                if Group.make_json_BG() != {"Assign":{}}: Group.create_BG()
                if Group.make_json_LG() != {"Assign":{}}: Group.create_LG()
                if Group.make_json_TG() != {"Assign":{}}: Group.create_TG()
                if Material.make_json() != {"Assign":{}}: Material.create()
                if Load_Case.make_json() != {"Assign":{}}: Load_Case.create()
                if Load_SW.make_json() != {"Assign":{}}: Load_SW.create()
                if Load_Node.make_json() != {"Assign":{}}: Load_Node.create()
                if Load_Element.make_json() != {"Assign":{}}: Load_Element.create()
            if request == "call" or request == "GET":
                Node.update_class()
                Element.update_class()
                DBSec.update_class()
                Load_Case.update_class()
                Group.update_class()
                Material.update_class()
                Load_SW.update_class()
                Load_Node.update_class()
                Load_Element.update_class()
        if set == 2:
            if request == "update" or request == "create" or request == "PUT":
                if Node.make_json() != {"Assign":{}}: Node.create()
                if Element.make_json() != {"Assign":{}}: Element.create()
                if DBSec.make_json() != {"Assign":{}}: DBSec.create()
                if Group.make_json_BG() != {"Assign":{}}: Group.create_BG()
                if Group.make_json_LG() != {"Assign":{}}: Group.create_LG()
                if Group.make_json_TG() != {"Assign":{}}: Group.create_TG()
                if Material.make_json() != {"Assign":{}}: Material.create()
                if Group.make_json_SG() != {"Assign":{}}: Group.create_SG()
                if Support.make_json() != {"Assign":{}}: Support.create()
                if Load_Case.make_json() != {"Assign":{}}: Load_Case.create()
                if Load_SW.make_json() != {"Assign":{}}: Load_SW.create()
                if Load_Node.make_json() != {"Assign":{}}: Load_Node.create()
                if Load_Element.make_json() != {"Assign":{}}: Load_Element.create()
            if request == "call" or request == "GET": 
                Node.update_class()
                Element.update_class()
                DBSec.update_class()
                Group.update_class()
                Load_Case.update_class()
                Material.update_class()
                Support.update_class()
                Load_SW.update_class()
                Load_Node.update_class()
                Load_Element.update_class()
#---------------------------------------------------------------------------------------------------------------

#14 Function to select nodes/elements in a defined model along the axis or global planes
def get_select(crit_1 = "X", crit_2 = 0, crit_3 = 0, st = 'a', en = 'a', tolerance = 0, no = "", el = ""):
    """Get list of nodes/elements as required.\n
    crit_1 (=> Along: "X", "Y", "Z". OR, IN: "XY", "YZ", "ZX". OR "USM"),\n
    crit_2 (=> With Ordinate value: Y value, X value, X Value, Z value, X value, Y value. OR Material ID),\n
    crit_3 (=> At Ordinate 2 value: Z value, Z value, Y value, 0, 0, 0. OR Section ID),\n
    starting ordinate, end ordinate, tolerance, node dictionary, element dictionary.\n
    Sample:  get_select("Y", 0, 2) for selecting all nodes and elements parallel Y axis with X ordinate as 0 and Z ordinate as 2."""
    output = {'NODE':[], 'ELEM':[]}
    ok = 0
    if no == "": no = Node.make_json()
    if el == "": el = Element.make_json()
    if crit_1 == "USM":
        materials = Material.make_json()
        sections = DBSec.make_json()
        elements = el
        k = list(elements.keys())[0]
        mat_nos = list((materials["Assign"].keys()))
        sect_nos = list((sections["Assign"].keys()))
        elem = {}
        for m in mat_nos:
            elem[int(m)] = {}
            for s in sect_nos:
                    elem[int(m)][int(s)] = []
        for e in elements[k].keys(): elem[((elements[k][e]['MATL']))][((elements[k][e]['SECT']))].append(int(e))
        output['ELEM'] = elem[crit_2][crit_3]
        ok = 1
    elif no != "" and el != "":
        n_key = list(no.keys())[0]
        e_key = list(el.keys())[0]
        if n_key == "Assign": no["Assign"] = {str(key):value for key,value in no["Assign"].items()}
        if e_key == "Assign": el["Assign"] = {str(key):value for key,value in el["Assign"].items()}
        if crit_1 == "X": 
            cr2 = "Y"
            cr3 = "Z"
            ok = 1
        if crit_1 == "Y": 
            cr2 = "X"
            cr3 = "Z"
            ok = 1
        if crit_1 == "Z": 
            cr2 = "X"
            cr3 = "Y"
            ok = 1
        if crit_1 == "XY" or crit_1 == "YX":
            cr2 = "Z"
            ok = 1
        if crit_1 == "YZ" or crit_1 == "ZY":
            cr2 = "X"
            ok = 1
        if crit_1 == "ZX" or crit_1 == "XZ":
            cr2 = "Y"
            ok = 1
        if len(crit_1) == 1 and ok == 1:
            if st == 'a': st = min([v[crit_1] for v in no[n_key].values()])
            if en == 'a': en = max([v[crit_1] for v in no[n_key].values()])
            for n in no[n_key].keys():
                curr = no[n_key][n]
                if curr[cr2] >= crit_2 - tolerance and curr[cr2] <= crit_2 + tolerance:
                    if curr[cr3] >= crit_3 - tolerance and curr[cr3] <= crit_3 + tolerance:
                        if curr[crit_1] >= st and curr[crit_1] <= en: output['NODE'].append(int(n))
            for e in el[e_key].keys():
                curr_0 = no[n_key][str(el[e_key][e]['NODE'][0])]
                curr_1 = no[n_key][str(el[e_key][e]['NODE'][1])]
                if curr_0[cr2] == curr_1[cr2] and curr_0[cr3] == curr_1[cr3]:
                    if curr_0[cr2] >= crit_2 - tolerance and curr_0[cr2] <= crit_2 + tolerance:
                        if curr_0[cr3] >= crit_3 - tolerance and curr_0[cr3] <= crit_3 + tolerance:
                            if curr_1[cr2] >= crit_2 - tolerance and curr_1[cr2] <= crit_2 + tolerance:
                                if curr_1[cr3] >= crit_3 - tolerance and curr_1[cr3] <= crit_3 + tolerance:
                                    if curr_0[crit_1] >= st and curr_0[crit_1] <= en and curr_1[crit_1] >= st and curr_1[crit_1] <= en:
                                        output['ELEM'].append(int(e))
        if len(crit_1) == 2 and ok == 1:
            if st == 'a': st = min(min([v[crit_1[0]] for v in no[n_key].values()]), min([v[crit_1[1]] for v in no[n_key].values()]))
            if en == 'a': en = max(max([v[crit_1[0]] for v in no[n_key].values()]), max([v[crit_1[1]] for v in no[n_key].values()]))
            for n in no[n_key].keys():
                curr = no[n_key][n]
                if curr[cr2] >= crit_2 - tolerance and curr[cr2] <= crit_2 + tolerance:
                    if curr[crit_1[0]] >= st and curr[crit_1[1]] >= st and curr[crit_1[0]] <= en and curr[crit_1[1]] <= en: output['NODE'].append(int(n))
            for e in el[e_key].keys():
                curr_0 = no[n_key][str(el[e_key][e]['NODE'][0])]
                curr_1 = no[n_key][str(el[e_key][e]['NODE'][1])]
                if curr_0[cr2] == curr_1[cr2]:
                    if curr_0[cr2] >= crit_2 - tolerance and curr_0[cr2] <= crit_2 + tolerance:
                        if curr_1[cr2] >= crit_2 - tolerance and curr_1[cr2] <= crit_2 + tolerance:
                            if curr_0[crit_1[0]] >= st and curr_0[crit_1[0]] <= en and curr_1[crit_1[0]] >= st and curr_1[crit_1[0]] <= en:
                                if curr_0[crit_1[1]] >= st and curr_0[crit_1[1]] <= en and curr_1[crit_1[1]] >= st and curr_1[crit_1[1]] <= en:
                                    output['ELEM'].append(int(e))
    if ok != 1: output = "Incorrect input.  Please check the syntax!"
    return output
#---------------------------------------------------------------------------------------------------------------

#15 Class to define userdefined material property
class Material:
    """Name, Type, density, damping, E, force unit, length unit, heat unit, temperature unit.\n
    Sample: Material("Deck_con", E = 28000) to define concrete."""
    materials = []
    def __init__(self, name, des_type = "CONC", specific_heat = 0, conduction = 0, plastic_id = 0, plastic_name = "", use_mass_dens = False, damping = 0.05,
                density_1 = 25, E_1 = 30_000_000, thermal_1 = 1.2e-5, poisson_1 = 0.2, standard_1 = "", db_1 = "", mass_1 = 0,
                density_2 = 0, E_2 = 0, thermal_2 = 0, poisson_2 = 0, standard_2 = "", db_2 = "", mass_2 = 0, 
                E_3 = 0, thermal_3 = 0, poisson_3 = 0, shear_1 = 0, shear_2 = 0, shear_3 = 0, id = None):
        self.NAME = name
        self.TYPE = des_type
        self.SPH = specific_heat
        self.CON = conduction
        self.PID = plastic_id
        self.PNM = plastic_name
        self.UMD = use_mass_dens
        self.DAMP = damping
        self.DENS1 = density_1
        self.E1 = E_1
        self.TH1 = thermal_1
        self.PSN1 = poisson_1
        self.STD1 = standard_1
        self.DB1 = db_1
        self.MAS1 = mass_1
        self.DENS2 = density_2
        self.E2 = E_2
        self.TH2 = thermal_2
        self.PSN2 = poisson_2
        self.STD2 = standard_2
        self.DB2 = db_2
        self.MAS2 = mass_2
        self.E3 = E_3
        self.TH3 = thermal_3
        self.PSN3 = poisson_3
        self.SH1 = shear_1
        self.SH2 = shear_2
        self.SH3 = shear_3
        self.PTYP1 = 0
        self.PTYP2 = 0
        if id == None: id = 1
        if len(Material.materials) >= 1 and id!= None:
            ids = [i.ID for i in Material.materials]
            if id in ids: id = max(ids) + 1
        self.ID = id
        Material.materials.append(self)
    
    @classmethod
    def make_json(cls):
        json = {"Assign":{}}
        for i in Material.materials:
            data_1 = {}
            if i.E3 != 0: 
                i.PTYP1 = 3
                data_1 = {"P_TYPE": i.PTYP1,
                "ELAST_M": [i.E1, i.E2, i.E3],
                "POISN_M": [i.PSN1, i.PSN2, i.PSN3],
                "THERMAL_M": [i.TH1, i.TH2, i.TH3],
                "SHEAR_M": [i.SH1, i.SH2, i.SH3],
                "DEN": i.DENS1,
                "MASS": i.MAS1}
            elif i.STD1 != "" and i.DB1 != "": 
                i.PTYP1 = 1
                data_1 = {"P_TYPE": i.PTYP1,
                "STANDARD": i.STD1,
                "CODE": "",
                "DB": i.DB1}
            elif i.E1 != 0 or i.PSN1 != 0 or i.TH1 != 0 or i.DENS1 != 0 or i.MAS1 != 0:
                i.PTYP1 = 2
                data_1 = {"P_TYPE": i.PTYP1,
                    "ELAST": i.E1,
                    "POISN": i.PSN1,
                    "THERMAL": i.TH1,
                    "DEN": i.DENS1,
                    "MASS": i.MAS1}
            data_2 = {}
            if i.STD2 != "" and i.DB2 != "": 
                i.PTYP2 = 1
                data_2 = {"P_TYPE": i.PTYP2,
                "STANDARD": i.STD2,
                "CODE": "",
                "DB": i.DB2}
            elif i.E2 != 0 or i.PSN2 != 0 or i.TH2 != 0 or i.DENS2 != 0 or i.MAS2 != 0:
                i.PTYP2 = 2
                data_2 = {"P_TYPE": i.PTYP2,
                "ELAST": i.E2,
                "POISN": i.PSN2,
                "THERMAL": i.TH2,
                "DEN": i.DENS2,
                "MASS": i.MAS2}
                
            json["Assign"][i.ID] = {
                "TYPE": i.TYPE,
                "NAME": i.NAME,
                "HE_SPEC": i.SPH,
                "HE_COND": i.CON,
                "PLMT": i.PID,
                "P_NAME": i.PNM,
                "bMASS_DENS": i.UMD,
                "DAMP_RAT": i.DAMP,
                "PARAM":[data_1]
            }
            if data_2 != {}: json["Assign"][i.ID]["PARAM"].append(data_2)
            if data_1 == {}: print("Imporper input in Material class!")
        return json
    
    @classmethod
    def create(cls):
        MidasAPI("PUT","/db/MATL",Material.make_json())
        
    @classmethod
    def call_json(cls):
        return MidasAPI("GET","/db/MATL")
    
    @classmethod
    def update_class(cls):
        units()
        a = Material.call_json()
        if a != {'message': ''}:
            Material.materials = []
            for k, v in a['MATL'].items():
                if len(v['PARAM']) == 1:
                    if v['PARAM'][0]['P_TYPE'] == 1:
                        Material(v['NAME'], v['TYPE'], v['HE_SPEC'], v['HE_COND'], v['PLMT'], v['P_NAME'],v['bMASS_DENS'], v['DAMP_RAT'], 
                                standard_1 = v['PARAM'][0]['STANDARD'], db_1 = v['PARAM'][0]['DB'], id = k)
                    elif v['PARAM'][0]['P_TYPE'] == 2:
                        Material(v['NAME'], v['TYPE'], v['HE_SPEC'], v['HE_COND'], v['PLMT'], v['P_NAME'],v['bMASS_DENS'], v['DAMP_RAT'],
                                v['PARAM'][0]['DEN'], v['PARAM'][0]['ELAST'], v['PARAM'][0]['THERMAL'], v['PARAM'][0]['POISN'], "", "", v['PARAM'][0]['MASS'], id = k)
                    else:
                        Material(v['NAME'], v['TYPE'], v['HE_SPEC'], v['HE_COND'], v['PLMT'], v['P_NAME'],v['bMASS_DENS'], v['DAMP_RAT'],
                                v['PARAM'][0]['DEN'], v['PARAM'][0]['ELAST_M'][0], v['PARAM'][0]['THERMAL_M'][0], v['PARAM'][0]['POISN_M'][0],"", "", v['PARAM'][0]['MASS'], 0,
                                v['PARAM'][0]['ELAST_M'][1], v['PARAM'][0]['THERMAL_M'][1], v['PARAM'][0]['POISN_M'][1], "", "", 0,
                                v['PARAM'][0]['ELAST_M'][2], v['PARAM'][0]['THERMAL_M'][2], v['PARAM'][0]['POISN_M'][2],
                                v['PARAM'][0]['SHEAR_M'][0], v['PARAM'][0]['SHEAR_M'][1], v['PARAM'][0]['SHEAR_M'][2], k)
                else:
                    if v['PARAM'][0]['P_TYPE'] == 1 and v['PARAM'][1]['P_TYPE'] == 1:
                        Material(v['NAME'], v['TYPE'], v['HE_SPEC'], v['HE_COND'], v['PLMT'], v['P_NAME'],v['bMASS_DENS'], v['DAMP_RAT'], 0, 0, 0, 0,
                                v['PARAM'][0]['STANDARD'], v['PARAM'][0]['DB'], 0, 0, 0, 0, 0, v['PARAM'][1]['STANDARD'],v['PARAM'][1]['DB'], id = k)
                    elif v['PARAM'][0]['P_TYPE'] == 1 and v['PARAM'][1]['P_TYPE'] == 2:
                        Material(v['NAME'], v['TYPE'], v['HE_SPEC'], v['HE_COND'], v['PLMT'], v['P_NAME'],v['bMASS_DENS'], v['DAMP_RAT'], 0, 0, 0, 0,
                                v['PARAM'][0]['STANDARD'], v['PARAM'][0]['DB'], 0, v['PARAM'][1]['DEN'], v['PARAM'][1]['ELAST'], v['PARAM'][1]['THERMAL'], v['PARAM'][1]['POISN'], id = k)
                    elif v['PARAM'][0]['P_TYPE'] == 2 and v['PARAM'][1]['P_TYPE'] == 1:
                        Material(v['NAME'], v['TYPE'], v['HE_SPEC'], v['HE_COND'], v['PLMT'], v['P_NAME'],v['bMASS_DENS'], v['DAMP_RAT'], 
                                v['PARAM'][0]['DEN'], v['PARAM'][0]['ELAST'], v['PARAM'][0]['THERMAL'], v['PARAM'][0]['POISN'], "", "",
                                v['PARAM'][0]['MASS'], 0, 0, 0, 0, v['PARAM'][1]['STANDARD'],v['PARAM'][1]['DB'], id = k)
                    else:
                        Material(v['NAME'], v['TYPE'], v['HE_SPEC'], v['HE_COND'], v['PLMT'], v['P_NAME'],v['bMASS_DENS'], v['DAMP_RAT'], 
                                v['PARAM'][0]['DEN'], v['PARAM'][0]['ELAST'], v['PARAM'][0]['THERMAL'], v['PARAM'][0]['POISN'], "", "",
                                v['PARAM'][0]['MASS'], v['PARAM'][1]['DEN'], v['PARAM'][1]['ELAST'], v['PARAM'][1]['THERMAL'], v['PARAM'][1]['POISN'],"", "", v['PARAM'][1]['MASS'], id = k)
#---------------------------------------------------------------------------------------------------------------

#16 Function to create a RC T girder grillage
def grillage(span_length = 20, width = 8, support = "fix", x_loc = 0, girder_depth = 0, girder_width = 0, girder_no = 0, 
            web_thk = 0, slab_thk = 0, dia_no = 2, dia_depth = 0, dia_width = 0, overhang = 0, skew = 0, mat_E = 30_000_000):
    """Span length, width, support, girder depth, girder width, no. of girders, web thickness, slab thickness, skew.  All inputs are in SI units.
    Sample: grillage (span_length = 20, width = 8, support = "fix", skew = 20)"""
    units()
    if span_length > 0 and width > 0:
        #Data proofing and initial calcs:
        if girder_depth == 0: girder_depth = max(1, round(span_length/20,3))
        if girder_no == 0: girder_no = int(width/2)
        if girder_width == 0: girder_width = width/girder_no
        if slab_thk == 0: slab_thk = round(span_length/100,1)+0.05
        if web_thk == 0: web_thk = round(girder_width/8,3)
        if dia_depth == 0: dia_depth = girder_depth - slab_thk
        if dia_width == 0: dia_width = web_thk
        if dia_no <=1:
            print("At least 2 diaphragms are required.  No. of diaphragm is changed to 2.")
            dia_no = 2
        if dia_no >= 2: 
            overhang = max(overhang, dia_width/2)
            cc_diaph = span_length / (dia_no - 1)
        elem_len = round(cc_diaph / (round(cc_diaph,0)), 6)
        if overhang > elem_len/2:
            o_div = int(round(overhang/elem_len + 1, 0))
            o_elem_len = overhang / o_div
        if overhang > 0 and overhang <= elem_len/2:
            o_div = 1
            o_elem_len = overhang
        if overhang == 0:
            o_div = 0
            o_elem_len = 0
        
        #Generate material properties:
        Material("Concrete_X_"+str(x_loc), E_1 = mat_E)
        Material("Dummy_X_"+str(x_loc), E_1 = mat_E, density_1 = 0)
        
        #Generate section properties:
        global section_ids
        sec_id = len(section_ids)
        if overhang > 0:
            if o_div > 1: DBSec("Overhang_X_"+str(x_loc), slab_thk,o_elem_len, id = sec_id + 1 ,offset='CT')                                                #1 -8
            DBSec("Start_X_"+str(x_loc), slab_thk, o_elem_len / 2, id = sec_id + 2, offset = 'RT')                                                          #2 -7
            DBSec("End_X_"+str(x_loc), slab_thk, o_elem_len / 2, id = sec_id + 3, offset = 'LT')                                                            #3 -6
        if dia_no >=2:
            DBSec("Diap_X_"+str(x_loc), dia_depth, dia_width, id = sec_id + 4, offset = 'CT', uor = 1, vo = 1, vo_i = -slab_thk)                            #4 -5
        DBSec("T Beam_X_"+str(x_loc), girder_depth, girder_width, web_thk, slab_thk, shape = "T", id = sec_id + 5, offset = 'CT')                           #5 -4
        DBSec("Slab_X_"+str(x_loc), slab_thk, elem_len, id = sec_id + 6, offset = 'CT')                                                                     #6 -3
        DBSec("Slab_sup_st_X_"+str(x_loc), slab_thk, (elem_len + o_elem_len) / 2, id = sec_id + 7, offset = 'RT', uor = 1, ho = 1, ho_i = o_elem_len/2)     #7 -2
        DBSec("Slab_sup_en_X_"+str(x_loc), slab_thk, (elem_len + o_elem_len) / 2, id = sec_id + 8, offset = 'LT', uor = 1, ho = 1, ho_i = o_elem_len/2)     #8 -1
        
        #Generate transverse beams:
        nos = cc_diaph / elem_len
        if nos/int(nos) != 1:
            nos = nos + 1
            elem_len = cc_diaph/nos
        for h in range(max(0,dia_no - 1)):
            for i in range (int(nos + 1)):
                #Regular slab for fist and last section of the span
                if h == 0 or h == dia_no - 2:       
                    if i!= 0 and i != nos:Beam(length = round(width, 3), x = (h * cc_diaph) + x_loc + overhang + i * elem_len ,h_angle=90, 
                                                mID = Material.materials[-1].ID, sID = DBSec.sections[-3].ID, elen = round(girder_width / 2, 3), elen_type="min")
                #Regular slab for all inernal sections of the span
                if h > 0 and h < dia_no - 2:Beam(length = round(width, 3), x = (h * cc_diaph) + x_loc + overhang + i * elem_len ,h_angle=90, 
                        mID = Material.materials[-1].ID, sID = DBSec.sections[-3].ID, elen = round(girder_width / 2, 3), elen_type="min")
            #Last slab for all sections of the span, except the first & last sections
            if h!= 0: Beam(length = round(width, 3), x = (h * cc_diaph) + x_loc + overhang ,h_angle=90, 
                            mID = Material.materials[-1].ID, sID = DBSec.sections[-3].ID, elen = round(girder_width / 2, 3), elen_type="min")
            #First unsymmetric slab of the first section
            if h == 0:Beam(length = round(width, 3), x = (h * cc_diaph) + x_loc + overhang + 0, h_angle=90, 
                            mID = Material.materials[-1].ID, sID = DBSec.sections[-2].ID, elen = round(girder_width / 2, 3), elen_type="min")
            #Last unsymmetric slab of the last section
            if h == dia_no - 2: Beam(length = round(width, 3), x = (h * cc_diaph) + x_loc + overhang + nos * elem_len, h_angle=90, 
                                    mID = Material.materials[-1].ID, sID = DBSec.sections[-1].ID, elen = round(girder_width / 2, 3), elen_type="min")
            #All diaphrams except the span end diaphragm
            if dia_no > 0:
                Beam(length = round(width, 3), x = (h * cc_diaph) + x_loc + overhang, h_angle=90, 
                    mID = Material.materials[-2].ID, sID = DBSec.sections[-5].ID, elen = round(girder_width / 2, 3), elen_type="min")
        #Span end diaphragm
        if dia_no > 0:
            Beam(length = round(width, 3), x = x_loc + overhang + span_length, h_angle=90, 
                mID = Material.materials[-2].ID, sID = DBSec.sections[-5].ID, elen = round(girder_width / 2, 3), elen_type="min")
        
        if overhang > 0:
            for i in range (o_div + 1):
                #Span start overhang internal slabs
                if i!= 0 and i != o_div and o_div >= 2: Beam(length = round(width, 3), x = x_loc + i * o_elem_len ,h_angle=90, 
                                            mID = Material.materials[-1].ID, sID = DBSec.sections[-8].ID, elen = round(girder_width / 2, 3), elen_type="min")
                #Span start unsymmetric slab
                if i == 0: Beam(length = round(width, 3), x = x_loc, h_angle=90, 
                                mID = Material.materials[-1].ID, sID = DBSec.sections[-7].ID, elen = round(girder_width / 2, 3), elen_type="min")
            for i in range (o_div + 1):
                #Span end overhang inernal slabs
                if i!= 0 and i != o_div and o_div >= 2: Beam(length = round(width, 3), x = x_loc + overhang + span_length + i * o_elem_len ,h_angle=90, 
                                            mID = Material.materials[-1].ID, sID = DBSec.sections[-8].ID, elen = round(girder_width / 2, 3), elen_type="min")
                #Span end unsymmetric slab
                if i == o_div: Beam(length = round(width, 3), x = x_loc + 2 * overhang + span_length, h_angle=90, 
                                mID = Material.materials[-1].ID, sID = DBSec.sections[-6].ID, elen = round(girder_width / 2, 3), elen_type="min")
        
        #Generate longitudinal girders:
        for i in range(girder_no):
            #Overhang start length
            Beam(length = o_div * o_elem_len, x = x_loc, y = round(girder_width / 2, 3) + round(girder_width * i, 3), 
                mID = Material.materials[-2].ID, sID = DBSec.sections[-4].ID, elen = o_elem_len)
            #Span length
            Beam(length = nos * elem_len * (dia_no - 1), x = x_loc + overhang, y = round(girder_width / 2, 3) + round(girder_width * i, 3),
                mID = Material.materials[-2].ID, sID = DBSec.sections[-4].ID, elen = elem_len)
            #Overhang end length
            Beam(length = o_div * o_elem_len, x = x_loc + overhang + span_length, y = round(girder_width / 2, 3) + round(girder_width * i, 3), 
                mID = Material.materials[-2].ID, sID = DBSec.sections[-4].ID, elen = o_elem_len)
        
        #Remove duplicate entries (if any) from the node classes:
        remove_duplicate(elem_dict= "NA", tolerance = 0.01)
        
        #Generate Boundary Group, Load Group, Load Cases:
        Group("B","Support_X_"+str(x_loc))
        Group("L", "DL", "SIDL")
        Load_Case("D","Self-Weight", "Wearing Course")
        Load_SW("Self-Weight", lg = "DL")
        
        #Generate the defined content in a connected midas Civil NX model file
        create_model()
        
        #Call the data for generated nodes & elements
        n = Node.make_json()
        e = Element.make_json()
        
        #Create girder structure groups and provide supports at the ends of girders:
        for i in range (girder_no):
            li = get_select("X",crit_2 = round(girder_width / 2 + i * girder_width, 3), st = x_loc, en = x_loc + span_length + 2 * overhang, no = n, el = e, tolerance = 0.01)
            Group("S","Longi_"+str(i+1)+"_"+str(x_loc), elist = [li['ELEM']])
            for j in li['NODE']:
                if n[list(n.keys())[0]][str(j)]['X'] == x_loc + overhang or n[list(n.keys())[0]][str(j)]['X'] == x_loc + overhang + nos * elem_len * (dia_no - 1):
                    Support(j,support, "Support_X_"+str(x_loc))
        x_ord = []
        for i in li['ELEM']:
            if n['Assign'][str(e['Assign'][str(i)]['NODE'][0])]['X'] not in x_ord: x_ord.append(n['Assign'][str(e['Assign'][str(i)]['NODE'][0])]['X'])
            if n['Assign'][str(e['Assign'][str(i)]['NODE'][1])]['X'] not in x_ord: x_ord.append(n['Assign'][str(e['Assign'][str(i)]['NODE'][1])]['X'])
        
        #Create transverse element group and add appropriate nodes & elements:
        Group("S","Transverse_"+str(x_loc))
        Group("S","Transverse")
        
        for i in x_ord:
            li = get_select("Y",crit_2= i, no = n, el = e, tolerance = 0.01)
            Group.update_SG("Transverse_"+str(x_loc), elist = [li['ELEM']])
            Group.update_SG("Transverse", elist = [li['ELEM']])
            for j in li['ELEM']:
                if e['Assign'][str(j)]['SECT'] != DBSec.sections[-5].ID:
                    #Wearing course load on the start and end slab:
                    if i == x_loc or i == x_loc + 2 * overhang + span_length:
                        Load_Element(j, "Wearing Course", -22 * 0.075 * o_elem_len * mt.cos(mt.radians(skew)) / 2)
                    #Wearing course load on the overhang part:
                    elif i < x_loc + overhang or i > x_loc + overhang + span_length:
                        Load_Element(j, "Wearing Course", -22 * 0.075 * o_elem_len * mt.cos(mt.radians(skew)))
                    #Wearing course load on the support location:
                    elif i == x_loc + overhang or i == x_loc + overhang + span_length:
                        Load_Element(j, "Wearing Course", -22 * 0.075 * (o_elem_len + elem_len) * mt.cos(mt.radians(skew)) / 2)
                    else:
                        Load_Element(j, "Wearing Course", -22 * 0.075 * elem_len * mt.cos(mt.radians(skew)))
            for j in li['NODE']:
                if n[list(n.keys())[0]][str(j)]['Y'] == 0 or n[list(n.keys())[0]][str(j)]['Y'] == round(width,3):
                    if i != x_ord[-1] and i != x_ord[0]:
                        Load_Node(j, "CB","SIDL",FZ = -(x_ord[x_ord.index(i) + 1] - x_ord[x_ord.index(i) - 1]) * 5)
                    else:
                        Load_Node(j, "CB","SIDL",FZ = -(x_ord[1] - x_ord[0]) * 5)
            
        #Generate the supports & groups:
        create_model(set = 2)
        #Assign skew to the structure:
        if skew != 0:
            for i in Node.nodes:
                if x_loc <= i.X and x_loc + 2 * overhang + span_length >= i.X:
                    i.X += i.Y * mt.tan(mt.radians(skew))
            if overhang > 0:
                if o_div > 1: DBSec("Overhang_X_"+str(x_loc), slab_thk,o_elem_len * mt.cos(mt.radians(skew)), id = sec_id + 1 ,offset='CT')
                DBSec("Start_X_"+str(x_loc), slab_thk, o_elem_len * mt.cos(mt.radians(skew)) / 2, id = sec_id + 2, offset = 'RT')
                DBSec("End_X_"+str(x_loc), slab_thk, o_elem_len * mt.cos(mt.radians(skew)) / 2, id = sec_id + 3, offset = 'LT')
            DBSec("Slab_X_"+str(x_loc), slab_thk, elem_len * mt.cos(mt.radians(skew)), id = sec_id + 6, offset = 'CT')
            DBSec("Slab_sup_st_X_"+str(x_loc), slab_thk, (elem_len + o_elem_len) * mt.cos(mt.radians(skew)) / 2, id = sec_id + 7, offset = 'RT', uor = 1, ho = 1, ho_i = o_elem_len * mt.cos(mt.radians(skew))/2)
            DBSec("Slab_sup_en_X_"+str(x_loc), slab_thk, (elem_len + o_elem_len) * mt.cos(mt.radians(skew)) / 2, id = sec_id + 8, offset = 'LT', uor = 1, ho = 1, ho_i = o_elem_len * mt.cos(mt.radians(skew))/2)
            DBSec.create()
            Node.create()
        
        #Analyzed the model file
        # analyze()
#---------------------------------------------------------------------------------------------------------------

#17 Class to define self weight:
class Load_SW:
    """Load Case Name, direction, Value, Load Group.\n
    Sample: Load_SW("Self-Weight", "Z", -1, "DL")"""
    data = []
    def __init__(self, lc, dir = "Z", value = -1, lg = ""):
        chk = 0
        for i in Load_Case.cases:
            if lc in i.NAME: chk = 1
        if chk == 0: Load_Case("D", lc)
        if lg != "":
            chk = 0
            a = [v['NAME'] for v in Group.make_json_LG()["Assign"].values()]
            if lg in a: chk = 1
            if chk == 0: Group("L", lg)
        if dir == "X":
            fv = [value, 0, 0]
        elif dir == "Y":
            fv = [0, value, 0]
        else:
            fv = [0, 0, value]
        self.LC = lc
        self.DIR = dir
        self.FV = fv
        self.LG = lg
        self.ID = len(Load_SW.data) + 1
        Load_SW.data.append(self)
    
    @classmethod
    def make_json(cls):
        json = {"Assign":{}}
        for i in cls.data:
            json["Assign"][i.ID] = {
                "LCNAME": i.LC,
                "GROUP_NAME": i.LG,
                "FV": i.FV
            }
        return json
    
    @classmethod
    def create(cls):
        MidasAPI("PUT","/db/BODF",Load_SW.make_json())
    
    @classmethod
    def call_json(cls):
        return MidasAPI("GET","/db/BODF")
    
    @classmethod
    def update_class(cls):
        a = Load_SW.call_json()
        if a != {'message': ''}:
            for i in list(a['BODF'].keys()):
                if a['BODF'][i]['FV'][0] != 0:
                    di = "X"
                    va = a['BODF'][i]['FV'][0]
                elif a['BODF'][i]['FV'][1] != 0:
                    di = "Y"
                    va = a['BODF'][i]['FV'][1]
                else:
                    di = "Z"
                    va = a['BODF'][i]['FV'][2]
                Load_SW(a['BODF'][i]['LCNAME'], di, va, a['BODF'][i]['GROUP_NAME'])
#---------------------------------------------------------------------------------------------------------------

#18 Class to add Nodal Loads:
class Load_Node:
    """Creates node loads and converts to JSON format.
    Example: Load_Node(101, "LC1", "Group1", FZ = 10)
    """
    data = []
    def __init__(self, node, lc, lg = "", FX = 0, FY = 0, FZ= 0, MX =0, MY =0, MZ=0, id = ""):
        chk = 0
        for i in Load_Case.cases:
            if lc in i.NAME: chk = 1
        if chk == 0: Load_Case("USER", lc)
        if lg != "":
            chk = 0
            a = [v['NAME'] for v in Group.make_json_LG()["Assign"].values()]
            if lg in a: chk = 1
            if chk == 0: Group("L", lg)
        self.NODE = node
        self.LCN = lc
        self.LDGR = lg
        self.FX = FX
        self.FY = FY
        self.FZ = FZ
        self.MX = MX
        self.MY = MY
        self.MZ = MZ
        if id == "": id = len(Load_Node.data) + 1
        self.ID = id
        Load_Node.data.append(self)
    
    @classmethod
    def make_json(cls):
        json = {"Assign": {}}
        for i in cls.data:
            if i.NODE not in list(json["Assign"].keys()):
                json["Assign"][i.NODE] = {"ITEMS": []}
            json["Assign"][i.NODE]["ITEMS"].append({
                "ID": i.ID,
                "LCNAME": i.LCN,
                "GROUP_NAME": i.LDGR,
                "FX": i.FX,
                "FY": i.FY,
                "FZ": i.FZ,
                "MX": i.MX,
                "MY": i.MY,
                "MZ": i.MZ
            })
        return json
    
    @classmethod
    def create(cls):
        MidasAPI("PUT", "/db/CNLD",Load_Node.make_json())
    
    @classmethod
    def call_json(cls):
        return MidasAPI("GET", "/db/CNLD")
    
    @classmethod
    def update_class(cls):
        cls.data = []
        a = Load_Node.call_json()
        if a != {'message': ''}:
            for i in a['CNLD'].keys():
                for j in range(len(a['CNLD'][i]['ITEMS'])):
                    Load_Node(int(i),a['CNLD'][i]['ITEMS'][j]['LCNAME'], a['CNLD'][i]['ITEMS'][j]['GROUP_NAME'], 
                        a['CNLD'][i]['ITEMS'][j]['FX'], a['CNLD'][i]['ITEMS'][j]['FY'], a['CNLD'][i]['ITEMS'][j]['FZ'], 
                        a['CNLD'][i]['ITEMS'][j]['MX'], a['CNLD'][i]['ITEMS'][j]['MY'], a['CNLD'][i]['ITEMS'][j]['MZ'],
                        a['CNLD'][i]['ITEMS'][j]['ID'])
#---------------------------------------------------------------------------------------------------------------

#19 Class to define Beam Loads:
class Load_Element:
    data = []
    def __init__(self, element: int, lc: str, value: float, lg: str = "", direction: str = "GZ",
        id = "", D = [0, 1, 0, 0], P = [0, 0, 0, 0], cmd = "BEAM", typ = "UNILOAD", use_ecc = False, use_proj = False,
        eccn_dir = "LZ", eccn_type = 1, ieccn = 0, jeccn = 0.0000195, adnl_h = False, adnl_h_i = 0, adnl_h_j = 0.0000195): 
        """
        element: Element Number 
        lc (str): Load case name
        lg (str, optional): Load group name. Defaults to ""
        value (float): Load value
        direction (str): Load direction (e.g., "GX", "GY", "GZ", "LX", "LY", "LZ"). Defaults to "GZ"
        id (str, optional): Load ID. Defaults to auto-generated
        D: Relative distance (list with 4 values, optional) based on length of element. Defaults to [0, 1, 0, 0]
        P: Magnitude of UDL at corresponding position of D (list with 4 values, optional). Defaults to [value, value, 0, 0]
        cmd: Load command (e.g., "BEAM", "LINE", "TYPICAL")
        typ: Load type (e.g., "CONLOAD", "CONMOMENT", "UNITLOAD", "UNIMOMENT", "PRESSURE")
        use_ecc: Use eccentricity (True or False). Defaults to False.
        use_proj: Use projection (True or False). Defaults to False.
        eccn_dir: Eccentricity direction (e.g., "GX", "GY", "GZ", "LX", "LY", "LZ"). Defaults to "LZ"
        eccn_type: Eccentricity from offset (1) or centroid (0). Defaults to 1.
        ieccn, jeccn: Eccentricity values at i-end and j-end of the element
        adnl_h: Consider additional H when applying pressure on beam (True or False). Defaults to False.
        adnl_h_i, adnl_h_j: Additional H values at i-end and j-end of the beam.  Defaults to 0.\n
        Example:
        - Load_Beam(115, "UDL_Case", "", -50.0, "GZ")  # No eccentricity
        - Load_Beam(115, "UDL_Case", "", -50.0, "GZ", ieccn=2.5)  # With eccentricity
        """
        chk = 0
        for i in Load_Case.cases:
            if lc in i.NAME: chk = 1
        if chk == 0: Load_Case("USER", lc)
        if lg != "":
            chk = 0
            a = [v['NAME'] for v in Group.make_json_LG()["Assign"].values()]
            if lg in a:
                chk = 1
            if chk == 0:
                Group("L", lg)
        D = (D + [0] * 4)[:4]
        P = (P + [0] * 4)[:4]
        if P == [0, 0, 0, 0]: P = [value, value, 0, 0]
        if eccn_type != 0 or eccn_type != 1: eccn_type = 0
        if direction not in ("GX", "GY", "GZ", "LX", "LY", "LZ"): direction = "GZ"
        if eccn_dir not in ("GX", "GY", "GZ", "LX", "LY", "LZ"): eccn_dir = "LY"
        if cmd not in ("BEAM", "LINE", "TYPICAL"): cmd = "BEAM"
        if typ not in ("CONLOAD", "CONMOMENT", "UNILOAD", "UNIMOMENT","PRESSURE"): typ = "UNILOAD"
        if use_ecc == False:
            if ieccn != 0 or jeccn != 0.0000195: use_ecc = True
        self.ELEMENT = element
        self.LCN = lc
        self.LDGR = lg
        self.VALUE = value
        self.DIRECTION = direction
        self.CMD = cmd
        self.TYPE = typ
        self.USE_PROJECTION = use_proj
        self.USE_ECCEN = use_ecc
        self.ECCEN_TYPE = eccn_type
        self.ECCEN_DIR = eccn_dir
        self.IECC = ieccn
        if jeccn == 0.0000195:
            self.JECC = 0
            self.USE_JECC = False
        else:
            self.JECC = jeccn
            self.USE_JECC = True
        self.D = D
        self.P = P
        self.USE_H = adnl_h
        self.I_H = adnl_h_i
        if adnl_h == 0.0000195:
            self.USE_JH = False
            self.J_H = 0
        else:
            self.USE_JH = True
            self.J_H = adnl_h_j
        
        if id == "":
            id = len(Load_Element.data) + 1
        self.ID = id
        Load_Element.data.append(self)
    
    @classmethod
    def make_json(cls):
        json = {"Assign": {}}
        for i in cls.data:
            item_data = {
                "ID": i.ID,
                "LCNAME": i.LCN,
                "GROUP_NAME": i.LDGR,
                "CMD": i.CMD,
                "TYPE": i.TYPE,
                "DIRECTION": i.DIRECTION,
                "USE_PROJECTION": i.USE_PROJECTION,
                "USE_ECCEN": i.USE_ECCEN,
                "D": i.D,
                "P": i.P
            }
            if i.USE_ECCEN == True:
                item_data.update({
                    "ECCEN_TYPE": i.ECCEN_TYPE,
                    "ECCEN_DIR": i.ECCEN_DIR,
                    "I_END": i.IECC,
                    "J_END": i.JECC,
                    "USE_J_END": i.USE_JECC
                })
            if i.TYPE == "PRESSURE":
                item_data.update({
                    "USE_ADDITIONAL": i.USE_H,
                    "ADDITIONAL_I_END": i.I_H,
                    "ADDITIONAL_J_END": i.J_H,
                    "USE_ADDITIONAL_J_END": i.J_H
                })
            if i.ELEMENT not in json["Assign"]:
                json["Assign"][i.ELEMENT] = {"ITEMS": []}
            json["Assign"][i.ELEMENT]["ITEMS"].append(item_data)
        return json
    
    @classmethod
    def create(cls):
        MidasAPI("PUT", "/db/bmld", Load_Element.make_json())
    
    @classmethod
    def call_json(cls):
        return MidasAPI("GET", "/db/bmld")
    
    @classmethod
    def update_class(cls):
        cls.data = []
        a = Load_Element.call_json()
        if a != {'message': ''}:
            for i in a['BMLD'].keys():
                for j in range(len(a['BMLD'][i]['ITEMS'])):
                    if a['BMLD'][i]['ITEMS'][j]['USE_ECCEN'] == True and a['BMLD'][i]['ITEMS'][j]['USE_ADDITIONAL'] == True:
                        Load_Element(i,a['BMLD'][i]['ITEMS'][j]['LCNAME'], a['BMLD'][i]['ITEMS'][j]['P'][0], a['BMLD'][i]['ITEMS'][j]['GROUP_NAME'],
                            a['BMLD'][i]['ITEMS'][j]['DIRECTION'], a['BMLD'][i]['ITEMS'][j]['ID'], a['BMLD'][i]['ITEMS'][j]['D'], a['BMLD'][i]['ITEMS'][j]['P'],
                            a['BMLD'][i]['ITEMS'][j]['CMD'], a['BMLD'][i]['ITEMS'][j]['TYPE'], a['BMLD'][i]['ITEMS'][j]['USE_ECCEN'], a['BMLD'][i]['ITEMS'][j]['USE_PROJECTION'],
                            a['BMLD'][i]['ITEMS'][j]['ECCEN_DIR'], a['BMLD'][i]['ITEMS'][j]['ECCEN_TYPE'], a['BMLD'][i]['ITEMS'][j]['I_END'], a['BMLD'][i]['ITEMS'][j]['J_END'],
                            a['BMLD'][i]['ITEMS'][j]['USE_ADDITIONAL'], a['BMLD'][i]['ITEMS'][j]['ADDITIONAL_I_END'], a['BMLD'][i]['ITEMS'][j]['ADDITIONAL_J_END'])
                    elif a['BMLD'][i]['ITEMS'][j]['USE_ECCEN'] == False and a['BMLD'][i]['ITEMS'][j]['USE_ADDITIONAL'] == True:
                        Load_Element(i,a['BMLD'][i]['ITEMS'][j]['LCNAME'], a['BMLD'][i]['ITEMS'][j]['P'][0], a['BMLD'][i]['ITEMS'][j]['GROUP_NAME'],
                            a['BMLD'][i]['ITEMS'][j]['DIRECTION'], a['BMLD'][i]['ITEMS'][j]['ID'], a['BMLD'][i]['ITEMS'][j]['D'], a['BMLD'][i]['ITEMS'][j]['P'],
                            a['BMLD'][i]['ITEMS'][j]['CMD'], a['BMLD'][i]['ITEMS'][j]['TYPE'], a['BMLD'][i]['ITEMS'][j]['USE_ECCEN'], a['BMLD'][i]['ITEMS'][j]['USE_PROJECTION'],
                            adnl_h = a['BMLD'][i]['ITEMS'][j]['USE_ADDITIONAL'], adnl_h_i = a['BMLD'][i]['ITEMS'][j]['ADDITIONAL_I_END'], adnl_h_j = a['BMLD'][i]['ITEMS'][j]['ADDITIONAL_J_END'])
                    elif a['BMLD'][i]['ITEMS'][j]['USE_ECCEN'] == True and a['BMLD'][i]['ITEMS'][j]['USE_ADDITIONAL'] == False:
                        Load_Element(i,a['BMLD'][i]['ITEMS'][j]['LCNAME'], a['BMLD'][i]['ITEMS'][j]['P'][0], a['BMLD'][i]['ITEMS'][j]['GROUP_NAME'],
                            a['BMLD'][i]['ITEMS'][j]['DIRECTION'], a['BMLD'][i]['ITEMS'][j]['ID'], a['BMLD'][i]['ITEMS'][j]['D'], a['BMLD'][i]['ITEMS'][j]['P'],
                            a['BMLD'][i]['ITEMS'][j]['CMD'], a['BMLD'][i]['ITEMS'][j]['TYPE'], a['BMLD'][i]['ITEMS'][j]['USE_ECCEN'], a['BMLD'][i]['ITEMS'][j]['USE_PROJECTION'],
                            a['BMLD'][i]['ITEMS'][j]['ECCEN_DIR'], a['BMLD'][i]['ITEMS'][j]['ECCEN_TYPE'], a['BMLD'][i]['ITEMS'][j]['I_END'], a['BMLD'][i]['ITEMS'][j]['J_END'])
                    else:
                        Load_Element(i,a['BMLD'][i]['ITEMS'][j]['LCNAME'], a['BMLD'][i]['ITEMS'][j]['P'][0], a['BMLD'][i]['ITEMS'][j]['GROUP_NAME'],
                            a['BMLD'][i]['ITEMS'][j]['DIRECTION'], a['BMLD'][i]['ITEMS'][j]['ID'], a['BMLD'][i]['ITEMS'][j]['D'], a['BMLD'][i]['ITEMS'][j]['P'],
                            a['BMLD'][i]['ITEMS'][j]['CMD'], a['BMLD'][i]['ITEMS'][j]['TYPE'], a['BMLD'][i]['ITEMS'][j]['USE_ECCEN'], a['BMLD'][i]['ITEMS'][j]['USE_PROJECTION'])
#---------------------------------------------------------------------------------------------------------------

#20 Class to define Elastic Links:
class Elastic_Link:
    links = []
    
    def __init__(self, 
                i_node: int, 
                j_node: int,
                link_type: str = "GEN",
                SDx: float = 0, 
                SDy: float = 0, 
                SDz: float = 0, 
                SRx: float = 0, 
                SRy: float = 0, 
                SRz: float = 0,  
                group: str = "", 
                id: int = None, 
                shear: bool = False, 
                dr_y: float = 0.5, 
                dr_z: float = 0.5, 
                beta_angle: float = 0, 
                dir: str = "Dy", 
                func_id: int = 1, 
                distance_ratio: float = 0,
                rigid_dir = [False] * 6):
        """
        Elastic link. 
        Parameters:
            i_node: The first node ID
            j_node: The second node ID
            link_type: Type of link (GEN, RIGID, TENS, COMP, MULTI LINEAR, SADDLE, RAIL INTERACT) (default "GEN")
            sdx: Spring stiffness in X direction (default 0)
            sdy: Spring stiffness in Y direction (default 0)
            sdz: Spring stiffness in Z direction (default 0)
            srx: Rotational stiffness around X axis (default 0)
            sry: Rotational stiffness around Y axis (default 0)
            srz: Rotational stiffness around Z axis (default 0)
            group: The group name (default "")
            id: The link ID (optional)
            shear: Consider shear effects (default False)
            dr_y: Distance ratio for Y direction (default 0.5)
            dr_z: Distance ratio for Z direction (default 0.5)
            beta_angle: Rotation angle in degrees (default 0)
            dir: Direction for MULTI LINEAR or RAIL INTERACT links (default "Dy")
            func_id: Function ID for MULTI LINEAR or RAIL INTERACT links (default 1)
            distance_ratio: Distance ratio for MULTI LINEAR or RAIL INTERACT links (default 0)
        
        Examples:
            ```python
            # General link with all stiffness parameters
            ElasticLink(1, 2, "Group1", 1, "GEN", 1000, 1000, 1000, 100, 100, 100)     
            # Rigid link
            ElasticLink(3, 4, "Group2", 2, "RIGID")
            # Tension-only link
            ElasticLink(5, 6, "Group3", 3, "TENS", 500)
            # Compression-only link
            ElasticLink(7, 8, "Group4", 4, "COMP", 500)
            # Rail Track Type link
            ElasticLink(9, 10, "Group5", 5, "RAIL INTERACT", dir="Dy", func_id=1)
            # Multi Linear Link
            ElasticLink(11, 12, "Group6", 6, "MULTI LINEAR", dir="Dy", func_id=1)
            # Saddle type link
            ElasticLink(13, 14, "Group7", 7, "SADDLE")
            ```
        """
        # Check if group exists, create if not
        if group != "":
            a = [v['NAME'] for v in Group.make_json_BG()["Assign"].values()]
            if group not in a: Group("B", group)
        
        # Validate link type
        valid_types = ["GEN", "RIGID", "TENS", "COMP", "MULTI LINEAR", "SADDLE", "RAIL INTERACT"]
        if link_type not in valid_types: link_type = "GEN"
        
        # Validate direction for MULTI LINEAR
        if link_type == "MULTI LINEAR":
            valid_directions = ["Dx", "Dy", "Dz", "Rx", "Ry", "Rz"]
            if dir not in valid_directions: dir = "Dy"
        
        # Validate direction for RAIL INTERACT
        if link_type == "RAIL INTERACT":
            valid_directions = ["Dy", "Dz"]
            if dir not in valid_directions: dir = "Dy"
        
        self.I_NODE = i_node
        self.J_NODE = j_node
        self.GROUP_NAME = group
        self.LINK_TYPE = link_type
        self.ANGLE = beta_angle
        
        # Parameters for all link types
        self.SDX = SDx
        self.SDY = SDy
        self.SDZ = SDz
        self.SRX = SRx
        self.SRY = SRy
        self.SRZ = SRz
        self.RIGID_DIR = rigid_dir
        self.bSHEAR = shear
        self.DR_Y = dr_y
        self.DR_Z = dr_z
        
        # Parameters for MULTI LINEAR and RAIL INTERACT
        self.Direction = dir
        self.Function_ID = func_id
        self.Distance_ratio = distance_ratio
        
        # Auto-assign ID if not provided
        if len(Elastic_Link.links) == 0 and id is None: 
            id = 1
        elif id is None or id in [i.ID for i in Elastic_Link.links]:
            id = max([i.ID for i in Elastic_Link.links]) + 1
        self.ID = id
        
        Elastic_Link.links.append(self)
    
    @classmethod
    def make_json(cls):
        """
        Converts ElasticLink data to JSON format for API submission.
        Example: ElasticLink.make_json()
        """
        data = {}
        
        for link in cls.links:
            link_data = {
                "NODE": [link.I_NODE, link.J_NODE],
                "LINK": link.LINK_TYPE,
                "ANGLE": link.ANGLE,
                "BNGR_NAME": link.GROUP_NAME
            }
            
            # Add type-specific parameters
            if link.LINK_TYPE == "GEN":
                link_data["R_S"] = link.RIGID_DIR
                link_data["SDR"] = [
                    link.SDX,
                    link.SDY,
                    link.SDZ,
                    link.SRX,
                    link.SRY,
                    link.SRZ
                ]
                
            elif link.LINK_TYPE in ["TENS", "COMP"]:
                link_data["SDR"] = [link.SDX, 0, 0, 0, 0, 0]
                
            elif link.LINK_TYPE == "MULTI LINEAR":
                link_data["MLFC"] = link.Function_ID
                
            elif link.LINK_TYPE == "RAIL INTERACT":
                link_data["RLFC"] = link.Function_ID
            
            if link.LINK_TYPE not in ["MULTI LINEAR", "RAIL INTERACT"]:
                link_data["DR"] = [link.DR_Y, link.DR_Z]
            else:
                direction_mapping = {"Dx": 0, "Dy": 1, "Dz": 2, "Rx": 3, "Ry": 4, "Rz": 5}
                link_data["DRENDI"] = link.Distance_ratio
                link_data["DIR"] = direction_mapping.get(link.Direction)
            
            if link.LINK_TYPE != "MULTI LINEAR": link_data["bSHEAR"] = link.bSHEAR
            data[link.ID] = link_data
            
        return {"Assign": data}
    
    @classmethod
    def create(cls):
        """ Sends all ElasticLink data to connected Civil NX model file.
        Example: ElasticLink.create() """
        MidasAPI("PUT", "/db/elnk", cls.make_json())
    
    @classmethod
    def call_json(cls):
        """ Retrieves ElasticLink data from Midas API.
        Example: ElasticLink.call_json() """
        return MidasAPI("GET", "/db/elnk")
    
    @classmethod
    def update_class(cls):
        """ Generates data for ElasticLink class in python for further modifications.
        Example: ElasticLink.update_class() """
        cls.links = []
        a = cls.call_json()
        
        if a != {'message': ''}:
            for link_id, link_data in a.get("ELNK").items(): 
                sdx = sdy = sdz = srx = sry = srz = 0
                shear = False
                dr_y = dr_z = 0.5
                direction = "Dy"
                func_id = 1
                distance_ratio = 0.5

                if link_data["LINK"] == "GEN" and "SDR" in link_data:
                    sdx, sdy, sdz, srx, sry, srz = link_data["SDR"]
                    shear = link_data.get("bSHEAR")
                    if shear and "DR" in link_data:
                        dr_y, dr_z = link_data["DR"]

                elif link_data["LINK"] in ["TENS", "COMP"] and "SDR" in link_data:
                    sdx = link_data["SDR"][0]
                    shear = link_data.get("bSHEAR")
                    if shear and "DR" in link_data:
                        dr_y, dr_z = link_data["DR"]

                elif link_data["LINK"] == "MULTI LINEAR":
                    dir_mapping = {0: "Dx", 1: "Dy", 2: "Dz", 3: "Rx", 4: "Ry", 5: "Rz"}
                    direction = dir_mapping.get(link_data.get("DIR"))
                    func_id = link_data.get("MLFC")
                    distance_ratio = link_data.get("DRENDI")

                elif link_data["LINK"] == "RAIL INTERACT":
                    dir_mapping = {1: "Dy", 2: "Dz"}
                    direction = dir_mapping.get(link_data.get("DIR"))
                    func_id = link_data.get("RLFC")
                    shear = link_data.get("bSHEAR")
                    if shear and "DRENDI" in link_data: distance_ratio = link_data["DRENDI"]

                Elastic_Link(
                    link_data["NODE"][0],
                    link_data["NODE"][1],
                    link_data["LINK"],
                    sdx, sdy, sdz, srx, sry, srz,
                    link_data.get("BNGR_NAME", ""),
                    int(link_id),
                    shear, dr_y, dr_z,
                    link_data.get("ANGLE", 0),
                    direction, func_id, distance_ratio, 
                    link_data.get("R_S", [False] * 6)
                )
#---------------------------------------------------------------------------------------------------------------

#21 Class to define PSC 1-CELL, 2-CELL & Half Sections
class PSC_BOX:
    sections = []
    
    def __init__(self, name = "PSC 1 Cell", id = 0, shape = "1CEL", jo1 = True, jo2 = False, jo3 = False, ji1 = True, ji2 = False, ji3 = True, ji4 = False, ji5 = True,
        z1 = True, z3 = True, t1 = True, t2 = True, t3 = True, tt = True, ho1 = 0.2, ho2 = 0.3, ho21 = 0, ho22 = 0, ho3 = 2.5, ho31 = 0, bo1 = 1.5, bo11 = 0.5, bo12 = 0,
        bo2 = 0.5, bo21 = 0, bo3 = 2.25, hi1 = 0.24, hi2 = 0.26, hi21 = 0, hi22 = 0, hi3 = 2.05, hi31 = 0.71, hi4 = 0.2, hi41 = 0, hi42 = 0, hi5 = 0.25, bi1 = 2.2, 
        bi11 = 0.7, bi12 = 0, bi21 = 2.2, bi3 = 1.932, bi31 = 0.7, bi32 = 0, bi4 = 0, offset="CT", center_loc = 0, uor = 0, ho = 0, vo = 0, ho_i = 0, vo_i = 0, sd = True, 
        we = True, wcai = True, wcaj = True, shck = True, wcpi = [[0]*6, [0]*6], wcpj = [[0]*6, [0]*6], z1v = 0, z3v = 0, t1v = 0, t2v = 0, t3v = 0, ttv = 0, 
        symm = True, smhl = False, mesh = False, user_stiff = False, opt1 = "", opt2 = ""):
        
        if len(section_ids) == 0 and id == 0: 
            section_count = 1
        elif len(section_ids) != 0 and id == 0:
            section_count = max(section_ids) + 1
        if id != 0:
            if id in section_ids and id in [i.ID for i in PSC_BOX.sections]:
                print(f"Section ID {id}, already exists and is now updated with new input.")
            elif id in section_ids and id not in [i.ID for i in PSC_BOX.sections]:
                section_count = max(section_ids) + 1
                print(f"Section ID {id} already exists.  New ID {section_count} is assigned to the section {name}.")
            else:
                section_count = id
        
        self.NAME = name
        self.ID = section_count
        self.SHAPE = shape
        self.JO1 = jo1
        self.JO2 = jo2
        self.JO3 = jo3
        self.JI1 = ji1
        self.JI2 = ji2
        self.JI3 = ji3
        self.JI4 = ji4
        self.JI5 = ji5
        self.Z1 = z1
        self.Z3 = z3
        self.T1 = t1
        self.T2 = t2
        self.T3 = t3
        self.TT = tt
        self.HO1 = ho1
        self.HO2 = ho2
        self.HO21 = ho21
        self.HO22 = ho22
        self.HO3 = ho3
        self.HO31 = ho31
        self.BO1 = bo1
        self.BO11 = bo11
        self.BO12 = bo12
        self.BO2 = bo2
        self.BO21 = bo21
        self.BO3 = bo3
        self.HI1 = hi1
        self.HI2 = hi2
        self.HI21 = hi21
        self.HI22 = hi22
        self.HI3 = hi3
        self.HI31 = hi31
        self.HI4 = hi4
        self.HI41 = hi41
        self.HI42 = hi42
        self.HI5 = hi5
        self.BI1 = bi1
        self.BI11 = bi11
        self.BI12 = bi12
        self.BI21 = bi21
        self.BI3 = bi3
        self.BI31 = bi31
        self.BI32 = bi32
        self.BI4 = bi4
        self.OFFSET = offset
        self.CL = center_loc
        self.UOR = uor
        self.HO = ho
        self.VO = vo
        self.HOI = ho_i
        self.VOI = vo_i
        self.SD = sd
        self.WE = we
        self.WCAI = wcai
        self.WCAJ = wcaj
        self.SHCK = shck
        self.WCPI = wcpi
        self.WCPJ = wcpj
        self.Z1V = z1v
        self.Z3V = z3v
        self.T1V = t1v
        self.T2V = t2v
        self.T3V = t3v
        self.TTV = ttv
        self.SYMM = symm
        self.SMHL = smhl
        self.MESH = mesh
        self.US = user_stiff
        self.OPT1 = opt1
        self.OPT2 = opt2
        PSC_BOX.sections.append(self)
        section_ids.append(int(section_count))
    
    @classmethod
    def make_json(cls):
        json = {"Assign":{}}
        for k in cls.sections:
            json["Assign"][k.ID] = {
                "SECTTYPE": "PSC",
                "SECT_NAME": k.NAME,
                "SECT_BEFORE": {
                "OFFSET_PT": k.OFFSET,
                "OFFSET_CENTER": k.CL,
                "USER_OFFSET_REF": k.UOR,
                "HORZ_OFFSET_OPT": k.HO,
                "USERDEF_OFFSET_YI": k.HOI,
                "VERT_OFFSET_OPT": k.VO,
                "USERDEF_OFFSET_ZI": k.VOI,
                "USE_SHEAR_DEFORM": k.SD,
                "USE_WARPING_EFFECT": k.WE,
                "SHAPE": k.SHAPE,
                "SECT_I":{
                    "vSIZE_PSC_A": [k.HO1, k.HO2, k.HO21, k.HO22, k.HO3, k.HO31],
                    "vSIZE_PSC_B": [k.BO1, k.BO11, k.BO12, k.BO2, k.BO21, k.BO3],
                    "vSIZE_PSC_C": [k.HI1, k.HI2, k.HI21, k.HI22, k.HI3, k.HI31, k.HI4, k.HI41, k.HI42, k.HI5],
                    "vSIZE_PSC_D": [k.BI1, k.BI11, k.BI12, k.BI21, k.BI3, k.BI31, k.BI32],
                    "SWIDTH": k.HO1
                },
                "WARPING_CHK_AUTO_I": k.WCAI,
                "WARPING_CHK_AUTO_J": k.WCAJ,
                "SHEAR_CHK": k.SHCK,
                "WARPING_CHK_POS_I": k.WCPI,
                "WARPING_CHK_POS_J": k.WCPJ,
                "USE_AUTO_SHEAR_CHK_POS": [[k.Z1, False, k.Z3], [False, False, False]],
                "SHEAR_CHK_POS":[[k.Z1V, 0, k.Z3V], [0, 0, 0]],
                "USE_WEB_THICK":[k.TT, False],
                "WEB_THICK":[k.TTV, 0],
                "USE_WEB_THICK_SHEAR":[[k.T1, k.T2, k.T3],[False, False, False]],
                "WEB_THICK_SHEAR":[[k.T1V, k.T2V, k.T3V],[0, 0, 0]],
                "USE_SYMMETRIC": k.SYMM,
                "USE_SMALL_HOLE": k.SMHL,
                "USE_USER_DEF_MESHSIZE": k.MESH,
                "USE_USER_INTPUT_STIFF": k.US,
                "PSC_OPT1": k.OPT1,
                "PSC_OPT2": k.OPT2,
                "JOINT":[k.JO1, k.JO2, k.JO3, k.JI1, k.JI2, k.JI3, k.JI4, k.JI5]
                }
            }
            #Modify PSC_D list for 2CEL section
            if k.SHAPE == "2CEL": 
                json["Assign"][k.ID]['SECT_BEFORE']['SECT_I']['vSIZE_PSC_D'].append(k.BI4)
            elif k.SHAPE == "1CEL":
                json["Assign"][k.ID]['SECT_BEFORE']['SECT_I']['vSIZE_PSC_D'].append(0)
        return json
    
    @classmethod
    def create(cls):
        MidasAPI("PUT","/db/sect", PSC_BOX.make_json())
    
    @classmethod
    def call_json(cls):
        return MidasAPI("GET","/db/sect")
    
    @classmethod
    def update_class(cls):
        a = PSC_BOX.call_json()
        if a != {'message': ''}:
            shps = ['1CEL', '2CEL', 'PSCH']
            b = []
            for i in list(a['SECT'].keys()):
                if a['SECT'][i]['SECT_BEFORE']['SHAPE'] in shps: b.append(int(i))
            global section_ids
            section_ids = [i for i in section_ids if i not in [int(j) for j in b]]
            PSC_BOX.sections = []
            for k, v in a['SECT'].items():
                shp = v['SECT_BEFORE']['SHAPE']
                if v["SECTTYPE"] == "PSC" and shp in shps:
                    AP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_A']
                    BP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_B']
                    CP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_C']
                    DP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_D']
                    JS = v['SECT_BEFORE']['JOINT']
                    if shp == "2CEL":
                        bi4 = DP[7]
                    else:
                        bi4 = 0
                    PSC_BOX(v['SECT_NAME'], k, shp, JS[0], JS[1], JS[2], JS[3], JS[4], JS[5], JS[6], JS[7],
                        v['SECT_BEFORE']['USE_AUTO_SHEAR_CHK_POS'][0][0], v['SECT_BEFORE']['USE_AUTO_SHEAR_CHK_POS'][0][2],
                        v['SECT_BEFORE']['USE_WEB_THICK_SHEAR'][0][0], v['SECT_BEFORE']['USE_WEB_THICK_SHEAR'][0][1], v['SECT_BEFORE']['USE_WEB_THICK_SHEAR'][0][2],
                        v['SECT_BEFORE']['USE_WEB_THICK'][0], AP[0], AP[1], AP[2], AP[3], AP[4], AP[5], BP[0], BP[1], BP[2], BP[3], BP[4], BP[5],
                        CP[0], CP[1], CP[2], CP[3], CP[4], CP[5], CP[6], CP[7], CP[8], CP[9], DP[0], DP[1], DP[2], DP[3], DP[4], DP[5], DP[6], bi4,
                        v['SECT_BEFORE']['OFFSET_PT'], v['SECT_BEFORE']['OFFSET_CENTER'], v['SECT_BEFORE']['USER_OFFSET_REF'], v['SECT_BEFORE']['HORZ_OFFSET_OPT'],
                        v['SECT_BEFORE']['VERT_OFFSET_OPT'], v['SECT_BEFORE']['USERDEF_OFFSET_YI'], v['SECT_BEFORE']['USERDEF_OFFSET_ZI'],
                        v['SECT_BEFORE']['USE_SHEAR_DEFORM'], v['SECT_BEFORE']['USE_WARPING_EFFECT'], v['SECT_BEFORE']['WARPING_CHK_AUTO_I'],
                        v['SECT_BEFORE']['WARPING_CHK_AUTO_J'], v['SECT_BEFORE']['SHEAR_CHK'], v['SECT_BEFORE']['WARPING_CHK_POS_I'],
                        v['SECT_BEFORE']['WARPING_CHK_POS_J'], v['SECT_BEFORE']['SHEAR_CHK_POS'][0][0], v['SECT_BEFORE']['SHEAR_CHK_POS'][0][2],
                        v['SECT_BEFORE']['WEB_THICK_SHEAR'][0][0], v['SECT_BEFORE']['WEB_THICK_SHEAR'][0][1], v['SECT_BEFORE']['WEB_THICK_SHEAR'][0][2],
                        v['SECT_BEFORE']['WEB_THICK'][0], v['SECT_BEFORE']['USE_SYMMETRIC'], v['SECT_BEFORE']['USE_SMALL_HOLE'], v['SECT_BEFORE']['USE_USER_DEF_MESHSIZE'],
                        v['SECT_BEFORE']['USE_USER_INTPUT_STIFF'], v['SECT_BEFORE']['PSC_OPT1'], v['SECT_BEFORE']['PSC_OPT2'])
#---------------------------------------------------------------------------------------------------------------

#22 Class to define PSC n-CELL section
class PSC_NCELL:
    sections = []
    
    def __init__(self, name = "nCell", id = 0, shape = "NCEL",  z1 = True, z3 = True, t1 = True, t2 = True, t3 = True, tt = True, 
        h1 = 2, h2 = 0.3, h3 = 0.2, h4 = 0.25, h5 = 0.3, b1 = 10, b2 = 1.5, b3 = 0.25, b4 = 0.3, b5 = 0.3, b6 = 0.25, b7 = 1, b8 = 0, 
        offset="CT", center_loc = 0, uor = 0, ho = 0, vo = 0, ho_i = 0, vo_i = 0, sd = True, we = True,
        wcai = True, wcaj = True, shck = True, wcpi = [[0]*6, [0]*6], wcpj = [[0]*6, [0]*6], z1v = 0, z3v = 0, t1v = 0, t2v = 0, t3v = 0, ttv = 0, 
        symm = True, smhl = False, mesh = False, user_stiff = False, opt1 = "SLOPE", opt2 = "3"):
        
        if len(section_ids) == 0 and id == 0: 
            section_count = 1
        elif len(section_ids) != 0 and id == 0:
            section_count = max(section_ids) + 1
        if id != 0:
            if id in section_ids and id in [i.ID for i in PSC_NCELL.sections]:
                print(f"Section ID {id}, already exists and is now updated with new input.")
            elif id in section_ids and id not in [i.ID for i in PSC_NCELL.sections]:
                section_count = max(section_ids) + 1
                print(f"Section ID {id} already exists.  New ID {section_count} is assigned to the section {name}.")
            else:
                section_count = id
        
        self.NAME = name
        self.ID = section_count
        self.SHAPE = shape
        self.Z1 = z1
        self.Z3 = z3
        self.T1 = t1
        self.T2 = t2
        self.T3 = t3
        self.TT = tt
        self.H1 = h1
        self.H2 = h2
        self.H3 = h3
        self.H4 = h4
        self.H5 = h5
        self.B1 = b1
        self.B2 = b2
        self.B3 = b3
        self.B4 = b4
        self.B5 = b5
        self.B6 = b6
        self.B7 = b7
        self.B8 = b8
        self.OFFSET = offset
        self.CL = center_loc
        self.UOR = uor
        self.HO = ho
        self.VO = vo
        self.HOI = ho_i
        self.VOI = vo_i
        self.SD = sd
        self.WE = we
        self.WCAI = wcai
        self.WCAJ = wcaj
        self.SHCK = shck
        self.WCPI = wcpi
        self.WCPJ = wcpj
        self.Z1V = z1v
        self.Z3V = z3v
        self.T1V = t1v
        self.T2V = t2v
        self.T3V = t3v
        self.TTV = ttv
        self.SYMM = symm
        self.SMHL = smhl
        self.MESH = mesh
        self.US = user_stiff
        self.OPT1 = opt1
        self.OPT2 = opt2
        PSC_NCELL.sections.append(self)
        section_ids.append(int(section_count))
    
    @classmethod
    def make_json(cls):
        json = {"Assign":{}}
        for k in cls.sections:
            json["Assign"][k.ID] = {
                "SECTTYPE": "PSC",
                "SECT_NAME": k.NAME,
                "SECT_BEFORE": {
                "OFFSET_PT": k.OFFSET,
                "OFFSET_CENTER": k.CL,
                "USER_OFFSET_REF": k.UOR,
                "HORZ_OFFSET_OPT": k.HO,
                "USERDEF_OFFSET_YI": k.HOI,
                "VERT_OFFSET_OPT": k.VO,
                "USERDEF_OFFSET_ZI": k.VOI,
                "USE_SHEAR_DEFORM": k.SD,
                "USE_WARPING_EFFECT": k.WE,
                "SHAPE": k.SHAPE,
                "SECT_I":{
                    "vSIZE_PSC_A": [k.H1, k.H2, k.H3, k.H4, k.H5],
                    "vSIZE_PSC_B": [k.B1, k.B2, k.B3, k.B4, k.B5, k.B6, k.B7, k.B8],
                    "SWIDTH": k.H1
                },
                "WARPING_CHK_AUTO_I": k.WCAI,
                "WARPING_CHK_AUTO_J": k.WCAJ,
                "SHEAR_CHK": k.SHCK,
                "WARPING_CHK_POS_I": k.WCPI,
                "WARPING_CHK_POS_J": k.WCPJ,
                "USE_AUTO_SHEAR_CHK_POS": [[k.Z1, False, k.Z3], [False, False, False]],
                "SHEAR_CHK_POS":[[k.Z1V, 0, k.Z3V], [0, 0, 0]],
                "USE_WEB_THICK":[k.TT, False],
                "WEB_THICK":[k.TTV, 0],
                "USE_WEB_THICK_SHEAR":[[k.T1, k.T2, k.T3],[False, False, False]],
                "WEB_THICK_SHEAR":[[k.T1V, k.T2V, k.T3V],[0, 0, 0]],
                "USE_SYMMETRIC": k.SYMM,
                "USE_SMALL_HOLE": k.SMHL,
                "USE_USER_DEF_MESHSIZE": k.MESH,
                "USE_USER_INTPUT_STIFF": k.US,
                "PSC_OPT1": k.OPT1,
                "PSC_OPT2": k.OPT2,
                }
            }
        return json
    
    @classmethod
    def create(cls):
        MidasAPI("PUT","/db/sect", PSC_NCELL.make_json())
    
    @classmethod
    def call_json(cls):
        return MidasAPI("GET","/db/sect")
    
    @classmethod
    def update_class(cls):
        a = PSC_NCELL.call_json()
        if a != {'message': ''}:
            b = []
            for i in list(a['SECT'].keys()):
                if a['SECT'][i]['SECT_BEFORE']['SHAPE'] == 'NCEL': b.append(int(i))
            global section_ids
            section_ids = [i for i in section_ids if i not in [int(j) for j in b]]
            PSC_NCELL.sections = []
            for k, v in a['SECT'].items():
                shp = v['SECT_BEFORE']['SHAPE']
                if v["SECTTYPE"] == "PSC" and shp == "NCEL":
                    AP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_A']
                    BP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_B']
                    PSC_NCELL(v['SECT_NAME'], k, shp, v['SECT_BEFORE']['USE_AUTO_SHEAR_CHK_POS'][0][0], v['SECT_BEFORE']['USE_AUTO_SHEAR_CHK_POS'][0][2],
                        v['SECT_BEFORE']['USE_WEB_THICK_SHEAR'][0][0], v['SECT_BEFORE']['USE_WEB_THICK_SHEAR'][0][1], v['SECT_BEFORE']['USE_WEB_THICK_SHEAR'][0][2],
                        v['SECT_BEFORE']['USE_WEB_THICK'][0], AP[0], AP[1], AP[2], AP[3], AP[4], BP[0], BP[1], BP[2], BP[3], BP[4], BP[5], BP[6], BP[7],
                        v['SECT_BEFORE']['OFFSET_PT'], v['SECT_BEFORE']['OFFSET_CENTER'], v['SECT_BEFORE']['USER_OFFSET_REF'], v['SECT_BEFORE']['HORZ_OFFSET_OPT'],
                        v['SECT_BEFORE']['VERT_OFFSET_OPT'], v['SECT_BEFORE']['USERDEF_OFFSET_YI'], v['SECT_BEFORE']['USERDEF_OFFSET_ZI'],
                        v['SECT_BEFORE']['USE_SHEAR_DEFORM'], v['SECT_BEFORE']['USE_WARPING_EFFECT'], v['SECT_BEFORE']['WARPING_CHK_AUTO_I'],
                        v['SECT_BEFORE']['WARPING_CHK_AUTO_J'], v['SECT_BEFORE']['SHEAR_CHK'], v['SECT_BEFORE']['WARPING_CHK_POS_I'],
                        v['SECT_BEFORE']['WARPING_CHK_POS_J'], v['SECT_BEFORE']['SHEAR_CHK_POS'][0][0], v['SECT_BEFORE']['SHEAR_CHK_POS'][0][2],
                        v['SECT_BEFORE']['WEB_THICK_SHEAR'][0][0], v['SECT_BEFORE']['WEB_THICK_SHEAR'][0][1], v['SECT_BEFORE']['WEB_THICK_SHEAR'][0][2],
                        v['SECT_BEFORE']['WEB_THICK'][0], v['SECT_BEFORE']['USE_SYMMETRIC'], v['SECT_BEFORE']['USE_SMALL_HOLE'], v['SECT_BEFORE']['USE_USER_DEF_MESHSIZE'],
                        v['SECT_BEFORE']['USE_USER_INTPUT_STIFF'], v['SECT_BEFORE']['PSC_OPT1'], v['SECT_BEFORE']['PSC_OPT2'])
#---------------------------------------------------------------------------------------------------------------

#23 Class to define PSC n-CELL 2 section
class PSC_NCELL2:
    sections = []
    
    def __init__(self, name = "nCell2", id = 0, shape = "NCE2", jo = False, ji = False, z1 = True, z3 = True, t1 = True, t2 = True, t3 = True, tt = True, 
        slb = 10, ho1 = 0.2, ho2 = 0.1, ho21 = 0, ho3 = 0.3, ho4 = 1.4, bo1 = 1, bo11 = 0, bo2 = 0.5, bo3 = 0.5, bo4 = 1.75, bo5 = 0.5, hi1 = 0.3, hi2 = 0.15, hi21 = 0, 
        hi3 = 0.15, hi4 = 0.2, hi5 = 0.2, hi6 = 0.25, bi1 = 0.25, bi2 = 0.3, bi21 = 0, bi3 = 0.3, bi4 = 0.4, bi5 = 0.4, bi6 = 0.125, bi7 = 0.3, bi8 = 0.4, 
        r1 = 1, r2 = 0.5, offset="CT", center_loc = 0, uor = 0, ho = 0, vo = 0, ho_i = 0, vo_i = 0, sd = True, we = True, wcai = True, wcaj = True, shck = True, 
        wcpi = [[0]*6, [0]*6], wcpj = [[0]*6, [0]*6], z1v = 0, z3v = 0, t1v = 0, t2v = 0, t3v = 0, ttv = 0,  symm = True, smhl = False, 
        mesh = False, user_stiff = False, opt1 = "POLYGON", opt2 = "3"):
        
        if len(section_ids) == 0 and id == 0: 
            section_count = 1
        elif len(section_ids) != 0 and id == 0:
            section_count = max(section_ids) + 1
        if id != 0:
            if id in section_ids and id in [i.ID for i in PSC_NCELL2.sections]:
                print(f"Section ID {id}, already exists and is now updated with new input.")
            elif id in section_ids and id not in [i.ID for i in PSC_NCELL2.sections]:
                section_count = max(section_ids) + 1
                print(f"Section ID {id} already exists.  New ID {section_count} is assigned to the section {name}.")
            else:
                section_count = id
        
        self.NAME = name
        self.ID = section_count
        self.SHAPE = shape
        self.JO = jo
        self.JI = ji
        self.Z1 = z1
        self.Z3 = z3
        self.T1 = t1
        self.T2 = t2
        self.T3 = t3
        self.TT = tt
        self.SLB = slb
        self.HO1 = ho1
        self.HO2 = ho2
        self.HO21 = ho21
        self.HO3 = ho3
        self.HO4 = ho4
        self.BO1 = bo1
        self.BO11 = bo11
        self.BO2 = bo2
        self.BO3 = bo3
        self.BO4 = bo4
        self.BO5 = bo5
        self.HI1 = hi1
        self.HI2 = hi2
        self.HI21 = hi21
        self.HI3 = hi3
        self.HI4 = hi4
        self.HI5 = hi5
        self.HI6 = hi6
        self.BI1 = bi1
        self.BI2 = bi2
        self.BI21 = bi21
        self.BI3 = bi3
        self.BI4 = bi4
        self.BI5 = bi5
        self.BI6 = bi6
        self.BI7 = bi7
        self.BI8 = bi8
        self.R1 = r1
        self.R2 = r2
        self.OFFSET = offset
        self.CL = center_loc
        self.UOR = uor
        self.HO = ho
        self.VO = vo
        self.HOI = ho_i
        self.VOI = vo_i
        self.SD = sd
        self.WE = we
        self.WCAI = wcai
        self.WCAJ = wcaj
        self.SHCK = shck
        self.WCPI = wcpi
        self.WCPJ = wcpj
        self.Z1V = z1v
        self.Z3V = z3v
        self.T1V = t1v
        self.T2V = t2v
        self.T3V = t3v
        self.TTV = ttv
        self.SYMM = symm
        self.SMHL = smhl
        self.MESH = mesh
        self.US = user_stiff
        self.OPT1 = opt1
        self.OPT2 = opt2
        PSC_NCELL2.sections.append(self)
        section_ids.append(int(section_count))
    
    @classmethod
    def make_json(cls):
        json = {"Assign":{}}
        for k in cls.sections:
            json["Assign"][k.ID] = {
                "SECTTYPE": "PSC",
                "SECT_NAME": k.NAME,
                "SECT_BEFORE": {
                "OFFSET_PT": k.OFFSET,
                "OFFSET_CENTER": k.CL,
                "USER_OFFSET_REF": k.UOR,
                "HORZ_OFFSET_OPT": k.HO,
                "USERDEF_OFFSET_YI": k.HOI,
                "VERT_OFFSET_OPT": k.VO,
                "USERDEF_OFFSET_ZI": k.VOI,
                "USE_SHEAR_DEFORM": k.SD,
                "USE_WARPING_EFFECT": k.WE,
                "SHAPE": k.SHAPE,
                "SECT_I":{
                    "vSIZE_PSC_A": [k.HO1, k.HO2, k.HO21, k.HO3, k.HO4, k.BO1, k.BO11, k.BO2, k.BO3, k.BO4, k.BO5],
                    "vSIZE_PSC_B": [k.HI1, k.HI2, k.HI21, k.HI3, k.HI4, k.HI5, k.HI6, k.BI1, k.BI2, k.BI21, k.BI3, k.BI4, k.BI5, k.BI6, k.BI7, k.BI8, k.R1, k.R2],
                    "vSIZE_PSC_C": [k.HO1, k.HO2, k.HO21, k.HO3, k.HO4, k.BO1, k.BO11, k.BO2, k.BO3, k.BO4, k.BO5],
                    "vSIZE_PSC_D": [k.HI1, k.HI2, k.HI21, k.HI3, k.HI4, k.HI5, k.HI6, k.BI1, k.BI2, k.BI21, k.BI3, k.BI4, k.BI5, k.BI6, k.BI7, k.BI8, k.R1, k.R2],
                    "SWIDTH": k.SLB
                },
                "WARPING_CHK_AUTO_I": k.WCAI,
                "WARPING_CHK_AUTO_J": k.WCAJ,
                "SHEAR_CHK": k.SHCK,
                "WARPING_CHK_POS_I": k.WCPI,
                "WARPING_CHK_POS_J": k.WCPJ,
                "USE_AUTO_SHEAR_CHK_POS": [[k.Z1, False, k.Z3], [False, False, False]],
                "SHEAR_CHK_POS":[[k.Z1V, 0, k.Z3V], [0, 0, 0]],
                "USE_WEB_THICK":[k.TT, False],
                "WEB_THICK":[k.TTV, 0],
                "USE_WEB_THICK_SHEAR":[[k.T1, k.T2, k.T3],[False, False, False]],
                "WEB_THICK_SHEAR":[[k.T1V, k.T2V, k.T3V],[0, 0, 0]],
                "USE_SYMMETRIC": k.SYMM,
                "USE_SMALL_HOLE": k.SMHL,
                "USE_USER_DEF_MESHSIZE": k.MESH,
                "USE_USER_INTPUT_STIFF": k.US,
                "PSC_OPT1": k.OPT1,
                "PSC_OPT2": k.OPT2,
                "JOINT":[k.JO, k.JI]
                }
            }
        return json
    
    @classmethod
    def create(cls):
        MidasAPI("PUT","/db/sect", PSC_NCELL2.make_json())
    
    @classmethod
    def call_json(cls):
        return MidasAPI("GET","/db/sect")
    
    @classmethod
    def update_class(cls):
        a = PSC_NCELL2.call_json()
        if a != {'message': ''}:
            b = []
            for i in list(a['SECT'].keys()):
                if a['SECT'][i]['SECT_BEFORE']['SHAPE'] == 'NCE2': b.append(int(i))
            global section_ids
            section_ids = [i for i in section_ids if i not in [int(j) for j in b]]
            PSC_NCELL2.sections = []
            for k, v in a['SECT'].items():
                shp = v['SECT_BEFORE']['SHAPE']
                if v["SECTTYPE"] == "PSC" and shp == 'NCE2':
                    AP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_A']
                    BP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_B']
                    JS = v['SECT_BEFORE']['JOINT']
                    PSC_NCELL2(v['SECT_NAME'], k, shp, JS[0], JS[1], v['SECT_BEFORE']['USE_AUTO_SHEAR_CHK_POS'][0][0], v['SECT_BEFORE']['USE_AUTO_SHEAR_CHK_POS'][0][2],
                        v['SECT_BEFORE']['USE_WEB_THICK_SHEAR'][0][0], v['SECT_BEFORE']['USE_WEB_THICK_SHEAR'][0][1], v['SECT_BEFORE']['USE_WEB_THICK_SHEAR'][0][2],
                        v['SECT_BEFORE']['USE_WEB_THICK'][0], v['SECT_BEFORE']['SECT_I']['SWIDTH'], AP[0], AP[1], AP[2], AP[3], AP[4], AP[5], AP[6], AP[7], AP[8], 
                        AP[9], AP[10], BP[0], BP[1], BP[2], BP[3], BP[4], BP[5], BP[6], BP[7], BP[8], BP[9], BP[10], BP[11], BP[12], BP[13], BP[14], BP[15], BP[16], BP[17],
                        v['SECT_BEFORE']['OFFSET_PT'], v['SECT_BEFORE']['OFFSET_CENTER'], v['SECT_BEFORE']['USER_OFFSET_REF'], v['SECT_BEFORE']['HORZ_OFFSET_OPT'],
                        v['SECT_BEFORE']['VERT_OFFSET_OPT'], v['SECT_BEFORE']['USERDEF_OFFSET_YI'], v['SECT_BEFORE']['USERDEF_OFFSET_ZI'],
                        v['SECT_BEFORE']['USE_SHEAR_DEFORM'], v['SECT_BEFORE']['USE_WARPING_EFFECT'], v['SECT_BEFORE']['WARPING_CHK_AUTO_I'],
                        v['SECT_BEFORE']['WARPING_CHK_AUTO_J'], v['SECT_BEFORE']['SHEAR_CHK'], v['SECT_BEFORE']['WARPING_CHK_POS_I'],
                        v['SECT_BEFORE']['WARPING_CHK_POS_J'], v['SECT_BEFORE']['SHEAR_CHK_POS'][0][0], v['SECT_BEFORE']['SHEAR_CHK_POS'][0][2],
                        v['SECT_BEFORE']['WEB_THICK_SHEAR'][0][0], v['SECT_BEFORE']['WEB_THICK_SHEAR'][0][1], v['SECT_BEFORE']['WEB_THICK_SHEAR'][0][2],
                        v['SECT_BEFORE']['WEB_THICK'][0], v['SECT_BEFORE']['USE_SYMMETRIC'], v['SECT_BEFORE']['USE_SMALL_HOLE'], v['SECT_BEFORE']['USE_USER_DEF_MESHSIZE'],
                        v['SECT_BEFORE']['USE_USER_INTPUT_STIFF'], v['SECT_BEFORE']['PSC_OPT1'], v['SECT_BEFORE']['PSC_OPT2'])
#---------------------------------------------------------------------------------------------------------------

#24 Class to define non-composite PSC I and Mid sections
class PSC_I:
    sections = []
    
    def __init__(self, name = "PSC I", id = 0, shape = "PSCI", j1 = False, jl1 = True, jl2 = False, jl3 = False, jl4 = False, jr1 = True, jr2 = False, jr3 = False, 
        jr4 = False, z1 = True, z3 = True, t1 = True, t2 = True, t3 = True, tt = True, h1 = 0, hl1 = 0.15, hl2 = 0.2, hl21 = 0.05, hl22 = 0, hl3 = 1, hl4 = 0.15, 
        hl41 = 0, hl42 = 0, hl5 = 0.2, bl1 = 0.125, bl2 = 0.75, bl21 = 0.5, bl22 = 0, bl4 = 0.3, bl41 = 0, bl42 = 0, hr1 = 0.15, hr2 = 0.2, hr21 = 0.05, hr22 = 0, 
        hr3 = 1, hr4 = 0.15, hr41 = 0, hr42 = 0, hr5 = 0.2, br1 = 0.125, br2 = 0.75, br21 = 0.5, br22 = 0, br4 = 0.3, br41 = 0, br42 = 0, offset="CT", center_loc = 0, 
        uor = 0, ho = 0, vo = 0, ho_i = 0, vo_i = 0, sd = True, we = True, wcai = True, wcaj = True, shck = True, wcpi = [[0]*6, [0]*6], wcpj = [[0]*6, [0]*6], 
        z1v = 0, z3v = 0, t1v = 0, t2v = 0, t3v = 0, ttv = 0, symm = True, smhl = False, mesh = False, user_stiff = False, opt1 = "", opt2 = ""):
        
        if len(section_ids) == 0 and id == 0: 
            section_count = 1
        elif len(section_ids) != 0 and id == 0:
            section_count = max(section_ids) + 1
        if id != 0:
            if id in section_ids and id in [i.ID for i in PSC_I.sections]:
                print(f"Section ID {id}, already exists and is now updated with new input.")
            elif id in section_ids and id not in [i.ID for i in PSC_I.sections]:
                section_count = max(section_ids) + 1
                print(f"Section ID {id} already exists.  New ID {section_count} is assigned to the section {name}.")
            else:
                section_count = id
        
        self.NAME = name
        self.ID = section_count
        self.SHAPE = shape
        self.J1 = j1
        self.JL1 = jl1
        self.JL2 = jl2
        self.JL3 = jl3
        self.JL4 = jl4
        self.JR1 = jr1
        self.JR2 = jr2
        self.JR3 = jr3
        self.JR4 = jr4
        self.Z1 = z1
        self.Z3 = z3
        self.T1 = t1
        self.T2 = t2
        self.T3 = t3
        self.TT = tt
        self.H1 = h1
        self.HL1 = hl1
        self.HL2 = hl2
        self.HL21 = hl21
        self.HL22 = hl22
        self.HL3 = hl3
        self.HL4 = hl4
        self.HL41 = hl41
        self.HL42 = hl42
        self.HL5 = hl5
        self.BL1 = bl1
        self.BL2 = bl2
        self.BL21 = bl21
        self.BL22 = bl22
        self.BL4 = bl4
        self.BL41 = bl41
        self.BL42 = bl42
        self.HR1 = hr1
        self.HR2 = hr2
        self.HR21 = hr21
        self.HR22 = hr22
        self.HR3 = hr3
        self.HR4 = hr4
        self.HR41 = hr41
        self.HR42 = hr42
        self.HR5 = hr5
        self.BR1 = br1
        self.BR2 = br2
        self.BR21 = br21
        self.BR22 = br22
        self.BR4 = br4
        self.BR41 = br41
        self.BR42 = br42
        self.OFFSET = offset
        self.CL = center_loc
        self.UOR = uor
        self.HO = ho
        self.VO = vo
        self.HOI = ho_i
        self.VOI = vo_i
        self.SD = sd
        self.WE = we
        self.WCAI = wcai
        self.WCAJ = wcaj
        self.SHCK = shck
        self.WCPI = wcpi
        self.WCPJ = wcpj
        self.Z1V = z1v
        self.Z3V = z3v
        self.T1V = t1v
        self.T2V = t2v
        self.T3V = t3v
        self.TTV = ttv
        self.SYMM = symm
        self.SMHL = smhl
        self.MESH = mesh
        self.US = user_stiff
        self.OPT1 = opt1
        self.OPT2 = opt2
        PSC_I.sections.append(self)
        section_ids.append(int(section_count))
    
    @classmethod
    def make_json(cls):
        json = {"Assign":{}}
        for k in cls.sections:
            json["Assign"][k.ID] = {
                "SECTTYPE": "PSC",
                "SECT_NAME": k.NAME,
                "SECT_BEFORE": {
                "OFFSET_PT": k.OFFSET,
                "OFFSET_CENTER": k.CL,
                "USER_OFFSET_REF": k.UOR,
                "HORZ_OFFSET_OPT": k.HO,
                "USERDEF_OFFSET_YI": k.HOI,
                "VERT_OFFSET_OPT": k.VO,
                "USERDEF_OFFSET_ZI": k.VOI,
                "USE_SHEAR_DEFORM": k.SD,
                "USE_WARPING_EFFECT": k.WE,
                "SHAPE": k.SHAPE,
                "SECT_I":{
                    "vSIZE_PSC_A": [k.H1, k.HL1, k.HL2, k.HL21, k.HL22, k.HL3, k.HL4, k.HL41, k.HL42, k.HL5],
                    "vSIZE_PSC_B": [k.BL1, k.BL2, k.BL21, k.BL22, k.BL4, k.BL41, k.BL42],
                    "vSIZE_PSC_C": [k.HR1, k.HR2, k.HR21, k.HR22, k.HR3, k.HR4, k.HR41, k.HR42, k.HR5],
                    "vSIZE_PSC_D": [k.BR1, k.BR2, k.BR21, k.BR22, k.BR4, k.BR41, k.BR42],
                    "SWIDTH": k.H1
                },
                "WARPING_CHK_AUTO_I": k.WCAI,
                "WARPING_CHK_AUTO_J": k.WCAJ,
                "SHEAR_CHK": k.SHCK,
                "WARPING_CHK_POS_I": k.WCPI,
                "WARPING_CHK_POS_J": k.WCPJ,
                "USE_AUTO_SHEAR_CHK_POS": [[k.Z1, False, k.Z3], [False, False, False]],
                "SHEAR_CHK_POS":[[k.Z1V, 0, k.Z3V], [0, 0, 0]],
                "USE_WEB_THICK":[k.TT, False],
                "WEB_THICK":[k.TTV, 0],
                "USE_WEB_THICK_SHEAR":[[k.T1, k.T2, k.T3],[False, False, False]],
                "WEB_THICK_SHEAR":[[k.T1V, k.T2V, k.T3V],[0, 0, 0]],
                "USE_SYMMETRIC": k.SYMM,
                "USE_SMALL_HOLE": k.SMHL,
                "USE_USER_DEF_MESHSIZE": k.MESH,
                "USE_USER_INTPUT_STIFF": k.US,
                "PSC_OPT1": k.OPT1,
                "PSC_OPT2": k.OPT2,
                "JOINT":[k.J1, k.JL1, k.JL2, k.JL3, k.JL4, k.JR1, k.JR2, k.JR3, k.JR4]
                }
            }
            #Modify PSC_D list for 2CEL section
            if k.SHAPE == "PSCM": 
                json["Assign"][k.ID]['SECT_BEFORE']['SECT_I']['vSIZE_PSC_B'] = [k.BL1, k.BL2, k.BL21, k.BL22, k.BL41, k.BL42]
                json["Assign"][k.ID]['SECT_BEFORE']['SECT_I']['vSIZE_PSC_D'] = [k.BR1, k.BR2, k.BR21, k.BR22, k.BR41, k.BR42]
        return json
    
    @classmethod
    def create(cls):
        MidasAPI("PUT","/db/sect", PSC_I.make_json())
    
    @classmethod
    def call_json(cls):
        return MidasAPI("GET","/db/sect")
    
    @classmethod
    def update_class(cls):
        a = PSC_I.call_json()
        if a != {'message': ''}:
            shps = ['PSCI', 'PSCM']
            b = []
            for i in list(a['SECT'].keys()):
                if a['SECT'][i]['SECT_BEFORE']['SHAPE'] in shps: b.append(int(i))
            global section_ids
            section_ids = [i for i in section_ids if i not in [int(j) for j in b]]
            PSC_I.sections = []
            for k, v in a['SECT'].items():
                shp = v['SECT_BEFORE']['SHAPE']
                if v["SECTTYPE"] == "PSC" and shp in shps:
                    AP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_A']
                    BP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_B']
                    CP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_C']
                    DP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_D']
                    JS = v['SECT_BEFORE']['JOINT']
                    if shp == "PSCM":
                        BP.insert(4, 0)
                        DP.insert(4, 0)
                    PSC_I(v['SECT_NAME'], k, shp, JS[0], JS[1], JS[2], JS[3], JS[4], JS[5], JS[6], JS[7], JS[8],
                        v['SECT_BEFORE']['USE_AUTO_SHEAR_CHK_POS'][0][0], v['SECT_BEFORE']['USE_AUTO_SHEAR_CHK_POS'][0][2],
                        v['SECT_BEFORE']['USE_WEB_THICK_SHEAR'][0][0], v['SECT_BEFORE']['USE_WEB_THICK_SHEAR'][0][1], v['SECT_BEFORE']['USE_WEB_THICK_SHEAR'][0][2],
                        v['SECT_BEFORE']['USE_WEB_THICK'][0], AP[0], AP[1], AP[2], AP[3], AP[4], AP[5], AP[6], AP[7], AP[8], AP[9], BP[0], BP[1], BP[2], BP[3], 
                        BP[4], BP[5], BP[6], CP[0], CP[1], CP[2], CP[3], CP[4], CP[5], CP[6], CP[7], CP[8], DP[0], DP[1], DP[2], DP[3], DP[4], DP[5], DP[6],
                        v['SECT_BEFORE']['OFFSET_PT'], v['SECT_BEFORE']['OFFSET_CENTER'], v['SECT_BEFORE']['USER_OFFSET_REF'], v['SECT_BEFORE']['HORZ_OFFSET_OPT'],
                        v['SECT_BEFORE']['VERT_OFFSET_OPT'], v['SECT_BEFORE']['USERDEF_OFFSET_YI'], v['SECT_BEFORE']['USERDEF_OFFSET_ZI'],
                        v['SECT_BEFORE']['USE_SHEAR_DEFORM'], v['SECT_BEFORE']['USE_WARPING_EFFECT'], v['SECT_BEFORE']['WARPING_CHK_AUTO_I'],
                        v['SECT_BEFORE']['WARPING_CHK_AUTO_J'], v['SECT_BEFORE']['SHEAR_CHK'], v['SECT_BEFORE']['WARPING_CHK_POS_I'],
                        v['SECT_BEFORE']['WARPING_CHK_POS_J'], v['SECT_BEFORE']['SHEAR_CHK_POS'][0][0], v['SECT_BEFORE']['SHEAR_CHK_POS'][0][2],
                        v['SECT_BEFORE']['WEB_THICK_SHEAR'][0][0], v['SECT_BEFORE']['WEB_THICK_SHEAR'][0][1], v['SECT_BEFORE']['WEB_THICK_SHEAR'][0][2],
                        v['SECT_BEFORE']['WEB_THICK'][0], v['SECT_BEFORE']['USE_SYMMETRIC'], v['SECT_BEFORE']['USE_SMALL_HOLE'], v['SECT_BEFORE']['USE_USER_DEF_MESHSIZE'],
                        v['SECT_BEFORE']['USE_USER_INTPUT_STIFF'], v['SECT_BEFORE']['PSC_OPT1'], v['SECT_BEFORE']['PSC_OPT2'])
#---------------------------------------------------------------------------------------------------------------

#25 Class to define non-composite PSC T section
class PSC_T:
    sections = []
    
    def __init__(self, name = "PSC T", id = 0, shape = "PSCT", j1 = False, jl1 = False, jl2 = True, jl3 = False, jl4 = False, jr1 = False, jr2 = False, jr3 = False, 
        jr4 = False, z1 = True, z3 = True, t1 = True, t2 = True, t3 = True, tt = True, h1 = 0, hl1 = 0.05, hl2 = 0.05, hl3 = 0.5, bl1 = 0.05, bl2 = 0.05, bl3 = 0.5, 
        bl4 = 0.6, hl21 = 0, hl22 = 0, hl31 = 0, hl32 = 0, bl21 = 0, bl22 = 0, bl31 = 0, bl32 = 0, hr1 = 0.05, hr2 = 0.05, hr3 = 0.5, br1 = 0.05, br2 = 0.05, br3 = 0.5, 
        br4 = 0.6, hr21 = 0, hr22 = 0, hr31 = 0, hr32 = 0, br21 = 0, br22 = 0, br31 = 0, br32 = 0, offset="CT", center_loc = 0, uor = 0, ho = 0, vo = 0, ho_i = 0, 
        vo_i = 0, sd = True, we = True, wcai = True, wcaj = True, shck = True, wcpi = [[0]*6, [0]*6], wcpj = [[0]*6, [0]*6], z1v = 0, z3v = 0, t1v = 0, t2v = 0, 
        t3v = 0, ttv = 0, symm = True, smhl = False, mesh = False, user_stiff = False, opt1 = "", opt2 = ""):
        
        if len(section_ids) == 0 and id == 0: 
            section_count = 1
        elif len(section_ids) != 0 and id == 0:
            section_count = max(section_ids) + 1
        if id != 0:
            if id in section_ids and id in [i.ID for i in PSC_T.sections]:
                print(f"Section ID {id}, already exists and is now updated with new input.")
            elif id in section_ids and id not in [i.ID for i in PSC_T.sections]:
                section_count = max(section_ids) + 1
                print(f"Section ID {id} already exists.  New ID {section_count} is assigned to the section {name}.")
            else:
                section_count = id
        
        self.NAME = name
        self.ID = section_count
        self.SHAPE = shape
        self.J1 = j1
        self.JL1 = jl1
        self.JL2 = jl2
        self.JL3 = jl3
        self.JL4 = jl4
        self.JR1 = jr1
        self.JR2 = jr2
        self.JR3 = jr3
        self.JR4 = jr4
        self.Z1 = z1
        self.Z3 = z3
        self.T1 = t1
        self.T2 = t2
        self.T3 = t3
        self.TT = tt
        self.H1 = h1
        self.HL1 = hl1
        self.HL2 = hl2
        self.HL3 = hl3
        self.HL21 = hl21
        self.HL22 = hl22
        self.HL31 = hl31
        self.HL32 = hl32
        self.BL1 = bl1
        self.BL2 = bl2
        self.BL3 = bl3
        self.BL4 = bl4
        self.BL21 = bl21
        self.BL22 = bl22
        self.BL31 = bl31
        self.BL32 = bl32
        self.HR1 = hr1
        self.HR2 = hr2
        self.HR3 = hr3
        self.HR21 = hr21
        self.HR22 = hr22
        self.HR31 = hr31
        self.HR32 = hr32
        self.BR1 = br1
        self.BR2 = br2
        self.BR3 = br3
        self.BR4 = br4
        self.BR21 = br21
        self.BR22 = br22
        self.BR31 = br31
        self.BR32 = br32
        self.OFFSET = offset
        self.CL = center_loc
        self.UOR = uor
        self.HO = ho
        self.VO = vo
        self.HOI = ho_i
        self.VOI = vo_i
        self.SD = sd
        self.WE = we
        self.WCAI = wcai
        self.WCAJ = wcaj
        self.SHCK = shck
        self.WCPI = wcpi
        self.WCPJ = wcpj
        self.Z1V = z1v
        self.Z3V = z3v
        self.T1V = t1v
        self.T2V = t2v
        self.T3V = t3v
        self.TTV = ttv
        self.SYMM = symm
        self.SMHL = smhl
        self.MESH = mesh
        self.US = user_stiff
        self.OPT1 = opt1
        self.OPT2 = opt2
        PSC_T.sections.append(self)
        section_ids.append(int(section_count))
    
    @classmethod
    def make_json(cls):
        json = {"Assign":{}}
        for k in cls.sections:
            json["Assign"][k.ID] = {
                "SECTTYPE": "PSC",
                "SECT_NAME": k.NAME,
                "SECT_BEFORE": {
                "OFFSET_PT": k.OFFSET,
                "OFFSET_CENTER": k.CL,
                "USER_OFFSET_REF": k.UOR,
                "HORZ_OFFSET_OPT": k.HO,
                "USERDEF_OFFSET_YI": k.HOI,
                "VERT_OFFSET_OPT": k.VO,
                "USERDEF_OFFSET_ZI": k.VOI,
                "USE_SHEAR_DEFORM": k.SD,
                "USE_WARPING_EFFECT": k.WE,
                "SHAPE": k.SHAPE,
                "SECT_I":{
                    "vSIZE_PSC_A": [k.H1, k.HL1, k.HL2, k.HL3, k.BL1, k.BL2, k.BL3, k.BL4],
                    "vSIZE_PSC_B": [k.HL21, k.HL22, k.HL21, k.HL32, k.BL21, k.BL22, k.BL31, k.BL32],
                    "vSIZE_PSC_C": [k.HR1, k.HR2, k.HR3, k.BR1, k.BR2, k.BR3, k.BR4],
                    "vSIZE_PSC_D": [k.HR21, k.HR22, k.HR21, k.HR32, k.BR21, k.BR22, k.BR31, k.BR32],
                    "SWIDTH": k.H1
                },
                "WARPING_CHK_AUTO_I": k.WCAI,
                "WARPING_CHK_AUTO_J": k.WCAJ,
                "SHEAR_CHK": k.SHCK,
                "WARPING_CHK_POS_I": k.WCPI,
                "WARPING_CHK_POS_J": k.WCPJ,
                "USE_AUTO_SHEAR_CHK_POS": [[k.Z1, False, k.Z3], [False, False, False]],
                "SHEAR_CHK_POS":[[k.Z1V, 0, k.Z3V], [0, 0, 0]],
                "USE_WEB_THICK":[k.TT, False],
                "WEB_THICK":[k.TTV, 0],
                "USE_WEB_THICK_SHEAR":[[k.T1, k.T2, k.T3],[False, False, False]],
                "WEB_THICK_SHEAR":[[k.T1V, k.T2V, k.T3V],[0, 0, 0]],
                "USE_SYMMETRIC": k.SYMM,
                "USE_SMALL_HOLE": k.SMHL,
                "USE_USER_DEF_MESHSIZE": k.MESH,
                "USE_USER_INTPUT_STIFF": k.US,
                "PSC_OPT1": k.OPT1,
                "PSC_OPT2": k.OPT2,
                "JOINT":[k.J1, k.JL1, k.JL2, k.JL3, k.JL4, k.JR1, k.JR2, k.JR3, k.JR4]
                }
            }
        return json
    
    @classmethod
    def create(cls):
        MidasAPI("PUT","/db/sect", PSC_T.make_json())
    
    @classmethod
    def call_json(cls):
        return MidasAPI("GET","/db/sect")
    
    @classmethod
    def update_class(cls):
        a = PSC_T.call_json()
        if a != {'message': ''}:
            b = []
            for i in list(a['SECT'].keys()):
                if a['SECT'][i]['SECT_BEFORE']['SHAPE'] == 'PSCT': b.append(int(i))
            global section_ids
            section_ids = [i for i in section_ids if i not in [int(j) for j in b]]
            PSC_T.sections = []
            for k, v in a['SECT'].items():
                shp = v['SECT_BEFORE']['SHAPE']
                if v["SECTTYPE"] == "PSC" and shp == "PSCT":
                    AP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_A']
                    BP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_B']
                    CP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_C']
                    DP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_D']
                    JS = v['SECT_BEFORE']['JOINT']
                    PSC_T(v['SECT_NAME'], k, shp, JS[0], JS[1], JS[2], JS[3], JS[4], JS[5], JS[6], JS[7], JS[8],
                        v['SECT_BEFORE']['USE_AUTO_SHEAR_CHK_POS'][0][0], v['SECT_BEFORE']['USE_AUTO_SHEAR_CHK_POS'][0][2],
                        v['SECT_BEFORE']['USE_WEB_THICK_SHEAR'][0][0], v['SECT_BEFORE']['USE_WEB_THICK_SHEAR'][0][1], v['SECT_BEFORE']['USE_WEB_THICK_SHEAR'][0][2],
                        v['SECT_BEFORE']['USE_WEB_THICK'][0], AP[0], AP[1], AP[2], AP[3], AP[4], AP[5], AP[6], AP[7], BP[0], BP[1], BP[2], BP[3], 
                        BP[4], BP[5], BP[6], BP[7], CP[0], CP[1], CP[2], CP[3], CP[4], CP[5], CP[6], DP[0], DP[1], DP[2], DP[3], DP[4], DP[5], DP[6], DP[7],
                        v['SECT_BEFORE']['OFFSET_PT'], v['SECT_BEFORE']['OFFSET_CENTER'], v['SECT_BEFORE']['USER_OFFSET_REF'], v['SECT_BEFORE']['HORZ_OFFSET_OPT'],
                        v['SECT_BEFORE']['VERT_OFFSET_OPT'], v['SECT_BEFORE']['USERDEF_OFFSET_YI'], v['SECT_BEFORE']['USERDEF_OFFSET_ZI'],
                        v['SECT_BEFORE']['USE_SHEAR_DEFORM'], v['SECT_BEFORE']['USE_WARPING_EFFECT'], v['SECT_BEFORE']['WARPING_CHK_AUTO_I'],
                        v['SECT_BEFORE']['WARPING_CHK_AUTO_J'], v['SECT_BEFORE']['SHEAR_CHK'], v['SECT_BEFORE']['WARPING_CHK_POS_I'],
                        v['SECT_BEFORE']['WARPING_CHK_POS_J'], v['SECT_BEFORE']['SHEAR_CHK_POS'][0][0], v['SECT_BEFORE']['SHEAR_CHK_POS'][0][2],
                        v['SECT_BEFORE']['WEB_THICK_SHEAR'][0][0], v['SECT_BEFORE']['WEB_THICK_SHEAR'][0][1], v['SECT_BEFORE']['WEB_THICK_SHEAR'][0][2],
                        v['SECT_BEFORE']['WEB_THICK'][0], v['SECT_BEFORE']['USE_SYMMETRIC'], v['SECT_BEFORE']['USE_SMALL_HOLE'], v['SECT_BEFORE']['USE_USER_DEF_MESHSIZE'],
                        v['SECT_BEFORE']['USE_USER_INTPUT_STIFF'], v['SECT_BEFORE']['PSC_OPT1'], v['SECT_BEFORE']['PSC_OPT2'])
#---------------------------------------------------------------------------------------------------------------

#26 Class to define Composite PSC I section
class COMP_PSC_I:
    sections = []
    
    def __init__(self, name = "Comp PSC I", id = 0, shape = "CI", j1 = False, jl1 = True, jl2 = False, jl3 = False, jl4 = False, jr1 = True, jr2 = False, jr3 = False, 
        jr4 = False, h1 = 0, hl1 = 0.15, hl2 = 0.2, hl21 = 0.05, hl22 = 0, hl3 = 1, hl4 = 0.15, hl41 = 0, hl42 = 0, hl5 = 0.2, bl1 = 0.125, bl2 = 0.75, bl21 = 0.5, 
        bl22 = 0, bl4 = 0.3, bl41 = 0, bl42 = 0, hr1 = 0.15, hr2 = 0.2, hr21 = 0.05, hr22 = 0, hr3 = 1, hr4 = 0.15, hr41 = 0, hr42 = 0, hr5 = 0.2, br1 = 0.125, 
        br2 = 0.75, br21 = 0.5, br22 = 0, br4 = 0.3, br41 = 0, br42 = 0, offset="CT", center_loc = 0, uor = 0, ho = 0, vo = 0, ho_i = 0, vo_i = 0, sd = True, we = True, 
        m = 1.01, den_rat = 1, poisn_g = 0.2, poisn_s = 0.2, thermal_rat = 1, E_multi = False, m_creep = 3, m_shrink = 6, opt1 = "", opt2 = "", Bc = 2, tc = 0.22, Hh = 0):
        
        if len(section_ids) == 0 and id == 0: 
            section_count = 1
        elif len(section_ids) != 0 and id == 0:
            section_count = max(section_ids) + 1
        if id != 0:
            if id in section_ids and id in [i.ID for i in COMP_PSC_I.sections]:
                print(f"Section ID {id}, already exists and is now updated with new input.")
            elif id in section_ids and id not in [i.ID for i in COMP_PSC_I.sections]:
                section_count = max(section_ids) + 1
                print(f"Section ID {id} already exists.  New ID {section_count} is assigned to the section {name}.")
            else:
                section_count = id
        
        self.NAME = name
        self.ID = section_count
        self.SHAPE = shape
        self.J1 = j1
        self.JL1 = jl1
        self.JL2 = jl2
        self.JL3 = jl3
        self.JL4 = jl4
        self.JR1 = jr1
        self.JR2 = jr2
        self.JR3 = jr3
        self.JR4 = jr4
        self.H1 = h1
        self.HL1 = hl1
        self.HL2 = hl2
        self.HL21 = hl21
        self.HL22 = hl22
        self.HL3 = hl3
        self.HL4 = hl4
        self.HL41 = hl41
        self.HL42 = hl42
        self.HL5 = hl5
        self.BL1 = bl1
        self.BL2 = bl2
        self.BL21 = bl21
        self.BL22 = bl22
        self.BL4 = bl4
        self.BL41 = bl41
        self.BL42 = bl42
        self.HR1 = hr1
        self.HR2 = hr2
        self.HR21 = hr21
        self.HR22 = hr22
        self.HR3 = hr3
        self.HR4 = hr4
        self.HR41 = hr41
        self.HR42 = hr42
        self.HR5 = hr5
        self.BR1 = br1
        self.BR2 = br2
        self.BR21 = br21
        self.BR22 = br22
        self.BR4 = br4
        self.BR41 = br41
        self.BR42 = br42
        self.OFFSET = offset
        self.CL = center_loc
        self.UOR = uor
        self.HO = ho
        self.VO = vo
        self.HOI = ho_i
        self.VOI = vo_i
        self.SD = sd
        self.WE = we
        self.M = m
        self.DEN_RAT = den_rat
        self.PG = poisn_g
        self.PS = poisn_s
        self.TR = thermal_rat
        self.EMULT = E_multi
        self.MCR = m_creep
        self.MSH = m_shrink
        self.OPT1 = opt1
        self.OPT2 = opt2
        self.BC = Bc
        self.TC = tc
        self.HH = Hh
        COMP_PSC_I.sections.append(self)
        section_ids.append(int(section_count))
    
    @classmethod
    def make_json(cls):
        json = {"Assign":{}}
        for k in cls.sections:
            json["Assign"][k.ID] = {
                "SECTTYPE": "COMPOSITE",
                "SECT_NAME": k.NAME,
                "SECT_BEFORE": {
                "OFFSET_PT": k.OFFSET,
                "OFFSET_CENTER": k.CL,
                "USER_OFFSET_REF": k.UOR,
                "HORZ_OFFSET_OPT": k.HO,
                "USERDEF_OFFSET_YI": k.HOI,
                "VERT_OFFSET_OPT": k.VO,
                "USERDEF_OFFSET_ZI": k.VOI,
                "USE_SHEAR_DEFORM": k.SD,
                "USE_WARPING_EFFECT": k.WE,
                "SHAPE": k.SHAPE,
                "SECT_I":{
                    "vSIZE_PSC_A": [k.H1, k.HL1, k.HL2, k.HL21, k.HL22, k.HL3, k.HL4, k.HL41, k.HL42, k.HL5],
                    "vSIZE_PSC_B": [k.BL1, k.BL2, k.BL21, k.BL22, k.BL4, k.BL41, k.BL42],
                    "vSIZE_PSC_C": [k.HR1, k.HR2, k.HR21, k.HR22, k.HR3, k.HR4, k.HR41, k.HR42, k.HR5],
                    "vSIZE_PSC_D": [k.BR1, k.BR2, k.BR21, k.BR22, k.BR4, k.BR41, k.BR42],
                },
                "MATL_ELAST": k.M,
                "MATL_DENS": k.DEN_RAT,
                "MATL_POIS_S": k.PG,
                "MATL_POIS_C": k.PS,
                "MATL_THERMAL": k.TR,
                "USE_MULTI_ELAST": k.EMULT,
                "LONGTERM_ESEC": k.MCR,
                "SHRINK_ESEC": k.MSH,
                "PSC_OPT1": k.OPT1,
                "PSC_OPT2": k.OPT2,
                "JOINT":[k.J1, k.JL1, k.JL2, k.JL3, k.JL4, k.JR1, k.JR2, k.JR3, k.JR4]
                },
                "SECT_AFTER":{
                    "SLAB": [k.BC, k.TC, k.HH]
                }
            }
        return json
    
    @classmethod
    def create(cls):
        MidasAPI("PUT","/db/sect", COMP_PSC_I.make_json())
    
    @classmethod
    def call_json(cls):
        return MidasAPI("GET","/db/sect")
    
    @classmethod
    def update_class(cls):
        a = COMP_PSC_I.call_json()
        if a != {'message': ''}:
            b = []
            for i in list(a['SECT'].keys()):
                if a['SECT'][i]['SECT_BEFORE']['SHAPE'] == 'CI': b.append(int(i))
            global section_ids
            section_ids = [i for i in section_ids if i not in [int(j) for j in b]]
            COMP_PSC_I.sections = []
            for k, v in a['SECT'].items():
                shp = v['SECT_BEFORE']['SHAPE']
                if v["SECTTYPE"] == "COMPOSITE" and shp == "CI":
                    AP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_A']
                    BP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_B']
                    CP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_C']
                    DP = v['SECT_BEFORE']['SECT_I']['vSIZE_PSC_D']
                    JS = v['SECT_BEFORE']['JOINT']
                    if 'LONGTERM_ESEC' not in list(v['SECT_BEFORE'].keys()): v['SECT_BEFORE']['LONGTERM_ESEC'] = 0
                    if 'SHRINK_ESEC' not in list(v['SECT_BEFORE'].keys()): v['SECT_BEFORE']['SHRINK_ESEC'] = 0
                    COMP_PSC_I(v['SECT_NAME'], k, shp, JS[0], JS[1], JS[2], JS[3], JS[4], JS[5], JS[6], JS[7], JS[8], AP[0], AP[1], AP[2], AP[3], AP[4], AP[5], AP[6],
                        AP[7], AP[8], AP[9], BP[0], BP[1], BP[2], BP[3], BP[4], BP[5], BP[6], CP[0], CP[1], CP[2], CP[3], CP[4], CP[5], CP[6], CP[7], CP[8], DP[0], 
                        DP[1], DP[2], DP[3], DP[4], DP[5], DP[6], v['SECT_BEFORE']['OFFSET_PT'], v['SECT_BEFORE']['OFFSET_CENTER'], v['SECT_BEFORE']['USER_OFFSET_REF'],
                        v['SECT_BEFORE']['HORZ_OFFSET_OPT'], v['SECT_BEFORE']['VERT_OFFSET_OPT'], v['SECT_BEFORE']['USERDEF_OFFSET_YI'], 
                        v['SECT_BEFORE']['USERDEF_OFFSET_ZI'], v['SECT_BEFORE']['USE_SHEAR_DEFORM'], v['SECT_BEFORE']['USE_WARPING_EFFECT'],
                        v['SECT_BEFORE']['MATL_ELAST'], v['SECT_BEFORE']['MATL_DENS'], v['SECT_BEFORE']['MATL_POIS_S'], v['SECT_BEFORE']['MATL_POIS_C'],
                        v['SECT_BEFORE']['MATL_THERMAL'], v['SECT_BEFORE']['USE_MULTI_ELAST'], v['SECT_BEFORE']['LONGTERM_ESEC'], v['SECT_BEFORE']['SHRINK_ESEC'], 
                        v['SECT_BEFORE']['PSC_OPT1'], v['SECT_BEFORE']['PSC_OPT2'], v['SECT_AFTER']['SLAB'][0], v['SECT_AFTER']['SLAB'][1], v['SECT_AFTER']['SLAB'][2])
#---------------------------------------------------------------------------------------------------------------

#27 Class to define PSC Value type section
class PSC_VAL:
    sections = []
    
    def __init__(self, name = "PSC VALUE", id = 0, shape = "VALU", calc = True, th1 = True, th2 = True, th3 = True, offset="CT", 
        center_loc = 0, uor = 0, ho = 0, vo = 0, ho_i = 0, vo_i = 0, sd = True, we = True, ht = 0, bt = 0, t1 = 0, t2 = 0, shck = True, 
        z1v = 0, z3v = 0, uaq = [[True, True, True],[False, False, False]], aq = [[0, 0, 0,], [0, 0, 0]], ttv = 0, t1v = 0, t2v = 0, t3v = 0, op = [], ip = []):
        
        if len(section_ids) == 0 and id == 0: 
            section_count = 1
        elif len(section_ids) != 0 and id == 0:
            section_count = max(section_ids) + 1
        if id != 0:
            if id in section_ids and id in [i.ID for i in PSC_VAL.sections]:
                print(f"Section ID {id}, already exists and is now updated with new input.")
            elif id in section_ids and id not in [i.ID for i in PSC_VAL.sections]:
                section_count = max(section_ids) + 1
                print(f"Section ID {id} already exists.  New ID {section_count} is assigned to the section {name}.")
            else:
                section_count = id
        
        self.NAME = name
        self.ID = section_count
        self.SHAPE = shape
        self.CALC = calc
        self.OFFSET = offset
        self.CL = center_loc
        self.UOR = uor
        self.HO = ho
        self.VO = vo
        self.HOI = ho_i
        self.VOI = vo_i
        self.SD = sd
        self.WE = we
        self.HT = ht
        self.BT = bt
        self.T1 = t1
        self.T2 = t2
        self.SHCK = shck
        self.Z1V = z1v
        self.Z3V = z3v
        self.UAQ = uaq
        self.AQ = aq
        self.TTV = ttv
        self.TH1 = th1
        self.TH2 = th2
        self.TH3 = th3
        self.T1V = t1v
        self.T2V = t2v
        self.T3V = t3v
        self.OP = op
        self.IP = ip
        PSC_VAL.sections.append(self)
        section_ids.append(int(section_count))
    
    @classmethod
    def make_json(cls):
        json = {"Assign":{}}
        for k in cls.sections:
            json["Assign"][k.ID] = {
                "SECTTYPE": "PSC",
                "SECT_NAME": k.NAME,
                "CALC_OPT": k.CALC,
                "SECT_BEFORE": {
                "OFFSET_PT": k.OFFSET,
                "OFFSET_CENTER": k.CL,
                "USER_OFFSET_REF": k.UOR,
                "HORZ_OFFSET_OPT": k.HO,
                "USERDEF_OFFSET_YI": k.HOI,
                "VERT_OFFSET_OPT": k.VO,
                "USERDEF_OFFSET_ZI": k.VOI,
                "USE_SHEAR_DEFORM": k.SD,
                "USE_WARPING_EFFECT": k.WE,
                "SHAPE": k.SHAPE,
                "SECT_I":{
                    "vSIZE": [k.HT, k.BT, k.T1, k.T2]
                },
                "SHEAR_CHK": k.SHCK,
                "SHEAR_CHK_POS":[[k.Z1V, 0, k.Z3V], [0, 0, 0]],
                "USE_AUTO_QY": k.UAQ,
                "AUTO_QY": k.AQ,
                "WEB_THICK":[k.TTV, 0],
                "USE_WEB_THICK_SHEAR":[[k.TH1, k.TH2, k.TH3],[False, False, False]],
                "WEB_THICK_SHEAR":[[k.T1V, k.T2V, k.T3V],[0, 0, 0]]
                }
            }
            #Add Outer polygon
            OP = [{"VERTEX":[]}]
            for i in k.OP:
                OP[0]["VERTEX"].append({"X": i[0], "Y":i[1]})
            #Add inner polygon
            IP = []
            for i in range(len(k.IP)):
                IP.append({"VERTEX":[]})
                for j in k.IP[i]:
                    IP[i]["VERTEX"].append({"X": j[0], "Y":j[1]})
            json["Assign"][k.ID]['SECT_BEFORE']['SECT_I']['OUTER_POLYGON'] = OP
            json["Assign"][k.ID]['SECT_BEFORE']['SECT_I']['INNER_POLYGON'] = IP
        return json
    
    @classmethod
    def create(cls):
        MidasAPI("PUT","/db/sect", PSC_VAL.make_json())
    
    @classmethod
    def call_json(cls):
        return MidasAPI("GET","/db/sect")
    
    @classmethod
    def update_class(cls):
        a = PSC_VAL.call_json()
        if a != {'message': ''}:
            b = []
            for i in list(a['SECT'].keys()):
                if a['SECT'][i]['SECT_BEFORE']['SHAPE'] == 'VALU': b.append(int(i))
            global section_ids
            section_ids = [i for i in section_ids if i not in [int(j) for j in b]]
            PSC_VAL.sections = []
            for k, v in a['SECT'].items():
                shp = v['SECT_BEFORE']['SHAPE']
                if v["SECTTYPE"] == "PSC" and shp == 'VALU':
                    op = []
                    ip = []
                    OP = v['SECT_BEFORE']['SECT_I']['OUTER_POLYGON']
                    for i in range(len(OP[0]['VERTEX'])):
                        op.append((OP[0]['VERTEX'][i]['X'], OP[0]['VERTEX'][i]['Y']))
                    if 'INNER_POLYGON' in list(v['SECT_BEFORE']['SECT_I'].keys()):
                        IP = v['SECT_BEFORE']['SECT_I']['INNER_POLYGON']
                        for i in range(len(IP)):
                            ip.append([])
                            for j in range(len(IP[i]['VERTEX'])):
                                ip[i].append((IP[i]['VERTEX'][j]['X'], IP[i]['VERTEX'][j]['Y']))
                    if 'AUTO_QY' not in list(v['SECT_BEFORE'].keys()): 
                        aqy = [[0, 0, 0], [0, 0, 0]]
                    else:
                        aqy = v['SECT_BEFORE']['AUTO_QY']
                    if 'WEB_THICK_SHEAR' not in list(v['SECT_BEFORE'].keys()): 
                        th1, th2, th3 = 0, 0, 0
                    else:
                        th1 = v['SECT_BEFORE']['WEB_THICK_SHEAR'][0][0]
                        th2 = v['SECT_BEFORE']['WEB_THICK_SHEAR'][0][1]
                        th3 = v['SECT_BEFORE']['WEB_THICK_SHEAR'][0][2]
                    PSC_VAL(v['SECT_NAME'], k, shp, True, v['SECT_BEFORE']['USE_WEB_THICK_SHEAR'][0][0], v['SECT_BEFORE']['USE_WEB_THICK_SHEAR'][0][1], 
                        v['SECT_BEFORE']['USE_WEB_THICK_SHEAR'][0][2], v['SECT_BEFORE']['OFFSET_PT'], v['SECT_BEFORE']['OFFSET_CENTER'], 
                        v['SECT_BEFORE']['USER_OFFSET_REF'], v['SECT_BEFORE']['HORZ_OFFSET_OPT'], v['SECT_BEFORE']['VERT_OFFSET_OPT'], 
                        v['SECT_BEFORE']['USERDEF_OFFSET_YI'], v['SECT_BEFORE']['USERDEF_OFFSET_ZI'], v['SECT_BEFORE']['USE_SHEAR_DEFORM'], 
                        v['SECT_BEFORE']['USE_WARPING_EFFECT'], v['SECT_BEFORE']['SECT_I']['vSIZE'][0], v['SECT_BEFORE']['SECT_I']['vSIZE'][1],
                        v['SECT_BEFORE']['SECT_I']['vSIZE'][2], v['SECT_BEFORE']['SECT_I']['vSIZE'][3], v['SECT_BEFORE']['SHEAR_CHK'],
                        v['SECT_BEFORE']['SHEAR_CHK_POS'][0][0], v['SECT_BEFORE']['SHEAR_CHK_POS'][0][2],v['SECT_BEFORE']['USE_AUTO_QY'], aqy,
                        v['SECT_BEFORE']['WEB_THICK'][0], th1, th2, th3, op, ip)
#---------------------------------------------------------------------------------------------------------------

#28 Class to generate load combinations
class Load_Combination:
    data = []
    valid = ["General", "Steel", "Concrete", "SRC", "Composite Steel Girder", "Seismic", "All"]
    com_map = {
            "General": "/db/LCOM-GEN",
            "Steel": "/db/LCOM-STEEL",
            "Concrete": "/db/LCOM-CONC",
            "SRC": "/db/LCOM-SRC",
            "Composite Steel Girder": "/db/LCOM-STLCOMP",
            "Seismic": "/db/LCOM-SEISMIC"
        }
    def __init__(self, name, case, classification = "General", active = "ACTIVE", typ = "Add", id = 0, desc = ""):
        """Name, List of tuple of load cases & factors, classification, active, type. \n
        Sample: Load_Combination('LCB1', [('Dead Load(CS)',1.5), ('Temperature(ST)',0.9)], 'General', 'Active', 'Add')"""
        if not isinstance(case, list):
            print("case should be a list that contains tuple of load cases & factors.\nEg: [('Load1(ST)', 1.5), ('Load2(ST)',0.9)]")
            return
        for i in case:
            if not isinstance(i, tuple):
                print(f"{i} is not a tuple.  case should be a list that contains tuple of load cases & factors.\nEg: [('Load1(ST)', 1.5), ('Load2(ST)',0.9)]")
                return
            if not isinstance(i[0], str):
                print(f"{i[0]} is not a string.  case should be a list that contains tuple of load cases & factors.\nEg: [('Load1(ST)', 1.5), ('Load2(ST)',0.9)]")
                return
            if i[0][-1] != ")":
                print(f"Load case type is not mentioned for {i[0]}.  case should be a list that contains tuple of load cases & factors.\nEg: [('Load1(ST)', 1.5), ('Load2(ST)',0.9)]")
                return
            if not isinstance(i[1],(int, float)):
                print(f"{i[1]} is not a number.  case should be a list that contains tuple of load cases & factors.\nEg: [('Load1(ST)', 1.5), ('Load2(ST)',0.9)]")
                return

        if classification not in Load_Combination.valid[:-1]:
            print(f'"{classification}" is not a valid input.  It is changed to "General".')
            classification = "General"
            
        if classification in ["General", "Seismic"]:
            if active not in ["ACTIVE", "INACTIVE"]: active = "ACTIVE"
        if classification in  ["Steel", "Concrete", "SRC", "Composite Steel Girder"]:
            if active not in ["STRENGTH", "SERVICE", "INACTIVE"]: active = "STRENGTH"
        
        typ_map = {"Add": 0, "Envelope": 1, "ABS": 2, "SRSS": 3, 0:0, 1:1, 2:2, 3:3}
        if typ not in list(typ_map.keys()): typ = "Add"
        if classification not in ["General", "Seismic"] and typ_map.get(typ) == 2: typ = "Add"
        
        if id == 0 and len(Load_Combination.data) == 0: 
            id = 1
        elif id == 0 and len(Load_Combination.data) != 0:
            id = max([i.ID for i in Load_Combination.data]) + 1
        elif id != 0 and id in [i.ID for i in Load_Combination.data]:
            if classification in [i.CLS for i in Load_Combination.data if i.ID == id]:
                print(f"ID {id} is already defined.  Existing combination would be replaced.")
                
        
        combo = []
        valid_anl = ["ST", "CS", "MV", "SM", "RS", "TH", "CB", "CBC", "CBS", "CBR", "CBSC", "CBSM"] #Need to figure out for all combination types
        for i in case:
            a = i[0].rsplit('(', 1)[1].rstrip(')')
            if a in valid_anl:
                combo.append({
                    "ANAL": a,
                    "LCNAME":i[0].rsplit('(', 1)[0],
                    "FACTOR": i[1]
                })
        self.NAME = name
        self.CASE = combo
        self.CLS = classification
        self.ACT = active
        self.TYPE = typ_map.get(typ)
        self.ID = id
        self.DESC = desc
        Load_Combination.data.append(self)
    
    @classmethod
    def make_json(cls, classification = "All"):
        if len(Load_Combination.data) == 0:
            print("No Load Combinations defined!  Define the load combination using the 'Load_Combination' class before making json file.")
            return
        if classification not in Load_Combination.valid:
            print(f'"{classification}" is not a valid input.  It is changed to "General".')
            classification = "General"
        json = {k:{'Assign':{}} for k in Load_Combination.valid[:-1]}
        for i in Load_Combination.data:
            if i.CLS == classification or classification == "All":
                json[i.CLS]['Assign'][i.ID] = {
                    "NAME": i.NAME,
                    "ACTIVE": i.ACT,
                    "iTYPE": i.TYPE,
                    "DESC": i.DESC,
                    "vCOMB":i.CASE
                }
        json = {k:v for k,v in json.items() if v != {'Assign':{}}}
        return json
    
    @classmethod
    def call_json(cls, classification = "All"):
        if classification not in Load_Combination.valid:
            print(f'"{classification}" is not a valid input.  It is changed to "General".')
            classification = "General"
        combos = {k:{} for k in Load_Combination.valid[:-1]}
        for i in Load_Combination.valid[:-1]:
            if classification == i or classification == "All":
                combos[i] = MidasAPI("GET",Load_Combination.com_map.get(i))
        json = {k:v for k,v in combos.items() if v != {'message':''}}
        return json
    
    @classmethod
    def create(cls, classification = "All"):
        if len(Load_Combination.data) == 0:
            print("No Load Combinations defined!  Define the load combination using the 'Load_Combination' class before creating these in the model.")
            return
        if classification not in Load_Combination.valid:
            print(f'"{classification}" is not a valid input.  It is changed to "General".')
            classification = "General"
        json = Load_Combination.make_json(classification)
        for i in Load_Combination.valid[:-1]:
            if classification == i or classification == "All":
                if i in list(json.keys()):
                    a = list(json[i]['Assign'].keys())
                    b=""
                    for j in range(len(a)):
                        b += str(a[j]) + ","
                    if b != "": b = "/" + b[:-1]
                    MidasAPI("DELETE", Load_Combination.com_map.get(i) + b)     #Delete existing combination if any
                    MidasAPI("PUT", Load_Combination.com_map.get(i), json[i])   #Create new combination
    
    @classmethod
    def update_class(cls, classification = "All"):
        json = Load_Combination.call_json(classification)
        if json != {}:
            keys = list(json.keys())
            for i in keys:
                for k,v in json[i][Load_Combination.com_map.get(i)[4:]].items():
                    c = []
                    for j in range(len(v['vCOMB'])):
                        c.append((v['vCOMB'][j]['LCNAME'] + "("+ v['vCOMB'][j]['ANAL'] + ")", v['vCOMB'][j]['FACTOR']))
                    Load_Combination(v['NAME'], c, i, v['ACTIVE'], v['iTYPE'], int(k), v['DESC'])
    
    @classmethod
    def delete(cls, classification = "All", ids = []):
        json = Load_Combination.call_json(classification)
        a = ""
        for i in range(len(ids)):
            a += str(ids[i]) + ","
        a = "/" + a[:-1]
        if json == {}: 
            print("No load combinations are defined to delete.  Define load combinations before using this command.")
        for i in list(json.keys()):
            MidasAPI("DELETE",Load_Combination.com_map.get(i) + a)
#---------------------------------------------------------------------------------------------------------------

#29 Beam result table (IMCOMPLETE)
class Beam_Result_Table:
    force_input_data = []
    stress_input_data = []
    
    def __init__(self, table_of = "FORCE", elem = [], case = [], cs = False, stage = [], step = [], location = "i"):
        if table_of in ["FORCE", "STRESS"]:
            self.TAB = table_of
        else:
            print(f"Please enter 'FORCE' or 'STRESS' as string in capital. {table_of} is not a vaild input.")
            return
        Element.update_class()
        if elem != []:
            a = [i.ID for i in Element.elements if i.ID in elem and i.TYPE == "BEAM"]
            b = [i for i in elem if i not in a]
            elem = a
            if b != []: print(f"The element/s {b} are not defined in the model.  These would be skipped.")
        if elem == []: 
            print(f"Since no valid elements were provided, table is generated for all defined beam elements.")
            elem = [i.ID for i in Element.elements if i.TYPE == "BEAM"]
        self.ELEM = elem
        Load_Case.update_class()
        Load_Combination.update_class()
        ca = Load_Case.make_json()
        co = Load_Combination.make_json()
        if case == [] and cs == False:
            print(f"Since no load cases/combinations are provided for output, results are tabulated for all static load cases.")
            for i in ca["Assign"]:
                case.append(ca["Assign"][i]["NAME"]+"(ST)")
        if case != []:
            for i in range(len(case)):
                if case[i][-1] != ")": 
                    case[i]+="(ST)"
        self.CASE = case
        if location not in ["i", "1/4", "2/4", "3/4", "j"]:
            print(f'{location} not in ["i", "1/4", "2/4", "3/4", "j"]. Output is tablulated for "i" location.')
            location = "i"
        self.LOC = location
        if table_of == "FORCE":
            Beam_Result_Table.force_input_data.append(self)
        elif table_of == "STRESS":
            Beam_Result_Table.stress_input_data.append(self)
        
    @classmethod
    def make_json(cls, json_of = "FORCE"):
        analyze()
        if json_of == "FORCE":1
            
#---------------------------------------------------------------------------------------------------------------

#Function to get stress table JSON output, just the DATA list.
def stress_tab(elem, case):
    """Element list.  Sample stress_tab([3,5], "Self-Weight(ST)").  Returns Cb1 to Cb4 for list of entered elements"""
    if elem == None: elem = list(MidasAPI("GET","/db/ELEM")['ELEM'].keys())
    if case == None: 
        a = MidasAPI("GET","/db/STLD")['STLD']
        for i in range(max(list(a.keys()))):
            if a[i]['TYPE'] not in ['CS']: case.append(str(a[i]["NAME"])+"(ST)")
    stress = {"Argument": {
                "TABLE_NAME": "BeamStress",
                "TABLE_TYPE": "BEAMSTRESS",
                "UNIT": {
                    "FORCE": "N",
                    "DIST": "mm"
                },
                "STYLES": {
                    "FORMAT": "Fixed",
                    "PLACE": 12
                },
                "COMPONENTS": [
                    "Elem",
                    "Load",
                    "Part",
                    "Cb1(-y+z)",
                    "Cb2(+y+z)",
                    "Cb3(+y-z)",
                    "Cb4(-y-z)"
                ],
                "NODE_ELEMS": {
                    "KEYS": [
                        int(item) for item in elem
                    ]
                },
                "LOAD_CASE_NAMES": case,
                "PARTS": [
                    "PartI",
                    "Part1/4",
                    "Part2/4",
                    "Part3/4",
                    "PartJ"
                ]
            }}
    raw = (MidasAPI("POST","/post/TABLE",stress)['BeamStress']['DATA'])
    return(raw)
#---------------------------------------------------------------------------------------------------------------
#Function to call max beam stress results
def max_beam_stress(elem, case):
    """Element list.  Sample:  max_beam_stress([10,18,5], "Self-Weight(ST)") to get maximum stress among these 3 elements.
    Enter max_beam_stress([],[]) to get maximum stress in the entire structure for the first static load case."""
    db = 0
    if elem == None: elem = list(MidasAPI("GET","/db/ELEM")['ELEM'].keys())
    if case == None: 
        for i in range(max(list(MidasAPI("GET","/db/STLD")['STLD'].keys()))):
            case.append(str(MidasAPI("GET","/db/STLD")['STLD'][i]["NAME"])+"(ST)")
    if type(elem == list):
        for i in range(len(elem)):
            if type(elem[i])!= int: db+=1
        if db == 0:
            raw = stress_tab(elem, case)
            current_stress = float(0)
            for i in range(len(raw)):
                max_stress = max(current_stress, float(raw[i][4]),float(raw[i][5]),float(raw[i][6]),float(raw[i][7]))
                current_stress = max_stress
            return(current_stress)
        if db!= 0: print("Enter list of element ID (list of integers only!)")
    if type(elem)!= list: print("Enter list of element ID (list of integers only!) or leave it empty for max stress in structure.")
#---------------------------------------------------------------------------------------------------------------
#Function to call min beam stress results
def min_beam_stress(elem, case):
    """Element list, Load case name or combination.  Sample:  min_beam_stress([10,18,5], ["Self-Weight(ST)"]) to get minimum stress among these 3 elements.
    Enter min_beam_stress([],[]) to get minimum stress in the entire structure for the first static load case."""
    db = 0
    if elem == None: elem = list(MidasAPI("GET","/db/ELEM")['ELEM'].keys())
    if case == None: 
        for i in range(max(list(MidasAPI("GET","/db/STLD")['STLD'].keys()))):
            case.append(str(MidasAPI("GET","/db/STLD")['STLD'][i]["NAME"])+"(ST)")
    if type(elem == list):
        for i in range(len(elem)):
            if type(elem[i])!= int: db+=1
        if db == 0:
            raw = stress_tab(elem, case)
            current_stress = float(0)
            for i in range(len(raw)):
                min_stress = min(current_stress, float(raw[i][4]),float(raw[i][5]),float(raw[i][6]),float(raw[i][7]))
                current_stress = min_stress
            return(current_stress)
        if db!= 0: print("Enter list of element ID (list of integers only!)")
    if type(elem)!= list: print("Enter list of element ID (list of integers only!) or leave it empty for min stress in structure.")
#---------------------------------------------------------------------------------------------------------------
#Function to get force table JSON output, just the DATA list.
def force_tab(elem, case):
    """Element list.  Sample force_tab([23,5]).  Returns element forces for list of entered elements"""
    if elem == None: elem = list(MidasAPI("GET","/db/ELEM")['ELEM'].keys())
    if case == None: 
        for i in range(max(list(MidasAPI("GET","/db/STLD")['STLD'].keys()))):
            case.append(str(MidasAPI("GET","/db/STLD")['STLD'][i]["NAME"])+"(ST)")
    force = {
        "Argument": {
            "TABLE_NAME": "BeamForce",
            "TABLE_TYPE": "BEAMFORCE",
            "EXPORT_PATH": "C:\\MIDAS\\Result\\Output.JSON",
            "UNIT": {
                "FORCE": "kN",
                "DIST": "m"
            },
            "STYLES": {
                "FORMAT": "Fixed",
                "PLACE": 12
            },
            "COMPONENTS": [
                "Elem",
                "Load",
                "Part",
                "Axial",
                "Shear-y",
                "Shear-z",
                "Torsion",
                "Moment-y",
                "Moment-z",
                "Bi-Moment",
                "T-Moment",
                "W-Moment"
            ],
            "NODE_ELEMS": {
                "KEYS": [
                    int(item) for item in elem
                ]
            },
            "LOAD_CASE_NAMES": case,
            "PARTS": [
                "PartI",
                "Part1/4",
                "Part2/4",
                "Part3/4",
                "PartJ"
            ]
        }
    }
    raw = (MidasAPI("POST","/post/TABLE",force)['BeamForce']['DATA'])
    return(raw)
#---------------------------------------------------------------------------------------------------------------
#Function to call beam force results
def beam_force(req = 3, elem = [], case = [], loc = 1):
    """Request, Element list, Case list, Location.  Sample:  beam_force(elem=[10,18,5], case ="Self-Weight(ST)") to get forces at I end in these 3 elements.
    req = (1 --> Maximum force)(2 --> Minimum force)(3 --> Forces for all elements at requested location).
    loc = (1 --> i-end)(2 --> Part1/2)(3 --> Part2/4)(4 --> Part3/4)(5 --> j end)  
    Enter beam_force() to get forces at I end in all elements for all load cases."""
    db = 0
    dir = {"Axial":float(0),
        "Shear-y":float(0),
        "Shear-z":float(0),
        "Torsion":float(0),
        "Moment-y":float(0),
        "Moment-z":float(0),
        "Bi-Moment":float(0),
        "T-Moment":float(0),
        "W-Moment":float(0)}
    dir_2 = {
        "Axial":[],
        "Shear-y":[],
        "Shear-z":[],
        "Torsion":[],
        "Moment-y":[],
        "Moment-z":[],
        "Bi-Moment":[],
        "T-Moment":[],
        "W-Moment":[]}
    if elem == []: elem = [int(item) for item in list(MidasAPI("GET","/db/ELEM")['ELEM'].keys())]
    if case == []: 
        a = MidasAPI("GET","/db/STLD")['STLD']
        for i in range(int(max(list(a.keys())))):
            if a[str(i+1)]['TYPE'] not in ['CS']: case.append(str(a[str(i+1)]["NAME"])+"(ST)")
    if type(elem == list):
        for i in range(len(elem)):
            if type(elem[i])!= int: db+=1
        if (db == 0):
            raw = force_tab(elem, case)
            for i in range(len(raw)):
                if req == 1:
                    dir["Axial"] = max(dir["Axial"], float(raw[i][4]))
                    dir["Shear-y"] = max(dir["Shear-y"],float(raw[i][5]))
                    dir["Shear-z"] = max(dir["Shear-z"],float(raw[i][6]))
                    dir["Torsion"] = max(dir["Torsion"],float(raw[i][7]))
                    dir["Moment-y"] = max(dir["Moment-y"],float(raw[i][8]))
                    dir["Moment-z"] = max(dir["Moment-z"],float(raw[i][9]))
                    if len(raw[0])>10:
                        dir["Bi-Moment"] = max(dir["Bi-Moment"],float(raw[i][10]))
                        dir["T-Moment"] = max(dir["T-Moment"],float(raw[i][11]))
                        dir["W-Moment"] = max(dir["W-Moment"],float(raw[i][12]))
                if req == 2:
                    dir["Axial"] = min(dir["Axial"], float(raw[i][4]))
                    dir["Shear-y"] = min(dir["Shear-y"],float(raw[i][5]))
                    dir["Shear-z"] = min(dir["Shear-z"],float(raw[i][6]))
                    dir["Torsion"] = min(dir["Torsion"],float(raw[i][7]))
                    dir["Moment-y"] = min(dir["Moment-y"],float(raw[i][8]))
                    dir["Moment-z"] = min(dir["Moment-z"],float(raw[i][9]))
                    if len(raw[0])>10:
                        dir["Bi-Moment"] = min(dir["Bi-Moment"],float(raw[i][10]))
                        dir["T-Moment"] = min(dir["T-Moment"],float(raw[i][11]))
                        dir["W-Moment"] = min(dir["W-Moment"],float(raw[i][12]))
                if (loc == int(raw[i][0]) and req == 3):
                    dir_2["Axial"].append(float(raw[i][4]))
                    dir_2["Shear-y"].append(float(raw[i][5]))
                    dir_2["Shear-z"].append(float(raw[i][6]))
                    dir_2["Torsion"].append(float(raw[i][7]))
                    dir_2["Moment-y"].append(float(raw[i][8]))
                    dir_2["Moment-z"].append(float(raw[i][9]))
                    if len(raw[0])>10:
                        dir_2["Bi-Moment"].append(float(raw[i][10]))
                        dir_2["T-Moment"].append(float(raw[i][11]))
                        dir_2["W-Moment"].append(float(raw[i][12]))
                    loc += 5
            if req != 3: return(dir)
            if req == 3: return(dir_2)
        if db!= 0: print("Enter list of element ID (list of integers only!)")
    if type(elem)!= list: print("Enter list of element ID (list of integers only!) or leave it empty for max force in structure.")
#---------------------------------------------------------------------------------------------------------------
#Function to get summary of maximum & minimum forces for each unique section & element
def force_summary(mat = 1, sec = 1, elem = [], case = []):
    """Request type (1 for overall summary, 2  for required material & section, 3 for list of elements).  Sample:
    force_summary() for overall max & min forces for each type of unique material & section used in the software.
    force_summary(2, mat = [1,4], sec = [1,2]) for max & min force for (material 1 + section 1), (material 1 + section 2), (material 4 +  section 1) and (material 4 + section 2).
    force_summary(3, elem = [1,2,3,4]) for max & min force summary for unique material & section property combination among elements 1, 2, 3 & 4."""
    analyze()
    if elem == []: 
        li = get_select("USM", mat, sec)
    else:
        li = elem
    res = {}
    for i in li:
        a = beam_force(1,i,case)
        b = beam_force(2,i,case)
        res[i] = {"max":a,"min":b}
    return(res)
#---------------------------------------------------------------------------------------------------------------
#Function to get summary of maximum & minimum stresses for each unique section & element
def stress_summary(req = 1, mat = [], sec = [], elem = [], case = []):
    """Request type (1 for overall summary, 2  for required material & section, 3 for list of elements).  Sample:
    stress_summary() for overall max & min stress for each type of unique material & section used in the software.
    stress_summary(2, mat = [1,4], sec = [1,2]) for max & min stress for (material 1 + section 1), (material 1 + section 2), (material 4 +  section 1) and (material 4 + section 2).
    stress_summary(3, elem = [1,2,3,4]) for max & min stress summary for unique material & section property combination among elements 1, 2, 3 & 4."""
    analyze()
    if elem == []: 
        li = get_select("USM", mat, sec)
    else:
        li = elem
    res = {}
    for i in li:
        a = stress_tab(elem, case)
        max_str= {"top": 0,"bot": 0}                                #Empty dictionary to store max top stress results based on materil ID and section ID
        min_str = {"top": 0,"bot": 0}                               #Empty dictionary to store min top stress results based on materil ID and section ID
        for i in range(len(a)):
            max_str["top"] = max(max_str["top"],float(a[i][4]),float(a[i][5]))
            max_str["bot"] = max(max_str["bot"],float(a[i][6]),float(a[i][7]))
            min_str["top"] = min(min_str["top"],float(a[i][4]),float(a[i][5]))
            min_str["bot"] = min(min_str["bot"],float(a[i][6]),float(a[i][7]))
        res[i] = ({"max":max_str,"min":min_str})
    return(res)
#---------------------------------------------------------------------------------------------------------------
#Function to get section properties of the specific ID
def sect_prop(id=[]):
    """List of section ID.  Sample: Enter Sect_prop[3,4] for properties of section ID 4 & 5.  
    Enter sect_prop() for properties of all defined sections."""
    dir = {}
    units("N",length="MM")
    sect = MidasAPI("GET","/ope/SECTPROP")
    if id == []: a = list(sect['SECTPROP'].keys())
    if (id != [] and type(id)!= int): a = [str(e) for e in id]
    if type(id) == int: a = [str(id)]
    for i in a:
        if i in sect['SECTPROP'].keys():
            dir.update({int(i):{"Area":None , "Iy":None, "Iz":None, "Yl":None, "Yr":None, "Zt":None, "Zb":None,
            "Y1":None, "Z1":None, "Y2":None, "Z2":None, "Y3":None, "Z3":None, "Y4":None, "Z4":None}})
            data = [float(sect['SECTPROP'][i]['DATA'][0][1])]
            for j in list(range(4,10))+list(range(16,24)):
                data.append(float(sect['SECTPROP'][i]['DATA'][j][1]))
            for idx, key in enumerate(dir[int(i)]):
                dir[int(i)][key] = data[idx]
        elif i not in sect['SECTPROP'].keys(): print ("Section id", i, "is not defined in connected model.")
    units()
    return(dir)
#---------------------------------------------------------------------------------------------------------------

#Function to find premissible prestress and eccentricities by Magnel method
def magnel(Mi, Mf, act, att, acs, ats, area, Iy, yt, yb, R, bf = 0.3, c = 0.1, PS = 1422, strand_area = 139, max_strands = 50):
    """Initial moment(kNm, +ve for sagging), Final moment (kNm, +ve for sagging), Allowable compression at transfer (MPa, -ve), Allowable tension at transfer (MPa, +ve), Allowable compression at service (MPa, -ve), 
    Allowable tension at service (MPa, +ve), Area of girder (m^2), Iy of girder (m^4), CG to top fiber (m, +ve), CG to bottom fiber (m, -ve), Prestress loss ratio, bottom flange depth, cover for effective tendon.
    Sample: magnel(235, 809, -12.5, 1,-18.7, 2.3, 3.0287, 12.76433, 0.98, -0.734, 0.17)"""
    def ar(ps,ecc):
        """List of prestress, List of concurrent eccentricities.  Enter sequentially (clockwise or anti-clockwise)."""
        if (type(ps) == list and type(ecc) == list):
            if (len(ps) == 3 and len(ecc) == 3):
                a = (1/2)*abs(ps[0]*(ecc[1]-ecc[2])+ps[1]*(ecc[2]-ecc[0])+ps[2]*(ecc[0]-ecc[1]))
            elif (len(ps) == 4 and len(ecc) == 4):
                a = (1/2)*abs((ps[0]*ecc[1]+ps[1]*ecc[2]+ps[2]*ecc[3]+ps[3]*ecc[0])-(ps[1]*ecc[0]+ps[2]*ecc[1]+ps[3]*ecc[2]+ps[0]*ecc[3]))
            return(a)
    def ps_pt_chk(p,e,ps,ecc):
        """Selected Prestress, Selected eccentricity, Permissible prestress list, concurrent eccentricity list.  Enter sequentially (clockwise or anti-clockwise)"""
        if (len(ps)== 4 and len(ecc) == 4):
            area_q = round(ar(ps,ecc),5)
            t1 = ar([p,ps[0],ps[1]],[e,ecc[0],ecc[1]])
            t2 = ar([p,ps[1],ps[2]],[e,ecc[1],ecc[2]])
            t3 = ar([p,ps[2],ps[3]],[e,ecc[2],ecc[3]])
            t4 = ar([p,ps[3],ps[0]],[e,ecc[3],ecc[0]])
            area_t = round((t1+t2+t3+t4),5)
            if area_q == area_t: 
                return(1)
            else:
                return(0)
    if (act <= 0 and att >=0 and acs<= act and ats>= att and area > 0 and Iy > 0 and yt > 0 and yb< 0 and R >= 0 and R <= 1 and Mi <= Mf):
        ftf = acs * -1000
        fti = att * -1000
        fbf = ats * -1000
        fbi = act * -1000
        h = yt - yb
        zt = Iy/yt
        zb = Iy/yb
        kt = zt/area
        kb = zb/area
        zt_min = (Mf - R * Mi)/(ftf - R * fti)
        zb_min = (Mf - R * Mi)/(fbf - R * fbi)
        if (zt >= zt_min and zb <= zb_min):
            LP = ((R * fti * zt - fbf * zb) + (Mf - R * Mi))/(R * (kt - kb))
            Le = ((fbf * zb - Mf)/R)*(1 / LP) - zb / area
            IP = (area / h) * (yt * fbi - yb * fti)
            Ie = (fti * zt - Mi) * (1 / IP) - zt / area
            HP = ((ftf * zt - R * fbi * zb) - (Mf - R * Mi))/(R * (kt - kb))
            He = (fbi * zb - Mi) * (1 / HP) - zb / area
            FP = (area / R / h) * (yt * fbf - yb * ftf)
            Fe = ((ftf * zt - Mf) / R) * (1 / FP) - zt / area
            P = [LP, IP, HP, FP]
            e = [Le, Ie, He, Fe]
            e_max = yb + c
            if bf != 0: e_min = yb + bf - c
            if bf == 0:e_min = - c
            e_inc = (e_max-e_min)/4
            e_range = [e_min, e_min + e_inc, e_min + 2 * e_inc, e_min + 3 * e_inc, e_max]
            dir = {'P':[],'e':[],'PT_area':[]}
            for i in range(max_strands):
                F = i * strand_area * PS / 1000
                for j in range(len(e_range)):
                    if ps_pt_chk(F, e_range[j], P, e) == 1:
                        dir['P'].append(F)
                        dir['e'].append(e_range[j])
                        dir['PT_area'].append(i * strand_area)
            for i in range(len(dir['P'])):
                plt.plot(dir['P'][i],dir['e'][i],marker = "o")
                plt.plot([dir['P'][i], dir['P'][i]],[dir['e'][i], min(e_max, Le, Ie, He, Fe) - 0.05],ls=":", color = "red")
                plt.plot([dir['P'][i], min(P) - 50],[dir['e'][i], dir['e'][i]],ls=":", color = "red")
            P.append(LP)
            e.append(Le)
            plt.plot(P, e ,marker="X", label = "Magnel Zone", color = "g", ls = "-")
            plt.fill_between(P, e, color = 'lightgreen',alpha = 0.25)
            x = [min(P) - 50, max(P) + 50]
            y = [yb, yb]
            plt.plot(x, y, color = "black", ls = "-", label = "Bottom Flange")
            y = [yb+bf, yb+bf]
            plt.plot(x, y, color = "black", ls = "-")
            plt.show()
            return(dir)
        else:
            print("Section needs to be modified.")
            return(2)
    else:
        print("Please check the input and ensure that values are entered with proper signs.")
        return(1)
#---------------------------------------------------------------------------------------------------------------
#Function to get section inputs of the specific ID
def sect_inp(sec):
    """Section ID.  Enter one section id or list of section IDs.  Sample:  sect_inp(1) OR sect_inp([3,2,5])"""
    units()
    a = MidasAPI("GET","/db/SECT",{"Assign":{}})
    if type(sec)==int: sec = [sec]
    b={}
    for s in sec:
        if str(s) in a['SECT'].keys() : b.update({s : a['SECT'][str(s)]})
    # if elem = [0] and sec!=0: b.update({sec : })
    if b == {}: b = "The required section ID is not defined in connected model file."
    return(b)
#---------------------------------------------------------------------------------------------------------------
#Function to remove duplicate set of values from 2 lists
def unique_lists(li1, li2):
    if type (li1) == list and type (li2) == list:
        if len(li1) == len(li2):
            indices_to_remove = []
            for i in range(len(li1)):
                for j in range(i+1,len(li1)):
                    if li1[i] == li1[j] and li2[i] == li2[j]:
                        indices_to_remove.append(j)
            for index in sorted(indices_to_remove, reverse = True):
                del li1[index]
                del li2[index]
#---------------------------------------------------------------------------------------------------------------
#Function to get centerline of the cross-section PSC 1-Cell & 2-Cell
def PSC_1CEL_XY(sec, offset = "CC"):
    fig , ax = plt.subplots()
    """INCOMPLETE.  Section ID.  Sample:  PSC_1CEL(3)."""
    if type(sec) == int:
        inp = sect_inp(sec)
        prop = sect_prop(sec)
        if inp[sec]['SECTTYPE'] == 'PSC' and inp[sec]['SECT_BEFORE']['SHAPE'][-3:] == 'CEL':
            oh = inp[sec]['SECT_BEFORE']['SECT_I']['vSIZE_PSC_A']
            ob = inp[sec]['SECT_BEFORE']['SECT_I']['vSIZE_PSC_B']
            ih = inp[sec]['SECT_BEFORE']['SECT_I']['vSIZE_PSC_C']
            ib = inp[sec]['SECT_BEFORE']['SECT_I']['vSIZE_PSC_D']
            oht = oh[0] + oh[1] + oh[4]
            iht = ih[0] + ih[1] + ih[4] + ih[6] + ih[9]
            diff_ht = oht - iht
            if oht > iht: 
                y0 = (prop[sec]['Zt']/1000 - diff_ht)   #y0
            else:
                y0 = (prop[sec]['Zt']/1000)             #y0
            x0 = (0)                                    #x0
            x1 = (ob[0] + ob[3] + ob[5])                #x1
            y1 = (y0 + diff_ht)                         #y1
            x2 = (x1)                                   #x2
            y2 = (y1 - oh[0])                           #y2
            x3 = (x1 - ob[1])                           #x3
            y3 = (y2 - oh[2])                           #y3
            x4 = (x3 - max(0, ob[2]-ob[1]))             #x4
            y4 = (y2 - oh[3])                           #y4
            x5 = (x1 - ob[0])                           #x5
            y5 = (y2 - oh[1])                           #y5
            x6 = (x5 - ob[3] + ob[4])                   #x6
            y6 = (y5 - oh[4] + oh[5])                   #y6
            x7 = (ob[5])                                #x7
            y7 = (y6 - oh[5])                           #y7
            x8 = (0)                                    #x8
            y8 = (y7)                                   #y8
            external = []
            x = [x0, x1, x2, x3, x4, x5, x6, x7, x8]
            y = [y0, y1, y2, y3, y4, y5, y6, y7, y8]
            for i in range(len(x)): external.append((x[i],y[i]))
            x_1 = [-a for a in x]
            x_1.reverse()
            x = x + x_1
            y.extend(reversed(y))
            if oht > iht: 
                y0 = (prop[sec]['Zt']/1000 - diff_ht - ih[0])   #iy0
            else:
                y0 = (prop[sec]['Zt']/1000 - ih[0])             #iy0
            if inp[sec]['SECT_BEFORE']['SHAPE'] == '1CEL':
                x0 = (0)                                        #ix0
            else:
                x0 = ib[7]                                      #ix0
            y1 = (y0 - ih[2])                                   #iy1
            x1 = (x0 + ib[1])                                   #ix1
            y2 = (y1 + max(0, ih[3] - ih[2]))                   #iy2
            x2 = (x1 + max(0, ib[2] - ib[1]))                   #ix2
            y3 = (y0 - ih[1])                                   #iy3
            x3 = (ib[0])                                        #ix3
            y4 = (y3 - ih[5])                                   #iy4
            x4 = (ib[3])                                        #ix4
            y5 = (y0 - ih[1] - ih[4])                           #iy5
            x5 = (ib[4])                                        #ix5
            y8 = y5 - ih[6]                                     #iy8
            x8 = x0                                             #ix8
            y7 = y8 + ih[7]                                     #iy7
            x7 = ib[5]                                          #ix7
            y6 = y8 + max(ih[7], ih[8])                         #iy6
            x6 = max (ib[5], ib[6])                             #ix6
            internal = []
            ix = [x0, x1, x2, x3, x4, x5, x6, x7, x8]
            iy = [y0, y1, y2, y3, y4, y5, y6, y7, y8]
            for i in range(len(ix)): internal.append((ix[i],iy[i]))
            ix_1 = [-a for a in ix]
            ix_1.reverse()
            unique_lists(x, y)
            x.append(x[0])
            y.append(y[0])
            if inp[sec]['SECT_BEFORE']['SHAPE'] == '1CEL':
                ix = ix + ix_1
                iy.extend(reversed(iy))
            else:
                iy_1 = iy[::-1]
                unique_lists(ix_1, iy_1)
                ix_1.append(ix_1[0])
                iy_1.append(iy_1[0])
            unique_lists(ix, iy)
            ix.append(ix[0])
            iy.append(iy[0])
    if inp[sec]['SECT_BEFORE']['SHAPE'] == '1CEL':
        a = x, y, ix, iy
    else:
        a =  x, y, ix, iy, ix_1, iy_1
    
    def perpendicular_point(x1, y1, x2, y2, x3, y3, l=0):
        """Function to get orthogonal point on line (x1,y1)-(x2,y2) from point (x3,y3). Enter l=0 for point 3 in between 1 & 2.  Enter l=1 for other scenario."""
        if x2 != x1:
            m = (y2 - y1) / (x2 - x1)
            c = y1 - m * x1
            x_perp = (x3 + m * (y3 - c)) / (1 + m**2)
            y_perp = m * x_perp + c
        else:
            x_perp, y_perp = x1, y3
        
        l1 = ((x_perp - x1)**2 + (y_perp - y1)**2)**0.5
        l2 = ((x_perp - x2)**2 + (y_perp - y2)**2)**0.5
        l3 = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
        thk = ((x3 - x_perp)**2 + (y3 - y_perp)**2)**0.5
        if round(l1 + l2,5) == round(l3,5) and l == 0:
            return x_perp, y_perp, thk
        elif l==1:
            return x_perp, y_perp, thk
    
    def lower_2(data):
        """Find the lower 2 coordinates in a web"""
        sorted_items = sorted(data.items(), key=lambda item: item[1]['ym'])
        smallest_two = sorted_items[:2]
        result = [(item[1]['xm'], item[1]['ym']) for item in smallest_two]
        return result
    
    def left_2(data):
        """Find the left 2 coordinates in a flange"""
        sorted_items = sorted(data.items(), key=lambda item: item[1]['xm'])
        smallest_two = sorted_items[:2]
        result = [(item[1]['xm'], item[1]['ym']) for item in smallest_two]
        return result
    
    def intersect(x1, y1, x2, y2, x3, y3, x4, y4):
        """To find intersection points of 2 lines, used to find intersection of webs and bottom flange"""
        den = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)
        det_t = (x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)
        det_u = (x3 - x1) * (y2 - y1) - (y3 - y1) * (x2 - x1)
        t = det_t / den
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        return (x , y)
    
    def ortho_line_plot(li1, li2, li3, li4, lines, d = 1, h = 1, v = 1):
        """li1 & li2 are list of X & Y ordinates of curve 1.  li3 & li4 are X&Y of curve 2.
        Orthogonal lines are created from curve 2 vertices on curve 1."""
        for x3, y3 in zip(li3,li4):
            for i in range(len(li1) - 1):
                x1, y1 = li1[i], li2[i]
                x2, y2 = li1[i + 1], li2[i + 1]
                lin = perpendicular_point(x1, y1, x2, y2, x3, y3)
                if type(lin) == tuple:
                    if lin[2] <= d and lin[2]>=0.0001:
                        if h == 0 and v== 0:
                            if y3 != lin[1] and x3 != lin[0]:
                                lines.append((x3, y3, lin[0], lin[1], lin[2]))
                        elif h == 0:
                            if y3 != lin[1]:
                                lines.append((x3, y3, lin[0], lin[1], lin[2]))
                        elif v == 0:
                            if x3 != lin[0]:
                                lines.append((x3, y3, lin[0], lin[1], lin[2]))
                        else:
                            lines.append((x3, y3, lin[0], lin[1], lin[2]))
    
    def point_on_line(x1, y1, x2, y2, x3, y3):
        """Function to check if the point (x3,y3) is on line (x1,y1)-(x2,y2).  Used to distinguish dictionaries for flanges & webs."""
        if round((y2 - y1) * (x3 - x1),5) == round((y3 - y1) * (x2 - x1),5):
            return 1
        else:
            return 0
    
    def part_len(dic, length):
        """Function used to divid a curve to required length."""
        for i in range(1, len(dic)):
            dist = ((dic[i]['xm'] - dic[i+1]['xm'])**2 + (dic[i]['ym'] - dic[i+1]['ym'])**2)**0.5
            if dist > length:
                nos = int(dist/length) + 1
                for j in range(1, nos):
                    dic.update({i+0.01*j:{
                        'thk': dic[i]['thk']+(dic[i+1]['thk'] - dic[i]['thk'])*j/nos,
                        'xm': dic[i]['xm']+(dic[i+1]['xm'] - dic[i]['xm'])*j/nos,
                        'ym': dic[i]['ym']+(dic[i+1]['ym'] - dic[i]['ym'])*j/nos}})
    
    def reorder(dic):
        """Reorder a dictionary based on it's keys and renumber them from 1 onwards"""
        sorted_dic = {k:v for k,v in sorted(dic.items())}
        new = {i: value for i, value in enumerate(sorted_dic.values(), start=1)}
        return new
    
    def xysort(dic, x=1):
        """Reorder a dictionary based on xm and ym values.  Enter x = 1 for sorting xm first and then ym.  Enter 0 for ym first and xm later."""
        if x == 1:
            sorted_data = {k: v for k, v in sorted(dic.items(), key=lambda item: (item[1]['xm'], item[1]['ym']))}
            new_dic = {i: value for i, value in enumerate(sorted_data.values(), start=1)}
        elif x == 0:
            sorted_data = {k: v for k, v in sorted(dic.items(), key=lambda item: (item[1]['ym'], item[1]['xm']))}
            new_dic = {i: value for i, value in enumerate(sorted_data.values(), start=1)}
        return new_dic
    
    def center_top(flange):
        x = max(value['xm'] for value in flange.values())
        
    def connector(web = [], flange = []):
        """List of web dictionaries, List of flange dictionaries.  Used to create connecting lines from webs to flanges."""
        if web !=[] and flange !=[]:
            y2 = min(value['ym'] for value in flange[1].values())
            
            # Find top and bottom ordinate of each web
            xw_max, yw_max = [], []
            xw_min, yw_min = [], []
            thk_min, thk_max = [], []
            for dic in web:
                max_ym_key = max(dic, key=lambda k: dic[k]['ym'])
                xw_max.append(dic[max_ym_key]['xm'])
                yw_max.append(dic[max_ym_key]['ym'])
                thk_max.append(dic[max_ym_key]['thk'])
                min_ym_key = min(dic, key=lambda k: dic[k]['ym'])
                xw_min.append(dic[min_ym_key]['xm'])
                yw_min.append(dic[min_ym_key]['ym'])
                thk_min.append(dic[min_ym_key]['thk'])
                
            # Find intersection point of each web with both the flanges
            xo_max, yo_max = [None]*len(xw_max), [None]*len(yw_max)
            xo_min, yo_min = [], []
            for i in range(len(xw_min)):
                dist = 999999
                for dic in flange:
                    for j in range(1,len(dic)-1):
                        pp = perpendicular_point(dic[j]['xm'], dic[j]['ym'], dic[j+1]['xm'], dic[j+1]['ym'], xw_max[i], yw_max[i])
                        if pp != None:
                            dist = min(dist, pp[2])
                            if pp[2] <= dist:
                                xo_max[i] = pp[0]
                                yo_max[i] = pp[1]
            flange_left_xy = left_2(flange[1])
            web_left_xy = lower_2(web[0])
            if len(web)>2: mid_xy = lower_2(web[2])
            pp = intersect(web_left_xy[0][0], web_left_xy[0][1], web_left_xy[1][0], web_left_xy[1][1], 
                        flange_left_xy[0][0], flange_left_xy[0][1], flange_left_xy[1][0], flange_left_xy[1][1])
            xo_min.append(pp[0])
            yo_min.append(pp[1])
            xo_min.append(pp[0] * -1)
            yo_min.append(pp[1])
            if len(web)>2:
                pp = intersect(mid_xy[0][0], mid_xy[0][1], mid_xy[1][0], mid_xy[1][1], 
                        0, y2, 5, y2)
                xo_min.append(pp[0])
                yo_min.append(pp[1])
            return [xo_max, yo_max, thk_max, xo_min, yo_min, thk_min]
            
    external_polygon = plt.Polygon(list(zip(a[0], a[1])), closed=True, fill=None, edgecolor='black')
    plt.gca().add_patch(external_polygon)
    
    internal_polygon = plt.Polygon(list(zip(a[2], a[3])), closed=True, fill=None, edgecolor='red')
    plt.gca().add_patch(internal_polygon)
    
    ortho_lines =[]
    ortho_line_plot(a[0],a[1],a[2],a[3], ortho_lines)
    ortho_line_plot(a[0],a[1],a[0],a[1], ortho_lines, h = 0)
    if len(a) == 6:
        internal_polygon = plt.Polygon(list(zip(a[4], a[5])), closed=True, fill=None, edgecolor='red')
        plt.gca().add_patch(internal_polygon)
        ortho_line_plot(a[0],a[1],a[4],a[5], ortho_lines)
        ortho_line_plot(a[4],a[5],a[2],a[3], ortho_lines, d = 0.5)
    plt.xlim(-5, 5)
    plt.ylim(-2, 2)
    plt.gca().set_aspect('equal', adjustable='box')
    dic = {}
    
    # Ploting orthogonal lines and creating the dictionary
    for i in range(len(ortho_lines)):
        plt.plot([ortho_lines[i][0],ortho_lines[i][2]],[ortho_lines[i][1],ortho_lines[i][3]],'g-')
        if (ortho_lines[i][2] - ortho_lines[i][0]) !=0:
            m = (ortho_lines[i][3] - ortho_lines[i][1])/(ortho_lines[i][2] - ortho_lines[i][0])
        else:
            m = 10000
        update = 1
        if dic != {}:
            for j in list(dic.keys()):
                if dic[j]['x1'] == ortho_lines[i][0] and dic[j]['y1'] == ortho_lines[i][1] and dic[j]['x2'] == ortho_lines[i][2] and dic[j]['y2'] == ortho_lines[i][3]: update = 0
        if update == 1:
            dic.update({i:{
                'x1': ortho_lines[i][0],
                'y1': ortho_lines[i][1],
                'x2': ortho_lines[i][2],
                'y2': ortho_lines[i][3],
                'thk': ortho_lines[i][4],
                'slope': m,
                'xm': (ortho_lines[i][0] + ortho_lines[i][2])/2,
                'ym': (ortho_lines[i][1] + ortho_lines[i][3])/2}})
        update = 1
    del ortho_lines
    
    # Sorting the dictionary based on the vertical ordinates and then in accordance to horizontal ordinates
    sorted_data = {k: v for k, v in sorted(dic.items(), key=lambda item: (item[1]['xm'], item[1]['ym']))}
    new_dic = {i: value for i, value in enumerate(sorted_data.values(), start=0)}
    del sorted_data
    
    # Separating and creating new dictionaries, bifurcating the webs and flanges
    s, t, u, v, w = 1, 1, 1, 1, 1
    mid_web, top_flange, bot_flange, left_web, right_web = {}, {}, {}, {}, {}
    for i in new_dic.keys():
        if point_on_line(external[0][0], external[0][1], external[1][0], external[1][1], new_dic[i]['x2'], new_dic[i]['y2']) == 1:
            top_flange.update({t : new_dic[i]})
            t += 1
        elif point_on_line(external[0][0], external[0][1], -1*external[1][0], external[1][1], new_dic[i]['x2'], new_dic[i]['y2']) == 1:
            top_flange.update({t : new_dic[i]})
            t =+ 1
        elif point_on_line(external[7][0], external[7][1], external[8][0], external[8][1], new_dic[i]['x2'], new_dic[i]['y2']) == 1:
            bot_flange.update({u : new_dic[i]})
            u += 1
        elif point_on_line(external[5][0], external[5][1], external[7][0], external[7][1], new_dic[i]['x2'], new_dic[i]['y2']) == 1:
            right_web.update({v : new_dic[i]})
            v += 1
        elif point_on_line(-1*external[5][0], external[5][1], -1*external[7][0], external[7][1], new_dic[i]['x2'], new_dic[i]['y2']) == 1:
            left_web.update({w : new_dic[i]})
            w += 1
        elif point_on_line(-1*internal[0][0], internal[0][1], -1*internal[8][0], internal[8][1], new_dic[i]['x2'], new_dic[i]['y2']) == 1:
            mid_web.update({s : new_dic[i]})
            s += 1
    
    #Creating the dictionary with connecting points
    if mid_web == {}: li = connector([left_web, right_web],[top_flange, bot_flange])
    if mid_web != {}: li = connector([left_web, right_web, mid_web],[top_flange, bot_flange])
    
    # Update flange and web dictionaries to consider end points
    top_flange.update({0.0001:{'xm':li[0][0],
                        'ym': li[1][0],
                        'thk': li[2][0]},
                    0.0002:{'xm':li[0][1],
                        'ym': li[1][1],
                        'thk': li[2][1]}})
    if mid_web != {}:
        top_flange.update({0.0003:{'xm':li[0][2],
                        'ym': li[1][2],
                        'thk': li[2][2]}})
    bot_flange.update({0.0001:{'xm':li[3][0],
                        'ym': li[4][0],
                        'thk': li[5][0]},
                    0.0002:{'xm':li[3][1],
                        'ym': li[4][1],
                        'thk': li[5][1]}})
    if mid_web != {}:
        bot_flange.update({0.0003:{'xm':li[3][2],
                        'ym': li[4][2],
                        'thk': li[5][2]}})
    left_web.update({0.0001:{'xm':li[0][0],
                        'ym':li[1][0],
                        'thk': li[2][0]},
                    0.0002:{'xm':li[3][0],
                        'ym':li[4][0],
                        'thk': li[5][0]}})
    right_web.update({0.0001:{'xm':li[0][1],
                        'ym':li[1][1],
                        'thk': li[2][1]},
                    0.0002:{'xm':li[3][1],
                        'ym':li[4][1],
                        'thk': li[5][1]}})
    if mid_web != {}:
        mid_web.update({0.0001:{'xm':li[0][2],
                            'ym':li[1][2],
                            'thk': li[2][2]},
                        0.0002:{'xm':li[3][2],
                            'ym':li[4][2],
                            'thk': li[5][2]}})
    
    # Sort and renumber flange and web dictionaries to consider connecting elements at proper locations
    top_flange = xysort(top_flange,1)
    bot_flange = xysort(bot_flange,1)
    right_web = xysort(right_web,0)
    left_web = xysort(left_web,0)
    if mid_web != {}: mid_web = xysort(mid_web,0)
    
    # Dividing the flanges & webs close to the required length of elements
    dictionary = [top_flange, bot_flange, right_web, left_web]
    for i in range(len(dictionary)):
        part_len(dictionary[i], 0.3)
        dictionary[i] = reorder(dictionary[i])
    top_flange = dictionary[0]
    bot_flange = dictionary[1]
    right_web = dictionary[2]
    left_web = dictionary[3]
    if mid_web != {}:
        part_len(mid_web,0.3)
        mid_web = reorder(mid_web)
    
    # Plotting the centerline of the cross section
    for i in range(1, len(top_flange)):
        current = top_flange[i]
        next1 = top_flange[i + 1]
        plt.plot([next1['xm'], current['xm']], [next1['ym'], current['ym']], 'y-', marker ='o')
    for i in range(1, len(bot_flange)):
        current = bot_flange[i]
        next1 = bot_flange[i + 1]
        plt.plot([next1['xm'], current['xm']], [next1['ym'], current['ym']], 'y-', marker ='o')
    for i in range(1, len(left_web)):
        current = left_web[i]
        next1 = left_web[i + 1]
        plt.plot([next1['xm'], current['xm']], [next1['ym'], current['ym']], 'y-', marker ='o')
    for i in range(1, len(right_web)):
        current = right_web[i]
        next1 = right_web[i + 1]
        plt.plot([next1['xm'], current['xm']], [next1['ym'], current['ym']], 'y-', marker ='o')
    for i in range(1, len(mid_web)):
        current = mid_web[i]
        next1 = mid_web[i + 1]
        plt.plot([next1['xm'], current['xm']], [next1['ym'], current['ym']], 'y-', marker ='o')
    # Display plot
    # plt.show()
    # ax.plot(x, y, label=f'Section')
    ax.set_title(f'Centerline Plot')
    # ax.legend()
    return fig
#---------------------------------------------------------------------------------------------------------------
#Function to get the number of tendons and distributed based on effective tendon
def tendon_req(dir, elem, cc, dc, s1 = 98.7, s2 = 140, min_strand = 7, max_strand = 19, max_tendon = 5, maxt_extrf = 2):
    """INCOMPLETE"""
    eff_P = dir['P'][0]
    eff_ecc = dir['e'][0]
    eff_PT_area = dir['PT_area'][0]



# Function to get PSC section for dropdown 
def get_Section():
    response = MidasAPI('GET', '/db/sect')
    section_list = []

    if 'SECT' in response:
        for sect_id, sect_data in response['SECT'].items():
            sect_type = sect_data.get('SECTTYPE', '')
            shape = sect_data.get('SECT_BEFORE', {}).get('SHAPE', '')

            if sect_type == "PSC" and shape in ["1CEL", "2CEL"]:
                section_list.append((int(sect_id), sect_data.get('SECT_NAME', 'Unnamed Section')))

    return section_list
