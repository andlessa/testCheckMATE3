#!/usr/bin/env python3

"""Simple code for running CheckMATE over a set of SLHA files."""

#Uses an input file to loop over input files and run CheckMATE over them.
#The calculation goes through the following steps
# 1) Generate input steering cards for CheckMATE
# 2) Run CheckMATE for each card
# 3) Move results to output folder

#First tell the system where to find the modules:
import sys,os,glob,shutil
from configParserWrapper import ConfigParserExt
import logging,shutil
import subprocess
import time,datetime
import multiprocessing
import tempfile
import pyslha

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s at %(asctime)s'
logging.basicConfig(format=FORMAT,datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)


def getCheckMateCard(parser):
    """
    Create a process card using the user defined input.

    :param parser: ConfigParser object with all the parameters needed

    :return: The path to the process card
    """
    cardFile = tempfile.mkstemp(suffix='.dat', prefix='checkmateCard_',
                                   dir=os.getcwd())
    os.close(cardFile[0])
    cardFile = os.path.abspath(cardFile[1])

    cardF = open(cardFile,'w')
    cardF.write("[Parameters]\n")
    pars = parser.toDict(raw=False)["CheckMateParameters"]
    for key,val in pars.items():
        cardF.write("%s: %s\n" %(key,val))

    #Get tags of processes:
    processTags = [tag for tag in parser.sections()
                    if (tag.lower() != 'options' and  tag.lower() != 'checkmateparameters')]

    for pTag in processTags:
        process = parser.toDict(raw=False)[pTag]
        if not 'Name' in process:
            logger.error("The field 'Name' must be defined in %s" %pTag)
            return False
        cardF.write("\n[%s]\n" %process['Name'])
        for key,val in process.items():
            if key == 'Name': continue
            cardF.write("%s: %s\n" %(key,val))
    cardF.close()

    return cardFile

def RunCheckMate(parserDict):
    """
    Run CheckMATE using the parameters given in parser.

    :param parser: ConfigParser object with all the parameters needed.
    """
    t0 = time.time()
    parser = ConfigParserExt()
    parser.read_dict(parserDict)

    pars = parser.toDict(raw=False)["options"]

    outputFolder = os.path.abspath(parser.get("CheckMateParameters","OutputDirectory"))
    resultFolder = os.path.join(outputFolder,parser.get("CheckMateParameters","Name"))
    if os.path.isdir(resultFolder):
        logger.info("Results folder %s found." %resultFolder)
        if parser.get("CheckMateParameters","OutputExists") == 'overwrite':
            logger.info("Overwriting")
            shutil.rmtree(resultFolder)
        else:
            logger.info("Skipping" %resultFolder)
            return "---- %s skipped" %resultFolder
    cardFile = getCheckMateCard(parser)
    logger.debug('Steering card %s created' %cardFile)

    #Create output dirs, if do not exist:
    try:
        os.makedirs(outputFolder)
    except:
        pass

    #Run CheckMate
    checkmatePath = os.path.abspath(pars['checkmateFolder'])
    checkmateBin = os.path.join(checkmatePath,'bin')
    logger.info('Running checkmate with steering card: %s ' %cardFile)
    logger.debug('Running: python2 ./CheckMATE %s at %s' %(cardFile,checkmateBin))
    run = subprocess.Popen('python2 ./CheckMATE %s' %(cardFile)
                       ,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=checkmateBin)
    output,errorMsg= run.communicate()
    logger.debug('CheckMATE error:\n %s \n' %errorMsg)
    logger.debug('CheckMATE output:\n %s \n' %output)

    os.remove(cardFile)

    logger.info("Done in %3.2f min" %((time.time()-t0)/60.))

    #Remove parton level events:
    if pars['cleanUp'] is True:
        mg5folder = os.path.join(resultFolder,'mg5amcatnlo')
        if os.path.isdir(mg5folder):
            logger.debug('Removing data from: %s \n' %mg5folder)
            for f in os.listdir(mg5folder):
                file_path = os.path.join(mg5folder, f)
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
        analysisfolder = os.path.join(resultFolder,'analysis')
        if os.path.isfile(os.path.join(analysisfolder,'analysisstdout_atlas_1712_02118_ew.log')):
            os.remove(os.path.join(analysisfolder,'analysisstdout_atlas_1712_02118_ew.log'))

    now = datetime.datetime.now()

    return "Finished running CheckMATE at %s" %(now.strftime("%Y-%m-%d %H:%M"))


