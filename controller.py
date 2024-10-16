import ctypes
from time import sleep

# Simplified MouseInput struct definition
class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),   # Relative movement in X direction
                ("dy", ctypes.c_long),   # Relative movement in Y direction
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),  # Mouse movement flag
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class Input(ctypes.Structure):
    class _InputUnion(ctypes.Union):
        _fields_ = [("mi", MouseInput)]
    _anonymous_ = ("u",)
    _fields_ = [("type", ctypes.c_ulong), ("u", _InputUnion)]

# Constants for mouse input
INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001  # Only move the mouse, no other actions
MOUSEEVENTF_LEFTDOWN = 0x0002  # Left mouse button down
MOUSEEVENTF_LEFTUP = 0x0004    # Left mouse button up
MOUSEEVENTF_RIGHTDOWN = 0x0008 # Right mouse button down
MOUSEEVENTF_RIGHTUP = 0x0010   # Right mouse button up

class CrosshairMover:
    def __init__(self, mouse_delay=0.01):
        self.mouse_delay = mouse_delay
        self.extra = ctypes.c_ulong(0)

    def mouse_move(self, x, y, smoothing_factor=0.05):
        # Move the mouse by the provided x and y values
        rel_x, rel_y = int(x), int(y)

        # Smooth the movement by dividing it into smaller steps
        steps = max(abs(rel_x), abs(rel_y), 1)  # Ensure at least 1 step
        step_x = rel_x / steps
        step_y = rel_y / steps
        sleep_time = self.mouse_delay * smoothing_factor

        # Accumulate fractional movement
        accumulated_x, accumulated_y = 0.0, 0.0

        for _ in range(steps):
            # Accumulate the fractional part of the movement
            accumulated_x += step_x
            accumulated_y += step_y

            # Only move when we have a full step in either direction
            move_x = int(accumulated_x)
            move_y = int(accumulated_y)

            # Subtract the full steps that were moved from the accumulated values
            accumulated_x -= move_x
            accumulated_y -= move_y

            if move_x != 0 or move_y != 0:
                # Prepare mouse input for relative movement
                mi = MouseInput(move_x, move_y, 0, MOUSEEVENTF_MOVE, 0, ctypes.pointer(self.extra))

                # Create the Input object and specify that it's a mouse input
                input_obj = Input(type=INPUT_MOUSE)
                input_obj.mi = mi

                # Send the input using SendInput (Windows API)
                ctypes.windll.user32.SendInput(1, ctypes.byref(input_obj), ctypes.sizeof(input_obj))

            # Delay to mimic human-like behavior
            sleep(sleep_time)

    def click(self, button="left"):
        # Prepare mouse input for clicking action
        if button == "left":
            down_flag = MOUSEEVENTF_LEFTDOWN
            up_flag = MOUSEEVENTF_LEFTUP
        elif button == "right":
            down_flag = MOUSEEVENTF_RIGHTDOWN
            up_flag = MOUSEEVENTF_RIGHTUP
        else:
            raise ValueError("Invalid button. Use 'left' or 'right'.")

        # Click down
        self._send_click_event(down_flag)
        sleep(0.05)  # Small delay between down and up
        # Click up
        self._send_click_event(up_flag)

    def _send_click_event(self, flag):
        """Helper function to send mouse click events."""
        mi = MouseInput(0, 0, 0, flag, 0, ctypes.pointer(self.extra))

        input_obj = Input(type=INPUT_MOUSE)
        input_obj.mi = mi

        ctypes.windll.user32.SendInput(1, ctypes.byref(input_obj), ctypes.sizeof(input_obj))

    def interpolate_coordinates(self, target_pos):
        # Simple movement without scaling
        x, y = target_pos
        return [(x, y)]


# Example usage:
if __name__ == "__main__":
    mover = CrosshairMover(mouse_delay=0.01)

    # Smoothly move the mouse to a relative position
    mover.mouse_move(150, 200, smoothing_factor=0.1)

    # Perform a left mouse click
    mover.click("left")

    # Perform a right mouse click
    mover.click("right")
