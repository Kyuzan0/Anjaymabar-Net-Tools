"""Custom Toggle Switch Widget for SMB Network Manager."""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPropertyAnimation, pyqtProperty, pyqtSignal, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QPen


class ToggleSwitch(QWidget):
    """A modern sliding toggle switch widget with smooth animation."""
    
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 26)
        self._checked = False
        self._knob_position = 3.0  # Float for smooth animation
        self._enabled = True
        
        # Animation setup
        self.animation = QPropertyAnimation(self, b"knob_position")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        
        self.setCursor(Qt.PointingHandCursor)
    
    @pyqtProperty(float)
    def knob_position(self):
        """Get the current knob position."""
        return self._knob_position
    
    @knob_position.setter
    def knob_position(self, pos):
        """Set the knob position and trigger repaint."""
        self._knob_position = pos
        self.update()
    
    def setChecked(self, checked, animate=True):
        """Set the checked state with animation."""
        if self._checked != checked:
            self._checked = checked
            
            # Calculate target position
            # OFF: knob at left (x=3)
            # ON: knob at right (x=27 for 50px width, 20px knob, 3px margin)
            start_pos = self._knob_position
            end_pos = 27.0 if checked else 3.0
            
            if animate:
                self.animation.stop()
                self.animation.setStartValue(start_pos)
                self.animation.setEndValue(end_pos)
                self.animation.start()
            else:
                self._knob_position = end_pos
                self.update()
    
    def isChecked(self):
        """Return whether the switch is checked."""
        return self._checked
    
    def setEnabled(self, enabled):
        """Enable or disable the toggle switch."""
        self._enabled = enabled
        if enabled:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ForbiddenCursor)
        self.update()
        super().setEnabled(enabled)
    
    def mousePressEvent(self, event):
        """Handle mouse press event to toggle the switch."""
        if not self._enabled:
            return
        
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)
            self.toggled.emit(self._checked)
    
    def paintEvent(self, event):
        """Paint the toggle switch."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate animation progress (0 to 1) based on knob position
        progress = (self._knob_position - 3.0) / 24.0  # 24 = 27 - 3
        progress = max(0.0, min(1.0, progress))  # Clamp to 0-1
        
        # Determine colors based on state and enabled status
        if not self._enabled:
            gray = QColor("#E0E0E0")  # Light gray (disabled OFF)
            green = QColor("#A5D6A7")  # Light green (disabled ON)
            circle_color = QColor("#F5F5F5")  # Light white (disabled)
        else:
            gray = QColor("#BDBDBD")  # Gray (OFF)
            green = QColor("#4CAF50")  # Green (ON)
            circle_color = QColor("#FFFFFF")  # White
        
        # Interpolate background color based on animation progress
        r = int(gray.red() + (green.red() - gray.red()) * progress)
        g = int(gray.green() + (green.green() - gray.green()) * progress)
        b = int(gray.blue() + (green.blue() - gray.blue()) * progress)
        bg_color = QColor(r, g, b)
        
        # Draw background track
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 13, 13)
        
        # Draw shadow for knob (only when enabled)
        knob_diameter = 20
        knob_y = (self.height() - knob_diameter) // 2  # Center vertically
        
        if self._enabled:
            shadow_color = QColor(0, 0, 0, 30)
            painter.setBrush(shadow_color)
            painter.drawEllipse(int(self._knob_position) + 1, knob_y + 1, knob_diameter, knob_diameter)
        
        # Draw knob (circle) at animated position
        painter.setBrush(circle_color)
        painter.drawEllipse(int(self._knob_position), knob_y, knob_diameter, knob_diameter)