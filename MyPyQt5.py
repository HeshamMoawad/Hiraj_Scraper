import typing

import pandas
from PyQt5.QtCore import (QCoreApplication, QEasingCurve, QPoint, QPointF,
                          QPropertyAnimation, QRect, QRectF,
                          QSequentialAnimationGroup, QSize, Qt, pyqtProperty,
                          pyqtSignal, pyqtSlot)
from PyQt5.QtGui import QBrush, QColor, QIcon, QPainter, QPaintEvent, QPen
from PyQt5.QtWidgets import *
from styles import Styles

class MyQTreeWidget(QTreeWidget,QWidget):
    onLengthChanged = pyqtSignal(int)
    childChanged = pyqtSignal(int)
    _CHILD_COUNT = 0
    _ROW_INDEX = 0
    def __init__(self, parent: typing.Optional[QWidget] = ...) -> None:
        super().__init__(parent)
        
    def extract_data_to_DataFrame(self)-> pandas.DataFrame:
        self.COLUMN_NAMES = [self.headerItem().text(i) for i in range(self.columnCount())]
        self.df = pandas.DataFrame(columns=self.COLUMN_NAMES)
        for col_index in range(self.columnCount()):
            col_vals = []
            for row_index in range(self.topLevelItemCount()):
                text = self.topLevelItem(row_index).text(col_index)
                col_vals.append(text)
                for ch_index in range(self.topLevelItem(row_index).childCount()):
                    chtext = self.topLevelItem(row_index).child(ch_index).text(col_index)
                    col_vals.append(chtext)
            self.df[self.COLUMN_NAMES[col_index]] = col_vals
        return self.df

    def extract_data_to_list(self,index_of_column)->list:
        return self.extract_data_to_DataFrame()[self.COLUMN_NAMES[index_of_column]].to_list()
    
    def extract_data_to_string(self,index_of_column)->str:
        return self.extract_data_to_DataFrame()[self.COLUMN_NAMES[index_of_column]].to_string(index=False)

    def extract_columns(self,lista)->str:
        return self.extract_data_to_DataFrame()[[self.COLUMN_NAMES[i] for i in lista]].to_string(index=False)

    def appendData(self,items:list=None,childs:list=None)->None:
        item_ = QTreeWidgetItem(self)
        for i in range(self.columnCount()):
            self.topLevelItem(self._ROW_INDEX).setText(i,items[i])
        if childs != None:
            childindex = 0
            if type(childs[0]) is list :
                for child in childs:
                    child_ = QTreeWidgetItem(item_)
                    for i in range(self.columnCount()):
                        item = self.topLevelItem(self._ROW_INDEX)
                        item.child(childindex).setText(i, child[i])
                    self.childChanged.emit(item.childCount())
                    self._CHILD_COUNT+=1
                    childindex += 1
            else:
                child_ = QTreeWidgetItem(item_)
                for i in range(self.columnCount()):
                    item = self.topLevelItem(self._ROW_INDEX)
                    item.child(childindex).setText(i, childs[i])
                self._CHILD_COUNT+=1
                self.childChanged.emit(item.childCount())

        self._ROW_INDEX += 1
        self.onLengthChanged.emit(self._ROW_INDEX)

    
    
    @pyqtProperty(int)
    def length(self):
        return self._ROW_INDEX
    
    # @length.setter
    # def length(self,value):
    #     self._ROW_INDEX = value
    
    def setColumns(self, columns: list) -> None:
        for column in columns:
            self.headerItem().setText(columns.index(column),str(column))

    def takeTopLevelItem(self, index: int) -> QTreeWidgetItem:
        self._ROW_INDEX -= 1
        self.onLengthChanged.emit(self._ROW_INDEX)
        if self.topLevelItem(index).childCount() >= 1:
            self._CHILD_COUNT = self._CHILD_COUNT - self.topLevelItem(index).childCount()
        return super().takeTopLevelItem(index)

    def childrenCount(self)-> int:
        count = 0
        for row in range(self._ROW_INDEX):
            count = count + self.topLevelItem(row).childCount()
        return count

    def clear(self) -> None:
        self._ROW_INDEX = 0
        self._CHILD_COUNT = 0
        self.onLengthChanged.emit(self._ROW_INDEX)
        return super().clear()



