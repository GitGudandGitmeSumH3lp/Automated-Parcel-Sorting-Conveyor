# Automated Parcel Sorting Conveyor

A Raspberry Pi-powered system with a full-featured web dashboard for monitoring and control. The system uses OCR, a robotic arm, and an automated transfer switch to autonomously sort packages. 

---

## 🖥️ The Web Dashboard: System Control Center

To provide a user-friendly way to manage the sorter, I developed a complete web interface using Flask. This dashboard serves as the central hub for real-time monitoring, hardware diagnostics, and system testing.

| Dashboard Main Page | Real-Time Camera Stream |
| :---: | :---: |
| ![Main Dashboard](/assets/documentation/dashboard.png) | ![Cam Finder](/assets/documentation/camfinder.png) |
| ![Main Dashboard](/assets/documentation/dashboard1.png) |
| *The main dashboard provides a high-level overview of the system's status and recent activity.* | *Live video from the sorter's camera can be viewed directly in the browser.* |

### Parcel Label Generator

To streamline the testing of the OCR and sorting logic, I built a parcel label generator. This tool creates realistic, scannable labels with randomized destination data, removing the need for physical parcels during software validation.

![Parcel Generator](/assets/documentation/parcelgen.png)


---
## 🚀 Project Overview

This project is a low-cost, scalable solution for automating parcel sorting, designed for small-to-medium logistics operations. It addresses key industry challenges like manual sorting errors and power instability by integrating **Optical Character Recognition (OCR)**, **Robotic Automation**, and a **Solar-Assisted Power System**.

---

## 🔧 A Visual Deep-Dive into the System

### 1. Software Logic & Flow

The system's operational logic is designed for efficiency and error handling. The flowchart below illustrates the decision-making process, from parcel detection to final sorting and potential rerouting.

![Software Flowchart](/assets/hardware/Softwareflowchart.jpg)

### 2. OCR in Action: The Vision System

The core of the identification process is the OCR system. It captures an image of a parcel's label, preprocesses it to enhance readability, and uses Tesseract OCR to extract the destination text. This simulation demonstrates the accuracy of the text extraction.

![OCR Simulation](/assets/documentation/ocr.png)

### 3. Hardware & System Architecture

The hardware is integrated into a cohesive system controlled by a Raspberry Pi. The schematic diagram shows the power and data connections between all major components, while the framework diagram illustrates the flow of data from input (sensors) to output (robotic arm).

| System Schematic | Conceptual Framework (IPO) |
| :---: | :---: |
| ![Hardware Schematic](/assets/hardware/PictureSchematic.png) | ![System Framework](/assets/hardware/image_2025-10-16_192404940.png) 

---

## 💻 Tech Stack

| Category          | Technologies Used                                                              |
| ----------------- | ------------------------------------------------------------------------------ |
| **Software**      | `Python`, `Flask`, `OpenCV`, `Tesseract OCR`, `Raspberry Pi OS`                  |
| **Hardware**      | `Raspberry Pi 5`, `MG995 Servo Motors`, `PCA99685 Driver`, `ESP32 Cam / Webcam`  |
| **Power System**  | `Automatic Transfer Switch (ATS)`, `Solar Panels`, `PWM Charge Controller`       |

## 👥 The Project Team

This project was a collaborative effort by the following Computer Engineering students at Bestlink College of the Philippines.

*   Anave, Feliza C.
*   Delgado, Christian C.
*   Delgado, John Josua B.
*   De Leon, Eunice Joy M.
*   Inocencio, Christian Angelo B.
*   Veriña, Carlo
