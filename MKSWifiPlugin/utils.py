from cura.CuraApplication import CuraApplication
from UM.Math.Vector import Vector
from UM.Application import Application
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from cura.Snapshot import Snapshot
from PyQt5.QtCore import Qt
import os
from ctypes import *
from UM.Logger import Logger
import binascii
import platform
from UM.Platform import Platform
from array import array
from UM.i18n import i18nCatalog
from UM.Message import Message

def getRect():
    left = None
    front = None
    right = None
    back = None
    for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):
        if node.getBoundingBoxMesh():
            if not left or node.getBoundingBox().left < left:
                left = node.getBoundingBox().left
            if not right or node.getBoundingBox().right > right:
                right = node.getBoundingBox().right
            if not front or node.getBoundingBox().front > front:
                front = node.getBoundingBox().front
            if not back or node.getBoundingBox().back < back:
                back = node.getBoundingBox().back
    if not (left and front and right and back):
        return 0
    result = max((right - left), (front - back))
    return result


def add_screenshot(img, width, height, img_type):
    result = ""
    b_image = img.scaled(width, height, Qt.KeepAspectRatio)
    # b_image.save(os.path.abspath("")+"\\test_"+str(width)+"_.png")
    # img.save(os.path.abspath("") + "\\testb_" + str(width) + "_.png")
    img_size = b_image.size()
    result += img_type
    datasize = 0
    for i in range(img_size.height()):
        for j in range(img_size.width()):
            pixel_color = b_image.pixelColor(j, i)
            r = pixel_color.red() >> 3
            g = pixel_color.green() >> 2
            b = pixel_color.blue() >> 3
            rgb = (r << 11) | (g << 5) | b
            strHex = "%x" % rgb
            if len(strHex) == 3:
                strHex = '0' + strHex[0:3]
            elif len(strHex) == 2:
                strHex = '00' + strHex[0:2]
            elif len(strHex) == 1:
                strHex = '000' + strHex[0:1]
            if strHex[2:4] != '':
                result += strHex[2:4]
                datasize += 2
            if strHex[0:2] != '':
                result += strHex[0:2]
                datasize += 2
            if datasize >= 50:
                datasize = 0
        # if i != img_size.height() - 1:
        result += '\rM10086 ;'
        if i == img_size.height() - 1:
            result += "\r"
    return result

def add_screenshot_new(img, width, height, img_type):
    # Logger.log("d", "add_screenshot." +  platform.system())
    Logger.log("d", "add_screenshot." +  CuraApplication.getInstance().getMachineManager().activeMachine.definition.id)
    Logger.log("d", "add_screenshot." +  CuraApplication.getInstance().getMachineManager().activeMachine.definition.name)
    if Platform.isOSX():
        pDll = CDLL(os.path.join(os.path.dirname(__file__), "libColPic.dylib"))
    elif Platform.isLinux():
        pDll = CDLL(os.path.join(os.path.dirname(__file__), "libColPic.so"))
    else:
        pDll = CDLL(os.path.join(os.path.dirname(__file__), "ColPic_X64.dll"))

    result = ""
    b_image = img.scaled(width, height, Qt.KeepAspectRatio)
    # b_image.save(os.path.abspath("")+"\\test_"+str(width)+"_.png")
    # img.save(os.path.abspath("") + "\\testb_" + str(width) + "_.png")
    img_size = b_image.size()
    color16 = array('H')
    try:
        # Logger.log("d", "try == ")
        for i in range(img_size.height()):
            for j in range(img_size.width()):
                pixel_color = b_image.pixelColor(j, i)
                r = pixel_color.red() >> 3
                g = pixel_color.green() >> 2
                b = pixel_color.blue() >> 3
                rgb = (r << 11) | (g << 5) | b
                color16.append(rgb)

        # int ColPic_EncodeStr(U16* fromcolor16, int picw, int pich, U8* outputdata, int outputmaxtsize, int colorsmax);
        fromcolor16 = color16.tobytes()
        outputdata = array('B',[0]*img_size.height()*img_size.width()).tobytes()
        resultInt = pDll.ColPic_EncodeStr(fromcolor16, img_size.height(), img_size.width(), outputdata, img_size.height()*img_size.width(), 1024)

        data0 = str(outputdata).replace('\\x00', '')
        data1 = data0[2:len(data0) - 2]
        eachMax = 1024 - 8 - 1
        maxline = int(len(data1)/eachMax)
        appendlen = eachMax - 3 - int(len(data1)%eachMax)

        for i in range(len(data1)):
            if i == maxline*eachMax:
                result += '\r;' + img_type + data1[i]
            elif i == 0:
                result += img_type + data1[i]
            elif i%eachMax == 0:
                result += '\r' + img_type + data1[i]
            else:
                result += data1[i]
        result += '\r;'
        for j in range(appendlen):
            result += '0'

    except Exception as e:
        Logger.log("d", "Exception == " + str(e))
    
    return result + '\r'


def take_screenshot():
    cut_image = Snapshot.snapshot(width = 900, height = 900)
    return cut_image
