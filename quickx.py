#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Author: lonewolf
# Date: 2013-10-26 11:23:48
# 
import sublime
import sublime_plugin
import functools
import os
import datetime
import json
import re
import subprocess
import sys
import time
import codecs
import glob
try:
    import helper
    import rebuild
    import definition
except ImportError:
    from . import helper
    from . import rebuild
    from . import definition

PROJECT_ROOT=""
TEMP_PATH="" 
# [wordsArr,showFunc,path,lineNum,type] type=0 user, 1 lua, 2 cocos2dx
DEFINITION_LIST=[]
USER_DEFINITION_LIST=[]


 
luaTemplate="""--
-- Author: ${author}
-- Date: ${date}
-- Name: ${_name}
--[===[  
    Class Name: 
    Class Application: 
    Key Value: 
    Key Function: 
]===]

local tt = tt
local ${_class} = class("${_class}", tt.BaseNode)

function ${_class}:ctor(func,height)
    ${_class}.super.ctor(self)
    self.func = func or function()  end
    local uiInfo = {
        {"layout"},
        {"nineBg"},
        {"sureBtn","onCallback"},
    }
    self.ccsLayer = self:loadCsbFile("csb/XXX/${_class}.csb",uiInfo)
    self.layout:setContentSize(cc.size(display.width, display.height))
    self:setNodeEventEnabel()
    self:onEventListener(handler(self, ${_class}.onTouch))
end

function ${_class}:onCallback(event)
    if event.target == self.sureBtn then
    
    end
end

function ${_class}:onEnter()

end

function ${_class}:onExit()

end

function ${_class}:onTouch(event)
    local enventtype = event.name
    if enventtype == "began" then
        return true
    elseif enventtype == "ended" then
        local x,y     =   event:getLocation().x, event:getLocation().y
        local touchPt = self.ccsLayer:convertToNodeSpace(cc.p(x, y))
        local rect    = self["nineBg"]:getBoundingBox()
        if cc.rectContainsPoint(rect ,touchPt) == false  then
            self:deleteMe(false)
        end
    end
end

function ${_class}:deleteMe(ft)
    if self.func and type(self.func) == "function"  then
        self.func(ft)
    end
end

return ${_class}

"""

# init plugin,load definitions
def init():
    global TEMP_PATH
    TEMP_PATH=sublime.packages_path()+"/User/quick-comminuty-dev.cache"
    global DEFINITION_LIST
    DEFINITION_LIST=json.loads(definition.data)
    global USER_DEFINITION_LIST
    path=os.path.join(TEMP_PATH,"user_definition.json")
    if os.path.exists(path):
        USER_DEFINITION_LIST=json.loads(helper.readFile(path))

def checkQuickxRoot():
    # quick_cocos2dx_root
    # settings = helper.loadSettings("quick-comminuty-dev")
    # quick_cocos2dx_root = settings.get("quick_cocos2dx_root", "")
    quick_cocos2dx_root=PROJECT_ROOT
    if len(quick_cocos2dx_root)==0:
        sublime.error_message("quick_cocos2dx_root no set, please run with player")
        return False
    return quick_cocos2dx_root

# def checkCocos2dxRoot():
#     # cocos2dx_root
#     settings = helper.loadSettings("quick-comminuty-dev")
#     cocos2dx_root = settings.get("cocos2dx_root", "")
#     if len(cocos2dx_root)==0:
#         sublime.error_message("cocos2dx_root no set")
#         return False
#     return cocos2dx_root

def checkPlayerPath(workdir):
    playerPath=""
    if sublime.platform()=="osx":
        playerPath=workdir+"/runtime/mac/*.app"
    elif sublime.platform()=="windows":
        playerPath=workdir+"/simulator/win32/*.exe"

    for filename in glob.glob(playerPath):
        playerPath=filename
        break

    if playerPath=="" or not os.path.exists(playerPath):
        if sublime.platform()=="osx":
            playerPath="/Applications/Cocos/Library/Simulator.app"

    if playerPath=="" or not os.path.exists(playerPath):
        sublime.error_message("player no exists")
        return False

    if sublime.platform()=="osx":
        playerName=playerPath.split("/")[-1]
        playerName=playerName.split(".")[0]
        playerPath=playerPath+"/Contents/MacOS/"+playerName

    return playerPath

