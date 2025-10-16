import cv2

print("Searching for available camera indices...")

for i in range(6):
    cap = cv2.VideoCapture(i)
    if cap.read()[0]:
        print(f"Camera found at index {i}")
        cap.release()
    else:
        print(f"No camera found at index {i}")