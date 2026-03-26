import serial
import time
import cv2
import os
import bisect
import threading
from matplotlib import pyplot as plt
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import mediapipe as mp
import numpy as np
staroVreme = 0
vidiSe = False
mp_hands = mp.tasks.vision.HandLandmarksConnections
def palacFja(x):
  return 0.56*np.sin(2.02*x+1.62)+0.449
def kaziprstFja(x):
  return 0.29*np.sin(2.89*x+1.87)+0.71
def srednjakFja(x):
  return 0.33*np.sin(2.46*x+1.94)+0.67
def domaliFja(x):
  return 0.38*np.sin(3.25*x+1.89)+0.64
def maliFja(x):
  return -0.45*x**2 -0.13*x + 0.99
def citajKamera1():
  global kamera1Najnoviji
  global camera1
  trenutno = 0
  while True:
    if time.time_ns() - trenutno < 100000000 and camera1.grab():
      ret, kamera1Najnoviji = camera1.retrieve()
      trenutno = time.time_ns()
    else:
      camera1.release()
      camera1 = cv2.VideoCapture(3, cv2.CAP_V4L2)
      camera1.set(cv2.CAP_PROP_FRAME_WIDTH, 360)
      camera1.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
      camera1.set(cv2.CAP_PROP_BUFFERSIZE, 1)
      camera1.set(cv2.CAP_PROP_FPS, 15)
      trenutno = time.time_ns()
def citajKamera2():
  global kamera2Najnoviji
  global camera2
  trenutno = 0
  while True:
    if time.time_ns() - trenutno < 100000000 and camera2.grab():
      ret, kamera2Najnoviji = camera2.retrieve()
      trenutno = time.time_ns()
    else:
      camera2.release()
      camera2 = cv2.VideoCapture(4, cv2.CAP_V4L2)
      camera2.set(cv2.CAP_PROP_FRAME_WIDTH, 360)
      camera2.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
      camera2.set(cv2.CAP_PROP_BUFFERSIZE, 1)
      camera2.set(cv2.CAP_PROP_FPS, 15)
      trenutno = time.time_ns()
palacModel = palacFja(np.linspace(0, 1, 180))
kaziprstModel = kaziprstFja(np.linspace(0, 0.9859, 176))
srednjakModel = srednjakFja(np.linspace(0, 1, 180))
domaliModel = domaliFja(np.linspace(0, 0.8684, 156))
maliModel = maliFja(np.linspace(0, 1, 180))
def trijangulacijaTacke(r1, r2):
  # MATRICE KAMERA OPISUJU KAKO SE KOORDINATE SA KAMERA PRESLIKAVAJU U SPOLJNE KOORDINATE (koordinatni pocetak je u uglu kartonskog nosaca)
  kameraB = np.array([[1, 0, 0, -1], [0, 0, -1, 0], [0, 1, 0, 0]])
  kameraB = np.dot(0.5*np.array([[772.81013182, 0, 320],[0, 779.95788961, 240 ],[0,0,2]]), kameraB)
  kameraA = np.array([[0, -1, 0, 1], [0, 0, -1, 0], [1, 0, 0, 0]])
  kameraA = np.dot(0.5*np.array([[768.3329645, 0, 320],[0, 770.36287522, 240 ],[0,0,2]]), kameraA)
  A = np.array([
      (r1[1])*kameraA[2] - kameraA[1],
      kameraA[0] - (r1[0])*kameraA[2],
      (r2[1])*kameraB[2] - kameraB[1],
      kameraB[0] - (r2[0])*kameraB[2],
  ])
  U, S, Vt = np.linalg.svd(A)
  trazeni = Vt[-1]
  izlaz = trazeni[:3]/trazeni[-1]
  return izlaz
def utvrdiDuzinuOpruzenog(tT, rbr):
  out = 0
  if rbr in range(1, 5):
    out = np.linalg.norm(tT[0]-tT[1+rbr*4])+np.linalg.norm(tT[1+rbr*4]-tT[2+rbr*4])+np.linalg.norm(tT[2+rbr*4]-tT[3+rbr*4])+np.linalg.norm(tT[3+rbr*4]-tT[4+rbr*4])
  elif rbr==0:
    out = np.linalg.norm(tT[0] - tT[2])+np.linalg.norm(tT[2]-tT[3])+np.linalg.norm(tT[3]-tT[4])
  return out
