# Instructions / Tips & Tricks for developers 
This file is added to help developers

## Preparations
* Code editor: Visual Studio Code
* Programming Language: Python
* Tool for unpacking WoT pkg-files: 7-Zip
* Tool for decompiling Python binary files: Uncompyle6 (for Python)
* Latest version of World of Tanks

## Extract Python files from latest version of WoT 
* Identify import statements in the mod file: 'mod_BRR.py'
  * ex: 'import AccountCommands'
* Go to WoT game folder and locate the file 'scripts.pkg' 
  * ex: C:\Games\World_of_Tanks_EU\res\packages
* Open the file using 7-Zip and navigate to the folder with relevant files
  * ex: \scripts\common to find file: AccountCommands.pyc
* Extract relevant file to temporary folder, or exctract all files from a spesific folder
* Decompile relevant files from the temporary folder using uncompyle6 from command line
  * ex: uncompyle6 -o .\AccountCommands.py .\AccountCommands.pyc
* Add the decompiled py-files to the same folder as the mod
