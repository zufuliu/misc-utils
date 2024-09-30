import winreg
import ctypes

indent = ' '*4
indent2 = indent*2

def DecodePNPID(value):
	result = []
	start = ord('A') - 1
	for i in range(3):
		bit = value & 0x1f
		value >>= 5
		result.append(chr(start + bit))
	return ''.join(reversed(result))

def GetEstablishedTiming(value, timing):
	result = []
	for index, item in enumerate(timing):
		index = 1 << (7 - index)
		if value & index:
			result.append(item)
	return ', '.join(result)

def GetEstablishedTiming3(values):
	timingIII = [
		# byte 6
		'640 x 350 @ 85 Hz',
		'640 x 400 @ 85 Hz',
		'720 x 400 @ 85 Hz',
		'640 x 480 @ 85 Hz',
		'848 x 480 @ 60 Hz',
		'800 x 600 @ 85 Hz',
		'1024 x 768 @ 85 Hz',
		'1152 x 864 @ 75 Hz',
		# byte 7
		'1280 x 768 @ 60 Hz (RB)',
		'1280 x 768 @ 60 Hz',
		'1280 x 768 @ 75 Hz',
		'1280 x 768 @ 85 Hz',
		'1280 x 960 @ 60 Hz',
		'1280 x 960 @ 85 Hz',
		'1280 x 1024 @ 60 Hz',
		'1280 x 1024 @ 85 Hz',
		# byte 8
		'1360 x 768 @ 60 Hz',
		'1440 x 900 @ 60 Hz (RB)',
		'1440 x 900 @ 60 Hz',
		'1440 x 900 @ 75 Hz',
		'1440 x 900 @ 85 Hz',
		'1400 x 1050 @ 60 Hz (RB)',
		'1400 x 1050 @ 60 Hz',
		'1400 x 1050 @ 75 Hz',
		# byte 9
		'1400 x 1050 @ 85 Hz',
		'1680 x 1050 @ 60 Hz (RB)',
		'1680 x 1050 @ 60 Hz',
		'1680 x 1050 @ 75 Hz',
		'1680 x 1050 @ 85 Hz',
		'1600 x 1200 @ 60 Hz',
		'1600 x 1200 @ 65 Hz',
		'1600 x 1200 @ 70 Hz',
		# byte 10
		'1600 x 1200 @ 75 Hz',
		'1600 x 1200 @ 85 Hz',
		'1792 x 1344 @ 60 Hz',
		'1792 x 1344 @ 75 Hz',
		'1856 x 1392 @ 60 Hz',
		'1856 x 1392 @ 75 Hz',
		'1920 x 1200 @ 60 Hz (RB)',
		'1920 x 1200 @ 60 Hz',
		# byte 11
		'1920 x 1200 @ 75 Hz',
		'1920 x 1200 @ 85 Hz',
		'1920 x 1440 @ 60 Hz',
		'1920 x 1440 @ 75 Hz',
	]

	result = []
	for index, item in enumerate(timingIII):
		value = values[index >> 3]
		index = 1 << (7 - (index & 7))
		if value & index:
			result.append(item)
	return ', '.join(result)

def DecodeStandardTiming(aspectList, horizontal, aspect):
	rate = (aspect & 63) + 60
	aspect = aspect >> 6
	aspect = aspectList[aspect]
	horizontal = (horizontal + 31)*8
	vertical = int(horizontal*aspect)
	return horizontal, vertical, rate

