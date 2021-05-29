import cv2
import face_recognition


cap = cv2.VideoCapture(0)

if not (cap.isOpened()):
    print("Could not open video device")
    
#To set the resolution 


while(True): 
# Capture frame-by-frame

    ret, frame = cap.read()

# Display the resulting frame

    cv2.imshow("preview",frame)

#Waits for a user input to quit the application

    if cv2.waitKey(1) & 0xFF == ord("q"):
        cv2.imwrite("thushar.png", frame)
        break

cap.release()

cv2.destroyAllWindows()
