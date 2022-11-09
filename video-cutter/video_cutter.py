import pathlib
import os

import sys
import cv2
import numpy as np

import PyQt5
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from pathlib import Path

file_abspath = os.path.abspath(__file__)
folder_abspath = os.path.dirname(file_abspath)

form_class = uic.loadUiType(os.path.join(folder_abspath, "simple_video.ui"))[0]

def letter_box_resize(img, dsize):

    original_height, original_width = img.shape[:2]
    target_width, target_height = dsize

    ratio = min(
        float(target_width) / original_width,
        float(target_height) / original_height)
    resized_height, resized_width = [
        round(original_height * ratio),
        round(original_width * ratio)
    ]

    img = cv2.resize(img, dsize=(resized_width, resized_height))

    pad_left = (target_width - resized_width) // 2
    pad_right = target_width - resized_width - pad_left
    pad_top = (target_height - resized_height) // 2
    pad_bottom = target_height - resized_height - pad_top

    # padding
    img = cv2.copyMakeBorder(img,
                             pad_top,
                             pad_bottom,
                             pad_left,
                             pad_right,
                             cv2.BORDER_CONSTANT,
                             value=(0, 0, 0))

    try:
        if not(img.shape[0] == target_height and img.shape[1] == target_width):  # 둘 중 하나는 같아야 함
            raise Exception('Letter box resizing method has problem.')
    except Exception as e:
        print('Exception: ', e)
        exit(1)

    return img

