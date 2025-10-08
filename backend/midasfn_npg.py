import math as mt
from midas_civil import *
import matplotlib.pyplot as plt
from scipy.interpolate import CubicHermiteSpline
import requests
import numpy as np

section_ids = []    #Global list of section IDs
segment = {}
array_1 = {}

MAPI_KEY("")
MAPI_BASEURL('')

def MidasAPI(method, command, body=None):
    """Method, Command, Body.  Sample: MidasAPI("PUT","/db/NODE",{"Assign":{1{'X':0, 'Y':0, 'Z':0}}})"""
    base_url = MAPI_BASEURL.baseURL
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

    try:
        return response.json()
    except Exception as e:
        print("Failed to parse JSON:", e)
        return None


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

#Function to check analysis status & perform analysis if not analyzed
def analyze():
    """Checkes whether a model is analyzed or not and then performs analysis if required."""
    r = (MidasAPI("POST","/post/TABLE",{"Argument": {"TABLE_NAME": "Reaction(Global)","TABLE_TYPE": "REACTIONG",}}))
    if 'error' in r.keys():
        MidasAPI("POST","/doc/SAVE",{"Argument":{}})
        MidasAPI("POST","/doc/ANAL",{"Assign":{}})
#--------------------------------------------------------------------------------------------------------------------------
#Function to remove duplicate nodes and elements from Node & Element classes
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
#--------------------------------------------------------------------------------------------------------------------------
#Class to define PSC 1-CELL, 2-CELL & Half Sections
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
#---------------------------------------------------------------------------------------------------------------------------
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
#---------------------------------------------------------------------------------------------------------------------------
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
#---------------------------------------------------------------------------------------------------------------------------
#Function to get centerline of the cross-section PSC 1-Cell & 2-Cell
def PSC_1CEL_XY(sec, offset = "CC"):
    """INCOMPLETE.  Section ID.  Sample:  PSC_1CEL(3)."""
    
    global segment 
    # segment ={}
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
    
    if sec not in segment:
        segment[sec] = {} 
    # Segmentation of polygons
    segment['sec'] = {
        'external': list(zip(x, y)),
        'internal_1': list(zip(ix, iy)),
    }
    ortho_lines =[]
    segment['ortho_lines'] = {
        'line_1': [] ,
        'line_2': []
    }
    if inp[sec]['SECT_BEFORE']['SHAPE'] == '2CEL':
        segment[sec]['internal_2'] = list(zip(ix_1, iy_1))
    
    external_polygon = plt.Polygon(list(zip(a[0], a[1])), closed=True, fill=None, edgecolor='black')
    plt.gca().add_patch(external_polygon)
    
    
    internal_polygon = plt.Polygon(list(zip(a[2], a[3])), closed=True, fill=None, edgecolor='red')
    plt.gca().add_patch(internal_polygon)
            
    
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
    
    # Plotting orthogonal lines and creating the dictionary
    for i in range(len(ortho_lines)):
        plt.plot([ortho_lines[i][0],ortho_lines[i][2]],[ortho_lines[i][1],ortho_lines[i][3]],'g-')
        segment['ortho_lines']['line_1'].append([ortho_lines[i][0],ortho_lines[i][2]])
        segment['ortho_lines']['line_2'].append([ortho_lines[i][1],ortho_lines[i][3]])
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
    
    #Plotting the centerline of the cross section
    segment['top_flange']={'Xm':[],'Ym':[], 'thk':[]}
    segment['bot_flange']={'Xm':[],'Ym':[], 'thk':[]}
    segment['left_web']={'Xm':[],'Ym':[], 'thk':[]}
    segment['right_web']={'Xm':[],'Ym':[], 'thk':[]}
    segment['mid_web']={'Xm':[],'Ym':[], 'thk':[]}
     
    for i in range(1, len(top_flange)):
        current = top_flange[i]
        next1 = top_flange[i + 1]
        plt.plot([next1['xm'], current['xm']], [next1['ym'], current['ym']], 'y-', marker ='o')
        thickness = ((current['thk'] + next1['thk'])/2)
        segment['top_flange']['Xm'].append([next1['xm'], current['xm']])
        segment['top_flange']['Ym'].append([next1['ym'], current['ym']])
        segment['top_flange']['thk'].append(thickness)
    
    for i in range(1, len(bot_flange)):
        current = bot_flange[i]
        next1 = bot_flange[i + 1]
        plt.plot([next1['xm'], current['xm']], [next1['ym'], current['ym']], 'y-', marker ='o')
        thickness = ((current['thk'] + next1['thk'])/2)
        segment['bot_flange']['Xm'].append([next1['xm'], current['xm']])
        segment['bot_flange']['Ym'].append([next1['ym'], current['ym']])
        segment['bot_flange']['thk'].append(thickness)
        
    for i in range(1, len(left_web)):
        current = left_web[i]
        next1 = left_web[i + 1]
        plt.plot([next1['xm'], current['xm']], [next1['ym'], current['ym']], 'y-', marker ='o')
        thickness = ((current['thk'] + next1['thk'])/2)
        segment['left_web']['Xm'].append([next1['xm'], current['xm']])
        segment['left_web']['Ym'].append([next1['ym'], current['ym']])
        segment['left_web']['thk'].append(thickness)
    
    for i in range(1, len(right_web)):
        current = right_web[i]
        next1 = right_web[i + 1]
        plt.plot([next1['xm'], current['xm']], [next1['ym'], current['ym']], 'y-', marker ='o')
        thickness = ((current['thk'] + next1['thk'])/2)
        segment['right_web']['Xm'].append([next1['xm'], current['xm']])
        segment['right_web']['Ym'].append([next1['ym'], current['ym']])
        segment['right_web']['thk'].append(thickness)
    
    for i in range(1, len(mid_web)):
        current = mid_web[i]
        next1 = mid_web[i + 1]
        plt.plot([next1['xm'], current['xm']], [next1['ym'], current['ym']], 'y-', marker ='o')
        thickness = ((current['thk'] + next1['thk'])/2)
        segment['mid_web']['Ym'].append([next1['ym'], current['ym']])
        segment['mid_web']['Ym'].append([next1['ym'], current['ym']])
        segment['mid_web']['thk'].append(thickness)
    # Display plot
    fig = plt.gcf()
    # plt.show()
    # print(dictionary[0])
    return fig 
