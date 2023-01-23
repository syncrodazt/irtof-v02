# -----------------------------------------------------------------------------
# Copyright (c) 2022, Lucid Vision Labs, Inc.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# -----------------------------------------------------------------------------

import ctypes
import sys

from arena_api.enums import PixelFormat
from arena_api.system import system

'''
Helios, Min and Max Depth: Introduction
    This example demonstrates the examination of 3D data. It requires a 
	3D-capable camera. It verifies the camera, configures its nodes, and then
	snaps an image. Afterwards, it searches over the image for the pixels with
	the lowest and highest z-values (depth), and prints it out to the console.
'''

UNSIGNED_16BIT_MAX = 65535
SIGNED_16BIT_MAX = 32767

# check if Helios2 camera used for the example
isHelios2 = False


def create_devices_with_tries():
	'''
	This function waits for the user to connect a device before raising
		an exception
	'''

	tries = 0
	tries_max = 1
	sleep_time_secs = 10
	while tries < tries_max:  # Wait for device for 60 seconds
		devices = system.create_device()
		if not devices:
			print(
				f'Try {tries+1} of {tries_max}: waiting for {sleep_time_secs} '
				f'secs for a device to be connected!')
			for sec_count in range(sleep_time_secs):
				time.sleep(1)
				print(f'{sec_count + 1 } seconds passed ',
					'.' * sec_count, end='\r')
			tries += 1
		else:
			print(f'Created {len(devices)} device(s)')
			return devices
	else:
		raise Exception(f'No device found! Please connect a device and run '
						f'the example again.')


def validate_device(device):

	# validate if Scan3dCoordinateSelector node exists.
	# If not, it is (probably) not a Helios Camera running the example
	try:
		scan_3d_operating_mode_node = device. \
			nodemap['Scan3dOperatingMode'].value
	except (KeyError):
		print('Scan3dCoordinateSelector node is not found. \
			Please make sure that Helios device is used for the example.\n')
		sys.exit()

	# validate if Scan3dCoordinateOffset node exists.
	# If not, it is (probably) that Helios Camera has an old firmware
	try:
		scan_3d_coordinate_offset_node = device. \
			nodemap['Scan3dCoordinateOffset'].value
	except (KeyError):
		print('Scan3dCoordinateOffset node is not found. \
			Please update Helios firmware.\n')
		sys.exit()

	# check if Helios2 camera used for the example
	device_model_name_node = device.nodemap['DeviceModelName'].value
	if 'HLT' in device_model_name_node:
		global isHelios2
		isHelios2 = True


class PointData:
	
	'''
	store x, y, z data in mm and intensity for a given point
	'''

	def __init__(self, x, y, z, intensity):
		self.x = x
		self.y = y
		self.z = z
		self.intensity = intensity


def find_min_and_max_z_for_signed(pdata_16bit, total_number_of_channels,
								channels_per_pixel, scale_x, scale_y, scale_z):

	# min_depth z value is set to SIGNED_16BIT_MAX to guarantee closer points
	# exist as this is the largest value possible
	min_depth = PointData(x=0, y=0, z=SIGNED_16BIT_MAX, intensity=0)
	max_depth = PointData(x=0, y=0, z=0, intensity=0)

	for i in range(0, total_number_of_channels, channels_per_pixel):

		# Extract channels from point/pixel
		#   The first channel is the x coordinate,
		#   the second channel is the y coordinate,
		#   the third channel is the z coordinate, and
		#   the fourth channel is intensity.
		# We offset by 1 for each channel because pdata_16bit is 16 bit
		#  integer
		x = pdata_16bit[i]
		y = pdata_16bit[i + 1]
		z = pdata_16bit[i + 2]
		intensity = pdata_16bit[i + 3]

		x = int(x * scale_x)
		y = int(y * scale_y)
		z = int(z * scale_z)

		if 0 < z < min_depth.z:
			min_depth.x = x
			min_depth.y = y
			min_depth.z = z
			min_depth.intensity = intensity

		elif z > max_depth.z:
			max_depth.x = x
			max_depth.y = y
			max_depth.z = z
			max_depth.intensity = intensity

	return min_depth, max_depth