class WindowClass(QMainWindow, form_class) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        
        self.video_capture = None
        
        #Icon Load
        self.pushButton_file_open.setIcon(QIcon(os.path.join(folder_abspath, 'images', 'icon_file_open.png')))
        
        self.pushButton_play.setIcon(QIcon(os.path.join(folder_abspath, 'images', 'icon_play.png')))
        self.pushButton_play.setIconSize(QSize(32, 32))
        
        self.pushButton_scene_save.setIcon(QIcon(os.path.join(folder_abspath, 'images', 'icon_save.png')))
        self.pushButton_scene_save.setIconSize(QSize(32, 32))
        
        self.pushButton_scene_remove.setIcon(QIcon(os.path.join(folder_abspath, 'images', 'icon_remove.png')))
        self.pushButton_scene_save.setIconSize(QSize(32, 32))

        self.pushButton_file_open.clicked.connect(self.load_video)
        self.pushButton_play.clicked.connect(self.play)
        self.pushButton_scene_init.pressed.connect(self.init_scene_setting)
        self.pushButton_scene_start.pressed.connect(self.set_scene_start_frame)
        self.pushButton_scene_end.pressed.connect(self.set_scene_end_frame)
        self.pushButton_scene_save.clicked.connect(self.save)
        self.pushButton_scene_remove.clicked.connect(self.remove_scene)
        self.pushButtonECGOk.clicked.connect(self.recodeECGQuality)
        self.pushButton_play.setEnabled(False)
        self.pushButton_scene_init.setEnabled(False)
        self.pushButton_scene_start.setEnabled(False)
        self.pushButton_scene_end.setEnabled(False)
        self.pushButton_scene_save.setEnabled(False)
        self.pushButton_scene_remove.setEnabled(False)

        self.horizontalSlider.setEnabled(False)
        self.horizontalSlider.valueChanged.connect(self.move_frame)

        self.comboBoxECG.setCurrentIndex(0)
        self.comboBoxECG.currentIndexChanged.connect(self.getECGPart)
        self.pushButtonECGRemove.clicked.connect(self.removeECGPart)
        self.radioButtonECGGood.toggled.connect(lambda:self.type_ecg_choose(self.radioButtonECGGood))
        self.radioButtonECGBad.toggled.connect(lambda:self.type_ecg_choose(self.radioButtonECGBad))
        self.radioButtonECGOther.toggled.connect(lambda:self.type_ecg_choose(self.radioButtonECGOther))

        self.radioButtonImgGood.toggled.connect(lambda:self.type_img_choose(self.radioButtonImgGood))
        self.radioButtonImgBad.toggled.connect(lambda:self.type_img_choose(self.radioButtonImgBad))
        self.radioButtonImgOther.toggled.connect(lambda:self.type_img_choose(self.radioButtonImgOther))

        self.radioButtonRhythmSinus.toggled.connect(lambda:self.type_rhythm_choose(self.radioButtonRhythmSinus))
        self.radioButtonRhythmArrh.toggled.connect(lambda:self.type_rhythm_choose(self.radioButtonRhythmArrh))

        self.scene_progressbar_timer = QTimer()
        
        self.video_play_timer = QTimer()
        self.video_play_timer.timeout.connect(self.read_next_frame)
        
        self.scene_progressbar_timer.setInterval(1000/60.)
        self.scene_progressbar_timer.timeout.connect(self.draw_scene_progress_bar)
        self.scene_progressbar_timer.start()

        QShortcut(Qt.Key_Space, self, self.play)

        self.listWidget.itemClicked.connect(self.move_scene)

        self.typeECG = {'ECG part': 'First part','ECG quality': 'undefined',
                        'Img quality': 'undefined',
                        'Rhythm': 'undefined',}

    def getECGPart(self):
        self.typeECG['ECG part'] = self.comboBoxECG.currentText()
    def video_capture_release(self):
        if self.video_capture == None:
            return None
        self.video_capture.release()
    
    def load_video(self):
        
        self.video_file = QFileDialog.getOpenFileName(self, "Open a file", folder_abspath , "video file (*.mp4 *.avi *.mkv *.MP4 *.AVI *.MKV)")[0]
        print(self.video_file)
        if len(self.video_file) == 0:
            return None
        
        self.scene_start_frame_index = 0
        self.scene_end_frame_index = 0
        
        self.video_name = Path(self.video_file).resolve().stem
        self.patient_name = self.video_file.split('/')[-2]
        print(self.patient_name)
        self.frame_index = 0

        self.video_capture_release()
        self.video_capture = cv2.VideoCapture(self.video_file, apiPreference=cv2.CAP_FFMPEG)
        
        if self.video_capture == None or not self.video_capture.isOpened():
            return self.video_capture_release()
   
        self.video_fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        self.video_num_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        
        self.video_play_timer.setInterval(1000./self.video_fps)
                
        self.horizontalSlider.blockSignals(True)
        self.horizontalSlider.setValue(0)
        self.horizontalSlider.blockSignals(False)
        
        self.horizontalSlider.setEnabled(True)
        self.horizontalSlider.setMinimum(0)
        self.horizontalSlider.setMaximum(self.video_num_frames)
        
        self.pushButton_play.setEnabled(True)
        self.pushButton_scene_init.setEnabled(False)
        self.pushButton_scene_start.setEnabled(True)
        self.pushButton_scene_end.setEnabled(False)
        self.pushButton_scene_save.setEnabled(True)
        self.pushButton_scene_remove.setEnabled(True)
        
        self.listWidget.clear()
        self.read_next_frame()
        
    def play(self):
        if not self.pushButton_play.isEnabled():
            return None
        
        if self.video_play_timer.isActive():
            self.pushButton_play.setIcon(QIcon(os.path.join(folder_abspath, "images", 'icon_play.png')))
            self.video_play_timer.stop()
        else:
            self.pushButton_play.setIcon(QIcon(os.path.join(folder_abspath, "images", 'icon_pause.png')))
            self.video_play_timer.start()
    
    def init_scene_setting(self):
        self.pushButton_scene_start.setEnabled(True)
        self.pushButton_scene_end.setEnabled(False)
        self.pushButton_scene_init.setEnabled(False)

    def set_scene_start_frame(self):
        self.scene_start_frame_index = self.frame_index
        
        self.pushButton_scene_start.setEnabled(False)
        self.pushButton_scene_end.setEnabled(True)
        self.pushButton_scene_init.setEnabled(True)

    def set_scene_end_frame(self):
        self.scene_end_frame_index = self.frame_index
        self.init_scene_setting()
        self.listWidget.addItem(str(self.scene_start_frame_index) + "_" + str(self.scene_end_frame_index))

    def recodeECGQuality(self):
        ecgQualityNote = ''
        if self.typeECG['ECG quality'] == 'Others':
            ecgQualityNote = self.lineEditECG.text()
        self.listWidgetECG.addItem(self.typeECG['ECG part']+ ' - '+self.typeECG['ECG quality']+' '+ecgQualityNote)

    def move_scene(self):
        if self.video_play_timer.isActive():
            self.video_play_timer.stop()
        
        clicked_item = self.listWidget.currentItem().text()
        clicked_item = clicked_item.split('_')
            
        start_frame_index = int(clicked_item[0])
        
        self.frame_index = start_frame_index
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index)
        
        self.read_next_frame()
        
        print(str(self.listWidget.currentRow()) + " : " + self.listWidget.currentItem().text())

    def remove_scene(self):
        self.removeItemRow = self.listWidget.currentRow()
        self.listWidget.takeItem(self.removeItemRow)

    def removeECGPart(self):
        self.removeItemRow = self.listWidgetECG.currentRow()
        self.listWidgetECG.takeItem(self.removeItemRow)
    def type_ecg_choose(self, btn):
        if btn.text()=='Good' and btn.isChecked()==True:
            self.typeECG['ECG quality'] = 'Good'
        elif btn.text()=='Bad' and btn.isChecked()==True:
            self.typeECG['ECG quality'] = 'Bad'
        elif btn.text()=='Others' and btn.isChecked()==True:
            self.typeECG['ECG quality'] = 'Others'

    def type_img_choose(self, btn):
        if btn.text()=='Good' and btn.isChecked()==True:
            self.typeECG['Img quality'] = 'Good'
        elif btn.text()=='Bad' and btn.isChecked()==True:
            self.typeECG['Img quality'] = 'Bad'
        elif btn.text()=='Others' and btn.isChecked()==True:
            self.typeECG['Img quality'] = 'Others'

    def type_rhythm_choose(self, btn):
        if btn.text()=='Sinus Rhythm' and btn.isChecked()==True:
            self.typeECG['Rhythm'] = 'Sinus Rhythm'
        elif btn.text()=='Arrhythmia' and btn.isChecked()==True:
            self.typeECG['Rhythm'] = 'Arrhythmia'
        elif btn.text()=='Others' and btn.isChecked()==True:
            self.typeECG['Rhythm'] = 'Others'

    def save(self):
        # 判断类型是否选择
        # print(self.radioButtonRateGood.isChecked())

        if self.listWidget.count() == 0:
            return None
        
        if self.video_play_timer.isActive():
            self.video_play_timer.stop()

        self.scene_progressbar_timer.stop()
        if not os.path.isdir("./" + self.video_name):
            os.mkdir("./" + self.video_name)
        if self.typeECG['Img quality']=='undefined':
            msg_box = QMessageBox(QMessageBox.Warning, "提示", "图像质量未标记")
            msg_box.exec_()
        if self.typeECG['Rhythm']=='undefined':
            msg_box = QMessageBox(QMessageBox.Warning, "提示", "心率类型未标记")
            msg_box.exec_()
        # 保存关键帧
        for item_index in range(self.listWidget.count()):
            item = self.listWidget.item(item_index).text()
            item = item.split('_')
            
            start_frame_index = int(item[0])
            end_frame_index = int(item[1])
            
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame_index)
            
            scene_folder = os.path.join("./label/",self.patient_name,self.video_name, "s" + format(item_index + 1, '02d'))
            print(scene_folder)
            for i in range(start_frame_index, end_frame_index):
                if not os.path.isdir(scene_folder):
                    os.makedirs(scene_folder)
                
                read_frame, frame = self.video_capture.read()
                
                frame_name = self.video_name + "_f" + format(i, '05d') + ".png"
                cv2.imwrite(os.path.join(scene_folder, frame_name), frame)
        # 保存信息
        with open(os.path.join("./label/",self.patient_name,self.video_name,self.video_name + '.txt'), 'w') as f:
            ImgNote = ''
            RhythmNote = ''
            if self.typeECG['Img quality'] == 'Others':
                ImgNote = self.lineEditImg.text()
            if self.typeECG['Rhythm'] == 'others':
                RhythmNote = self.lineEditRhythm.text()

            self.frameItems = self.listWidget.findItems('_',  Qt.MatchContains)
            f.write('keyFrameIndex: {')
            for i in range(len(self.frameItems)):
                f.write(self.frameItems[i].text())
                f.write(', ')
            f.write('}\n')
            self.ecgItems = self.listWidgetECG.findItems('-',  Qt.MatchContains)
            f.write('ecgQualityIndex: {')
            for i in range(len(self.ecgItems)):
                f.write(self.ecgItems[i].text())
                f.write(', ')
            f.write('}\n')

            f.write('Img quality: '+ self.typeECG['Img quality']+' '+ImgNote+'\n')
            f.write('Rhythm: '+ self.typeECG['Rhythm']+' '+RhythmNote)
            # print(1)

        self.scene_progressbar_timer.start()
        msg_box = QMessageBox(QMessageBox.Warning, "保存结果", "恭喜！标记保存完毕")
        msg_box.exec_()


    def move_frame(self):
        if self.video_play_timer.isActive():
            self.video_play_timer.stop()
            
        self.frame_index = self.horizontalSlider.value()-1
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index)
        
        self.read_next_frame()
        
        if not self.pushButton_scene_start.isEnabled():#
            if self.frame_index < self.scene_start_frame_index:
                QMessageBox.question(self, 'Message', 'Scene setting is intialized', QMessageBox.Yes)
                self.init_scene_setting()
            
    def read_next_frame(self):
        if not self.pushButton_play.isEnabled():
            return None
        
        read_frame, frame = self.video_capture.read()
        
        if read_frame:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = letter_box_resize(frame, (self.label_frame.width(), self.label_frame.height()))
            height, width, channels = frame.shape
            bytesPerLine = channels * width
            qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
            pixmap01 = QPixmap.fromImage(qImg)
            
            self.label_frame.setPixmap(pixmap01)
            self.frame_index += 1

            self.horizontalSlider.blockSignals(True)
            self.horizontalSlider.setValue(self.frame_index)
            self.horizontalSlider.blockSignals(False)
            
            self.label_frame_index.setText(str(self.frame_index)+ "/" + str(self.video_num_frames))

    def draw_scene_progress_bar(self):
        if not self.pushButton_play.isEnabled():
            return None
        
        scene_progress_bar = np.zeros((self.label_scene_progress_bar.height(), self.label_scene_progress_bar.width(), 3), np.uint8)
        
        if not self.pushButton_scene_start.isEnabled():
            start_frame_index = int(self.label_scene_progress_bar.width() * (float(self.scene_start_frame_index) / self.video_num_frames))
            end_frame_index = int(self.label_scene_progress_bar.width() * (float(self.frame_index) / self.video_num_frames))
            scene_progress_bar[:, start_frame_index:end_frame_index] = [255, 255, 0]
            
        for item_index in range(self.listWidget.count()):
            item = self.listWidget.item(item_index).text()
            item = item.split('_')
            
            start_frame_index = int(self.label_scene_progress_bar.width() * (float(item[0]) / self.video_num_frames))
            end_frame_index = int(self.label_scene_progress_bar.width() * (float(item[1]) / self.video_num_frames))
            
            scene_progress_bar[:, start_frame_index:end_frame_index] = [0, 255, 0]

        height, width, channels = scene_progress_bar.shape
        bytesPerLine = channels * width
        qImg = QImage(scene_progress_bar.data, width, height, bytesPerLine, QImage.Format_RGB888)
        pixmap01 = QPixmap.fromImage(qImg)
        self.label_scene_progress_bar.setPixmap(pixmap01)

if __name__ == "__main__" :
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()