#---------------------------------------------------------------------------------------------------------------------------
def plotsegment():
    global array_1
    # Initialize storage arrays
    array_1 = {
        'top_flange': {"X_coordinates": [], "Y_coordinates": [], "thickness": []},
        'bot_flange': {"X_coordinates": [], "Y_coordinates": [], "thickness": []},
        'right_web': {"X_coordinates": [], "Y_coordinates": [], "thickness": []},
        'left_web': {"X_coordinates": [], "Y_coordinates": [], "thickness": []},
        'mid_web': {"X_coordinates": [], "Y_coordinates": [], "thickness": []},
    }
    # --- TOP FLANGE ---
    X_coord = [segment['top_flange']["Xm"][0][1]]
    Y_coord = [segment['top_flange']["Ym"][0][1]]
    for i in range(len(segment['top_flange']['Xm'])):
        X_coord.append(segment['top_flange']["Xm"][i][0])
        Y_coord.append(segment['top_flange']["Ym"][i][0])

    array_1['top_flange']["X_coordinates"].append(X_coord)
    array_1['top_flange']["Y_coordinates"].append(Y_coord)
    array_1['top_flange']["thickness"].append(segment['top_flange']['thk'])
    # --- BOTTOM FLANGE ---
    X_coord = [segment['bot_flange']["Xm"][0][1]]
    Y_coord = [segment['bot_flange']["Ym"][0][1]]
    for i in range(len(segment['bot_flange']['Xm'])):
        X_coord.append(segment['bot_flange']["Xm"][i][0])
        Y_coord.append(segment['bot_flange']["Ym"][i][0])

    array_1['bot_flange']["X_coordinates"].append(X_coord)
    array_1['bot_flange']["Y_coordinates"].append(Y_coord)
    array_1['bot_flange']["thickness"].append(segment['bot_flange']['thk'])
    # --- LEFT WEB ---
    X_coord = [segment['left_web']["Xm"][0][1]]
    Y_coord = [segment['left_web']["Ym"][0][1]]
    for i in range(len(segment['left_web']['Xm'])):
        X_coord.append(segment['left_web']["Xm"][i][0])
        Y_coord.append(segment['left_web']["Ym"][i][0])

    array_1['left_web']["X_coordinates"].append(X_coord)
    array_1['left_web']["Y_coordinates"].append(Y_coord)
    array_1['left_web']["thickness"].append(segment['left_web']['thk'])
    # --- RIGHT WEB ---
    X_coord = [segment['right_web']["Xm"][0][1]]
    Y_coord = [segment['right_web']["Ym"][0][1]]
    for i in range(len(segment['right_web']['Xm'])):
        X_coord.append(segment['right_web']["Xm"][i][0])
        Y_coord.append(segment['right_web']["Ym"][i][0])

    array_1['right_web']["X_coordinates"].append(X_coord)
    array_1['right_web']["Y_coordinates"].append(Y_coord)
    array_1['right_web']["thickness"].append(segment['right_web']['thk'])
    # --- MID WEB (handle 1CEL / 2CEL cases) ---
    if not segment.get('mid_web'):  # 1CEL PSC (no mid web)
        array_1['mid_web']["X_coordinates"].append([0])
        array_1['mid_web']["Y_coordinates"].append([0])
        array_1['mid_web']["thickness"].append(0)
    else:  # 2CEL PSC (vertical mid web)
        Ym_values = segment['mid_web'].get('Ym', [])
        thk = segment['mid_web'].get('thk', 0)
        X_coord = [0 for _ in range(len(Ym_values))]
        Y_coord = []
        for ym in Ym_values:
            if isinstance(ym, list):  # sometimes [[y1, y2], ...]
                Y_coord.append(ym[1] if len(ym) > 1 else ym[0])
            else:
                Y_coord.append(ym)

        array_1['mid_web']["X_coordinates"].append(X_coord)
        array_1['mid_web']["Y_coordinates"].append(Y_coord)
        array_1['mid_web']["thickness"].append(thk)
        
    return array_1

