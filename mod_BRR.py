import BigWorld
import AccountCommands
import ResMgr

import base64
import cPickle
import httplib
import json
import os
import traceback
import zlib

from account_helpers import BattleResultsCache
from battle_results_shared import *
from debug_utils import *
from threading import Thread
from urlparse import urlparse
from gui.shared.utils.requesters import StatsRequester
from messenger.proto.bw import ServiceChannelManager
from functools import partial
from gui import ClientHangarSpace
from gui import hangar_vehicle_appearance
from PlayerEvents import g_playerEvents
LOG_NOTE('Battle Result Retriever Mod (BRR) for WoT 1.0 is made by the Wot Numbers Team (http://wotnumbers.com)')
LOG_NOTE('BRR initializing')
BATTLE_RESULTS_VERSION = 1
CACHE_DIR = os.path.join(os.path.dirname(unicode(BigWorld.wg_getPreferencesFilePath(), 'utf-8', errors='ignore')), 'battle_results')
todolist = []

def fetchresult(arenaUniqueID):
    LOG_NOTE('Lookup battle result for arenaUniqueId:', arenaUniqueID)
    if arenaUniqueID:
        battleResults = load(BigWorld.player().name, arenaUniqueID)
        if battleResults is not None:
            LOG_NOTE('Battle result found')
        proxy = partial(__onGetResponse, None)
        BigWorld.player()._doCmdInt3(AccountCommands.CMD_REQ_BATTLE_RESULTS, arenaUniqueID, 0, 0, proxy)
    else:
        return
    return


def __onGetResponse(callback, requestID, resultID, errorStr, ext={}):
    LOG_NOTE('Handler OnGetResponse invoked:', requestID, resultID)
    if resultID != AccountCommands.RES_STREAM:
        if callback is not None:
            try:
                callback(resultID, None)
            except:
                LOG_CURRENT_EXCEPTION()

        return
    BigWorld.player()._subscribeForStream(requestID, partial(__onStreamComplete, callback))
    return
    return


def __onStreamComplete(callback, isSuccess, data):
    LOG_NOTE('Handler OnStreamComplete invoked:', isSuccess)
    try:
        battleResults = cPickle.loads(zlib.decompress(data))
        LOG_NOTE('Stream complete:', isSuccess)
        save(BigWorld.player().name, battleResults)
    except:
        LOG_CURRENT_EXCEPTION()
        if callback is not None:
            callback(AccountCommands.RES_FAILURE, None)

    return


def getFolderNameArena(accountName, arenaUniqueID):
    battleStartTime = arenaUniqueID & 4294967295L
    battleStartDay = battleStartTime / 86400
    return os.path.join(CACHE_DIR, base64.b32encode('%s;%s' % (accountName, battleStartDay)))


def getFolderName(accountName):
    import time
    battleStartDay = int(time.time()) / 86400
    return os.path.join(CACHE_DIR, base64.b32encode('%s;%s' % (accountName, battleStartDay)))


def load(accountName, arenaUniqueID):
    LOG_NOTE('Loading battle file for arenaUniqueId:', arenaUniqueID)
    fileHandler = None
    try:
        fileName = os.path.join(getFolderNameArena(accountName, arenaUniqueID), '%s.dat' % arenaUniqueID)
        if not os.path.isfile(fileName):
            return
        fileHandler = open(fileName, 'rb')
        version, battleResults = cPickle.load(fileHandler)
    except:
        LOG_CURRENT_EXCEPTION()

    if fileHandler is not None:
        fileHandler.close()
    return battleResults


def save_existing(directory):
    createEnvironment()
    import string, shutil
    directory = string.replace(directory, '\\\\', '/')
    directory = string.replace(directory, '\\', '/')
    if not os.path.exists(directory):
        os.makedirs(directory)
    if os.path.exists(directory):
        LOG_NOTE('Checking existing battle result files in:', directory)
        try:
            for root, directories, files in os.walk(directory):
                for fileName in files:
                    LOG_NOTE('Checking file:', fileName)
                    if fileName.endswith('.dat'):
                        fullFileName = os.path.join(root, fileName)
                        if os.path.getsize(fullFileName) > 0:
                            fileNameADU = os.path.join('vBAddict', fileName)
                            if not os.path.exists(fileNameADU):
                                LOG_NOTE('Saving file:', fullFileName)
                                shutil.copyfile(fullFileName, fileNameADU)
                        else:
                            LOG_NOTE('File not ready for copy (empty):', fileName)

        except:
            LOG_CURRENT_EXCEPTION()

    else:
        LOG_NOTE('Folder not found:', directory)


def createEnvironment():
    import os
    try:
        if not os.path.isdir('vBAddict'):
            os.makedirs('vBAddict')
        if not os.path.exists('vBAddict'):
            return
    except Exception:
        e = None
        LOG_CURRENT_EXCEPTION()

    return


def save(accountName, battleResults):
    LOG_NOTE('Saving battle result for account:', accountName)
    fileHandler = None
    try:
        arenaUniqueID = battleResults[0]
        LOG_NOTE('Saving battle results for arenaUniqueID:', arenaUniqueID)
        folderName = getFolderNameArena(accountName, arenaUniqueID)
        if not os.path.isdir(folderName):
            os.makedirs(folderName)
        fileName = os.path.join(folderName, '%s.dat' % arenaUniqueID)
        fileHandler = open(fileName, 'wb')
        cPickle.dump((BATTLE_RESULTS_VERSION, battleResults), fileHandler, -1)
        save_existing(folderName)
    except:
        LOG_CURRENT_EXCEPTION()

    if fileHandler is not None:
        fileHandler.close()
    return


default_msg = ServiceChannelManager._ServiceChannelManager__addServerMessage
default_setup = hangar_vehicle_appearance.HangarVehicleAppearance._HangarVehicleAppearance__doFinalSetup

def custom_msg(self, message):
    LOG_NOTE('ServiceChannelManager.AddServerMessage invoked, received message:', message)
    if message.type == 2:
        try:
            arenaUniqueID = message.data.get('arenaUniqueID', 0)
            if arenaUniqueID > 0:
                todolist.append(arenaUniqueID)
        except:
            LOG_CURRENT_EXCEPTION()

    default_msg(self, message)


def custom_setup(self, buildIdx):
    LOG_NOTE('HangarVehicleAppearance.DoFinalSetup invoked')
    if todolist:
        LOG_NOTE('Processing battle files:', todolist)
        while todolist:
            temp = todolist.pop()
            fetchresult(int(temp))

        save_existing(getFolderName(BigWorld.player().name))
    default_setup(self, buildIdx)


LOG_NOTE('BRR installing')
ServiceChannelManager._ServiceChannelManager__addServerMessage = custom_msg
hangar_vehicle_appearance.HangarVehicleAppearance._HangarVehicleAppearance__doFinalSetup = custom_setup
LOG_NOTE('BRR loaded')