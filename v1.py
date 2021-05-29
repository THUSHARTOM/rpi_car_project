# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import serial

import adafruit_fingerprint
import face_recognition
import cv2
import numpy as np
import RPi.GPIO as GPIO
import time

##################
import smtplib
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from bs4 import BeautifulSoup as bs

email = "raspberryproject2021@gmail.com"
password = "raspberry@123"
# the sender's email
FROM = "raspberryproject2021@gmail.com"
# the receiver's email
TO   = "raspberryproject2021@gmail.com"
# the subject of the email (subject)
subject = "Unauthorised person detected"

# initialize the message we wanna send
msg = MIMEMultipart("alternative")
# set the sender's email
msg["From"] = FROM
# set the receiver's email
msg["To"] = TO
# set the subject
msg["Subject"] = subject


# set the body of the email as HTML
html = """
An unauthorised person tried to access your vehicle.
<b>Image</b>!
"""
# make the text version of the HTML
text = bs(html, "html.parser").text

text_part = MIMEText(text, "plain")
html_part = MIMEText(html, "html")
# attach the email body to the mail message
# attach the plain text version first
msg.attach(text_part)
msg.attach(html_part)


def send_mail(email, password, FROM, TO, msg):
    # initialize the SMTP server
    server = smtplib.SMTP("smtp.gmail.com", 587)
    # connect to the SMTP server as TLS mode (secure) and send EHLO
    server.starttls()
    # login to the account using the credentials
    server.login(email, password)
    # send the email
    server.sendmail(FROM, TO, msg.as_string())
    # terminate the SMTP session
    server.quit()


###########################

ledPin = 11     # GPIO 17
 
delay = 1   # 1s
GPIO.setmode(GPIO.BOARD)
GPIO.setup(ledPin, GPIO.OUT)    # initialize GPIO pin as OUTPUT pin
GPIO.output(ledPin, GPIO.LOW)


# Get a reference to webcam #0 (the default one)
video_capture = cv2.VideoCapture(0)

# Load a sample picture and learn how to recognize it.
obama_image = face_recognition.load_image_file("person1.png")
obama_face_encoding = face_recognition.face_encodings(obama_image)[0]

# Create arrays of known face encodings and their names
known_face_encodings = [
    obama_face_encoding
]

known_face_names = [
    "person1"
]

face_locations = []
face_encodings = []
face_names = []
process_this_frame = True

# import board
# uart = busio.UART(board.TX, board.RX, baudrate=57600)

# If using with a computer such as Linux/RaspberryPi, Mac, Windows with USB/serial converter:
uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)

# If using with Linux/Raspberry Pi and hardware UART:
# uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)

# If using with Linux/Raspberry Pi 3 with pi3-disable-bt
# uart = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

##################################################


def get_fingerprint():
    """Get a finger print image, template it, and see if it matches!"""
    print("Waiting for image...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    print("Templating...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    print("Searching...")
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True



# pylint: disable=too-many-statements
def enroll_finger(location):
    """Take a 2 finger images and template it, then store in 'location'"""
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Place finger on sensor...", end="", flush=True)
        else:
            print("Place same finger again...", end="", flush=True)

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Image taken")
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="", flush=True)
            elif i == adafruit_fingerprint.IMAGEFAIL:
                print("Imaging error")
                return False
            else:
                print("Other error")
                return False

        print("Templating...", end="", flush=True)
        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            print("Templated")
        else:
            if i == adafruit_fingerprint.IMAGEMESS:
                print("Image too messy")
            elif i == adafruit_fingerprint.FEATUREFAIL:
                print("Could not identify features")
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                print("Image invalid")
            else:
                print("Other error")
            return False

        if fingerimg == 1:
            print("Remove finger")
            time.sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    print("Creating model...", end="", flush=True)
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        print("Created")
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            print("Prints did not match")
        else:
            print("Other error")
        return False

    print("Storing model #%d..." % location, end="", flush=True)
    i = finger.store_model(location)
    if i == adafruit_fingerprint.OK:
        print("Stored")
    else:
        if i == adafruit_fingerprint.BADLOCATION:
            print("Bad storage location")
        elif i == adafruit_fingerprint.FLASHERR:
            print("Flash storage error")
        else:
            print("Other error")
        return False

    return True


def save_fingerprint_image(filename):
    """Scan fingerprint then save image to filename."""
    while finger.get_image():
        pass

    # let PIL take care of the image headers and file structure
    from PIL import Image  # pylint: disable=import-outside-toplevel

    img = Image.new("L", (256, 288), "white")
    pixeldata = img.load()
    mask = 0b00001111
    result = finger.get_fpdata(sensorbuffer="image")

    # this block "unpacks" the data received from the fingerprint
    #   module then copies the image data to the image placeholder "img"
    #   pixel by pixel.  please refer to section 4.2.1 of the manual for
    #   more details.  thanks to Bastian Raschke and Danylo Esterman.
    # pylint: disable=invalid-name
    x = 0
    # pylint: disable=invalid-name
    y = 0
    # pylint: disable=consider-using-enumerate
    for i in range(len(result)):
        pixeldata[x, y] = (int(result[i]) >> 4) * 17
        x += 1
        pixeldata[x, y] = (int(result[i]) & mask) * 17
        if x == 255:
            x = 0
            y += 1
        else:
            x += 1

    if not img.save(filename):
        return True
    return False


