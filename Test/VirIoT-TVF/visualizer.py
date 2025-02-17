import cefpyco
import sys
import time
import threading
import json
import os
#import netifaces as ni
from logging import basicConfig, getLogger, DEBUG, INFO

#import from tvFactoryLibrary
from common import common
from protocol import icnCefore
from protocol import kafka
#####

SETTING = "./config/nodeSetting.json"

if __name__ == '__main__':

    args = sys.argv
    common.checkARG(len(args))
    interest = str(args[1])
    funcList = common.analyzeInterest(interest)

    with open(SETTING, "r") as fp:
        setting = common.jsonReader(fp)

    hostIP = "dummy"
    #hostIP = ni.ifaddresses(setting["iface"])[ni.AF_INET][0]['addr']
    MODE = setting["mode"]
    SLEEP = int(setting["sleep"])/1000 #(sec)
    CACHETIME = int(setting["cache time"]) #(msec)
    EXPIRY = int(setting["expiry"]) #(msec)
    TIMEOUT = int(setting["timeout"]) #(msec)
    segSize = int(setting["segSize"])
    BROKER = setting["broker"]
    TOPIC_OUT = setting["topic to controller"]
    TOPIC_IN = setting["topic from controller"]
    HOST = setting["host"]
    revSize = setting["revSize"]
    logLevel = setting["logLevel"]

    if (logLevel == "info"):
        basicConfig(level=INFO)
    if (logLevel == "debug"):
        basicConfig(level=DEBUG)

    logger = getLogger(__name__)

    icnSetting = {"segSize":segSize, "cacheTime":CACHETIME, "expiry":EXPIRY, "timeout":TIMEOUT}
    vnfSetting = {"host":hostIP, "interval":SLEEP} 

    #set init value for log
    timeIntRev = 0
    timeIcnGet = 0
    timeProc = 0
    timeIcnPub = 0

    logger.info("[main] input interest name : {}".format(funcList))
    logger.info("[main] {}".format(icnSetting))
    logger.info("[main] {}".format(vnfSetting))

    kafkaBroker = kafka.kafkaConnect(BROKER)

    if (funcList[0] == "ccn:"):

        logger.info("[main] ccn (cefore) mode")

        with cefpyco.create_handle() as handle:

            while True:
                if funcList[2] != "":
                    reqName = [funcList[0], funcList[1] + "/" + funcList[2]]
                    intName = funcList[0] + "/" + funcList[1] + "/" + funcList[2]
                else:
                    reqName = [funcList[0], funcList[1]]
                    intName = funcList[0] + "/" + funcList[1]

                startTime = time.time()
                rxData = icnCefore.icnGetContentV2(handle, reqName, icnSetting)
                timeIcnGet = common.outMmSec(startTime)

                common.printExtractRawData(rxData['payload'], interest)
                common.imageWithResultWriter(rxData['payload'], interest)
                logger.info("[main] receive data size: {}".format(sys.getsizeof(str(rxData))))

                qosData = {"host": hostIP, "interest": intName, 
                           "qos":rxData["qos"], "numSeg":rxData["numSeg"],
                           "intRev": timeIntRev, "icnGet": timeIcnGet,
                           "proc": timeProc, "icnPub": timeIcnPub}

                logger.info("[main] performance {}".format(qosData))
                thread1 = threading.Thread(target=kafka.kafkaPubContent(kafkaBroker, json.dumps(qosData), TOPIC_OUT))

                time.sleep(SLEEP)


    if (funcList[0] == "kafka:"):

        logger.info("[main] kafka mode")

        if funcList[2] != "":
            TOPIC_SUB = funcList[1] + "_" + funcList[2]
        else:
            TOPIC_SUB = funcList[1]

        consumer = kafka.kafkaSubContent(BROKER, TOPIC_SUB)
        logger.info("[main] subscribe topic {}".format(TOPIC_SUB))

        startTime = time.time()

        for message in consumer:

            rxData = message.value.decode()
            common.printExtractRawData(rxData, interest)
            common.imageWithResultWriter(rxData, interest)