process=None
def runWithPlayer(srcDir):
    global process
    global PROJECT_ROOT
    arr=os.path.split(srcDir)
    workdir=arr[0]
    PROJECT_ROOT=workdir+"/frameworks/cocos2d-x"
    # root
    quick_cocos2dx_root = checkQuickxRoot()
    if not quick_cocos2dx_root:
        return
    # player path for platform
    playerPath=checkPlayerPath(workdir)
    if not playerPath:
        return

    # if sublime.platform()=="osx":
    #     playerPath=arr[0]+"/runtime/mac/test3D-desktop.app/Contents/MacOS/test3D-desktop"
    # elif sublime.platform()=="windows":
    #     playerPath=arr[0]+"/simulator/win32/test.exe"

    # if playerPath=="" or not os.path.exists(playerPath):
    #     sublime.error_message("player no exists")
    #     return

    args=[playerPath]
    # param
    srcDirName=arr[1]
    args.append("-workdir")
    args.append(workdir)
    args.append("-file")
    args.append(srcDirName+"/main.lua")
    configPath=srcDir+"/config.lua"
    if os.path.exists(configPath):
        f=codecs.open(configPath,"r","utf-8")
        width="640"
        height="1136"
        while True:
            line=f.readline()
            if line:
                # debug
                m=re.match("^DEBUG\s*=\s*(\d+)",line)
                if m:
                    debug=m.group(1)
                    if debug=="0":
                        args.append("-disable-write-debug-log")
                        args.append("-disable-console")
                    elif debug=="1":
                        args.append("-disable-write-debug-log")
                        args.append("-console")                            
                    else:
                        args.append("-write-debug-log")
                        args.append("-console")
                # resolution
                m=re.match("^CONFIG_SCREEN_WIDTH\s*=\s*(\d+)",line)
                if m:
                    width=m.group(1)
                m=re.match("^CONFIG_SCREEN_HEIGHT\s*=\s*(\d+)",line)
                if m:
                    height=m.group(1)
            else:
                break
        code="return "+ datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        configPath2=srcDir+"/BuildVersion.lua"
        helper.writeFile(configPath2, code)
        f.close()
        args.append("-size")
        args.append(width+"x"+height)
        args.append("-scale")
        args.append("0.5")
    if process:
        try:
            process.terminate()
        except Exception:
            pass
    if sublime.platform()=="osx":
        process=subprocess.Popen(args)
    elif sublime.platform()=="windows":
        process=subprocess.Popen(args)
    

class LuaNewFileCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.run_command("hide_panel")
        title = "untitle"
        on_done = functools.partial(self.on_done, dirs[0])
        v = self.window.show_input_panel(
            "File Name:", title + ".lua", on_done, None, None)
        v.sel().clear()
        v.sel().add(sublime.Region(0, len(title)))

    def on_done(self, path, name):
        filePath = os.path.join(path, name)
        if os.path.exists(filePath):
            sublime.error_message("Unable to create file, file exists.")
        else:
            code = luaTemplate
            # add attribute
            settings = helper.loadSettings("quick-comminuty-dev")
            format = settings.get("date_format", "%Y-%m-%d %H:%M:%S")
            date = datetime.datetime.now().strftime(format)
            code = code.replace("${date}", date)
            author=settings.get("author", "Your Name")
            code = code.replace("${author}", author)
            
            _name=settings.get("_name", name)
            code = code.replace("${_name}", _name)

            _myclass = _name.split('.')[0]
            code = code.replace("${_class}", _myclass)

            # save
            helper.writeFile(filePath, code)
            v=sublime.active_window().open_file(filePath)
            # cursor
            v.run_command("insert_snippet",{"contents":code})
            sublime.status_message("Lua file create success!")

    def is_enabled(self, dirs):
        return len(dirs) == 1


class QuickxRunWithPlayerCommand(sublime_plugin.WindowCommand):
    def __init__(self,window):
        super(QuickxRunWithPlayerCommand,self).__init__(window)

    def run(self, dirs):
        runWithPlayer(dirs[0])

    def is_enabled(self, dirs):
        if len(dirs)!=1:
            return False
        mainLuaPath=dirs[0]+"/main.lua"
        if not os.path.exists(mainLuaPath):
            return False
        return True

    def is_visible(self, dirs):
        return self.is_enabled(dirs)


class QuickxRunWithPlayerByFileCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # view path
        path=self.view.file_name()
        sublime.status_message(path)
        index=path.rfind("supereditor"+os.sep)
        # print(index)        
        if index!=-1:
            path=path[0:index]
        else:
            index=path.rfind("src"+os.sep)
            if index==-1:
                sublime.status_message("This file not in the 'src' folder")
                return
        path=path[0:index]+"src"
        runWithPlayer(path)
        
    def is_enabled(self):
        return helper.checkFileExt(self.view.file_name(),"lua")

    def is_visible(self):
        return self.is_enabled()


class QuickxGotoDefinitionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # select text
        sel=self.view.substr(self.view.sel()[0])
        if len(sel)==0:
            # extend to the `word` under cursor
            sel=self.view.substr(self.view.word(self.view.sel()[0]))
        # find all match file
        matchList=[]
        showList=[]
        for item in DEFINITION_LIST:
            for key in item[0]:
                if key==sel:
                    matchList.append(item)
                    showList.append(item[1])
        for item in USER_DEFINITION_LIST:
            if len(item)!=5:
                continue
            for key in item[0]:
                if key==sel:
                    matchList.append(item)
                    showList.append(item[1])
        if len(matchList)==0:
            sublime.status_message("Can not find definition '%s'"%(sel))
        elif len(matchList)==1:
            self.gotoDefinition(matchList[0])
        else:
            # multi match
            self.matchList=matchList
            on_done = functools.partial(self.on_done)
            self.view.window().show_quick_panel(showList,on_done)
        
    def on_done(self,index):
        if index==-1:
            return
        item=self.matchList[index]
        self.gotoDefinition(item)
    
    def gotoDefinition(self,item):
        definitionType=item[4]
        filepath=item[2]
        if definitionType==1:
            # lua
            quick_cocos2dx_root=checkQuickxRoot()
            if not quick_cocos2dx_root:
                return
            filepath=os.path.join(quick_cocos2dx_root,filepath)
        # elif definitionType==2:
        #     # cocos2dx
        #     cocos2dx_root=checkCocos2dxRoot()
        #     if not cocos2dx_root:
        #         return
        #     filepath=os.path.join(cocos2dx_root,filepath)
        if os.path.exists(filepath):
            self.view.window().open_file(filepath+":"+str(item[3]),sublime.ENCODED_POSITION)
        else:
            sublime.status_message("%s not exists"%(filepath))

    def is_enabled(self):
        return helper.checkFileExt(self.view.file_name(),"lua")

    def is_visible(self):
        return self.is_enabled()


class QuickxRebuildUserDefinitionCommand(sublime_plugin.WindowCommand):
    def __init__(self,window):
        super(QuickxRebuildUserDefinitionCommand,self).__init__(window)
        self.lastTime=0

    def run(self, dirs):
        curTime=time.time()
        if curTime-self.lastTime<3:
            sublime.status_message("Rebuild frequently!")
            return
        self.lastTime=curTime
        global USER_DEFINITION_LIST
        USER_DEFINITION_LIST=rebuild.rebuild(dirs[0],TEMP_PATH)
        path=os.path.join(TEMP_PATH, "user_definition.json")
        data=json.dumps(USER_DEFINITION_LIST)
        if not os.path.exists(TEMP_PATH):
            os.makedirs(TEMP_PATH)
        helper.writeFile(path,data)
        sublime.status_message("Rebuild user definition complete!")
    
    def is_enabled(self, dirs):
        return len(dirs)==1

    def is_visible(self, dirs):
        return self.is_enabled(dirs)

class QuickxCreateNewProjectCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        quick_cocos2dx_root = checkQuickxRoot()
        if not quick_cocos2dx_root:
            return
        cmdPath=""
        if sublime.platform()=="osx":
            cmdPath=quick_cocos2dx_root+"/quick/bin/create_project.sh"
        elif sublime.platform()=="windows":
            cmdPath=quick_cocos2dx_root+"/quick/bin/create_project.bat"
        if cmdPath=="" or not os.path.exists(cmdPath):
            sublime.error_message("command no exists")
            return
        self.cmdPath=cmdPath
        self.path=dirs[0]
        self.window.run_command("hide_panel")
        packageName="com.mygames.game01"
        on_done = functools.partial(self.on_done, self.path)
        v = self.window.show_input_panel(
            "Package Name:", packageName, on_done, None, None)
        v.sel().clear()
        v.sel().add(sublime.Region(0, len(packageName)))

    def on_done(self, path, packageName):
        if packageName=="":
            sublime.error_message("PackageName must not empty!")
            return
        dotIndex=packageName.rfind(".")
        if dotIndex==-1:
            sublime.error_message("PackageName must two levels,i.e. 'com.game01'.")
            return
        dirName=packageName[dotIndex+1:]
        for item in os.listdir(path):
            if item==dirName:
                sublime.error_message("Folder '%s' already exists."%(dirName))
                return
        self.packageName=packageName
        on_done = functools.partial(self.on_done2)
        v = self.window.show_input_panel(
            "Screen Orientation:(portrait or landscape)", "p", on_done, None, None)
        v.sel().clear()
        v.sel().add(sublime.Region(0, 1))

    def on_done2(self, orientation):
        if orientation=="l" or orientation=="landscape":
            orientation="landscape"
        else:
            orientation="portrait"
        args=[self.cmdPath,"-p",self.packageName,"-r",orientation]
        path=self.path
        if sublime.platform()=="osx":
            subprocess.Popen(args,cwd=path)
        elif sublime.platform()=="windows":
            child=subprocess.Popen(args,cwd=path)
            child.wait()
            self.window.run_command("refresh_folder_list")
    
    def is_enabled(self, dirs):
        return len(dirs)==1

    def is_visible(self, dirs):
        return self.is_enabled(dirs)

class QuickxCompileScriptsCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):        
        quick_cocos2dx_root = checkQuickxRoot()
        if not quick_cocos2dx_root:
            return
        cmdPath=""
        if sublime.platform()=="osx":
            cmdPath=quick_cocos2dx_root+"/quick/bin/compile_scripts.sh"
        elif sublime.platform()=="windows":
            cmdPath=quick_cocos2dx_root+"/quick/bin/compile_scripts.bat"
        if cmdPath=="" or not os.path.exists(cmdPath):
            sublime.error_message("compile_scripts no exists")
            return
        settings = helper.loadSettings("quick-comminuty-dev")
        self.cmdPath=cmdPath
        self.compile_scripts_key=settings.get("compile_scripts_key", "")
        self.window.run_command("hide_panel")
        output="res/game.zip"
        on_done = functools.partial(self.on_done, dirs[0])
        v = self.window.show_input_panel("Output File:", output, on_done, None, None)
        v.sel().clear()
        v.sel().add(sublime.Region(4, 8))

    def on_done(self, path, output):
        if output=="":
            sublime.error_message("Output File must not empty!")
            return
        arr=os.path.split(path)
        path=arr[0]
        src=arr[1]
        args=[self.cmdPath,"-i",src,"-o",output]
        if self.compile_scripts_key!="":
            args.append("-e")
            args.append("xxtea_zip")
            args.append("-ek")
            args.append(self.compile_scripts_key)
        if sublime.platform()=="osx":
            subprocess.Popen(args,cwd=path,env={"luajit":"/usr/local/bin/luajit"})
        elif sublime.platform()=="windows":
            child=subprocess.Popen(args,cwd=path)
            child.wait()
            self.window.run_command("refresh_folder_list")
    
    def is_enabled(self, dirs):
        return len(dirs)==1

    def is_visible(self, dirs):
        return self.is_enabled(dirs)

# build file definition when save file
class QuickxListener(sublime_plugin.EventListener):
    def __init__(self):
        self.lastTime=0

    def on_post_save(self, view):
        filename=view.file_name()
        if not filename:
            return
        if not helper.checkFileExt(filename,"lua"):
            return
        # rebuild user definition
        curTime=time.time()
        if curTime-self.lastTime<2:
            return
        self.lastTime=curTime
        a=rebuild.rebuildSingle(filename,TEMP_PATH)
        arr=a[0]
        path=a[1] 
        # remove prev
        global USER_DEFINITION_LIST
        for i in range(len(USER_DEFINITION_LIST)-1,0,-1):
            item=USER_DEFINITION_LIST[i]
            if item[2]==path:
                USER_DEFINITION_LIST.remove(item)
        USER_DEFINITION_LIST.extend(arr)
        path=os.path.join(TEMP_PATH, "user_definition.json")
        data=json.dumps(USER_DEFINITION_LIST)
        if not os.path.exists(TEMP_PATH):
            os.makedirs(TEMP_PATH)
        helper.writeFile(path,data)
        sublime.status_message("Current file definition rebuild complete!")

# st3
def plugin_loaded():
    sublime.set_timeout(init, 200)

# st2
if not helper.isST3():
    init()