##################################################


def get_num(max_number):
    """Use input() to get a valid number from 0 to the maximum size
    of the library. Retry till success!"""
    i = -1
    while (i > max_number - 1) or (i < 0):
        try:
            i = int(input("Enter ID # from 0-{}: ".format(max_number - 1)))
        except ValueError:
            pass
    return i


while True:
    print("----------------")
    if finger.read_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to read templates")
    print("Fingerprint templates: ", finger.templates)
    if finger.count_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to read templates")
    print("Number of templates found: ", finger.template_count)
    if finger.read_sysparam() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to get system parameters")
    print("Size of template library: ", finger.library_size)
    print("e) enroll print")
    print("f) find print")
    print("d) delete print")
    print("s) save fingerprint image")
    print("r) reset library")
    print("q) quit")
    print("----------------")
    c = input("> ")

    if c == "e":
        enroll_finger(get_num(finger.library_size))
    if c == "f":
        if get_fingerprint():
            print(finger.finger_id)
            if finger.finger_id == 2:
                print("person1 detected with confidence", finger.confidence)
                GPIO.output(ledPin, GPIO.HIGH)  # output 3.3 V from GPIO pin
                time.sleep(delay)   # delay for 1s
                GPIO.output(ledPin , GPIO.LOW)
                ### Starting Face recognition
                frame_num =10
                person_detected_flag = 0
                while frame_num>=0:
                    # Grab a single frame of video
                    ret, frame = video_capture.read()
                    time.sleep(1)
                    # Resize frame of video to 1/4 size for faster face recognition processing
                    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

                    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
                    rgb_small_frame = small_frame[:, :, ::-1]

                    # Only process every other frame of video to save time
                    if process_this_frame:
                        # Find all the faces and face encodings in the current frame of video
                        face_locations = face_recognition.face_locations(rgb_small_frame)
                        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                        face_names = []
                        for face_encoding in face_encodings:
                            # See if the face is a match for the known face(s)
                            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                            name = "Unknown"

                            # # If a match was found in known_face_encodings, just use the first one.
                            # if True in matches:
                            #     first_match_index = matches.index(True)
                            #     name = known_face_names[first_match_index]

                            # Or instead, use the known face with the smallest distance to the new face
                            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                            best_match_index = np.argmin(face_distances)
                            if matches[best_match_index]:
                                name = known_face_names[best_match_index]
                                if name == "person1":
                                    print("Face recognised")
                                    person_detected_flag =1
                                    GPIO.output(ledPin, GPIO.HIGH)
                                    break
                            face_names.append(name)

                    process_this_frame = not process_this_frame



                    # Hit 'q' on the keyboard to quit!
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    frame_num = frame_num - 1
                    
                if person_detected_flag == 0:
                    # Intruder detected
                    cv2.imwrite("intruder.png", frame)
                    
                    files_to_send = [
                            "intruder.png",
                        ]

                    for file in files_to_send:
                        # open the file as read in bytes
                        with open(file, "rb") as f:
                            # read the file content
                            data = f.read()
                            # create the attachment
                            attach_part = MIMEBase("application", "octet-stream")
                            attach_part.set_payload(data)
                        # encode the data to base 64
                        encoders.encode_base64(attach_part)
                        # add the header
                        attach_part.add_header("Content-Disposition", f"attachment; filename= {file}")
                        msg.attach(attach_part)
                        
                    send_mail(email, password, FROM, TO, msg)

                        
                # Release handle to the webcam
                video_capture.release()
                cv2.destroyAllWindows()

            else:
                print("Detected #", finger.finger_id, "with confidence", finger.confidence)
        else:
            ret, frame = video_capture.read()
            cv2.imwrite("intruder.png", frame)
            
            
            files_to_send = [
                    "intruder.png",
                ]

            for file in files_to_send:
                # open the file as read in bytes
                with open(file, "rb") as f:
                    # read the file content
                    data = f.read()
                    # create the attachment
                    attach_part = MIMEBase("application", "octet-stream")
                    attach_part.set_payload(data)
                # encode the data to base 64
                encoders.encode_base64(attach_part)
                # add the header
                attach_part.add_header("Content-Disposition", f"attachment; filename= {file}")
                msg.attach(attach_part)
                
            send_mail(email, password, FROM, TO, msg)
            
            video_capture.release()
            cv2.destroyAllWindows()
            
            print("Finger not found")
            
    if c == "d":
        if finger.delete_model(get_num(finger.library_size)) == adafruit_fingerprint.OK:
            print("Deleted!")
        else:
            print("Failed to delete")
    if c == "s":
        if save_fingerprint_image("fingerprint.png"):
            print("Fingerprint image saved")
        else:
            print("Failed to save fingerprint image")
    if c == "r":
        if finger.empty_library() == adafruit_fingerprint.OK:
            print("Library empty!")
        else:
            print("Failed to empty library")
    if c == "q":
        print("Exiting fingerprint example program")
        raise SystemExit

