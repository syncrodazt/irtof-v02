import cv2
import os
import time
import winsound as ws

from Camera import *
from WDT import *

### Settings ###

num_cameras_vis = 0
num_cameras_tof = 1
num_cameras_ir = 2
mode = 1  # 0: continuous, 1: with sound
wait_sec = 0.5

################


def main():
    save_dir = time.strftime("cal_data/%y%m%d_%H%M%S")
    os.makedirs(save_dir, exist_ok=True)
    cameras_vis = []
    cameras_tof = []
    cameras_ir = []

    # for c in range(num_cameras_vis):
    #     camera_vis = Vis_Camera(id=c+1)
    #     cameras_vis.append(camera_vis)

    for c in range(num_cameras_tof):
        camera_tof = Tof_Camera(id=c+1)
        cameras_tof.append(camera_tof)

    for c in range(num_cameras_ir):
        camera_ir = IR_Camera(id=c+1)
        cameras_ir.append(camera_ir)
    print("hey1")
    try:
        with cameras_tof[0].tof_device.start_stream(1):
            # cameras_tof[0].prepare_tof()
            sfp = SleepForPeriodic(0.1)
            count = 0
            print("hey2")

            sfp.start()
            while True:
                base_time = time.time()
                print("hey3")
                while True:
                    print(mode)
                    # buffer_3d = cameras_tof[0].generate_buffer()
                    # sfp.sleep()
                    # cv2.imshow("", tof_frame)
                    key = cv2.waitKey(1)
                    if key == ord("q"):
                        break

                    if mode == 0:
                        if key == ord("s"):
                            break
                    elif mode == 1:
                        if time.time() - base_time > wait_sec:
                            break

                print("hey4")

                if key == ord("q"):
                    break

                # Save images to files
                for c in range(num_cameras_tof):
                    path = os.path.join(
                        save_dir, f"tof{c+1}_{str(count).zfill(4)}")
                    cameras_tof[c].shoot_save(path)
                    print("hey51")
                    # cameras_tof[c].save_image(
                    #     buffer_3d, f"tof{c+1}_{str(count).zfill(4)}.jpg")
                    print("hey52")

                for c in range(num_cameras_ir):
                    ir_frame = cameras_ir[c].shoot_ir()
                    # Capture twice to avoid problems (I don't know why, but it's related to synchronization)
                    ir_frame = cameras_ir[c].shoot_ir()
                    path = os.path.join(
                        save_dir, f"ir{c+1}_{str(count).zfill(4)}.tif")
                    cv2.imwrite(path, ir_frame)

                count += 1
                print(count)
                if mode == 1:
                    ws.Beep(880, 500)

                sfp.sleep()

    finally:
        print("hey6")
        for c in range(num_cameras_tof):
            cameras_tof[c].dispose()

        for c in range(num_cameras_ir):
            cameras_ir[c].dispose()


if __name__ == '__main__':
    print('\nWARNING:\nTHIS EXAMPLE MIGHT CHANGE THE DEVICE(S) SETTINGS!')
    print('THIS EXAMPLE IS DESIGNED FOR HELIOUS 3D CAMERAS WITH LATEST '
          'FIRMWARE ONLY!')
    print('\nExample started\n')
    main()
    print('\nExample finished successfully')
