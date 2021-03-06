# cpu_001 Assembler
# Assemble code for CPU
# 
# CPU is described at
# 	http://land-boards.com/blwiki/index.php?title=IOP16_16-bit_I/O_CPU_Design
#
# Input File
#	File named: fileName.csv
# 	Input file is tightly constrained in CSV file
# 	Input File Header has to be -
#		['LABEL', 'OPCODE', 'REG_LABEL', 'OFFSET_ADDR', 'COMMENT']
# 
# Memory Map File (Optional)
#	File named: fileName_MMAP.csv
#	Memory map file Header has to be -
#		['IO_ADDR','DIR','MNEUMONIC']
#	IO_ADDR = 0XNN
#	DIR = R, W, or RW
#	Ex: ['0X00','R','LED_RD']
#
# Constants file (Optional)
#	File named: fileName_CONST.csv
#	Constants file Header has to be -
#		['LABEL','STRING']
#	Example
#		LABEL,STRING
#		STRING0,1234
#		STRING1,This is test string 1
#		STRING2,This is test string 2
#
# Output files
# 	inFileName_ROM.mif file - Quartus II ROM Memory Initialization File
#	inFileName.lst file - Listing file (with addresses)
#	constFileName_const.mif - Quartus II Constants Memory Initialization File
#
# Assembler opcodes
#	LRI - Load a register with an immediate value (byte)
#	SRL - Shift register left
#	SRR - Shift register right
#	RRL - Rotate register left
#	RRR - Rotate register right
#	IOW - Write a register to an I/O address
#	IOR - Read an I/O address to a register
#	ORI - OR a register with an immediate value
#	ARI - AND a register with an immediate value
#	JSR - Jump to a subroutine (single level only)
#	RTS - Return from subroutine
#	BEZ - Branch if equal to zero
#	BNZ - Branch if not equal to zero
#	JMP - Jump to an address
#
# Assembler Psuedo-opcodes
#	NOP - No operation
#	HLT - Halt (Jump to self)
#	BEQ - Branch if equal (same as BEZ)
#	BNE - Branch if not equal (Aame as BNZ)
#
# Error Messages
#	Error messages are pretty rudimentary.
#	Error messages are printed to the command window.
#	The line with the error is printed as a list of the line.
#	Missing labels are presented as a message.
# 	Only one error at a time is presented.
#

import binascii
import csv
import string
import os
import sys
from sys import version_info

from dgProgDefaultsTk import *
from dgReadCSVtoListTk import *
from dgWriteListtoCSVTk import *

from tkinter import filedialog
from tkinter import *
from tkinter import messagebox

defaultPath = ''
inFileName = ''
mmFileName = ''
constFileName = ''

memMapList = []
constantsList = []
asmList = []
labelsList = []
annotatedSource = []

verbose = True