def DumpEDID(edid):
	if len(edid) < 128 or edid[0:8] != b'\x00\xFF\xFF\xFF\xFF\xFF\xFF\x00':
		print(f'{indent}invalid EDID')
		return
	if sum(edid[0:128]) & 0xFF != 0x00:
		print(f'{indent}invalid Checksum')

	# Vendor & Product ID
	value = (edid[8] << 8) | edid[9]
	pnpid = DecodePNPID(value)
	# https://uefi.org/PNP_ID_List
	print(f'{indent}Manufacturer PNP ID: {pnpid} (0x{value:04X})')
	value = edid[0x0A] | (edid[0x0B] << 8)
	print(f'{indent}Product Code: {value} (0x{value:04X})')
	value = edid[0x0C] | (edid[0x0D] << 8) | (edid[0x0E] << 16) | (edid[0x0F] << 24)
	print(f'{indent}Serial Number: {value} (0x{value:08X})')
	# Week and Year of Manufacture or Model Year
	week = edid[0x10]
	year = edid[0x11] + 1990
	if week == 0xFF:
		print(f'{indent}Model Year: {year}')
	else:
		print(f'{indent}Year of Manufacture: {year}, Week of Manufacture: {week}')
	version = edid[0x12], edid[0x13]
	print(f'{indent}EDID Structure Version: {version[0]}.{version[1]}')

	# Basic Display Parameters and Features
	definition = edid[0x14]
	feature = edid[0x18]
	if definition & 128:
		print(f'{indent}Video Input Definition: Digital (0x{definition:02X})')
		value = (definition >> 4) & 0b111
		if value:
			print(f'{indent}Color Bit Depth: {(value + 2)*2}')
		else:
			print(f'{indent}Color Bit Depth: Undefined')
		value = definition & 0b1111
		if value < 6:
			typeList = ['Undefined', 'DVI', 'HDMI-a', 'HTMI-b', 'MDDI', 'DisplayPort']
			print(f'{indent}Digital Video Interface: {typeList[value]}')
		value = (feature >> 3) & 0b11
		typeList = ['RGB 4:4:4', 'RGB 4:4:4 & YCrCb 4:4:4', 'RGB 4:4:4 & YCrCb 4:2:2', 'RGB 4:4:4 & YCrCb 4:4:4 & YCrCb 4:2:2']
		print(f'{indent}Supported Color Encoding Format: {typeList[value]}')
	else:
		print(f'{indent}Video Input Definition: Analog (0x{definition:02X})')
		value = (definition >> 5) & 0b11
		typeList = ['0.700 : 0.300 : 1.000 V p-p', '0.714 : 0.286 : 1.000 V p-p', '1.000 : 0.400 : 1.400 V p-p', '0.700 : 0.000 : 0.700 V p-p']
		print(f'{indent}Signal Level Standard: {typeList[value]}')
		print(f'{indent}Video Setup: Blank-to-Black: {bool(definition & 16)}')
		print(f'{indent}Separate Sync H & V Signals: {bool(definition & 8)}')
		print(f'{indent}Composite Sync Signal on Horizontal: {bool(definition & 4)}')
		print(f'{indent}Composite Sync Signal on Green Video: {bool(definition & 2)}')
		print(f'{indent}Serration on the Vertical Sync: {bool(definition & 1)}')
		typeList = ['Monochrome', 'RGB', 'Non-RGB', 'Undefined']
		value = (feature >> 3) & 0b11
		print(f'{indent}Display Color Type: {typeList[value]}')
	# Horizontal and Vertical Screen Size or Aspect Ratio
	horizontal = edid[0x15]
	vertical = edid[0x16]
	if horizontal and vertical:
		print(f'{indent}Screen Size: {horizontal}cm x {vertical}cm')
	elif horizontal:
		print(f'{indent}Landscape Aspect Ratio: {(horizontal + 99)/100}')
	elif vertical:
		print(f'{indent}Portrait Aspect Ratio: {(vertical + 99)/100}')
	# Display Transfer Characteristics
	gamma = edid[0x17]
	if gamma != 0xFF:
		print(f'{indent}Gamma: {(gamma + 100)/100}')
	# Feature Support
	print(f'{indent}Standby Mode: {bool(feature & 128)}')
	print(f'{indent}Suspend Mode: {bool(feature & 64)}')
	print(f'{indent}Very Low Power: {bool(feature & 32)}')
	print(f'{indent}sRGB Standard is the default color space: {bool(feature & 4)}')
	print(f'{indent}Preferred Timing Mode includes the native pixel format: {bool(feature & 2)}')
	print(f'{indent}Display is continuous frequency: {bool(feature & 1)}')

	# Display x, y Chromaticity Coordinates
	print(f'{indent}Chromaticity Coordinates:')
	value = edid[0x19]
	x = (edid[0x1B] << 2) | (value >> 6)
	y = (edid[0x1C] << 2) | ((value >> 4) & 0b11)
	print(f'{indent2}Red: {x/1024:.3f}, {y/1024:.3f}')
	x = (edid[0x1D] << 2) | ((value >> 2) & 0b11)
	y = (edid[0x1E] << 2) | (value & 0b11)
	print(f'{indent2}Green: {x/1024:.3f}, {y/1024:.3f}')
	value = edid[0x1A]
	x = (edid[0x1F] << 2) | (value >> 6)
	y = (edid[0x20] << 2) | ((value >> 4) & 0b11)
	print(f'{indent2}Blue: {x/1024:.3f}, {y/1024:.3f}')
	x = (edid[0x21] << 2) | ((value >> 2) & 0b11)
	y = (edid[0x22] << 2) | (value & 0b11)
	print(f'{indent2}Default White Point: {x/1024:.3f}, {y/1024:.3f}')

	# Established Timings I & II
	timingI = [
		'720 x 400 @ 70Hz',
		'720 x 400 @ 88Hz',
		'640 x 480 @ 60Hz',
		'640 x 480 @ 67Hz',
		'640 x 480 @ 72Hz',
		'640 x 480 @ 75Hz',
		'800 x 600 @ 56Hz',
		'800 x 600 @ 60Hz',
	]
	timingII = [
		'800 x 600 @ 72Hz',
		'800 x 600 @ 75Hz',
		'832 x 624 @ 75Hz',
		'1024 x 768 @ 87Hz (I)',
		'1024 x 768 @ 60Hz',
		'1024 x 768 @ 70Hz',
		'1024 x 768 @ 75Hz',
		'1280 x 1024 @ 75Hz',
	]
	timingManufacturer = [
		'1152 x 870 @ 75Hz',
	]

	value = edid[0x23]
	print(f'{indent}Established Timing I: {GetEstablishedTiming(value, timingI)}')
	value = edid[0x24]
	print(f'{indent}Established Timing II: {GetEstablishedTiming(value, timingII)}')
	value = edid[0x25]
	print(f"{indent}Manufacturer's Timings: {GetEstablishedTiming(value, timingManufacturer)}")

	# Standard Timings
	offset = 0x26
	aspectList = [10/16, 3/4, 4/5, 9/16]
	if version < (1, 3):
		aspectList[0] = 1
	for timing in range(8):
		horizontal, rate = edid[offset], edid[offset + 1]
		offset += 2
		if horizontal == 1 and rate == 1:
			continue
		horizontal, vertical, rate = DecodeStandardTiming(aspectList, horizontal, rate)
		print(f'{indent}Standard Timing {timing + 1}: {horizontal} x {vertical} @ {rate} Hz')

	for block in range(4):
		clock = edid[offset] | (edid[offset + 1])
		if clock != 0:
			name = 'Detailed Timing Descriptor' if block else 'Preferred Timing Mode'
			print(f'{indent}{name}:')
			print(f'{indent2}Pixel Clock: {clock/100} MHz')
			value = edid[offset + 4]
			video = edid[offset + 2] | ((value & 0xF0) << 4)
			blank = edid[offset + 3] | ((value & 0x0F) << 8)
			print(f'{indent2}Horizontal Addressable Video: {video} pixels')
			print(f'{indent2}Horizontal Blanking: {blank} pixels')
			value = edid[offset + 7]
			video = edid[offset + 5] | ((value & 0xF0) << 4)
			blank = edid[offset + 6] | ((value & 0x0F) << 8)
			print(f'{indent2}Vertical Addressable Video: {video} lines')
			print(f'{indent2}Vertical Blanking: {blank} lines')
			value = edid[offset + 11]
			front = edid[offset + 8] | ((value & 0b1100_0000) << 2)
			pulse = edid[offset + 9] | ((value & 0b0011_0000) << 4)
			print(f'{indent2}Horizontal Front Porch: {front} pixels')
			print(f'{indent2}Horizontal Sync Pulse Width: {pulse} pixels')
			front = edid[offset + 10]
			pulse = (front & 0x0F) | ((value & 0b0011) << 4)
			front = (front >> 4) | ((value & 0b1100) << 2)
			print(f'{indent2}Vertical Front Porch: {front} lines')
			print(f'{indent2}Vertical Sync Pulse Width: {pulse} lines')
			value = edid[offset + 14]
			video = edid[offset + 12] | ((value & 0xF0) << 4)
			blank = edid[offset + 13] | ((value & 0x0F) << 8)
			print(f'{indent2}Horizontal Addressable Video Image Size: {video}mm')
			print(f'{indent2}Vertical Addressable Video Image Size: {blank}mm')
			print(f'{indent2}Right Horizontal Border: {edid[offset + 15]} pixels')
			print(f'{indent2}Top Vertical Border: {edid[offset + 16]} lines')
			value = edid[offset + 17]
			print(f'{indent2}Signal Interface Type Interlaced: {bool(value & 128)}')
			typeList = [
				'Normal Display – No Stereo',
				'Normal Display – No Stereo',
				'Field sequential stereo, right image when stereo sync signal = 1',
				'Field sequential stereo, left image when stereo sync signal = 1',
				'2-way interleaved stereo, right image on even lines',
				'2-way interleaved stereo, left image on even lines',
				'4-way interleaved stereo',
				'Side-by-Side interleaved stereo',
			]
			index = ((value >> 4) & 0b0110) | (value & 1)
			print(f'{indent2}Stereo Viewing Support: {typeList[index]}')
			if value & 16:
				if value & 8:
					print(f'{indent2}Digital Composite Sync With Serrations: {bool(value & 4)}')
				else:
					print(f'{indent2}Digital Vertical Sync is Positive: {bool(value & 4)}')
				print(f'{indent2}Horizontal Sync is Positive: {bool(value & 2)}')
			else:
				print(f'{indent2}Bipolar Analog Composite Sync: {bool(value & 8)}')
				print(f'{indent2}Analog Sync With Serrations: {bool(value & 4)}')
				print(f'{indent2}Analog Sync On RGB: {bool(value & 2)}')
		else:
			tag = edid[offset + 3]
			if tag == 0xFF:
				text = edid[offset + 5:offset + 17].decode('utf-8').strip()
				print(f'{indent}Display Product Serial Number: {text}')
			elif tag == 0xFE:
				text = edid[offset + 5:offset + 17].decode('utf-8').strip()
				print(f'{indent}Alphanumeric Data String: {text}')
			elif tag == 0xFD:
				print(f'{indent}Display Range Limits & Timing Descriptor:')
				flag = edid[offset + 4]
				vertical = flag & 0b11
				horizontal = (flag >> 2) & 0b11
				print(f'{indent2}Vertical Rate Offset: {vertical}')
				print(f'{indent2}Horizontal Rate Offset: {horizontal}')
				value = edid[offset + 5]
				if vertical == 0b11:
					value += 256
				print(f'{indent2}Minimum Vertical Rate: {value}')
				value = edid[offset + 6]
				if vertical & 0b10:
					value += 256
				print(f'{indent2}Maximum Vertical Rate: {value}')
				value = edid[offset + 7]
				if horizontal == 0b11:
					value += 256
				print(f'{indent2}Minimum Horizontal Rate: {value}')
				value = edid[offset + 8]
				if horizontal & 0b10:
					value += 256
				print(f'{indent2}Maximum Horizontal Rate: {value}')
				value = edid[offset + 9]*10
				print(f'{indent2}Maximum Pixel Clock: {value} MHz')
				flag = edid[offset + 10]
				result = 'None'
				if flag == 0 and feature & 1:
					result = 'Default GTF'
				elif flag == 1:
					result = 'Range Limits Only'
				elif result == 2:
					result = 'Secondary GTF'
				elif flag == 4 and feature & 1:
					result = 'CVT'
				print(f'{indent2}Video Timing Support Flag: 0x{flag:02X} {result}')
			elif tag == 0xFC:
				text = edid[offset + 5:offset + 17].decode('utf-8').strip()
				print(f'{indent}Display Product Name: {text}')
			elif tag == 0xFB:
				print(f'{indent}Color Point Descriptor:')
			elif tag == 0xFA:
				index = offset + 5
				for timing in range(6):
					horizontal, rate = edid[index], edid[index + 1]
					index += 2
					if horizontal == 1 and rate == 1:
						continue
					horizontal, vertical, rate = DecodeStandardTiming(aspectList, horizontal, rate)
					print(f'{indent}Standard Timing {timing + 9}: {horizontal} x {vertical} @ {rate} Hz')
			elif tag == 0xF9:
				print(f'{indent}Color Management Data Descriptor:')
			elif tag == 0xF8:
				index = offset + 6
				for descriptor in range(4):
					print(f'{indent}CVT 3 Byte Code Descriptor {descriptor + 1}:')
					value = edid[index + 1]
					vertical = edid[index] | ((value & 0xF0) << 4)
					aspect = (value >> 2) & 0b11
					aspect = [4/3, 16/9, 16/10, 15/9][aspect]
					vertical = (vertical + 1)*2
					horizontal = int(vertical*aspect)
					print(f'{indent2}Addressable Horizontal Pixel: {horizontal}')
					print(f'{indent2}Addressable Vertical Line: {vertical}')
					value = edid[index + 2]
					rate = [50, 60, 75, 85][(value >> 5) & 0b11]
					print(f'{indent2}Preferred Vertical Rate: {rate} Hz')
					rateList = ['50 Hz', '60 Hz', '75 Hz', '85 Hz', '60 Hz (RB)']
					result = []
					for bit, item in enumerate(rateList):
						bit = 1 << (5 - bit)
						if value & bit:
							result.append(item)
					rate = ', '.join(result)
					print(f'{indent2}Supported Vertical Rate: {rate}')
					index += 3
			elif tag == 0xF7:
				values = edid[offset+6:offset+11]
				print(f'{indent}Established Timings III: {GetEstablishedTiming3(values)}')
			elif tag == 0x10:
				print(f'{indent}Dummy Descriptor:')
			elif tag <= 0x0F:
				print(f'{indent}Manufacturer Specified Data:')
			else:
				print(f'{indent}Display Descriptor {tag:02X}:')
		offset += 18

	flag = edid[0x7E]
	print(f'{indent}Extension Flag: {flag:02X} {len(edid)}\n')