class AnimatedToggle(QCheckBox):

    _transparent_pen = QPen(Qt.transparent)
    _light_grey_pen = QPen(Qt.lightGray)

    def __init__(self,
        parent=None,
        bar_color=Qt.gray,
        checked_color="#00B0FF",
        handle_color=Qt.white,
        pulse_unchecked_color="#44999999",
        pulse_checked_color="#4400B0EE"
        ):
        super().__init__(parent)

        # Save our properties on the object via self, so we can access them later
        # in the paintEvent.
        self._bar_brush = QBrush(bar_color)
        self._bar_checked_brush = QBrush(QColor(checked_color).lighter())

        self._handle_brush = QBrush(handle_color)
        self._handle_checked_brush = QBrush(QColor(checked_color))

        self._pulse_unchecked_animation = QBrush(QColor(pulse_unchecked_color))
        self._pulse_checked_animation = QBrush(QColor(pulse_checked_color))

        # Setup the rest of the widget.
        self.setContentsMargins(8, 0, 8, 0)
        self._handle_position = 0

        self._pulse_radius = 0

        self.animation = QPropertyAnimation(self, b"handle_position", self)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.setDuration(200)  # time in ms

        self.pulse_anim = QPropertyAnimation(self, b"pulse_radius", self)
        self.pulse_anim.setDuration(350)  # time in ms
        self.pulse_anim.setStartValue(10)
        self.pulse_anim.setEndValue(20)

        self.animations_group = QSequentialAnimationGroup()
        self.animations_group.addAnimation(self.animation)
        self.animations_group.addAnimation(self.pulse_anim)

        self.stateChanged.connect(self.setup_animation)

    def sizeHint(self):
        return QSize(58, 45)

    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)

    @pyqtSlot(int)
    def setup_animation(self, value):
        self.animations_group.stop()
        if value:
            self.animation.setEndValue(1)
        else:
            self.animation.setEndValue(0)
        self.animations_group.start()

    def paintEvent(self, e: QPaintEvent):

        contRect = self.contentsRect()
        handleRadius = round(0.24 * contRect.height())

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(self._transparent_pen)
        barRect = QRectF(
            0, 0,
            contRect.width() - handleRadius, 0.40 * contRect.height()
        )
        barRect.moveCenter(contRect.center())
        rounding = barRect.height() / 2

        # the handle will move along this line
        trailLength = contRect.width() - 2 * handleRadius

        xPos = contRect.x() + handleRadius + trailLength * self._handle_position

        if self.pulse_anim.state() == QPropertyAnimation.Running:
            p.setBrush(
                self._pulse_checked_animation if
                self.isChecked() else self._pulse_unchecked_animation)
            p.drawEllipse(QPointF(xPos, barRect.center().y()),
                          self._pulse_radius, self._pulse_radius)

        if self.isChecked():
            p.setBrush(self._bar_checked_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setBrush(self._handle_checked_brush)

        else:
            p.setBrush(self._bar_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setPen(self._light_grey_pen)
            p.setBrush(self._handle_brush)

        p.drawEllipse(
            QPointF(xPos, barRect.center().y()),
            handleRadius, handleRadius)

        p.end()

    @pyqtProperty(float)
    def handle_position(self):
        return self._handle_position

    @handle_position.setter
    def handle_position(self, pos):
        """change the property
        we need to trigger QWidget.update() method, either by:
            1- calling it here [ what we doing ].
            2- connecting the QPropertyAnimation.valueChanged() signal to it.
        """
        self._handle_position = pos
        self.update()

    @pyqtProperty(float)
    def pulse_radius(self):
        return self._pulse_radius

    @pulse_radius.setter
    def pulse_radius(self, pos):
        self._pulse_radius = pos
        self.update()



class MyQSideMenu(QWidget):
    def __init__(self,
    parent:QWidget = None ,
    width:int = 100 ,
    hight:int = 300 ,
    ButtonsCount = 2 ,
    Duration:int = 400 ,
    DefultIconPath:str = None ,  
    ClickIconPath:str = None ,  
    **kwargs , 
    ):
        
        super().__init__(parent)
        self._width = width
        self._hight = hight
     
        self.MainFrame = QFrame(parent)
        self.MainFrame.setGeometry(QRect(0, 0, self._width, self._hight))
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.MainFrame.sizePolicy().hasHeightForWidth())
        self.MainFrame.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(self.MainFrame)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.MenuButton = QPushButton(self.MainFrame,text=" Menu")
        self.MenuButton.setFlat(True)
        sizePolicy = QSizePolicy(QSizePolicy.mum, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.MenuButton.sizePolicy().hasHeightForWidth())
        self.MenuButton.setSizePolicy(sizePolicy)
        self.gridLayout.addWidget(self.MenuButton, 0, 0, 1, 1, Qt.AlignLeft|Qt.AlignTop)
        self.SecondFrame = QFrame(self.MainFrame)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.SecondFrame.sizePolicy().hasHeightForWidth())
        self.SecondFrame.setSizePolicy(sizePolicy)
        self.SecondFrame.setFixedWidth(self._width)
        self.verticalLayout = QVBoxLayout(self.SecondFrame)
        self.Buttons = []
        for index in range(ButtonsCount):
            Button = QPushButton(self.SecondFrame,text="Test")
            Button.setSizePolicy(sizePolicy)
            Button.setFlat(True)
            self.verticalLayout.addWidget(Button)
            self.Buttons.append(Button)
        self.verticalLayout.setContentsMargins(0,0,0,0)
        self.gridLayout.addWidget(self.SecondFrame, 1, 0, 1, 1, Qt.AlignTop)
        self.gridLayout.setRowStretch(0, 1)
        self.gridLayout.setRowStretch(1, 9)
        self.Animation = QPropertyAnimation(self,b"WidthAnimation",self)
        self.Animation.setDuration(Duration)
        self.Animation.setStartValue(0)
        self.Animation.setEndValue(self.SecondFrame.width())
        self.MaxWidth = self.SecondFrame.width()
        self.SecondFrame.setFixedWidth(0)
        self.MenuButton.clicked.connect(self.StartAnimation)
        self.DefultIconPath = DefultIconPath
        self.ClickIconPath = ClickIconPath
        self.MenuButton.setIcon(QIcon(DefultIconPath)) if DefultIconPath != None else None


    def setButtonText(self,index:int,text:str):
        self.Buttons[index].setText(text)

    @pyqtProperty(int)
    def WidthAnimation(self):
        return self.SecondFrame.width()

    @WidthAnimation.setter
    def WidthAnimation(self,val):
        self.SecondFrame.setFixedWidth(val)

    def StartAnimation(self):
        if self.SecondFrame.width() == self.MaxWidth :
            self.MenuButton.setIcon(QIcon(self.DefultIconPath)) if self.DefultIconPath != None else None
            self.Animation.setDirection(self.Animation.Direction.Backward)
            self.Animation.start()

        elif self.SecondFrame.width() != self.MaxWidth :
            self.MenuButton.setIcon(QIcon(self.ClickIconPath)) if self.ClickIconPath != None else None
            self.Animation.setDirection(self.Animation.Direction.Forward)
            self.Animation.start()

    @pyqtSlot(int,str)
    def setButtonIcon(self,index:int,IconPath:str):
        self.Buttons[index].setIcon(QIcon(IconPath))
        

    def Connections(self,index:int,func):
        self.Buttons[index].clicked.connect(func)