class ControlClass:
	"""Methods to assemble IOP16 software.
	"""
	def runAssembler(self):
		"""The code that calls the other code
		"""
		global defaultPath
		global inFileName
		global asmList
		global labelsList
		global annotatedSource
		if defaultPath == '':
			self.loadDefaults()
		if not self.readAsmFile():
			return
		labelsList = self.makeLabelsList()
		program = self.makeProgram()
		# print("runAssembler: program",program)
		self.makeListFile(program)
		# print('runAssembler: Assembly File:',inFileName[inFileName.rfind("\\")+1:])
		self.outStuff()
		infoBox("Complete")
		
	def readAsmFile(self):
		""" readAsmFile
		"""
		global defaultPath
		global inFileName
		global asmList
		oldPath = defaultPath
		myCSVFileReadClass = ReadCSVtoList()	# instantiate the class
		myCSVFileReadClass.setVerboseMode(False)	# turn on verbose mode until all is working 
		myCSVFileReadClass.setUseSnifferFlag(True)
		doneReading = False
		asmList = myCSVFileReadClass.findOpenReadCSV(defaultPath,'Select ASM (CSV) File')	# read in TSV into list
		if asmList == []:
			errorDialog("runAssembler): No file selected")
			return
		defaultPath = myCSVFileReadClass.getLastPath()
		inFileName = myCSVFileReadClass.getLastPathFileName()
		if defaultPath != oldPath:
			self.storeNewPath()
		if asmList[0] != ['LABEL', 'OPCODE', 'REG_LABEL', 'OFFSET_ADDR', 'COMMENT','V3.0.0']:
			if len(asmList[0]) < 6:
				errorDialog('Header does not match expected values\nSee command window\nProbably needs the version number added to the final column header')
			elif asmList[0][5] != 'V3.0.0':
				errorDialog('Header does not match expected values\nSee command window\nCore rev s/b V3.0.0Should be ')
			else:
				errorDialog('Header does not match expected values\nSee command window')
			print('readAsmFile: header :',asmList[0])
			return False
		print("readAsmFile: Assembly Code file",mmFileName[mmFileName.rfind("\\")+1:])
		return True
		
	def readMMapFile(self):
		global defaultPath
		global memMapList
		global mmFileName
		if defaultPath == '':
			self.loadDefaults()
		oldPath = defaultPath
		myCSVFileReadClass = ReadCSVtoList()	# instantiate the class
		myCSVFileReadClass.setVerboseMode(False)	# turn on verbose mode until all is working 
		myCSVFileReadClass.setUseSnifferFlag(True)
		doneReading = False
		memMapList = myCSVFileReadClass.findOpenReadCSV(defaultPath,'Select Memory Map File (CSV) File')	# read in TSV into list
		if memMapList == []:
			errorDialog("runAssembler): No file selected")
			return
		defaultPath = myCSVFileReadClass.getLastPath()
		mmFileName = myCSVFileReadClass.getLastPathFileName()
		if defaultPath != oldPath:
			self.storeNewPath()
		if memMapList[0] != ['IO_ADDR','DIR','MNEUMONIC']:
			errorDialog('Header does not match expected values\nSee command window')
			print("readMMapFile: Label file header should be ['IO_ADDR','DIR','MNEUMONIC'], header was ",memMapList[0])
			return
		print("readMMapFile: Memory Map file",mmFileName[mmFileName.rfind("\\")+1:])
		# print("readMMapFile: memMapList",memMapList)
		return
		
	def loadDefaults(self):
		"""
		"""
		global defaultPath
		defaultParmsClass = HandleDefault()
		defaultParmsClass.initDefaults()
		defaultPath = defaultParmsClass.getKeyVal('DEFAULT_PATH')
		# print '(runAssembler): defaultPath',defaultPath
		return
	
	def storeNewPath(self):
		global defaultPath
		defaultParmsClass = HandleDefault()
		defaultParmsClass.initDefaults()
		defaultParmsClass.storeKeyValuePair('DEFAULT_PATH',defaultPath)
	
	def calcOffsetString(self,distanceInt):
		""" calcOffsetString
		"""
		dresultStr = ''
		if distanceInt < 0:
			distanceInt = (distanceInt ^ 4095) + 1
		distStr = hex(distanceInt).upper()
		if distStr[0] == '-':	# -0xffe
			if len(distStr) == 6:
				return distStr[3:]
			elif len(distStr) == 5:
				return '0' + distStr[3:]
			elif len(distStr) == 4:
				return '00' + distStr[3:]
		else:	#0x000
			if len(distStr) == 5:
				return distStr[2:]
			elif len(distStr) == 4:
				return '0' + distStr[2:]
			elif len(distStr) == 3:
				return '00' + distStr[2:]
		return distStr
	
	def getMemMapStr(self,ioAddr,ioRd,ioWr):
		""" getMemMapStr
		memMapList [
		['IO_ADDR', 'DIR', 'MNEUMONIC'], 
		['0x00', 'RW', 'USR_LED']
		"""
		global memMapList
		# print("getMemMapStr: memMapList",memMapList, '\nioAddr', ioAddr)
		# assert False,"getMemMapStr"
		if not memMapList:
			return ''
		for row in memMapList[1:]:
			if row[2] == ioAddr:
				if row[1] == 'RW':
					return row[2]
				elif ioRd and (row[1] == 'R'):
					return row[2]
				elif ioWr and (row[1] == 'W'):
					return row[2]
		print("getMemMapStr: memMapList",memMapList)
		print("getMemMapStr: Didnt find ioAddr",ioAddr)
		assert False,"Memory Map error"
		return ''
	
	def getMapAddr(self,ioAddrName,ioRd,ioWr):
		""" getMapAddr
		memMapList [
		['IO_ADDR', 'DIR', 'MNEUMONIC'], 
		['0x00', 'RW', 'USR_LED']
		"""
		global memMapList
		for row in memMapList[1:]:
			if row[2] == ioAddrName:
				if row[1] == 'RW':
					return row[0]
				elif (row[1] == 'W') and ioWr:
					return row[0]
				elif (row[1] == 'R') and ioRd:
					return row[0]
		print("getMapAddr: memMapList",memMapList)
		print("getMapAddr: ioAddr",ioAddrName,"not found in memory map")
		assert False,"Memory Map error"
	
	def makeProgram(self):
		""" makeProgram
		"""
		global constantsList
		global labelsList
		global asmList
		global verbose
		progCounter = 0
		program = []
		# print("makeProgram: constantsList",constantsList)
		for row in asmList[1:]:
			if verbose:
				print("makeProgram: row ",row)
			row[1] = row[1].upper()
			if row[1] != '':
				if row[1] == 'SLL':
					if row[3] != '0X01':
						assert False,'Only supports single shift'
					vecStr = '0x3'
					vecStr += row[2][-1]
					vecStr += "01"
					program.append(vecStr)
				elif row[1] == 'SLR':
					if row[3] != '0X01':
						assert False,'Only supports single shift'
					vecStr = '0x3'
					vecStr += row[2][-1]
					vecStr += "81"
					program.append(vecStr)
				elif row[1] == 'SAL':
					if row[3] != '0X01':
						assert False,'Only supports single shift'
					vecStr = '0x3'
					vecStr += row[2][-1]
					vecStr += "21"
					program.append(vecStr)
				elif row[1] == 'SAR':
					if row[3] != '0X01':
						assert False,'Only supports single shift'
					vecStr = '0x3'
					vecStr += row[2][-1]
					vecStr += "A1"
					program.append(vecStr)
				elif row[1] == 'RRL':
					if row[3] != '0X01':
						assert False,'Only supports single shift'
					vecStr = '0x3'
					vecStr += row[2][-1]
					vecStr += "41"
					program.append(vecStr)
				elif row[1] == 'RRR':
					if row[3] != '0X01':
						assert False,'Only supports single shift'
					vecStr = '0x3'
					vecStr += row[2][-1]
					vecStr += "C1"
					program.append(vecStr)
				elif row[1] == 'RTS':
					vecStr = '0x3008'
					program.append(vecStr) 
				elif row[1] == 'LRI':
					# print("makeProgram: LRI", row)
					vecStr = '0x4'
					vecStr += row[2][-1]
					if row[3][0:2] == '0X':
						vecStr += row[3][-2:]
						program.append(vecStr)
					else:
						constStr = self.findConstantsOffset(row[3])
						constStr = constStr[2:4]
						vecStr += constStr
						program.append(vecStr)
				elif row[1] == 'CMP':
					vecStr = '0x5'
					vecStr += row[2][-1]
					vecStr += row[3][-2:]
					program.append(vecStr)
				elif row[1] == 'IOR':
					vecStr = '0x6'
					vecStr += row[2][-1]
					if row[3][0:2] == "0X":
						vecStr += row[3][-2:]
					else:
						retAddr = self.getMapAddr(row[3],True,False)
						vecStr += retAddr[-2:]
					program.append(vecStr)
				elif row[1] == 'IOW':
					vecStr = '0x7'
					vecStr += row[2][-1]
					if row[3][0:2] == "0X":
						vecStr += row[3][-2:]
					else:
						retAddr = self.getMapAddr(row[3],False,True)
						vecStr += retAddr[-2:]
					program.append(vecStr)
				elif row[1] == 'XRI':
					vecStr = '0x8'
					vecStr += row[2][-1]
					vecStr += row[3][-2:]
					program.append(vecStr)
				elif row[1] == 'ORI':
					vecStr = '0x9'
					vecStr += row[2][-1]
					vecStr += row[3][-2:]
					program.append(vecStr)
				elif row[1] == 'NOP':	# Psuedo-Op
					vecStr = '0x9800'  # ORI Reg8,0x00	
					program.append(vecStr)
				elif row[1] == 'ARI':
					vecStr = '0xA'
					vecStr += row[2][-1]
					vecStr += row[3][-2:]
					program.append(vecStr)
				elif row[1] == 'ADI':
					vecStr = '0xB'
					vecStr += row[2][-1]
					vecStr += row[3][-2:]
					program.append(vecStr)
				elif row[1] == 'HLT':
					vecStr = '0xB'
					labelName = 'HLT_' + str(progCounter)
					distance = labelsList[labelName]
					distStr = self.calcOffsetString(distance)
					vecStr += distStr
					program.append(vecStr)
				elif row[1] == 'JSR':
					vecStr = '0xC'
					distance = labelsList[row[2]]
					distStr = self.calcOffsetString(distance)
					vecStr += distStr
					program.append(vecStr)
				elif row[1] == 'JMP':
					vecStr = '0xD'
					distance = labelsList[row[2]]
					distStr = self.calcOffsetString(distance)
					vecStr += distStr
					program.append(vecStr)
				elif row[1] == 'BEZ':
					vecStr = '0xE'
					distance = labelsList[row[2]]
					distStr = self.calcOffsetString(distance)
					vecStr += distStr
					program.append(vecStr)
				elif row[1] == 'BEQ':
					vecStr = '0xE'
					distance = labelsList[row[2]]
					distStr = self.calcOffsetString(distance)
					vecStr += distStr
					program.append(vecStr)
				elif row[1] == 'BNZ':
					vecStr = '0xF'
					distance = labelsList[row[2]]
					distStr = self.calcOffsetString(distance)
					vecStr += distStr
					program.append(vecStr)
				elif row[1] == 'BNE':
					vecStr = '0xF'
					distance = labelsList[row[2]]
					distStr = self.calcOffsetString(distance)
					vecStr += distStr
					program.append(vecStr)
				else:
					errorDialog('Bad instruction.\nSee command window') 
					print('makeProgram: bad instr', row)
					assert False,'bad instr'
				progCounter += 1
		# print('makeProgram: program',program)
		return program
	
	def findConstantsString(self,addrHexStr):
		global constantsList
		for row in constantsList:
			if row[1] == addrHexStr:
				return row[0]
		return ''
	
	def findConstantsOffset(self,constLabel):
		global constantsList
		for row in constantsList:
			if row[0] == constLabel:
				return row[1]
		return ''
	
	def makeListFile(self, program):
		"""Create the list file
		['', 'LRI', '0X01', '0x05', 'R1 POINTS TO STRING1', '']
		"""
		global asmList
		global annotatedSource
		global constantsList
		annotatedSource = []
		progOffset = 0
		for rowOffset in range(len(asmList)-1):
			# print("makeListFile: asmList[rowOffset]",asmList[rowOffset])
			annRow = []
			# Label
			annRow.append(asmList[rowOffset+1][0])
			# print('makeListFile: progOffset',progOffset)
			# Add copcode to listing
			if asmList[rowOffset+1][1] != '':
				annRow.append(program[progOffset])
				progOffset += 1
			else:
				annRow.append('')
			annRow.append(asmList[rowOffset+1][1])
			annRow.append(asmList[rowOffset+1][2])
			if (constantsList != []) and (asmList[rowOffset+1][1] == 'LRI'):
				# print("makeListFile: asmList[rowOffset]",asmList[rowOffset])
				# print("makeListFile: asmList[rowOffset+1][1]",asmList[rowOffset+1][1],asmList[rowOffset+1][3])
				foundStr = self.findConstantsString(asmList[rowOffset+1][3])
				if foundStr:
					# print("makeListFile: foundStr",foundStr)
					annRow.append(foundStr)
				else:
					annRow.append(asmList[rowOffset+1][3])
			else:
				annRow.append(asmList[rowOffset+1][3])
			annRow.append(asmList[rowOffset+1][4])
			#print(annRow)
			annotatedSource.append(annRow)	
		return
		
	def makeLabelsList(self):
		""" makeLabelsList
		"""
		global asmList
		labelsList= {}
		progCounter = 0
		for row in asmList[1:]:
			if row[0] != '':
				labelsList[row[0]] = progCounter
			if row[1] == 'HLT':
				labelName = 'HLT_' + str(progCounter)
				labelsList[labelName] = progCounter
			progCounter += 1
		#print('makeLabelsList: labelsList',labelsList)
		return labelsList
	
	def writeMIFFile(self, ):
		"""
		"""
		global inFileName
		global annotatedSource
		global mmFileName
		outFilePathName = inFileName[0:-4] + '_ROM.mif'
		print('writeMIFFile: MIF File:',outFilePathName[outFilePathName.rfind("\\")+1:])
		# for row in sourceFile:
			# print(row)
		outList = []
		outStr = '-- File: ' + outFilePathName
		outList.append(outStr)
		outList.append('-- Generated by pyAssemble_cpu_001.py')
		outList.append('-- ')
		outLen = 0
		for row in annotatedSource:
			if row[1] != '':
				outLen += 1
		outStr = 'DEPTH = '+ str(outLen) + ';'
		outList.append(outStr)
		outList.append('WIDTH = 16;')
		outList.append('ADDRESS_RADIX = DEC;')
		outList.append('DATA_RADIX = HEX;')
		outList.append('CONTENT BEGIN')
		lineCount = 0
		addrCount = 0
		outStr = ''
		# print('writeMIFFile: outList',outList)