def DumpAllEDID():
	parent = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Enum\DISPLAY", access=winreg.KEY_READ)
	maxSub = winreg.QueryInfoKey(parent)[0]
	for sub in range(maxSub):
		try:
			subName = winreg.EnumKey(parent, sub)
			subKey = winreg.OpenKeyEx(parent, subName, access=winreg.KEY_READ)
			try:
				path = winreg.EnumKey(subKey, 0)
				key = winreg.OpenKeyEx(subKey, rf'{path}\Device Parameters', access=winreg.KEY_READ)
				value = winreg.QueryValueEx(key, "EDID")
				if value:
					print(rf'{subName}\{path} EDID:')
					DumpEDID(value[0])
				winreg.CloseKey(key)
			except OSError:
				pass
			winreg.CloseKey(subKey)
		except OSError:
			pass
	winreg.CloseKey(parent)

# https://learn.microsoft.com/en-us/windows/win32/monitor/monitor-configuration
from ctypes.wintypes import BOOL, DWORD, CHAR, WCHAR, WPARAM, LPARAM, HANDLE, HMONITOR, HDC, LPRECT
PHYSICAL_MONITOR_DESCRIPTION_SIZE = 128
class PHYSICAL_MONITOR(ctypes.Structure):
	_fields_ = [
		('hPhysicalMonitor', HANDLE),
		('szPhysicalMonitorDescription', WCHAR * PHYSICAL_MONITOR_DESCRIPTION_SIZE)
	]