def find_min_and_max_z_for_unsigned(pdata_16bit, total_number_of_channels,
									channels_per_pixel, scale_x, scale_y, scale_z,
									offset_x, offset_y):
	# min_depth z value is set to SIGNED_16BIT_MAX to guarantee closer points
	# exist as this is the largest value possible
	min_depth = PointData(x=0, y=0, z=SIGNED_16BIT_MAX, intensity=0)
	max_depth = PointData(x=0, y=0, z=0, intensity=0)

	for i in range(0, total_number_of_channels, channels_per_pixel):

		# Extract channels from point/pixel
		#   The first channel is the x coordinate,
		#   the second channel is the y coordinate,
		#   the third channel is the z coordinate, and
		#   the fourth channel is intensity.
		# We offset by 1 for each channel because pdata_16bit is 16 bit
		#  integer
		x = pdata_16bit[i]
		y = pdata_16bit[i + 1]
		z = pdata_16bit[i + 2]
		intensity = pdata_16bit[i + 3]

		# if z is less than max value, as invalid values get
		# filtered to UNSIGNED_16BIT_MAX
		if z < UNSIGNED_16BIT_MAX:
			# Convert x, y and z to millimeters
			#   Using each coordinates' appropriate scales,
			#   convert x, y and z values to mm. For the x and y
			#   coordinates in an unsigned pixel format, we must then
			#   add the offset to our converted values in order to
			#   get the correct position in millimeters.
			x = int((x * scale_x) + offset_x)
			y = int((y * scale_y) + offset_y)
			z = int(z * scale_y)

			if 0 < z < min_depth.z:
				min_depth.x = x
				min_depth.y = y
				min_depth.z = z
				min_depth.intensity = intensity

			elif z > max_depth.z:
				max_depth.x = x
				max_depth.y = y
				max_depth.z = z
				max_depth.intensity = intensity

	return min_depth, max_depth