# Creating arrays to pass it into line to plate..  
def build_global_arrays():
    global array_1
    nodes = []
    lines = []
    thicknesses = []
    for part, data in array_1.items():
        Xs = data["X_coordinates"][0]
        Ys = data["Y_coordinates"][0]
        Thks = data["thickness"][0]
        # Special handling for mid_web (duplicate Y entries)
        if part == "mid_web":
            for i in range(len(Xs)-1):
                n1 = [Xs[i], Ys[i]]
                n2 = [Xs[i+1], Ys[i+1]]

                if n1 not in nodes:
                    nodes.append(n1)
                if n2 not in nodes:
                    nodes.append(n2)

                idx1 = nodes.index(n1)
                idx2 = nodes.index(n2)

                lines.append([idx1, idx2])
                thicknesses.append(Thks[i // 2])  # each thickness repeats twice
        else:
            for i in range(len(Thks)):
                n1 = [Xs[i], Ys[i]]
                n2 = [Xs[i+1], Ys[i+1]]

                if n1 not in nodes:
                    nodes.append(n1)
                if n2 not in nodes:
                    nodes.append(n2)

                idx1 = nodes.index(n1)
                idx2 = nodes.index(n2)

                lines.append([idx1, idx2])
                thicknesses.append(Thks[i])

    return np.array(nodes), np.array(lines), np.array(thicknesses)

# Function to get PSC section for dropdown UI 
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