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

import sys

from arena_api.__future__.save import Writer
from arena_api.system import system

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


def set_nodes(nodemap):
	'''
	Sets some node to get smoth resutls
	'''

	# set pixel format
	print('\tSetting pixelformat to Coord3D_ABCY16')
	nodemap.get_node('PixelFormat').value = 'Coord3D_ABCY16'
	# set operating mode distance

	print('\tSetting 3D operating mode')
	if isHelios2 is True:
		nodemap['Scan3dOperatingMode'].value = 'Distance3000mmSingleFreq'
	else:
		nodemap['Scan3dOperatingMode'].value = 'Distance1500mm'

	# set exposure time
	print('\tSetting time selector to Exp1000Us')
	nodemap['ExposureTimeSelector'].value = 'Exp1000Us'
	# set gain
	print('\tSetting conversion gain to low')
	nodemap['ConversionGain'].value = 'Low'
	# set image accumulation
	print('\tSetting accumulation to 4')
	nodemap['Scan3dImageAccumulation'].value = 4
	# Enable spatial filter
	print('\tEnable spatial filter')
	nodemap['Scan3dSpatialFilterEnable'].value = True
	# Enable confidence threshold
	print('\tEnable confidence threshold')
	nodemap['Scan3dConfidenceThresholdEnable'].value = True


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
	exposure_time_initial = nodemap['ExposureTimeSelector'].value
	conversion_gain_initial = nodemap['ConversionGain'].value
	image_accumulation_initial = nodemap['Scan3dImageAccumulation'].value
	spatial_filter_initial = nodemap['Scan3dSpatialFilterEnable'].value
	confidence_threshold_initial = nodemap['Scan3dConfidenceThresholdEnable'].value

	# Sets :
	# - pixelformat to Coord3D_ABCY16
	# - 3D operating mode to Distance1500mm
	# - time selector to Exp1000Us
	# - conversion gain to low
	# - accumulation to 4
	# - spatial filter
	# - confidence threshold to true
	print('\nSettings nodes for smooth results')
	set_nodes(nodemap)

	# Grab buffers ------------------------------------------------------------

	# Starting the stream allocates buffers and begins filling them with data.
	with device.start_stream(1):
		print(f'\nStream started with 1 buffer')
		print('\tGet a buffer')

		# This would timeout or return 1 buffers
		buffer = device.get_buffer()
		print('\tbuffer received')

		# create an image writer
		writer = Writer()

		# save function
		# buffer :
		#   buffer to save.
		# pattern :
		#   default name for the image is 'image_<count>.jpg' where count
		#   is a pre-defined tag that gets updated every time a buffer image
		#   is saved. More custom tags can be added using
		#   Writer.register_tag() function
		# kwargs (optional args) ignored if not an .ply image:
		#   - 'filter_points' default is True.
		#       Filters NaN points (A = B = C = -32,678)
		#   - 'is_signed' default is False.
		#       If pixel format is signed for example PixelFormat.Coord3D_A16s
		#       then this arg must be passed to the save function else
		#       the results would not be correct
		#   - 'scale' default is 0.25.
		#   - 'offset_a', 'offset_b' and 'offset_c' default to 0.0
		writer.save(buffer, 'my_3d_image_buffer.ply')
		print(f'\tImage saved {writer.saved_images[-1]}')

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
	nodemap['ExposureTimeSelector'].value = exposure_time_initial
	nodemap['ConversionGain'].value = conversion_gain_initial
	nodemap['Scan3dImageAccumulation'].value = image_accumulation_initial
	nodemap['Scan3dSpatialFilterEnable'].value = spatial_filter_initial
	nodemap['Scan3dConfidenceThresholdEnable'].value = confidence_threshold_initial

	# Destroy all created devices. This call is optional and will
	# automatically be called for any remaining devices when the system module
	#  is unloading.
	system.destroy_device()
	print('Destroyed all created devices')


if __name__ == '__main__':
	print('\nWARNING:\nTHIS EXAMPLE MIGHT CHANGE THE DEVICE(S) SETTINGS!')
	print('THIS EXAMPLE IS DESIGNED FOR HELIOUS 3D CAMERAS WITH LATEST FIRMWARE ONLY!')
	print('\nExample started\n')
	example_entry_point()
	print('\nExample finished successfully')
