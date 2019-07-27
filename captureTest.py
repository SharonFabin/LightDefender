import numpy as np
import cv2

cap = cv2.VideoCapture(0)
counter=0
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((6*7,3), np.float32)
objp[:,:2] = np.mgrid[0:7,0:6].T.reshape(-1,2)

while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()
    # img = frame
    # gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    # ret, corners = cv2.findChessboardCorners(gray, (7, 6), None)
    # if ret == True:
    #     objpoints.append(objp)
    #
    #     corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
    #     imgpoints.append(corners2)
    #
    #     # Draw and display the corners
    #     img = cv2.drawChessboardCorners(img, (7,6), corners2,ret)
    cv2.imshow("frame",frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'): # you can increase delay to 2 seconds here
        break
    if key==ord('r'):
        cv2.imwrite("sharon/img_"+str(counter)+".jpg",frame)
        counter+=1

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()