def example_entry_point():

	# Create a device
	devices = create_devices_with_tries()
	device = devices[0]
	print(f'Device used in the example:\n\t{device}')

	validate_device(device)

	# Get device stream nodemap
	tl_stream_nodemap = device.tl_stream_nodemap

	# Enable stream auto negotiate packet size
	tl_stream_nodemap['StreamAutoNegotiatePacketSize'].value = True

	# Enable stream packet resend
	tl_stream_nodemap['StreamPacketResendEnable'].value = True

	# Store nodes' initial values ---------------------------------------------
	nodemap = device.nodemap

	# get node values that will be changed in order to return their values at
	# the end of the example
	pixelFormat_initial = nodemap['PixelFormat'].value
	operating_mode_initial = nodemap['Scan3dOperatingMode'].value

	# Set nodes --------------------------------------------------------------
	# - pixelformat to Coord3D_ABCY16
	# - 3D operating mode
	print('\nSettings nodes:')
	pixel_format = PixelFormat.Coord3D_ABCY16
	print(f'\tSetting pixelformat to { pixel_format.name}')
	nodemap.get_node('PixelFormat').value = pixel_format

	print('\tSetting 3D operating mode')
	if isHelios2 is True:
		nodemap['Scan3dOperatingMode'].value = 'Distance3000mmSingleFreq'
	else:
		nodemap['Scan3dOperatingMode'].value = 'Distance1500mm'

	# Get node values ---------------------------------------------------------
	# get the coordinate scale in order to convert x, y and z values to mm as
	# well as the offset for x and y to correctly adjust values when in an
	# unsigned pixel format
	print('Get xyz coordinate scales and offsets from nodemap')
	nodemap["Scan3dCoordinateSelector"].value = "CoordinateA"
	scale_x = nodemap["Scan3dCoordinateScale"].value
	offset_x = nodemap["Scan3dCoordinateOffset"].value
	nodemap["Scan3dCoordinateSelector"].value = "CoordinateB"
	scale_y = nodemap["Scan3dCoordinateScale"].value
	offset_y = nodemap["Scan3dCoordinateOffset"].value
	nodemap["Scan3dCoordinateSelector"].value = "CoordinateC"
	scale_z = nodemap["Scan3dCoordinateScale"].value

	# Grab buffers ------------------------------------------------------------

	# Starting the stream allocates buffers and begins filling them with data.
	with device.start_stream(1):

		print(f'\nStream started with 1 buffer')
		print('\tGet a buffer')

		# This would timeout or return 1 buffers
		buffer = device.get_buffer()
		print('\tbuffer received')

		# buffer info ------------------------------------------------

		# "Coord3D_ABCY16s" and "Coord3D_ABCY16" pixelformats have 4
		# channels per pixel. Each channel is 16 bits and they represent:
		#   - x position
		#   - y postion
		#   - z postion
		#   - intensity
		channels_per_pixel = int(buffer.bits_per_pixel / 16)
		total_number_of_channels = buffer.width * buffer.height * channels_per_pixel

		# find points with min and max z values
		print('Finding points with min and max z values')

		if buffer.pixel_format == PixelFormat.Coord3D_ABCY16s:

			# Buffer.pdata is a (uint8, ctypes.c_ubyte) pointer.
			# This pixelformat has 4 channels, and each channel is 16 bits.
			# It is easier to deal with Buffer.pdata if it is casted to 16bits
			# so each channel value is read correctly.
			# The pixelformat is suffixed with "S" to indicate that the data
			# should be interpereted as signed.
			pdata_as_int16 = ctypes.cast(buffer.pdata,
										ctypes.POINTER(ctypes.c_int16))

			# offset is needed to generate the negative coordinates in the
			# unsigned integer only
			min_depth, max_depth = find_min_and_max_z_for_signed(pdata_as_int16,
																total_number_of_channels,
																channels_per_pixel,
																scale_x, scale_y, scale_z)

		elif buffer.pixel_format == PixelFormat.Coord3D_ABCY16:

			# Buffer.pdata is a (uint8, ctypes.c_ubyte) pointer.
			# This pixelformat has 4 channels, and each channel is 16 bits.
			# It is easier to deal with Buffer.pdata if it is casted to 16bits
			# so each channel value is read correctly.
			# The pixelformat is suffixed with "S" to indicate that the data
			# should be interpereted as signed. This One does not have "S" so
			# we cast it to unsigned
			pdata_as_uint16 = ctypes.cast(buffer.pdata,
										ctypes.POINTER(ctypes.c_uint16))

			# offset is needed to generate the negative coordinates in the
			# unsigned integer only
			min_depth, max_depth = find_min_and_max_z_for_unsigned(pdata_as_uint16,
																total_number_of_channels,
																channels_per_pixel,
																scale_x, scale_y, scale_z,
																offset_x, offset_y)

		else:
			raise Exception('This example requires the camera to be in either '
							f'3D image format Coord3D_ABCY16 or '
							f'Coord3D_ABCY16s')

		# display data
		print(f'\tMinimum depth point found with '
			f'z distance of {min_depth.z} mm and '
			f'intensity {min_depth.intensity} at coordinates '
			f'( {min_depth.x} mm, {min_depth.y } mm )')

		print(f'\tMaximum depth point found with '
			f'z distance of {max_depth.z} mm and '
			f'intensity {max_depth.intensity} at coordinates '
			f'( {max_depth.x} mm, {max_depth.y } mm )')

		# Requeue the chunk data buffers
		device.requeue_buffer(buffer)
		print(f'\tImage buffer requeued')

	# When the scope of the context manager ends, then 'Device.stop_stream()'
	# is called automatically
	print('Stream stopped')

	# Clean up ----------------------------------------------------------------

	# restores initial node values
	nodemap['PixelFormat'].value = pixelFormat_initial
	nodemap['Scan3dOperatingMode'].value = operating_mode_initial

	# Destroy all created devices. This call is optional and will
	# automatically be called for any remaining devices when the system module
	# is unloading.
	system.destroy_device()
	print('Destroyed all created devices')


if __name__ == '__main__':
	print('\nWARNING:\nTHIS EXAMPLE MIGHT CHANGE THE DEVICE(S) SETTINGS!')
	print('THIS EXAMPLE IS DESIGNED FOR HELIOUS 3D CAMERAS WITH LATEST FIRMWARE ONLY!')
	print('\nExample started\n')
	example_entry_point()
	print('\nExample finished successfully')