def main(parfile,verbose):
    """
    Submit parallel jobs using the parameter file.

    :param parfile: name of the parameter file.
    :param verbose: level of debugging messages.
    """
    level = args.verbose.lower()
    levels = { "debug": logging.DEBUG, "info": logging.INFO,
               "warn": logging.WARNING,
               "warning": logging.WARNING, "error": logging.ERROR }
    if not level in levels:
        logger.error ( "Unknown log level ``%s'' supplied!" % level )
        sys.exit()
    logger.setLevel(level = levels[level])

    parser = ConfigParserExt()
    ret = parser.read(parfile)
    if ret == []:
        logger.error( "No such file or directory: '%s'" % parfile)
        sys.exit()

    if not parser.has_option('options', 'input'):
        logger.error("An input file or folder must be defined.")
        sys.exit()
    else:
        inputF = parser.get('options','input')
        if os.path.isfile(inputF):
            inputFiles = [os.path.abspath(inputF)]
        elif "*" in inputF:
            inputFiles = [os.path.abspath(f) for f in glob.glob(inputF)]
        elif os.path.isdir(inputF):
            inputFiles = [os.path.abspath(os.path.join(inputF,f))
                          for f in os.listdir(inputF)
                          if os.path.isfile(os.path.join(inputF, f))]
        else:
            logger.error("Input format %s not accepted" %inputF)
            sys.exit()

    parserList = []
    for f in inputFiles:
        newParser = ConfigParserExt()
        newParser.read_dict(parser.toDict(raw=True))
        newParser.set("CheckMateParameters","SLHAFile",f)
        newParser.set("CheckMateParameters","Name",
                       os.path.splitext(os.path.basename(f))[0])
        newParser.set("CheckMateParameters","OutputDirectory",
                       os.path.abspath(parser.get("CheckMateParameters","OutputDirectory")))
        #Get tags of processes:
        processTags = [tag for tag in newParser.sections()
                        if (tag.lower() != 'options' and  tag.lower() != 'checkmateparameters')]

        #Get xsec dictionary:
        useSLHA = False
        unit = 'PB'
        xsecDict = {}
        if newParser.has_option("options","xsecUnit"):
            unit = newParser.get("options","xsecUnit")
        if newParser.has_option("options","useSLHAxsecs"):
            useSLHA = newParser.get("options","useSLHAxsecs")
            if not isinstance(useSLHA,dict):
                logger.error("useSLHAxsecs should be defined as dictionary with a key for each CheckMate process.")
                sys.exit()

            xsecsAll = pyslha.readSLHAFile(f).xsections
            for pTag,xsecTuple in useSLHA.items():
                if not xsecTuple in xsecsAll: continue
                xsecs = xsecsAll[xsecTuple].xsecs
                xsecs = sorted(xsecs, key = lambda xsec: xsec.qcd_order,
                                reverse=True)
                xsecDict[pTag] = xsecs[0]

        for pTag in processTags:
            pName = newParser.get(pTag,"Name")
            newParser.set(pTag,"MGparam",f)
            if useSLHA:
                if pTag in xsecDict:
                    newParser.set(pTag,"XSect", "%1.5g %s" %(xsecDict[pTag].value,unit))
                if pName in xsecDict:
                    newParser.set(pTag,"XSect", "%1.5g %s" %(xsecDict[pName].value,unit))

        parserList.append(newParser)

    ncpus = int(parser.get("options","ncpu"))
    if ncpus  < 0:
        ncpus =  multiprocessing.cpu_count()
    ncpus = min(ncpus,len(parserList))
    pool = multiprocessing.Pool(processes=ncpus)
    children = []
    #Loop over parsers and submit jobs
    logger.info("Submitting %i jobs over %i cores" %(len(parserList),ncpus))
    for newParser in parserList:
        logger.debug("Submitting job for file %s"
                    %(newParser.get("CheckMateParameters","SLHAFile")))
        parserDict = newParser.toDict(raw=False) #Must convert to dictionary for pickling
        p = pool.apply_async(RunCheckMate, args=(parserDict,))
        children.append(p)
        time.sleep(10)


    #Wait for jobs to finish:
    output = [p.get() for p in children]
    for out in output:
        print(out)


if __name__ == "__main__":

    import argparse
    ap = argparse.ArgumentParser( description=
            "Run CheckMATE over a set of input files to compute efficiencies for a given model." )
    ap.add_argument('-p', '--parfile', default='checkmate_parameters.ini',
            help='path to the parameters file. Default is checkmate_parameters.ini')
    ap.add_argument('-v', '--verbose', default='error',
            help='verbose level (debug, info, warning or error). Default is error')


    t0 = time.time()

    args = ap.parse_args()

    t0 = time.time()

    args = ap.parse_args()
    output = main(args.parfile,args.verbose)

    print("\n\nDone in %3.2f min" %((time.time()-t0)/60.))