#		assert False,'stop'
		for row in annotatedSource:
			if row[1] != '':
				if lineCount == 0:
					outStr += str(addrCount)
					outStr += ': '
				outStr += row[1][2:]
				if lineCount < 7:
					outStr += ' '
				lineCount += 1
				addrCount += 1	
				if lineCount == 8:
					lineCount = 0
					outStr += ';'
					outList.append(outStr)
					outStr = ''
		if outStr != '':
			outStr = outStr[0:-1]
			outStr += ';'
			outList.append(outStr)
		
		outList.append('END;')
		# for line in outList:
			# print(line)

		F = open(outFilePathName, 'w')
		for row in outList:
			F.writelines(row+'\n')
		F.close()

	def writeListFile(self):
		""" writeListFile
		"""
		global inFileName
		global memMapList
		global annotatedSource
		outFilePathName = inFileName[0:-4] + '.lst'
		print('writeListFile: List File:',outFilePathName[outFilePathName.rfind("\\")+1:])
		F = open(outFilePathName, 'w')
		outStr = 'ADR LABEL' + '\t\t' + 'MACH' + '\t' + 'OPC' + '\t' + 'V1[,V2]' + '\t\t\t' + '// COMMENT' + '\n'
		F.writelines(outStr)
		address = 0
		for row in annotatedSource:
			# Address column
			hexAddr = hex(address)
			hexAddr = hexAddr[2:]
			if len(hexAddr) == 1:
				hexAddr = '00' + hexAddr
			elif len(hexAddr) == 2:
				hexAddr = '0' + hexAddr
			else:
				hexAddr = hexAddr + ' '
			# Label
			label = row[0]
			if len(label) < 4:
				label += '\t'
			if len(label) < 8:
				label += '\t'
			# Machine code
			machineCode = row[1]
			# opcode
			opcode = row[2]
			if opcode == 'IOR':
				ioRd = True
				ioWr = False
			elif opcode == 'IOW':
				ioWr = True
				ioRd = False
			else:
				ioWr = False
				ioRd = False
			# register or label
			labelReg = row[3]
			if labelReg[0:2] == "0X":
				if labelReg[3] == "8":
					labelReg = "#0x00"
				elif labelReg[3] == "9":
					labelReg = "#0x01"
				elif labelReg[3] == "F":
					labelReg = "#0xFF"
				else:
					labelReg = "Reg" + labelReg[3]
			# 2nd op value
			opValue = row[4]
			if (ioRd or ioWr) and memMapList:
				strLabel = self.getMemMapStr(opValue,ioRd,ioWr)
				opValue = strLabel
				# print("writeListFile: row",row)
				# print("writeListFile: opValue",opValue)
			if opValue:
				labelPair = labelReg + ',' + opValue
			else:
				labelPair = labelReg
			if len(labelPair) < 4:
				labelPair += '\t'
			if len(labelPair) < 8:
				labelPair += '\t'
			if len(labelPair) < 12:
				labelPair += '\t'
			# if len(labelPair) < 16:
				# labelPair += '\t'
			# comment
			comment = '// ' + row[5]
			outStr = hexAddr + '\t' + label + '\t' + machineCode + '\t' + opcode + '\t' + labelPair + '\t' + comment + '\n'
			# print(outStr)
			F.writelines(outStr)
			address += 1
		F.close()
		
	def outStuff(self):
		"""
		[['LABEL', 'OPCODE', 'VAL4', 'VAL8', 'COMMENT'], ['INIT', 'NOP', '', '', ''], ['', 'LRI', '0X00', '0X01', 'LOAD START CMD'], ['', 'LRI', '0X01', '0X40', 'LOAD SLAVE ADDR<<1, WRITE'], ['', 'LRI', '0X02', '0X00', 'LOAD IDLE CMD'], ['', 'LRI', '0X03', '0X00', 'LOAD IODIRA REGISTER_OFFSET'], ['', 'LRI', '0X04', '0XFF', 'LOAD IODIRA_ALL_INS'], ['', 'IOW', '0X00', '0X00', 'ISSUE START CMD'], ['', 'IOW', '0X01', '0X00', 'ISSUE SLAVE ADDR<<1, WRITE'], ['', 'IOW', '0X02', '0X00', 'ISSUE IDLE CMD'], ['', 'IOW', '0X03', '0X00', 'ISSUE IODIRA REGISTER_OFFSET'], ['', 'IOW', '0X04', '0X00', 'ISSUE IODIRA_ALL_INS'], ['LDST000', 'IOR', '0X05', '0X00', 'READ STATUS'], ['', 'ARI', '0X05', '0X01', 'BUSY BIT'], ['', 'BNZ', '', 'LDST000', 'LOOP UNTIL NOT BUSY'], ['SELF', 'JMP', 'SELF', '', '']]
		"""
		global inFileName
		global memMapList
		global annotatedSource
		self.writeMIFFile()
		self.writeListFile()
		
	def processConstantsFile(self):
		"""The code that calls the other code
		"""
		global defaultPath
		global labelsList
		global program
		global annotatedSource
		global decConstantsList
		global constantsList
		defaultParmsClass = HandleDefault()
		defaultParmsClass.initDefaults()
		defaultPath = defaultParmsClass.getKeyVal('DEFAULT_PATH')
		# print ('processConstantsFile: defaultPath',defaultPath)
		myCSVFileReadClass = ReadCSVtoList()	# instantiate the class
		myCSVFileReadClass.setVerboseMode(False)	# turn on verbose mode until all is working 
		myCSVFileReadClass.setUseSnifferFlag(True)
		doneReading = False
		inList = myCSVFileReadClass.findOpenReadCSV(defaultPath,'Select CONSTS (CSV) File')	# read in TSV into list
		if inList == []:
			errorDialog("processConstantsFile): No file selected")
			return
		defaultPath = myCSVFileReadClass.getLastPath()
		defaultParmsClass.storeKeyValuePair('DEFAULT_PATH',defaultPath)
		if inList[0] != ['LABEL', 'STRING']:
			print('processConstantsFile: header :',inList[0])
			errorDialog('processConstantsFile: Header does not match expected values\nSee command window\nProbably needs the version number added to the final column header')
			assert False,'header does not match expected values'
		else:
			# print('processConstantsFile: header ok')
			pass
		inFileName = myCSVFileReadClass.getLastPathFileName()
		# print("processConstantsFile: constants list",inList)
		decConstantsList = self.makeAddressTableConstants(inList)
		constantsList = self.turnItAround(decConstantsList)
		# print("processConstantsFile: constantsList",constantsList)
		longOutStr = self.makeOutStrConstants(inList)
		# print("processConstantsFile: longOutStr\n",longOutStr)
		outAsciiVals = self.makeAsciiValsConstants(longOutStr)
		# print("processConstantsFile: outAsciiVals",outAsciiVals)
		contsAsciiTable = self.makeACSIITableConstants(outAsciiVals)
		# print("processConstantsFile: contsAsciiTable",contsAsciiTable)
		# print('processConstantsFile: inFileName',inFileName)
		self.outConstantsStuff(inFileName,contsAsciiTable,constantsList)
			
	def turnItAround(self,inList):
		outList = []
		for row in inList:
			outRow = []
			label = row[0]
			addr = row[1]
			addrHexStr = hex(addr)
			addrHex = addrHexStr.upper()
			if len(addrHex) == 3:
				addrHex = '0x0' + addrHex[2]
			outRow.append(label)
			outRow.append(addrHex)
			outList.append(outRow)
		return outList
	
	def makeACSIITableConstants(self,outAsciiVals):
		outValStrs = []
		for char in outAsciiVals:
			outValsLine = ''
			
			if char == [0,0]:
				outValsLine += '0'
				outValsLine += '0'
			else:
				for pair in char:
					outValsLine += chr(pair)
			outValStrs.append(outValsLine)
		return outValStrs
	
	def ascii_to_hexConstants(self,ascii_char):
		pos1 = binascii.hexlify(str(ascii_char).encode())
		hexStr = []
		hexStr.append(pos1[0])
		hexStr.append(pos1[1])
		return hexStr

	def makeAsciiValsConstants(self, longOutStr):
		outAsciiVals = []
		# print("makeAsciiValsConstants: longOutStr",longOutStr)
		for char in longOutStr:
			# print(char,end='')
			if char != '~':
				hex_str = self.ascii_to_hexConstants(char)
				outAsciiVals.append(hex_str)
				# print(hex_str)
			else:
				outAsciiVals.append([0,0])
		# print()
		return outAsciiVals
	
	def makeAddressTableConstants(self, inList):
		addressTable = []
		address = 0
		# print("makeAddressTableConstants: inList[1:]",inList[1:])
		for line in inList[1:]:
			addressTable.append([line[0],address])
			address += len(line[1]) + 1
		# print("makeAddressTableConstants: addressTable",addressTable)
		return addressTable

	def makeOutStrConstants(self, inList):
		outStr = ''
		for line in inList[1:]:
			for char in line[1]:
				outStr += char
			outStr += '~'
		return outStr

	def outConstantsMIF(self,inFileName,contsAsciiTable):
		outFilePathName = inFileName[0:-4] + '_const.mif'
		print('outConstantsMIF:',outFilePathName[outFilePathName.rfind("\\")+1:])
		# for row in sourceFile:
			# print(row)
		outList = []
		outStr = '-- File: ' + outFilePathName
		outList.append(outStr)
		outList.append('-- Generated by pyAssemble_cpu_001.py')
		outList.append('-- ')
		outLen = 0
		for row in contsAsciiTable:
			outLen += 1
		outStr = 'DEPTH = '+ str(outLen) + ';'
		outList.append(outStr)
		outList.append('WIDTH = 8;')
		outList.append('ADDRESS_RADIX = DEC;')
		outList.append('DATA_RADIX = HEX;')
		outList.append('CONTENT BEGIN')
		lineCount = 0
		addrCount = 0
		outStr = ''
		for row in contsAsciiTable:
			if lineCount == 0:
				outStr += str(addrCount)
				outStr += ': '
			outStr += row
			if lineCount < 7:
				outStr += ' '
			lineCount += 1
			if lineCount == 8:
				lineCount = 0
				outStr += ';'
				outList.append(outStr)
				outStr = ''
				addrCount += 8
		if outStr != '':
			outList.append(outStr + ';')
		outList.append('END;')
		# for line in outList:
			# print(line)
		F = open(outFilePathName, 'w')
		for row in outList:
			F.writelines(row+'\n')
		F.close()
		return
		
	def outConstantsLST(self,inFileName,addressTable):
		global constantsList
		outFilePathName = inFileName[0:-4] + '_CONSTOUT.csv'
		F = open(outFilePathName, 'w')
		address = 0
		print("addressTable",addressTable)
		outStr = 'LABEL,OFFSET\n'
		F.writelines(outStr)
		for row in addressTable:
			outStr = ''
			constantsRow = []
			label = row[0]
			addrOff = hex(row[1])
			if len(addrOff) == 3:
				addrOff = '0x0' + addrOff[2]
			print(label,addrOff)
			outStr = label + ',' + addrOff + '\n'
			constantsRow.append(label)
			constantsRow.append(addrOff)
			constantsList.append(constantsRow)
			F.writelines(outStr)
			address += 1
		F.close()
		return
	
	def outConstantsStuff(self,inFileName,contsAsciiTable,addressTable):
		"""
		[['LABEL', 'OPCODE', 'VAL4', 'VAL8', 'COMMENT'], ['INIT', 'NOP', '', '', ''], ['', 'LRI', '0X00', '0X01', 'LOAD START CMD'], ['', 'LRI', '0X01', '0X40', 'LOAD SLAVE ADDR<<1, WRITE'], ['', 'LRI', '0X02', '0X00', 'LOAD IDLE CMD'], ['', 'LRI', '0X03', '0X00', 'LOAD IODIRA REGISTER_OFFSET'], ['', 'LRI', '0X04', '0XFF', 'LOAD IODIRA_ALL_INS'], ['', 'IOW', '0X00', '0X00', 'ISSUE START CMD'], ['', 'IOW', '0X01', '0X00', 'ISSUE SLAVE ADDR<<1, WRITE'], ['', 'IOW', '0X02', '0X00', 'ISSUE IDLE CMD'], ['', 'IOW', '0X03', '0X00', 'ISSUE IODIRA REGISTER_OFFSET'], ['', 'IOW', '0X04', '0X00', 'ISSUE IODIRA_ALL_INS'], ['LDST000', 'IOR', '0X05', '0X00', 'READ STATUS'], ['', 'ARI', '0X05', '0X01', 'BUSY BIT'], ['', 'BNZ', '', 'LDST000', 'LOOP UNTIL NOT BUSY'], ['SELF', 'JMP', 'SELF', '', '']]
		"""
		self.outConstantsMIF(inFileName,contsAsciiTable)
		# self.outConstantsLST(inFileName,addressTable)
		return
	
		
class Dashboard:
	def __init__(self):
		self.win = Tk()
		self.win.geometry("320x240")
		self.win.title("pyAssemble-cpu001")

	def add_menu(self):
		self.mainmenu = Menu(self.win)
		self.win.config(menu=self.mainmenu)

		self.filemenu = Menu(self.mainmenu, tearoff=0)
		self.mainmenu.add_cascade(label="File",menu=self.filemenu)

		self.filemenu.add_command(label="Load Constants file",command=control.processConstantsFile)
		self.filemenu.add_command(label="Load Memory Map file",command=control.readMMapFile)
		self.filemenu.add_separator()
		self.filemenu.add_command(label="Run Assembler",command=control.runAssembler)
		self.filemenu.add_separator()
		self.filemenu.add_command(label="Exit",command=self.win.quit)

		self.win.mainloop()
		
if __name__ == "__main__":
	if version_info.major != 3:
		errorDialog("Requires Python 3")
	control = ControlClass()
	x = Dashboard()
	x.add_menu()
