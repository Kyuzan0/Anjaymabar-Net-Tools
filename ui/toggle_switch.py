"""Custom Toggle Switch Widget for SMB Network Manager."""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPropertyAnimation, pyqtProperty, pyqtSignal, QEasingCurve, QTimer, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QConicalGradient


class ToggleSwitch(QWidget):
    """A modern sliding toggle switch widget with smooth animation and loading state."""
    
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 26)
        self._checked = False
        self._knob_position = 3.0  # Float for smooth animation
        self._enabled = True
        self._loading = False  # Loading state
        self._spinner_angle = 0  # Spinner rotation angle
        
        # Animation setup
        self.animation = QPropertyAnimation(self, b"knob_position")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        
        # Spinner animation timer
        self._spinner_timer = QTimer(self)
        self._spinner_timer.timeout.connect(self._update_spinner)
        
        self.setCursor(Qt.PointingHandCursor)
    
    def _update_spinner(self):
        """Update spinner angle for animation."""
        self._spinner_angle = (self._spinner_angle + 15) % 360
        self.update()
    
    @pyqtProperty(float)
    def knob_position(self):
        """Get the current knob position."""
        return self._knob_position
    
    @knob_position.setter
    def knob_position(self, pos):
        """Set the knob position and trigger repaint."""
        self._knob_position = pos
        self.update()
    
    def setLoading(self, loading: bool):
        """Set the loading state and start/stop spinner animation."""
        if self._loading != loading:
            self._loading = loading
            if loading:
                self._spinner_timer.start(30)  # ~33 FPS for smooth animation
                self.setCursor(Qt.WaitCursor)
            else:
                self._spinner_timer.stop()
                if self._enabled:
                    self.setCursor(Qt.PointingHandCursor)
                else:
                    self.setCursor(Qt.ForbiddenCursor)
            self.update()
    
    def isLoading(self):
        """Return whether the switch is in loading state."""
        return self._loading
    
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
        if not self._loading:
            if enabled:
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ForbiddenCursor)
        self.update()
        super().setEnabled(enabled)
    
    def mousePressEvent(self, event):
        """Handle mouse press event to toggle the switch."""
        if not self._enabled or self._loading:
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
        if not self._enabled or self._loading:
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
        
        # Draw shadow for knob (only when enabled and not loading)
        knob_diameter = 20
        knob_y = (self.height() - knob_diameter) // 2  # Center vertically
        
        if self._enabled and not self._loading:
            shadow_color = QColor(0, 0, 0, 30)
            painter.setBrush(shadow_color)
            painter.drawEllipse(int(self._knob_position) + 1, knob_y + 1, knob_diameter, knob_diameter)
        
        # Draw knob (circle) at animated position
        painter.setBrush(circle_color)
        painter.drawEllipse(int(self._knob_position), knob_y, knob_diameter, knob_diameter)
        
        # Draw loading spinner on top of knob if loading
        if self._loading:
            self._draw_spinner(painter, int(self._knob_position), knob_y, knob_diameter)
    
    def _draw_spinner(self, painter, knob_x, knob_y, knob_diameter):
        """Draw a spinning loader on the knob."""
        # Calculate center of knob
        center_x = knob_x + knob_diameter / 2
        center_y = knob_y + knob_diameter / 2
        
        # Spinner properties
        spinner_radius = 6
        spinner_width = 2
        
        # Create gradient for spinner effect
        gradient = QConicalGradient(center_x, center_y, self._spinner_angle)
        gradient.setColorAt(0, QColor("#2196F3"))  # Blue
        gradient.setColorAt(0.5, QColor("#2196F3"))  # Blue
        gradient.setColorAt(0.7, QColor("#BBDEFB"))  # Light blue
        gradient.setColorAt(1, QColor(255, 255, 255, 0))  # Transparent
        
        # Draw spinner arc
        pen = QPen()
        pen.setBrush(gradient)
        pen.setWidth(spinner_width)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Draw arc (270 degrees, leaving 90 degrees gap)
        rect = QRectF(
            center_x - spinner_radius,
            center_y - spinner_radius,
            spinner_radius * 2,
            spinner_radius * 2
        )
        painter.drawArc(rect, self._spinner_angle * 16, 270 * 16)