LPPHYSICAL_MONITOR = ctypes.POINTER(PHYSICAL_MONITOR)
dxva2 = ctypes.windll.dxva2

def DumpMCCS(mccs):
	pass

def DumpMonitorInfo(hPhysicalMonitor):
	dwCapabilitiesStringLengthInCharacters = DWORD()
	result = dxva2.GetCapabilitiesStringLength(hPhysicalMonitor, ctypes.byref(dwCapabilitiesStringLengthInCharacters))
	if result and dwCapabilitiesStringLengthInCharacters.value:
		ASCIICapabilitiesString = CHAR*dwCapabilitiesStringLengthInCharacters.value
		pszASCIICapabilitiesString = ASCIICapabilitiesString()
		result = dxva2.CapabilitiesRequestAndCapabilitiesReply(hPhysicalMonitor, pszASCIICapabilitiesString, dwCapabilitiesStringLengthInCharacters.value)
		print(f'{indent2}Capabilities String: {pszASCIICapabilitiesString.value.decode('utf-8')}')
		DumpMCCS(pszASCIICapabilitiesString.value)
	dwMonitorCapabilities = DWORD()
	dwSupportedColorTemperatures = DWORD()
	if dxva2.GetMonitorCapabilities(hPhysicalMonitor, ctypes.byref(dwMonitorCapabilities), ctypes.byref(dwSupportedColorTemperatures)):
		print(f'{indent2}Monitor Capabilities: 0x{dwMonitorCapabilities.value:08X}')
		print(f'{indent2}Supported Color Temperatures: 0x{dwSupportedColorTemperatures.value:08X}')
	dtyDisplayTechnologyType = DWORD()
	if dxva2.GetMonitorTechnologyType(hPhysicalMonitor, ctypes.byref(dtyDisplayTechnologyType)):
		print(f'{indent2}Display Technology Type: {dtyDisplayTechnologyType.value}')