class QSideMenuNewStyle(QWidget):
    def __init__(
            self,
            parent,
            ButtonsCount:int = 2,
            PagesCount:int = 2 ,
            ButtonsSpacing:int = 3 ,
            Duration:int = 400 ,
            DefultIconPath:str = None ,
            ClickIconPath:str = None ,  
            StretchMenuForStacked:tuple=(1,5) ,
            StretchTopForBottomFrame:tuple = (1,6),
            ButtonsFrameFixedwidth:int=None,
            TopFrameFixedHight:int= 40,
            ExitButtonIconPath:str=None ,
            ButtonsFixedHight:int=None , 
            MaxButtonIconPath:str = None ,
            Mini_MaxButtonIconPath:str = None ,
            MiniButtonIconPath:str = None,

            **kwargs,

        ) -> None:
        super().__init__(parent)

        self.DefultIconPath = DefultIconPath
        self.ClickIconPath = ClickIconPath
        self.verticalLayout = QVBoxLayout(parent)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.TopFrame = QFrameDraggable(parent)
        self.TopFrame.setFixedHeight(TopFrameFixedHight) if TopFrameFixedHight != None else None
        self.horizontalLayout_2 = QHBoxLayout(self.TopFrame)
        self.MenuButton = QPushButton(self.TopFrame , text=" Menu")
        self.MenuButton.setFlat(True)
        # sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # sizePolicy.setHeightForWidth(self.MenuButton.sizePolicy().hasHeightForWidth())
        # self.MenuButton.setSizePolicy(sizePolicy)
        # self.MenuButton.setFixedWidth(100)
        self.MenuButton.setFixedHeight(self.TopFrame.height()-15)
        
        self.MenuButton.setStyleSheet(Styles.BUTTON)

        self.horizontalLayout_2.addWidget(self.MenuButton, 1, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignCenter)
        self.MainLabel = QLabel(self.TopFrame)
        self.MainLabel.setText("")
        self.horizontalLayout_2.addWidget(self.MainLabel, 4 ,Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignCenter)
        self.MiniButton = QPushButton(self.TopFrame)
        self.MiniButton.setStyleSheet(Styles.BUTTON)
        self.MiniButton.setFlat(True)
        self.MiniButton.setFixedSize(QSize(20,20))
        self.MiniButton.setIcon(QIcon(MiniButtonIconPath)) if MiniButtonIconPath != None else None
        self.horizontalLayout_2.addWidget(self.MiniButton, 0,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignCenter)
        self.MiniButton.clicked.connect(parent.parent().showMinimized)
        self.MaxButton = QPushButton(self.TopFrame)
        self.MaxButton.setStyleSheet(Styles.BUTTON)
        self.MaxButton.setFlat(True)
        self.MaxButton.setFixedSize(QSize(20,20))
        self.MaxButton.setIcon(QIcon(MaxButtonIconPath)) if MaxButtonIconPath != None else None
        self.MaxButton.clicked.connect(lambda : self.max_mini(self.parent().parent(),MaxButtonIconPath,Mini_MaxButtonIconPath,ButtonsFrameFixedwidth))
        self.horizontalLayout_2.addWidget(self.MaxButton, 0,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignCenter)
        self.ExitButton = QPushButton(self.TopFrame)
        self.ExitButton.setStyleSheet(Styles.BUTTON)
        self.ExitButton.setFlat(True)
        self.ExitButton.setFixedSize(QSize(20,20))
        self.ExitButton.setIcon(QIcon(ExitButtonIconPath)) if ExitButtonIconPath != None else None
        self.ExitButton.clicked.connect(parent.close)
        self.ExitButton.clicked.connect(QCoreApplication.instance().quit)        
        self.horizontalLayout_2.addWidget(self.ExitButton, 0, Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignCenter)
        self.horizontalLayout_2.setContentsMargins(5,5,6,5)
        self.verticalLayout.addWidget(self.TopFrame)
        self.BottomFrame = QFrame(parent)
        self.horizontalLayout = QHBoxLayout(self.BottomFrame)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.ButtonsFrame = QFrame(self.BottomFrame)
        self.ButtonsFrame.setFixedWidth(ButtonsFrameFixedwidth) if ButtonsFrameFixedwidth != None else None
        self.verticalLayout_2 = QVBoxLayout(self.ButtonsFrame)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setSpacing(ButtonsSpacing)
        self.Buttons = [] #ButtonsList

        for index in range(ButtonsCount) :
            Button = QPushButton(self.ButtonsFrame , text=f"Button {index}")
            sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            sizePolicy.setHeightForWidth(Button.sizePolicy().hasHeightForWidth())
            Button.setFixedHeight(ButtonsFixedHight) if ButtonsFixedHight != None else None
            Button.setSizePolicy(sizePolicy)
            Button.setStyleSheet(Styles.BUTTON)
            if index == ButtonsCount - 1 :
                self.verticalLayout_2.addWidget(Button ,1, Qt.AlignmentFlag.AlignTop)
            else :
                self.verticalLayout_2.addWidget(Button ,0, Qt.AlignmentFlag.AlignTop)
            Button.setFlat(True)
            self.Buttons.append(Button)

        self.horizontalLayout.addWidget(self.ButtonsFrame)
        self.stackedWidget = QStackedWidget(self.BottomFrame)
        self.Pages = []

        for Page in range(PagesCount):
            Page = QWidget()
            self.stackedWidget.addWidget(Page)
            self.Pages.append(Page)

        self.horizontalLayout.addWidget(self.stackedWidget)
        self.horizontalLayout.setStretch(0 , StretchMenuForStacked[0])
        self.horizontalLayout.setStretch(1, StretchMenuForStacked[1])
        
        self.verticalLayout.addWidget(self.BottomFrame)
        self.verticalLayout.setStretch(0 ,StretchTopForBottomFrame[0])
        self.verticalLayout.setStretch(1 , StretchTopForBottomFrame[1])
        self.MAXWIDTH = self.ButtonsFrame.width()
        self.NORMALWIDTH = self.MAXWIDTH
        self.Animation = QPropertyAnimation(self,b"Width",self)
        self.Animation.setDuration(Duration)
        self.MenuButton.setIcon(QIcon(DefultIconPath)) if DefultIconPath != None else None
        self.MenuButton.clicked.connect(self.MenuClick)
        self.ButtonsFrame.setFixedWidth(0)
        self.setCurrentPage(0)

    @pyqtProperty(int)
    def Width(self):
        return self.ButtonsFrame.width()
    
    @Width.setter
    def Width(self,val):
        self.ButtonsFrame.setFixedWidth(val)
        
    def MenuClick(self)-> None:
        if self.ButtonsFrame.width() == self.MAXWIDTH :
            self.MenuButton.setIcon(QIcon(self.DefultIconPath)) if self.DefultIconPath != None else None
            self.Animation.setStartValue(0)
            self.Animation.setEndValue(self.MAXWIDTH)
            self.Animation.setDirection(self.Animation.Direction.Backward)
            self.Animation.start()

        elif self.ButtonsFrame.width() != self.MAXWIDTH :
            self.Animation.setStartValue(0)
            self.Animation.setEndValue(self.MAXWIDTH)
            self.MenuButton.setIcon(QIcon(self.ClickIconPath)) if self.ClickIconPath != None else None
            self.Animation.setDirection(self.Animation.Direction.Forward)
            self.Animation.start()

    @pyqtSlot(int,str)
    def setButtonText(self,index:int,text:str)-> None:
        self.Buttons[index].setText(text)

    @pyqtSlot(int,str)
    def setButtonIcon(self,index:int,IconPath:str)-> None:
        self.Buttons[index].setIcon(QIcon(IconPath))
        
    def Connections(self,index:int,func):
        self.Buttons[index].clicked.connect(func)

    def GetButton(self,index:int)-> QPushButton:
        return self.Buttons[index]

    def GetPage(self,index:int)-> QWidget:
        return self.Pages[index]

    @pyqtSlot(int)
    def setCurrentPage(self,index:int):
        self.stackedWidget.setCurrentIndex(index)

    def max_mini(self , parent:QMainWindow , path1:str , path2:str , Fixedwidth):
        if parent.isMaximized():
            parent.showNormal()
            self.MaxButton.setIcon(QIcon(path1))
            self.MAXWIDTH = self.NORMALWIDTH
        else :
            parent.showMaximized()
            self.MaxButton.setIcon(QIcon(path2))
            self.MAXWIDTH = Fixedwidth + 150 if Fixedwidth is int else 200





class QFrameDraggable(QFrame):
    def __init__(self, parent: typing.Optional[QWidget] = ...) -> None:
        super().__init__(parent)
        self.oldPos = self.pos()

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint (event.globalPos() - self.oldPos)
        self.parent().parent().move(self.parent().parent().x() + delta.x(), self.parent().parent().y() + delta.y())
        self.oldPos = event.globalPos()
