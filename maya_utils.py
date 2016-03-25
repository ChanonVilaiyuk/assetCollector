import sys, os, shutil
import subprocess
import tempfile

def getMayaSceneAssetAssembly(mayaFile, batch = True) : 
    if batch : 
        pyCommand = 'O:/studioTools/maya/python/tool/utils/mayaPyCmd/getAssetList.py'
        runMayaBatch(pyCommand, mayaFile, '2016')

        tmpFile = 'mayaPyDictTmp.txt'
        tmpdir = tempfile.gettempdir()
        tmpPath = '%s/%s' % (tmpdir, tmpFile)

        if os.path.exists(tmpPath) : 
            f = open(tmpPath, 'r')
            data = f.read()
            f.close()

            result = eval(data)
            os.remove(tmpPath)

            return result 

def copyAsset(src, dst) : 
    # dst = 'C:/Users/Ta/Documents/freelance'
    data = getMayaSceneAssetAssembly(src)

    files = data['files']
    assemblyFiles = data['assemblyFiles']

    i = 0 
    for each in files : 
        srcCopy = each
        drive = os.path.splitdrive(srcCopy)[0]
        dstCopy = srcCopy.replace(drive, dst)

        if os.path.exists(srcCopy) : 
            copy(srcCopy, dstCopy)
            print '%s/%s copy %s ' % (i, len(files), dstCopy)

        i += 1 


    i = 0 
    for each in assemblyFiles : 
        srcCopy = each[0]
        status = each[1]

        if status : 
            dstCopy = srcCopy.replace('P:', dst)

            copy(srcCopy, dstCopy)
            print '%s/%s copy %s ' % (i, len(assemblyFiles), dstCopy)

        i += 1 


def runMayaBatch(pyCommand, mayaFile, version = '') : 

    if '2012' in version : 
        MAYA_PYTHON = 'C:\\Program Files\\Autodesk\\Maya2012\\bin\\mayapy.exe'

    if '2015' in version : 
        MAYA_PYTHON = 'C:\\Program Files\\Autodesk\\Maya2015\\bin\\mayapy.exe'

    if '2016' in version : 
        MAYA_PYTHON = 'C:\\Program Files\\Autodesk\\Maya2016\\bin\\mayapy.exe'
        
    # mayaCmdFlPath = 'O:/studioTools/maya/python/tool/myStandAlone/mayapyCmd.py'
    # filePath = 'O:/studioTools/maya/python/tool/myStandAlone/maya.ma'
    subprocess.call([MAYA_PYTHON, pyCommand, mayaFile])


def copy(src, dst) : 
    if os.path.exists(src) : 
        dstDir = dst.replace(dst.split('/')[-1], '')
        if not os.path.exists(dstDir) :
            os.makedirs(dstDir)

        shutil.copy2(src, dst)
    return dst