@ctypes.WINFUNCTYPE(BOOL, HMONITOR, HDC, LPRECT, LPARAM)
def MonitorEnumProc(hMonitor, hdc, rect, lParam):
	print('monitor:', hMonitor)
	dwNumberOfPhysicalMonitors = DWORD()
	if dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR(hMonitor, ctypes.byref(dwNumberOfPhysicalMonitors)):
		PhysicalMonitorArray = PHYSICAL_MONITOR*dwNumberOfPhysicalMonitors.value
		physicalMonitorList = PhysicalMonitorArray()
		if dxva2.GetPhysicalMonitorsFromHMONITOR(hMonitor, dwNumberOfPhysicalMonitors.value, physicalMonitorList):
			for physicalMonitor in physicalMonitorList:
				print(f'{indent}{physicalMonitor.hPhysicalMonitor}: {physicalMonitor.szPhysicalMonitorDescription}')
				DumpMonitorInfo(physicalMonitor.hPhysicalMonitor)
		dxva2.DestroyPhysicalMonitors(dwNumberOfPhysicalMonitors.value, physicalMonitorList)
	return 1

def EnumAllMonitor():
	ctypes.windll.user32.EnumDisplayMonitors(None, None, MonitorEnumProc, 0)

DumpAllEDID()
EnumAllMonitor()
