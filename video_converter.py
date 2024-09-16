import sys
import subprocess
import os
import re
import ctypes 
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QFileDialog, QLabel, QVBoxLayout, QComboBox, QCheckBox, QMessageBox, QSlider, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

def is_admin():
    if os.name == 'nt':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return os.geteuid() == 0

def request_permissions():
    if os.name == 'nt':  # Windows
        if not is_admin():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()
    else:  # macOS/Linux
        if not is_admin():
            print("This script requires elevated permissions. Please run as Admin or use sudo.")
            sys.exit()

class ConversionThread(QThread):
    finished_signal = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            self.finished_signal.emit('success')
        else:
            self.finished_signal.emit(f'failure: {stderr}')

class VideoConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Video Converter')
        self.setFixedSize(400, 450)  # Lock the window size
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QPushButton, QComboBox, QCheckBox, QSlider {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton:hover, QComboBox:hover, QCheckBox:hover, QSlider:hover {
                background-color: #45494a;
            }
            QSlider::handle:horizontal {
                background-color: green;
                border: 1px solid #555555;
                width: 10px;
                margin: -5px 0;
                border-radius: 5px;
            }
        """)

        font = QFont("Arial", 10)
        self.setFont(font)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.label = QLabel('Select a video file to convert', self)
        layout.addWidget(self.label)
        
        self.btn = QPushButton('Choose File', self)
        self.btn.clicked.connect(self.showDialog)
        layout.addWidget(self.btn)

        self.input_type_label = QLabel('Input File Type: ', self)
        layout.addWidget(self.input_type_label)
        
        self.output_type_label = QLabel('Output File Type:', self)
        layout.addWidget(self.output_type_label)

        self.output_type_combo = QComboBox(self)
        self.output_type_combo.addItems(["webm", "mp4", "avi", "mkv", "mov"])
        layout.addWidget(self.output_type_combo)

        self.bitrate_label = QLabel('Bitrate:', self)
        layout.addWidget(self.bitrate_label)
        
        self.bitrate_slider = QSlider(Qt.Horizontal)
        self.bitrate_slider.setMinimum(500)
        self.bitrate_slider.setMaximum(50000)
        self.bitrate_slider.setTickInterval(500)
        self.bitrate_slider.setTickPosition(QSlider.TicksBelow)
        self.bitrate_slider.valueChanged.connect(self.updateBitrateLabel)
        layout.addWidget(self.bitrate_slider)

        self.bitrate_value_label = QLabel('Bitrate: 1000k', self)
        layout.addWidget(self.bitrate_value_label)

        self.resolution_label = QLabel('Resolution:', self)
        layout.addWidget(self.resolution_label)
        
        self.resolution_combo = QComboBox(self)
        self.resolution_combo.addItems(["640x480", "1280x720", "1920x1080", "2560x1440", "3840x2160"])
        layout.addWidget(self.resolution_combo)
        
        self.audio_option = QComboBox(self)
        self.audio_option.addItems(["Keep Audio", "Remove Audio"])
        layout.addWidget(self.audio_option)
        
        self.metadata_checkbox = QCheckBox('Remove Metadata', self)
        layout.addWidget(self.metadata_checkbox)
        
        self.convertBtn = QPushButton('Convert', self)
        self.convertBtn.clicked.connect(self.convertVideo)
        layout.addWidget(self.convertBtn)

        self.status_label = QLabel('', self)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        self.show()
    
    def showDialog(self):
        self.input_file, _ = QFileDialog.getOpenFileName(self, 'Open file', '', 'Video Files (*.mp4 *.avi *.mov *.mkv *.flv *.webm)')
        if self.input_file:
            self.label.setText(self.input_file)
            input_file_type = self.input_file.split(".")[-1]
            self.input_type_label.setText(f'Input File Type: {input_file_type}')
            self.output_type_combo.setCurrentText(input_file_type)
            self.updateVideoStats()

    def updateVideoStats(self):
        command = f'ffmpeg -i "{self.input_file}"'
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()
        stderr = stderr.decode()

        bitrate_match = re.search(r'bitrate:\s(\d+)\s', stderr)
        resolution_match = re.search(r'Stream.*Video.* (\d+x\d+)', stderr)

        if bitrate_match:
            bitrate = bitrate_match.group(1) + 'k'
            bitrate_value = int(bitrate_match.group(1))
            self.bitrate_slider.setValue(bitrate_value)
            self.bitrate_value_label.setText(f'Bitrate: {bitrate}')
            self.updateBitrateLabel()  # Update color

        if resolution_match:
            resolution = resolution_match.group(1)
            if resolution in [self.resolution_combo.itemText(i) for i in range(self.resolution_combo.count())]:
                self.resolution_combo.setCurrentText(resolution)

    def updateBitrateLabel(self):
        value = self.bitrate_slider.value()
        resolution = self.resolution_combo.currentText()
        self.bitrate_value_label.setText(f'Bitrate: {value}k')

        # Adjust color based on bitrate and resolution
        if resolution == "640x480":
            if value <= 1000:
                color = 'background-color: green'
            elif value <= 1500:
                color = 'background-color: yellow'
            else:
                color = 'background-color: red'
        elif resolution == "1280x720":
            if value <= 3000:
                color = 'background-color: green'
            elif value <= 5000:
                color = 'background-color: yellow'
            else:
                color = 'background-color: red'
        elif resolution == "1920x1080":
            if value <= 6000:
                color = 'background-color: green'
            elif value <= 10000:
                color = 'background-color: yellow'
            else:
                color = 'background-color: red'
        elif resolution == "2560x1440":
            if value <= 10000:
                color = 'background-color: green'
            elif value <= 16000:
                color = 'background-color: yellow'
            else:
                color = 'background-color: red'
        else:  # 3840x2160
            if value <= 20000:
                color = 'background-color: green'
            elif value <= 30000:
                color = 'background-color: yellow'
            else:
                color = 'background-color: red'

        self.bitrate_slider.setStyleSheet(f'QSlider::handle:horizontal {{{color};}}')

    def generateUniqueFilename(self, base_name, extension):
        counter = 1
        new_filename = f"{base_name}.{extension}"
        while os.path.exists(new_filename):
            new_filename = f"{base_name}_{counter}.{extension}"
            counter += 1
        return new_filename

    def convertVideo(self):
        if self.input_file:
            output_extension = self.output_type_combo.currentText()
            base_name = self.input_file.rsplit('.', 1)[0] + '_converted'
            output_file = self.generateUniqueFilename(base_name, output_extension)

            command = ['ffmpeg', '-i', self.input_file.replace('\\', '/'), '-b:v', f'{self.bitrate_slider.value()}k']

            resolution = self.resolution_combo.currentText()
            command.extend(['-vf', f'scale={resolution.split("x")[0]}:{resolution.split("x")[1]}'])

            if self.audio_option.currentText() == "Remove Audio":
                command.append('-an')

            if self.metadata_checkbox.isChecked():
                command.extend(['-map_metadata', '-1'])
            
            command.append(output_file.replace('\\', '/'))

            self.status_label.setText('Conversion in progress...')
            self.status_label.setStyleSheet('color: yellow;')

            self.thread = ConversionThread(command)
            self.thread.finished_signal.connect(self.conversionFinished)
            self.thread.start()

    def conversionFinished(self, status):
        if status == 'success':
            self.status_label.setText('Conversion Complete')
            self.status_label.setStyleSheet('color: green;')
        else:
            self.status_label.setText(f'Conversion Failed: {status}')
            self.status_label.setStyleSheet('color: red;')

if __name__ == '__main__':
    request_permissions()
    app = QApplication(sys.argv)
    ex = VideoConverter()
    sys.exit(app.exec_())
