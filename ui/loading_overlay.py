"""Loading Overlay Widget for SMB Network Manager."""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QConicalGradient, QFont


class LoadingOverlay(QWidget):
    """A full-screen loading overlay with a spinning indicator and message."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._spinner_angle = 0
        self._message = "Loading..."
        
        # Make it transparent and cover parent
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        
        # Spinner animation timer
        self._spinner_timer = QTimer(self)
        self._spinner_timer.timeout.connect(self._update_spinner)
        
        # Initially hidden
        self.hide()
    
    def _update_spinner(self):
        """Update spinner angle for animation."""
        self._spinner_angle = (self._spinner_angle + 8) % 360
        self.update()
    
    def setMessage(self, message: str):
        """Set the loading message."""
        self._message = message
        self.update()
    
    def show(self, message: str = "Loading..."):
        """Show the loading overlay with a message."""
        self._message = message
        self._spinner_timer.start(25)  # ~40 FPS for smooth animation
        self.raise_()  # Bring to front
        super().show()
    
    def hide(self):
        """Hide the loading overlay."""
        self._spinner_timer.stop()
        super().hide()
    
    def resizeEvent(self, event):
        """Resize to match parent."""
        if self.parent():
            self.setGeometry(self.parent().rect())
        super().resizeEvent(event)
    
    def paintEvent(self, event):
        """Paint the loading overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw semi-transparent background
        painter.fillRect(self.rect(), QColor(255, 255, 255, 200))
        
        # Calculate center
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        # Draw loading box background
        box_width = 200
        box_height = 120
        box_x = center_x - box_width / 2
        box_y = center_y - box_height / 2
        
        # Draw rounded box with shadow
        shadow_color = QColor(0, 0, 0, 30)
        painter.setBrush(shadow_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(int(box_x + 3), int(box_y + 3), box_width, box_height, 12, 12)
        
        # Draw main box
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(QPen(QColor("#E0E0E0"), 1))
        painter.drawRoundedRect(int(box_x), int(box_y), box_width, box_height, 12, 12)
        
        # Draw spinner
        spinner_radius = 20
        spinner_width = 4
        spinner_center_y = center_y - 15
        
        # Create gradient for spinner effect
        gradient = QConicalGradient(center_x, spinner_center_y, self._spinner_angle)
        gradient.setColorAt(0, QColor("#2196F3"))  # Blue
        gradient.setColorAt(0.4, QColor("#2196F3"))  # Blue
        gradient.setColorAt(0.7, QColor("#90CAF9"))  # Light blue
        gradient.setColorAt(1, QColor(255, 255, 255, 0))  # Transparent
        
        # Draw spinner arc
        pen = QPen()
        pen.setBrush(gradient)
        pen.setWidth(spinner_width)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Draw arc (300 degrees, leaving 60 degrees gap)
        rect = QRectF(
            center_x - spinner_radius,
            spinner_center_y - spinner_radius,
            spinner_radius * 2,
            spinner_radius * 2
        )
        painter.drawArc(rect, self._spinner_angle * 16, 300 * 16)
        
        # Draw message text
        painter.setPen(QColor("#333333"))
        font = QFont()
        font.setPointSize(10)
        font.setWeight(QFont.Medium)
        painter.setFont(font)
        
        text_rect = QRectF(box_x, center_y + 15, box_width, 30)
        painter.drawText(text_rect, Qt.AlignCenter, self._message)
    
    def mousePressEvent(self, event):
        """Block mouse events while loading."""
        event.accept()
    
    def mouseReleaseEvent(self, event):
        """Block mouse events while loading."""
        event.accept()
