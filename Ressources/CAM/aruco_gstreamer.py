import cv2 as cv
from cv2 import aruco
import numpy as np
from cv2 import Rodrigues


matrix2kcam = np.array([[9.168133252568576381e+02, 0.000000000000000000e+00, 9.480443281135388816e+02],
                        [0.000000000000000000e+00, 9.191598647069464505e+02,
                            5.675943650016769197e+02],
                        [0.000000000000000000e+00, 0.000000000000000000e+00, 1.000000000000000000e+00]])
coeff2kcam = np.array([[-2.915983541126683787e-01, 8.652846125231630769e-02,
                      1.105053375820461115e-04, 4.650280792212821836e-04, -1.175981219883001812e-02]])


camera_matrix = matrix2kcam
dist_coeffs = coeff2kcam

marker_dict = cv.aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
# param_markers = aruco.DetectorParameters_create() #sur la tour et le raspberry pi
param_markers = cv.aruco.DetectorParameters()  # sur le pc portable
detector = cv.aruco.ArucoDetector(marker_dict, param_markers)


taillemarker = 0.1  # en mètre


font = cv.FONT_HERSHEY_PLAIN


def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1620,  # 1920  3840
    capture_height=1080,  # 1080 2160
    display_width=680,  # 960 680
    display_height=460,  # 540 460
    framerate=60,  # 30 pour la 4k 60 pour la 1080p
    flip_method=0,  # 0 si la caméra est montée à l'envers 2 sinon
):
    return (
        "nvarguscamerasrc sensor-id=%d ! "
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )


# Données de départ du tag 42
mat42 = np.eye(3, 3, dtype=np.float64)
rvecs42 = np.zeros((3, 1), dtype=np.float64)
tvecs42 = np.zeros((3, 1), dtype=np.float64)

# cap = cv.VideoCapture(1)
# cap = cv.VideoCapture(pipeline, cv.CAP_GSTREAMER)
# 0 si la caméra est montée à l'envers 2 sinon
cap = cv.VideoCapture(gstreamer_pipeline(flip_method=0), cv.CAP_GSTREAMER)

while True:
    ret, frame = cap.read()
    # frame = cv.imread('table_jeu.png')
    if not ret:
        break

    # corrected_frame = cv.undistort(frame, camera_matrix, dist_coeffs)
    gray_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

    # marker_corners, marker_IDs, reject = cv.aruco.detectMarkers(gray_frame, marker_dict, parameters=param_markers)
    marker_corners, marker_IDs, reject = detector.detectMarkers(gray_frame)

    if marker_corners:
        marker_centers = []
        for ids, corners in zip(marker_IDs, marker_corners):
            # cv.polylines(corrected_frame, [corners.astype(np.int32)], True, (0, 255, 255), 4, cv.LINE_AA)
            corners = corners.reshape(4, 2)
            corners = corners.astype(int)
            topLeft, topRight, bottomRight, bottomLeft = corners

            cv.line(frame, topLeft, topRight, (0, 255, 0), 2)
            cv.line(frame, topRight, bottomRight, (0, 255, 0), 2)
            cv.line(frame, bottomRight, bottomLeft, (0, 255, 0), 2)
            cv.line(frame, bottomLeft, topLeft, (0, 255, 0), 2)

            cx = int((topLeft[0] + bottomRight[0]) / 2.0)
            cy = int((topLeft[1] + bottomRight[1]) / 2.0)
            cv.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

            marker_centers.append((cx, cy))

            if len(marker_centers) > 1:
                for i in range(len(marker_centers) - 1):
                    cv.line(
                        frame, marker_centers[i], marker_centers[i + 1], (0, 0, 255), 2)

            rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(
                marker_corners, taillemarker, camera_matrix, dist_coeffs)  # OK

            for i in range(len(marker_IDs)):
                cv.drawFrameAxes(frame, camera_matrix,
                                 dist_coeffs, rvecs[i], tvecs[i], 0.03)
                print(f"id {marker_IDs[i]}", rvecs[i], tvecs[i])
                if marker_IDs[i] == 42:
                    rvecs42 = rvecs[i]
                    tvecs42 = tvecs[i]
                    mat42, _ = cv.Rodrigues(rvecs42)
                else:
                    mat, _ = cv.Rodrigues(rvecs[i])
                    relative_position = np.dot(
                        mat42.T, (tvecs[i].T - tvecs42.T))
                    relative_rotation = np.dot(mat42.T, mat)
                    rdest, _ = cv.Rodrigues(relative_rotation)
                    # si la valeur est fausse, multiplier par 10 au lieu de 100
                    print(f"t{marker_IDs[i]}/42: {relative_position.T * 100}")
                    print(f"r{marker_IDs[i]}/42: {np.degrees(rdest)}")
                    cv.putText(
                        frame, f"d{marker_IDs[i]}/42: {relative_position.T[0,0].round(4)*100} cm", (0, 30), font, 1, (0, 255, 0), 2, cv.LINE_AA)
                    cv.putText(
                        frame, f"r{marker_IDs[i]}/42: {np.degrees(rdest[2,0]).round(3)} °", (0, 50), font, 1, (0, 255, 0), 2, cv.LINE_AA)

            cv.putText(frame, f"ID: {ids[0]}", tuple(
                topRight), font, 1, (0, 255, 0), 2, cv.LINE_AA)
            # print("centre tag 2D: ",marker_centers)

    cv.imshow("frame", frame)
    stop = cv.waitKey(1)
    if stop == ord("s"):
        break

cap.release()
cv.destroyAllWindows()
