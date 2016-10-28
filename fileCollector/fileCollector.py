# -*- coding:utf-8 -*-
"""
###################
#
# Nuke文件打包插件
#
# 所有文件中所用的素材都会被拷贝到输出路径下的Sources中，打包出来的文件中的素材路径会被修改成当前文件夹的相对路径
#
# 注意:素材路径和输出路径有中文和空格会无法打包 素材路径格式需要使用%d格式 不能使用#格式
#
###################
"""

# 导入精确除法
from __future__ import division

import nuke
import nukescripts
import os
import shutil

import sys
import fileinput

reload(sys)
sys.setdefaultencoding("utf-8")


def collectFilesPanel():
    cp = nuke.Panel("项目打包      by jgcy", 450)
    cp.addSingleLineInput("输出文件名:", nuke.Root().name().split("/")[-1][:-3])
    # addSingleLineInput() 添加文本输入框

    dirTemp = list(os.path.split(nuke.root()['name'].getValue()))[0] + "/"
    cp.addFilenameSearch("输出路径:", dirTemp)

    cp.addEnumerationPulldown("输出节点方式:", "所有节点 仅打包所选节点")
    cp.addButton("取消")
    cp.addButton("打包")

    result = cp.show()

    if result == 1:
        outDir = cp.value("输出路径:") + "/"
        inScriptName = cp.value("输出文件名:")
        allOrSel = cp.value("输出节点方式:")

        if allOrSel == "所有节点":
            doNodes = nuke.allNodes('Read')

            nuke.selectAll()
            newPath = outDir + inScriptName + ".nk"

            # 判断输出路径是否存在
            if os.path.exists(outDir):
                nuke.nodeCopy(newPath)

            else:
                os.mkdir(outDir)
                nuke.nodeCopy(newPath)

            fmat = nuke.root().format()

            # 设置项目尺寸与时间帧到新文件中
            f = open(newPath, "a")
            f.write("\n")
            f.write("Root {\n")
            f.write("first_frame {0} \n".format(nuke.root()["first_frame"].getValue()))
            f.write("last_frame {0} \n".format(nuke.root()["last_frame"].getValue()))
            f.write("fps {0} \n".format(nuke.root()["fps"].getValue()))
            f.write(
                'format "{0} {1} {2} {3}"\n'.format(fmat.width(), fmat.height(), int(fmat.pixelAspect()), fmat.name()))
            f.write("}\n")
            f.close()

            nukescripts.clear_selection_recursive()

            return inScriptName, outDir, doNodes



        else:
            if nuke.selectedNodes() == []:
                nuke.message("请选择要输出的节点")

            doNodes = nuke.selectedNodes('Read')
            newPath = outDir + inScriptName + ".nk"

            # 判断输出路径是否存在
            if os.path.exists(outDir):

                nuke.nodeCopy(newPath)

            else:
                os.mkdir(outDir)
                nuke.nodeCopy(newPath)

            fmat = nuke.root().format()

            # 设置项目尺寸与时间帧到新文件中
            f = open(newPath, "a")
            f.write("\n")
            f.write("Root {\n")
            f.write("first_frame {0} \n".format(nuke.root()["first_frame"].getValue()))
            f.write("last_frame {0} \n".format(nuke.root()["last_frame"].getValue()))
            f.write("fps {0} \n".format(nuke.root()["fps"].getValue()))
            f.write(
                'format "{0} {1} {2} {3}"\n'.format(fmat.width(), fmat.height(), int(fmat.pixelAspect()), fmat.name()))
            f.write("}\n")
            f.close()

            return inScriptName, outDir, doNodes


def collectFiles(inScriptName, outDir, doNodes):
    os.chdir(outDir)
    if os.path.exists("Sources") is False:
        os.mkdir("Sources")

    NewScriptName = outDir + inScriptName + ".nk"

    # 进度对话框
    progTask = nuke.ProgressTask("Collecting...")

    for n in doNodes:
        fullPath = n['file'].getValue()
        splitPath = fullPath.split("/")
        # mediaPath 获取read节点上素材的文件夹
        mediaPath = splitPath[-2]
        # daMedia 获取read节点上素材的名称
        daMedia = splitPath[-1]
        # fExt 获取素材拓展名
        fExt = daMedia.split(".")[-1]

        # print mediaPath,daMedia,fExt

        # 获取序列文件夹路径
        seqFolder = fullPath[:fullPath.find(daMedia)]

        # 判断read节点是序列帧还是单帧图片
        # find()方法如果着不到字符串会返回-1
        if not daMedia.find("%") == -1:

            # 获取序列范围
            padd = int(daMedia[daMedia.find("%") + 2:daMedia.find("%") + 3])

            # 获取起始帧和结束帧
            startFrame = int(n["first"].getValue())
            endFrame = int(n["last"].getValue())
            # 获取序列名称
            seqName = daMedia.split(".")[0]
            seqNameDot = daMedia[:daMedia.find("%")]
            seqLen = daMedia.split(".")[-2]
            os.chdir(outDir + "Sources")
            if not os.path.exists(seqName):
                os.mkdir(seqName)

            os.chdir(seqName)
            for f in range(startFrame, endFrame + 1):

                if progTask.isCancelled():
                    nuke.message("素材将不能全部导出")
                    break

                # 进度条显示设置
                percent = int((f / endFrame) * 100)

                progTask.setProgress(percent)

                # zfill(宽度)设置字符串宽度 不够的用0补齐
                curFile = seqFolder + seqNameDot + str(f).zfill(padd) + "." + fExt
                copyFile = seqNameDot + str(f).zfill(padd) + "." + fExt
                shutil.copyfile(curFile, copyFile)

                progTask.setMessage("Copying:" + seqNameDot + str(f).zfill(padd) + "." + fExt)

            for i, line in enumerate(fileinput.input(NewScriptName, inplace=1)):
                sys.stdout.write(line.replace(fullPath,
                                              '\"\\[file dirname \\[value root.name]]/' + 'Sources/' + seqName + '/' + seqNameDot + seqLen + "." + fExt + '\"'))


        else:
            os.chdir(outDir + "Sources")
            shutil.copyfile(fullPath, daMedia)
            for i, line in enumerate(fileinput.input(NewScriptName, inplace=1)):
                sys.stdout.write(
                    line.replace(fullPath, '\"\\[file dirname \\[value root.name]]/' + 'Sources/' + daMedia + '\"'))


def mainFunc():
    collenctData = collectFilesPanel()

    if collenctData != None:
        collectFiles(collenctData[0], collenctData[1], collenctData[2])
