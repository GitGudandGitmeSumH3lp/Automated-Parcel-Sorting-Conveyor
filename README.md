# Automated Parcel Sorting Conveyor

### A Raspberry Pi-powered system that uses OCR, a robotic arm, and an automated transfer switch to autonomously sort packages.

![Project GIF]([Link to your GIF here])

---

## 🚀 Project Overview

This project is a low-cost, scalable solution for automating parcel sorting, designed for small-to-medium logistics operations. The system uses **Optical Character Recognition (OCR)** to read labels on a conveyor belt and a **5-axis robotic arm** to sort packages into different bins. To ensure continuous operation, it features a **solar-assisted Automatic Transfer Switch (ATS)** for power resilience.

### ✨ Key Features

*   **🤖 Robotic Arm Sorting:** Precisely moves packages from the conveyor to designated sorting areas.
*   **👁️ Computer Vision (OCR):** A webcam scans parcel labels, and Tesseract OCR software extracts the destination text.
*   **⚡ Smart Power Management:** An Automatic Transfer Switch (ATS) seamlessly switches between the main grid and a solar-powered battery backup, ensuring 24/7 uptime.
*   **⚙️ Centralized Control:** A **Raspberry Pi 5** serves as the brain of the operation, coordinating the camera, conveyor, and robotic arm.

---

---

## 💻 Tech Stack

| Category          | Technologies Used                                                              |
| ----------------- | ------------------------------------------------------------------------------ |
| **Software**      | `Python`, `Flask`, `OpenCV`, `Tesseract OCR`, `Raspberry Pi OS`                  |
| **Hardware**      | `Raspberry Pi 5`, `MG995 Servo Motors`, `PCA9685 Driver`, `ESP32 Cam / Webcam`   |
| **Power System**  | `Automatic Transfer Switch (ATS)`, `Solar Panels`, `PWM Charge Controller`       |

---

## 🔧 How It Works

1.  A parcel is placed on the conveyor belt.
2.  As it passes under the camera, an image of the label is captured.
3.  The Raspberry Pi processes the image, using OCR to determine the parcel's destination.
4.  The Pi calculates the parcel's position and commands the robotic arm to intercept it.
5.  The robotic arm picks up the parcel and places it in the correct sorting bin.

---