def projekcija(tT, rbr):
  if rbr in range(1, 5):
    P = tT[1+4*rbr]-tT[0]
    R = tT[4+4*rbr]-tT[0]
    return (R@P)/(P@P)*P
  elif rbr==0:
    P = tT[2]-tT[0]
    R = tT[4]-tT[0]
    return (R@P)/(P@P)*P
komanda = 15*'0'+'\n'
def arduinoIzlaz():
  arduino = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.2)
  vreme = 0
  global komanda
  while True:
    arduino.write(bytes(komanda, 'ascii'))
    arduino.reset_output_buffer()
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(base_options=base_options,
                                       num_hands=2)
detector = vision.HandLandmarker.create_from_options(options)
camera1 = cv2.VideoCapture(3, cv2.CAP_V4L2)
camera2 = cv2.VideoCapture(4, cv2.CAP_V4L2)
camera1.set(cv2.CAP_PROP_FRAME_WIDTH, 360)
camera1.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
camera2.set(cv2.CAP_PROP_FRAME_WIDTH, 360)
camera2.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
camera1.set(cv2.CAP_PROP_BUFFERSIZE, 1)
camera2.set(cv2.CAP_PROP_BUFFERSIZE, 1)
camera1.set(cv2.CAP_PROP_FPS, 15)
camera2.set(cv2.CAP_PROP_FPS, 15)
camera1.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
camera2.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
nit1 = threading.Thread(target = citajKamera1, args=())
nit2 = threading.Thread(target = citajKamera2, args=())
nit3 = threading.Thread(target = arduinoIzlaz, args=())
nit1.start()
nit2.start()
nit3.start()
while True:
  if time.time_ns()-staroVreme>100000000:
    staroVreme = time.time_ns()
    try:
      uimage=kamera1Najnoviji
    except:
      continue
    try:
      uimage=cv2.cvtColor(uimage, cv2.COLOR_BGR2RGB)
      image = mp.Image(image_format=mp.ImageFormat.SRGB, data=uimage)
    except:
      continue
    try:
      detection_result = detector.detect(image)
      koordinateA = np.array([(a.x*320, a.y*240) for a in detection_result.hand_landmarks[0]])
      vidiSe = True
    except:
      vidiSe = False
      continue
    try:
      uimage=kamera2Najnoviji
    except:
      continue
    try:
      uimage=cv2.cvtColor(uimage, cv2.COLOR_BGR2RGB)
      image = mp.Image(image_format=mp.ImageFormat.SRGB, data=uimage)
    except:
      continue
    try:
      detection_result = detector.detect(image)
      koordinateB = np.array([(a.x*320, a.y*240) for a in detection_result.hand_landmarks[0]])
      vidiSe = True
    except:
      vidiSe = False
      continue
    trijangulisaneTacke = np.zeros((21,3), dtype=np.float32)
    for i in range(21):
      trijangulisaneTacke[i,0],trijangulisaneTacke[i,1],trijangulisaneTacke[i,2] = trijangulacijaTacke(koordinateA[i], koordinateB[i])
    duzinePruzenih = np.array([utvrdiDuzinuOpruzenog(trijangulisaneTacke, i) for i in range(5)])
    duzineProjekcija = np.array([np.linalg.norm(projekcija(trijangulisaneTacke, i)) for i in range(5)])
    omer = np.zeros(5, dtype=np.float32)
    omer = duzineProjekcija/duzinePruzenih
    izlazi = np.zeros(5, dtype=np.uint8)
    izlazi[0] = bisect.bisect(-palacModel, -omer[0])
    izlazi[1] = bisect.bisect(-kaziprstModel, -omer[1])
    izlazi[2] = bisect.bisect(-srednjakModel, -omer[2])
    izlazi[3] = bisect.bisect(-domaliModel, -omer[3])
    izlazi[4] = bisect.bisect(-maliModel, -omer[4])
    komanda = "".join([f"{x:03}" for x in izlazi]) + "\n"
    if vidiSe:
      os.system("clear")
      print("Pozicije: "+komanda[0:3] + "," + komanda[3:6] + "," + komanda[6:9] + "," + komanda[9:12] + "," + komanda[12:16])
    else:
      os.system("clear")
      print("PODESITE POLOZAJ SAKE!")


