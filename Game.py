#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Future reference
# https://forum.gamer.com.tw/C.php?bsn=2450&snA=1356

# Future work
# Add an edit button and update JSON data instead of only replacing it completely.

import pyautogui
import pydirectinput
import tkinter as tk
import tkinter.messagebox
import tkinter.font as tkfont
import win32api, win32con, win32gui
import threading
import time
import py_win_keyboard_layout
import os
import pygetwindow as gw
import cv2
import aircv as ac
import numpy as np
import copy
from PIL import Image
import math
import json
import sys
import tempfile


class SafeStream:
    """Buffers text writes until a real output stream is attached.

    In --windowed PyInstaller builds sys.stdout/sys.stderr are None, so any
    print() before the log widget exists would raise. This shim swallows those
    writes (or passes them to an initial console target) and replays buffered
    text into the log widget once attach() is called.
    """

    def __init__(self, target=None):
        self._target = target
        self._buffer = []

    def attach(self, target):
        self._target = target
        pending, self._buffer = self._buffer, []
        for chunk in pending:
            self._safe_write(chunk)
        self.flush()

    def _safe_write(self, message):
        try:
            self._target.write(message)
            return True
        except Exception:
            return False

    def write(self, message):
        if not message:
            return
        if self._target is not None and self._safe_write(message):
            return
        self._buffer.append(message)

    def flush(self):
        if self._target is None:
            return
        try:
            self._target.flush()
        except Exception:
            pass


sys.stdout = SafeStream(sys.stdout)
sys.stderr = SafeStream(sys.stderr)

APP_BG = "#08111f"
APP_BG_ALT = "#0d1b2f"
GLASS_BG = "#13243a"
GLASS_BG_ALT = "#182c45"
GLASS_BORDER = "#36506f"
TEXT_MAIN = "#f3f8ff"
TEXT_MUTED = "#9fb3c9"
ACCENT_CYAN = "#6ee7f9"
ACCENT_MINT = "#8cf5c6"
ACCENT_AMBER = "#f8d77a"
ACCENT_ROSE = "#ff8ea3"
BUTTON_DARK = "#203653"

def match(IMSRC, IMOBJ, threshold=0.8, debug=False):
    # Ensure images use three color channels.
    if len(IMSRC.shape) == 2:  # grayscale to BGR
        IMSRC = cv2.cvtColor(IMSRC, cv2.COLOR_GRAY2BGR)
    if len(IMOBJ.shape) == 2:  # grayscale to BGR
        IMOBJ = cv2.cvtColor(IMOBJ, cv2.COLOR_GRAY2BGR)

    pos = ac.find_template(IMSRC, IMOBJ, threshold=threshold, rgb=False)
    if pos is not None:
        if debug:
            print(f"Template matched. Confidence {pos['confidence']:.2f}, position: {pos['result']}")
        cv2.rectangle(IMSRC, pos['rectangle'][0], pos['rectangle'][3], (0, 0, 255), 2)
        return pos
    return None

def position_return(screenshot, compare_object: str, x_offset: int = 10, y_offset: int = 10):
    IMSRC=np.array(screenshot)
    # Find the matching template.
    IMOBJ=cv2.imread(compare_object)
    # print(type(IMOBJ))
    position = match(IMSRC,IMOBJ)
    if position is not None:
        x, y = position["result"]
        return int(x + x_offset), int(y + y_offset)
    else:
        return (None, None)
    
def mouseclick():
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

START_BUTTON_CENTER_X_RATIO = 58 / 551
START_BUTTON_CENTER_Y_RATIO = 479 / 500

def launcher_start_click_position(left, top, width, height):
    return (
        left + round(width * START_BUTTON_CENTER_X_RATIO),
        top + round(height * START_BUTTON_CENTER_Y_RATIO),
    )

def exact_window_by_title(title):
    for window in gw.getAllWindows():
        if window.title == title:
            return window
    return None

def launcher_window_rect(window):
    hwnd = getattr(window, "_hWnd", None)
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,
            0,
            0,
            0,
            0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW,
        )
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_NOTOPMOST,
            0,
            0,
            0,
            0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW,
        )
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        return left, top, right - left, bottom - top
    return window.left, window.top, window.width, window.height

def click_launcher_start_button(timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        launcher_window = exact_window_by_title(game_window_title)
        if launcher_window is not None:
            left, top, width, height = launcher_window_rect(launcher_window)
            x, y = launcher_start_click_position(left, top, width, height)
            pyautogui.moveTo(x, y)
            mouseclick()
            print("Clicked launcher START button.")
            return True
        time.sleep(1)
    print(f"Could not find launcher window titled '{game_window_title}'.")
    return False
    
# === Core: safe click with retries and confidence checks ===
def safe_click(img_path, retries=5, threshold=0.75, delay=0.5):
    resolved_img_path = resolve_asset_path(img_path)
    for attempt in range(retries):
        screenshot = pyautogui.screenshot()
        IMSRC = np.array(screenshot)
        IMOBJ = cv2.imread(resolved_img_path)
        pos = match(IMSRC, IMOBJ, threshold)
        if pos is not None:
            x, y = map(int, pos['result'])
            pyautogui.moveTo(x, y)
            mouseclick()
            print(f"Clicked {img_path}")
            time.sleep(delay)
            # Confirm that the clicked button disappeared.
            screenshot2 = pyautogui.screenshot()
            IMSRC2 = np.array(screenshot2)
            pos_check = match(IMSRC2, IMOBJ, threshold)
            if pos_check is None:
                print("Button disappeared; click confirmed.")
                return True
            else:
                print("Button is still visible; click may have failed. Retrying...")
        else:
            print(f"Attempt {attempt+1}: could not find {img_path}")
        time.sleep(1)
    print(f"Could not click {img_path} after multiple attempts.")
    return False

def account(account_group: str):
    account_number = 0
    account_index = 0
    if(account_group.__eq__("1")):
        account_number = 3
        account_index= 0
    elif(account_group.__eq__("2")):
        account_number = 4
        account_index = 3
    elif(account_group.__eq__("3")):
        account_number = 6
        account_index = 7
    elif(myaccountlist.curselection()):
        account_index = myaccountlist.curselection()[0]
        account_number = 1
    
    return account_number, account_index


def empty_list():
    global openlist
    global olderlist
    openlist = []
    olderlist = []
    alltitles = gw.getAllTitles()
    for t in alltitles:
        if game_window_title in t:
            openlist.append(t)
            olderlist.append(t)
    print(openlist)
    print(olderlist)

def account_credentials(index):
    """Return (account_name, password) from AccountList (the source of truth).

    Reading here instead of the on-screen listbox means display masking can
    never feed masked placeholders into the game login. An out-of-range index
    returns empty strings, matching the old listbox.get() behavior so a group
    that runs past the saved accounts fails the login instead of crashing.
    """
    if index >= len(AccountList):
        return "", ""
    data = AccountList[index]
    return data.account, data.password


def AutoOpen(account_group: str):
    account_number, account_index = account(account_group)
    # pyautogui.hotkey('winleft', 'd')

    empty_list()
    if account_number == 0:
        return
    
    for i in range(account_number):
        print(f"Starting account {i+1}")
        if not os.path.exists(application_path):
            message = f"Launcher not found: {application_path}"
            print(message)
            ui_call(lambda: tk.messagebox.showerror("Launcher not found", message))
            return
        os.startfile(application_path, cwd=os.path.dirname(application_path))
        time.sleep(3)

        # Step 1: Start the game from the Global launcher.
        if not click_launcher_start_button():
            print("Could not click launcher START button; skipping this account.")
            continue

        # Wait for the login screen.
        waited = 0
        while not safe_click("image/agree.png", retries=1) and waited < 60:
            time.sleep(3)
            waited += 3
        if waited >= 60:
            print("Timed out while waiting for agree.png; skipping this account.")
            continue

        # Step 2: Switch keyboard layout.
        py_win_keyboard_layout.change_foreground_window_keyboard_layout(0x04090409)

        # Step 3: Enter the account credentials.
        login_account, login_password = account_credentials(account_index)
        pyautogui.press('backspace', presses=15, interval=0.05)
        pyautogui.write(login_account)
        time.sleep(1)
        pydirectinput.press('tab')
        pyautogui.write(login_password)
        pyautogui.press("enter")
        time.sleep(3)
        pyautogui.press("enter")
        time.sleep(3)
        pyautogui.press("enter")

        # Step 4: Enter the secondary password.
        if account_index < len(AccountList) and AccountList[account_index].second_password:
            pyautogui.write(AccountList[account_index].second_password)
        pyautogui.press("enter")
        pyautogui.press("enter")

        time.sleep(4)
        
        # Step 5: Detect the new game window.
        alltitles = gw.getAllTitles()
        global openlist, olderlist
        for t in alltitles:
            if game_window_title in t:
                openlist.append(t)
        now_window_list = list(set(openlist) - set(olderlist))
        openlist = list(set(openlist))
        olderlist = copy.deepcopy(openlist)
        now_window_name = gw.getWindowsWithTitle(now_window_list[0])[0]

        # Step 6: Enable auto attack.
        safe_click("image/attackpage1.png", retries=8)
        safe_click("image/autoattack.png", retries=8)

        # Step 7: Arrange the window.
        try:
            if account_group in ["2", "3"]:
                if i == 0:
                    now_window_name.moveTo(int(screen_width/25), int(screen_height/25))
                elif i == 1:
                    now_window_name.moveTo(int(screen_width/25 + now_window_name.width), int(screen_height/25))
                elif i == 2:
                    now_window_name.moveTo(int(screen_width/25), int(screen_height/25 + now_window_name.height))
                elif i == 3:
                    now_window_name.moveTo(int(screen_width/25 + now_window_name.width), int(screen_height/25 + now_window_name.height))
            now_window_name.minimize()
        except Exception as e:
            print(f"Failed to move the window: {e}")
        time.sleep(2)
        account_index += 1

    empty_list()
  
def get_mouse_pos():
    mouse_position.config(text='Mouse position: {}, {}'.format(*root.winfo_pointerxy()))
    root.after(100, get_mouse_pos)

def exe_time(loop):    
    if loop=="2":
        count = 5
    else:
        count = 1
    clicktreasure(count)

def clicktreasure(count):
    # Get the current windows.
    alltitles = gw.getAllTitles()
    i = 1
    while i <= count:
        for t in alltitles:
            if game_window_title in t:
                print(f'now window = {t}')
                now_window_name = gw.getWindowsWithTitle(t[0])[0]
                now_window_name.restore()
                now_window_name.activate()
                time.sleep(1)

                shot = pyautogui.screenshot(region=[now_window_name.left, now_window_name.top, now_window_name.width, now_window_name.height]) # x,y,w,h
                open_cv_image_np = np.array(shot)
                IMSRC=open_cv_image_np
                # Find the matching template.
                IMOBJ=cv2.imread(resource_path("image", "time.png"))
                position = match(IMSRC,IMOBJ)

                count_num = 0
                while position is None:
                    time.sleep(1)
                    shot = pyautogui.screenshot(region=[now_window_name.left, now_window_name.top, now_window_name.width, now_window_name.height]) # x,y,w,h
                    open_cv_image_np = np.array(shot)
                    IMSRC=open_cv_image_np
                    # Find the matching template.
                    IMOBJ=cv2.imread(resource_path("image", "time.png"))
                    position = match(IMSRC,IMOBJ)
                    count_num+=1

                    if count_num > 50:
                        print("Reward timer icon was not found in this window; skipping it.")
                        break
                
                if position is None:
                    now_window_name.minimize()
                    i+=1
                    continue

                position_xy = str(position[0]).replace('(', '').replace(')', "").split(", ")

                # Target mouse position.
                x = now_window_name.left + int(position_xy[0]) + 10
                y = now_window_name.top + int(position_xy[1]) + 10

                startPosition = (x, y)
                pyautogui.moveTo(startPosition)
                mouseclick()

                now_window_name.minimize()
                i+=1
        print("done")
        if count!=1:
            time.sleep(600)

def refresh():
    print("refresh")
    alltitles = gw.getAllTitles()

    myrefreshlist.delete(0, tk.END)
    for t in alltitles:
        if game_window_title in t:
            myrefreshlist.insert(tk.END, t)
    myrefreshlist.config(width=0)
    myrefreshlist.select_set(0)


dirname = os.path.dirname(os.path.abspath(__file__))

def resource_path(*parts):
    base_path = getattr(sys, "_MEIPASS", dirname)
    return os.path.join(base_path, *parts)

def config_path(name):
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), name)
    return os.path.join(dirname, name)

def resolve_asset_path(path):
    if os.path.isabs(path):
        return path
    return resource_path(*path.replace("\\", "/").split("/"))

def write_json_atomic(path, data, indent=4):
    """Serialize data to path atomically.

    Writes to a temp file in the same directory, then os.replace()s it over the
    target. A failure mid-serialize leaves the existing target untouched instead
    of truncating it to an empty/partial file that crashes the next startup.
    """
    directory = os.path.dirname(path) or "."
    tmp = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=directory, delete=False, suffix=".tmp"
    )
    try:
        with tmp:
            json.dump(data, tmp, indent=indent)
        os.replace(tmp.name, path)
    except BaseException:
        try:
            os.remove(tmp.name)
        except OSError:
            pass
        raise

application_path = r"C:\UserJoy\Angels Online Global\START.EXE"
game_window_title = "Angels Online Global"

def load_start_config():
    start_game_file = config_path('start_game.json')
    if not os.path.exists(start_game_file):
        start_game_file = resource_path('start_game.json')

    try:
        with open(start_game_file, encoding="utf-8") as f:
            start_config = json.load(f)
    except (OSError, ValueError):
        return application_path, game_window_title

    if not start_config:
        return application_path, game_window_title

    first_config = start_config[0]
    return (
        first_config.get('application_path', application_path),
        first_config.get('window_title', game_window_title),
    )

def launcher_path_is_valid(path):
    """True when path points at an existing file on disk (the START.EXE)."""
    return bool(path) and os.path.isfile(path)

def count_matching_titles(titles, needle):
    """Count window titles that contain needle. Empty needle matches nothing."""
    if not needle:
        return 0
    return sum(1 for title in titles if needle in title)

def open_game_window_count():
    """Number of currently open windows whose title matches the game."""
    return count_matching_titles(gw.getAllTitles(), game_window_title)

def saved_account_count():
    """Number of accounts currently held in memory."""
    return len(AccountList)

labels = [',', 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

_onnx_session = None
_onnx_input_name = None
ml_ready = False


def ensure_model_loaded():
    """Lazily load the ONNX model. Returns True if inference is available."""
    global _onnx_session, _onnx_input_name, ml_ready
    if _onnx_session is not None:
        return True
    try:
        import onnxruntime as ort

        session = ort.InferenceSession(
            resource_path("my_model.onnx"), providers=["CPUExecutionProvider"]
        )
        _onnx_session = session
        _onnx_input_name = session.get_inputs()[0].name
        ml_ready = True
    except Exception as exc:
        ml_ready = False
        print(f"Machine learning model unavailable: {exc}")
    return ml_ready


def label_from_prediction(prediction):
    """Map a model output vector to its label via the digit label table."""
    return labels[int(np.argmax(prediction))]

def find_now_position(gwcontent):
    # Use the current game position.
    # crop image
    center_x = int(gwcontent.left + gwcontent.width/2) - 1
    center_y = int(gwcontent.top + gwcontent.height/2) -1 + 18

    shot = pyautogui.screenshot(region=[gwcontent.right - gwcontent.width * 1 / 6 + 60, gwcontent.top + 130, 55, 13]) # x,y,w,h
    # shotfile = os.path.join(base_path, str(uuid.uuid4()) + '.png')
    # shot.save(shotfile)
    open_cv_image = np.array(shot)
    # Convert RGB to BGR 
    open_cv_image = open_cv_image[:, :, ::-1].copy()

    img_gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
    # apply binary thresholding
    ret, thresh = cv2.threshold(img_gray, 150, 255, cv2.THRESH_BINARY)                        
    # draw contours on the original image
    image_copy = open_cv_image.copy()
    contours, hierarchy = cv2.findContours(image=thresh, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
    print("---")

    height = 30
    width = 30

    results = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        crop_img = image_copy[y:y+h, x:x+w]
            
        top = math.ceil((height - h) / 2)
        left = math.ceil((width - w) / 2)
        bottom = top
        right = left
            
        if (top * 2) + h > height:
            top = top - 1
        if (left * 2) + w > width:
            left = left - 1
            
        a =  cv2.copyMakeBorder(crop_img, top, bottom, left, right, cv2.BORDER_CONSTANT,value=[132,121,8])

        color_coverted = cv2.cvtColor(a, cv2.COLOR_BGR2RGB)
        a=Image.fromarray(color_coverted)
        a = np.expand_dims(a, axis=0) # convert channels
            
        a = a.astype(np.float32)
        pred = _onnx_session.run(None, {_onnx_input_name: a})[0][0]
        prediction = label_from_prediction(pred)
        results.append((x, prediction))
        
    results.sort(key = lambda s: s[0])
    my_lst_str = ''.join(str(results[i][1]) for i in range(len(results)))
    x = my_lst_str.split(",")
    
    return int(x[0]), int(x[1]), center_x, center_y
    
def go_target(target_x, target_y, now_x:int, now_y:int, center_x, center_y, now_window_name):
    count = 1
    while(abs(now_x - target_x) > 3):
        mouse_x = center_x
        mouse_y = center_y
        if now_x > target_x:
            mouse_x -= 40
            print("Move left")
        elif now_x < target_x:
            mouse_x += 40
            print("Move right")
        else:
            print("No movement needed")
            
        difference = target_x - now_x        
        count_loop = math.ceil(abs(difference / 3))
        print(f'Execution count {count_loop}')
        j = 1
        while(j <= count_loop):            
            pyautogui.moveTo(mouse_x, mouse_y)
            mouseclick()
            time.sleep(2)
            j+=1
        now_x, now_y, center_x, center_y = find_now_position(now_window_name)
        count += 1
        
        if count > 8:
            print("break")
            break        
        
        print(mouse_x, mouse_y)
        time.sleep(3)
        
    count = 1
    while(abs(now_y - target_y) > 3):
        mouse_x = center_x
        mouse_y = center_y
                    
        if now_y > target_y:
            mouse_y += 35
            print("Move down")
        elif now_y < target_y:
            mouse_y -= 35
            print("Move up")
        else:
            print("No movement needed")
            
        difference = target_y - now_y        
        count_loop = math.ceil(abs(difference / 3))
        print(f'Execution count {count_loop}')   
        j = 1
        while(j <= count_loop):            
            pyautogui.moveTo(mouse_x, mouse_y)
            mouseclick()
            time.sleep(2)
            j+=1
        now_x, now_y, center_x, center_y = find_now_position(now_window_name)
        count += 1
        
        if count > 8:
            print("break")
            break
        
        print(mouse_x, mouse_y)
        time.sleep(3)
        
    print("done")

def autopilot():
    if not ensure_model_loaded():
        print("Navigation model unavailable; Auto Navigate is disabled.")
        ui_call(lambda: tk.messagebox.showinfo(
            "ML unavailable",
            "The navigation model could not be loaded, so Auto Navigate is disabled.",
        ))
        return
    try:
        # Get the selected game window.
        now_window_name = gw.getWindowsWithTitle(myrefreshlist.get(myrefreshlist.curselection()))[0]
        now_window_name.restore()
        now_window_name.activate()
        time.sleep(1)

        # Disable auto combat.
        pydirectinput.keyDown("alt")
        pydirectinput.press("d")
        pydirectinput.keyUp("alt")
        time.sleep(2)

        # Read the current position.
        x, y, center_x, center_y = find_now_position(now_window_name)

        # Move toward the target.
        position = mypgotargetlist.get(mypgotargetlist.curselection())
        position = position.split(", ")
        go_target(int(position[0]), int(position[1]), x, y, center_x, center_y, now_window_name)
    except Exception as exc:
        print(f"Auto navigate failed: {exc}")
        
# custom class
class AccountData:
    def __init__(self, account, password, second_password="", trade_password=""):
        self.account = account
        self.password = password
        self.second_password = second_password
        self.trade_password = trade_password
        
global AccountList
AccountList = []

PASSWORD_MASK = "••••••••"
passwords_revealed = False


def mask_password(password):
    """Return a fixed-width dot mask, or empty string for empty passwords."""
    return PASSWORD_MASK if password else ""


def render_password_list():
    """Rebuild the password listbox from AccountList, masked unless revealed."""
    mypasswordlist.delete(0, tk.END)
    for data in AccountList:
        shown = data.password if passwords_revealed else mask_password(data.password)
        mypasswordlist.insert(tk.END, shown)


def set_passwords_revealed(revealed):
    """Set whether saved passwords show as plaintext, then refresh the list."""
    global passwords_revealed
    passwords_revealed = revealed
    render_password_list()


def toggle_password_visibility():
    set_passwords_revealed(not passwords_revealed)
    reveal_button.config(
        text="Hide passwords" if passwords_revealed else "Show passwords"
    )


def make_password_field(parent):
    """A masked entry with a small inline eye that reveals just this field."""
    container = tk.Frame(parent, bg=GLASS_BG)
    container.columnconfigure(0, weight=1)
    entry = glass_entry(container, show="•")
    entry.grid(row=0, column=0, sticky="ew")
    eye = tk.Button(
        container,
        text="Show",
        bd=0,
        relief="flat",
        bg=APP_BG_ALT,
        fg=ACCENT_CYAN,
        activebackground=APP_BG_ALT,
        activeforeground=ACCENT_AMBER,
        cursor="hand2",
        font=("Segoe UI Emoji", 9),
    )

    def toggle():
        revealed = entry.cget("show") == ""
        entry.config(show="•" if revealed else "")
        eye.config(text="Show" if revealed else "Hide")

    eye.config(command=toggle)
    eye.grid(row=0, column=1, padx=(4, 0))
    return container, entry


def add_account_data(account_data, update_ui=True):
    AccountList.append(account_data)
    if update_ui:
        myaccountlist.insert(tk.END, account_data.account)
        render_password_list()

def clear_account_inputs():
    for entry in (input_account, input_password, input_second_password, input_trade_password):
        entry.delete(0, tk.END)

def savedata():
    # Check that both account and password were entered.
    if(input_account.get()!="" and input_password.get()!=""):
        test = AccountData(input_account.get(), input_password.get(), input_second_password.get(), input_trade_password.get())
        add_account_data(test)
        clear_account_inputs()
        print(f"Saved account: {test.account}")
    else:
        tk.messagebox.showinfo("Missing credentials", "Please enter both an account and a password.")
    

def outputdata():
    print("output")
    global AccountList
    
    data_file = config_path("data.json")
    file_exists  = os.path.exists(data_file)
    if file_exists:
        result = tk.messagebox.askokcancel(title = 'Overwrite data?',message='A data file already exists in this folder. Do you want to completely overwrite it?')
        if not result:
            return

    # Existing data will be overwritten after confirmation.
    payload = [z.__dict__ for z in AccountList]
    write_json_atomic(data_file, payload)
    print(json.dumps(payload))
        
def validate(P):
    print(P)
    if str.isdigit(P) or P == '':
        return True
    else:
        return False
    
def listbox_event(event):
    object = event.widget
    # print(type(object.curselection()))
    index = object.curselection()
    # mylabel.configure(text=object.get(index))

root = None  # the Tk root, assigned to tk.Tk() at startup

def ui_call(callback):
    """Run a callback on the Tkinter main thread, safe from worker threads."""
    if root is None:
        callback()
        return
    try:
        root.after(0, callback)
    except tk.TclError:
        callback()

class TextRedirector:
    def __init__(self, widget):
        self.widget = widget

    def write(self, message):
        if not message:
            return
        try:
            self.widget.after(0, self._append, message)
        except tk.TclError:
            pass

    def _append(self, message):
        try:
            self.widget.configure(state="normal")
            self.widget.insert(tk.END, message)
            self.widget.see(tk.END)
            self.widget.configure(state="disabled")
        except tk.TclError:
            pass

    def flush(self):
        pass

class Tooltip:
    """One hover tooltip shared across a widget and all of its descendants.

    Card-style buttons are a frame wrapping child labels. Binding a separate
    tooltip per widget is wrong: entering a child directly from outside fires
    Enter on both the parent (NotifyVirtual) and the child, so two boxes appear
    at once. Instead, a single instance binds every widget in the group, guards
    on one shared tip window, and debounces hiding so a parent->child crossing
    (Leave then Enter) cancels the pending hide instead of flickering.
    """

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        self._hide_job = None
        self._bind(widget)

    def _bind(self, widget):
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        for child in widget.winfo_children():
            self._bind(child)

    def _on_enter(self, _event=None):
        if self._hide_job is not None:
            self.widget.after_cancel(self._hide_job)
            self._hide_job = None
        self._show()

    def _on_leave(self, _event=None):
        if self._hide_job is not None:
            self.widget.after_cancel(self._hide_job)
        self._hide_job = self.widget.after(120, self._hide)

    def _show(self):
        if self.tip or not self.text:
            return
        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self.tip,
            text=self.text,
            bg="#0b1526",
            fg=TEXT_MAIN,
            font=("Segoe UI", 9),
            justify="left",
            wraplength=320,
            padx=8,
            pady=6,
            highlightbackground=GLASS_BORDER,
            highlightthickness=1,
        ).pack()

    def _hide(self):
        self._hide_job = None
        if self.tip:
            self.tip.destroy()
            self.tip = None


def attach_tooltip(widget, text):
    """Attach one shared hover tooltip to a widget and every descendant."""
    Tooltip(widget, text)


def open_launcher_editor():
    """Edit the launcher path / window title and persist to start_game.json."""
    global application_path, game_window_title
    dialog = tk.Toplevel(root)
    dialog.title("Edit linked install")
    dialog.configure(bg=APP_BG, padx=16, pady=14)
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()

    glass_label(dialog, "Launcher path (START.EXE)", muted=True, bg=APP_BG).pack(fill="x")
    path_entry = glass_entry(dialog)
    path_entry.insert(0, application_path)
    path_entry.pack(fill="x", pady=(2, 10))
    path_entry.config(width=60)

    glass_label(dialog, "Window title to match", muted=True, bg=APP_BG).pack(fill="x")
    title_entry = glass_entry(dialog)
    title_entry.insert(0, game_window_title)
    title_entry.pack(fill="x", pady=(2, 12))

    def save():
        global application_path, game_window_title
        application_path = path_entry.get().strip() or application_path
        game_window_title = title_entry.get().strip() or game_window_title
        write_json_atomic(
            config_path("start_game.json"),
            [{"application_path": application_path, "window_title": game_window_title}],
        )
        link_path_label.config(text=f"Launcher: {application_path}")
        link_title_label.config(text=f"Window title match: {game_window_title}")
        update_link_status()
        print(f"Updated launcher path to: {application_path}")
        dialog.destroy()

    glass_button(dialog, "Save", save, ACCENT_MINT).pack(fill="x")


def update_link_status():
    """Refresh the Linked Install panel's valid/invalid launcher indicator."""
    if launcher_path_is_valid(application_path):
        link_status_label.config(
            text="✓ Launcher found at this path.", fg=ACCENT_MINT
        )
    else:
        link_status_label.config(
            text="✗ Launcher not found - click Edit Launcher Path and set the correct START.EXE.",
            fg=ACCENT_ROSE,
        )


def confirm_and_run(title, summary, steps, requirements, run, run_label="Proceed"):
    """Glass-themed preview modal shown before an impactful action runs.

    requirements is a list of (label, met) pairs shown with a green check or a
    red cross. Unmet requirements are a warning, not a block: Proceed is always
    available so the user can override, but they always see the explanation and
    what is missing first.
    """
    all_met = all(met for _label, met in requirements)

    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.configure(bg=APP_BG)
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()

    tk.Frame(dialog, bg=ACCENT_CYAN, height=2, bd=0).pack(fill="x", side="top")
    body = tk.Frame(dialog, bg=APP_BG, padx=20, pady=18)
    body.pack(fill="both", expand=True)

    tk.Label(
        body, text=title, bg=APP_BG, fg=TEXT_MAIN,
        font=("Segoe UI Semibold", 14), anchor="w", justify="left",
    ).pack(fill="x")
    tk.Label(
        body, text=summary, bg=APP_BG, fg=TEXT_MUTED, font=("Segoe UI", 10),
        anchor="w", justify="left", wraplength=440,
    ).pack(fill="x", pady=(4, 14))

    if steps:
        tk.Label(
            body, text="What will happen", bg=APP_BG, fg=ACCENT_CYAN,
            font=("Segoe UI Semibold", 10), anchor="w",
        ).pack(fill="x")
        for number, step in enumerate(steps, start=1):
            tk.Label(
                body, text=f"{number}. {step}", bg=APP_BG, fg=TEXT_MAIN,
                font=("Segoe UI", 9), anchor="w", justify="left", wraplength=440,
            ).pack(fill="x", pady=1)

    if requirements:
        tk.Label(
            body, text="Requirements", bg=APP_BG, fg=ACCENT_CYAN,
            font=("Segoe UI Semibold", 10), anchor="w",
        ).pack(fill="x", pady=(12, 2))
        for label, met in requirements:
            row = tk.Frame(body, bg=APP_BG)
            row.pack(fill="x", pady=1)
            tk.Label(
                row, text="✓" if met else "✗", bg=APP_BG,
                fg=ACCENT_MINT if met else ACCENT_ROSE,
                font=("Segoe UI Semibold", 10), width=2, anchor="w",
            ).pack(side="left")
            tk.Label(
                row, text=label, bg=APP_BG, fg=TEXT_MAIN, font=("Segoe UI", 9),
                anchor="w", justify="left", wraplength=410,
            ).pack(side="left", fill="x", expand=True)

    if all_met:
        status_text = "All requirements met. Click " + run_label + " to start."
        status_color = ACCENT_MINT
        proceed_accent = ACCENT_MINT
    else:
        status_text = (
            "Heads up: the items marked with a red cross are not met, so this "
            "may not work. You can still proceed if you want to try."
        )
        status_color = ACCENT_AMBER
        proceed_accent = ACCENT_AMBER
    tk.Label(
        body, text=status_text, bg=APP_BG, fg=status_color, font=("Segoe UI", 9),
        anchor="w", justify="left", wraplength=440,
    ).pack(fill="x", pady=(14, 12))

    button_row = tk.Frame(body, bg=APP_BG)
    button_row.pack(fill="x")

    def proceed():
        dialog.destroy()
        run()

    glass_button(button_row, run_label, proceed, proceed_accent).pack(side="right")
    glass_button(button_row, "Cancel", dialog.destroy, GLASS_BORDER).pack(
        side="right", padx=(0, 8)
    )


def _launcher_requirement():
    return (
        f"Launcher exists at {application_path}",
        launcher_path_is_valid(application_path),
    )


def preview_open_group(account_group, title, summary, run):
    """Preview + gate one of the Launch buttons before AutoOpen runs."""
    requirements = [_launcher_requirement()]
    if account_group == " ":
        requirements.append(
            ("An account is selected in the vault", bool(myaccountlist.curselection()))
        )
    else:
        number, index = account(account_group)
        requirements.append(
            (
                f"{index + number} or more accounts saved (this group uses "
                f"accounts {index + 1}-{index + number})",
                saved_account_count() >= index + number,
            )
        )
    confirm_and_run(
        title=title,
        summary=summary,
        steps=[
            "Launch START.EXE once for each account in this group.",
            "Click the Global launcher's START button.",
            "Accept the prompt, set the keyboard layout, and type each login.",
            "Open the attack page and turn on Auto Attack.",
            "Tile and minimize each game window.",
        ],
        requirements=requirements,
        run=run,
        run_label="Launch now",
    )


def preview_claim(loop, run):
    """Preview + gate the Claim buttons before exe_time runs."""
    if loop == "2":
        summary = "Claim the reward timer in every open game window, then repeat on a loop."
        steps = [
            "Find every open Angels Online window.",
            "Restore and focus each window in turn.",
            "Screenshot it and locate the reward timer icon.",
            "Click the icon to claim, then minimize the window.",
            "Wait 10 minutes and repeat (5 passes total).",
        ]
    else:
        summary = "Claim the reward timer once in every open game window."
        steps = [
            "Find every open Angels Online window.",
            "Restore and focus each window in turn.",
            "Screenshot it and locate the reward timer icon.",
            "Click the icon to claim, then minimize the window.",
        ]
    confirm_and_run(
        title="Claim Rewards",
        summary=summary,
        steps=steps,
        requirements=[("At least one game window is open", open_game_window_count() >= 1)],
        run=run,
        run_label="Claim now",
    )


def preview_auto_navigate(run):
    """Preview + gate Auto Navigate before autopilot runs."""
    confirm_and_run(
        title="Auto Navigate",
        summary="Read your character's on-screen coordinates and walk the selected window to the chosen target.",
        steps=[
            "Restore and focus the selected game window.",
            "Turn off auto-combat so the character can move.",
            "Read the current coordinates with the bundled model.",
            "Click toward the selected target until it is reached.",
        ],
        requirements=[
            ("Navigation model is ready", bool(ml_ready)),
            ("A game window is selected (use Refresh first)", bool(myrefreshlist.curselection())),
            ("A navigation target is selected", bool(mypgotargetlist.curselection())),
        ],
        run=run,
        run_label="Navigate now",
    )


def preview_write_data(run):
    """Preview + gate Save Accounts to Disk before outputdata runs."""
    confirm_and_run(
        title="Save Accounts to Disk",
        summary="Write every saved account to data.json so they load automatically next launch.",
        steps=[
            f"Write {saved_account_count()} account(s) to {config_path('data.json')}.",
            "If data.json already exists, you will confirm the overwrite next.",
        ],
        requirements=[("At least one account is in the vault", saved_account_count() >= 1)],
        run=run,
        run_label="Write file",
    )


def configure_window(root):
    root.title('Angels Online Helper')
    root.geometry('1240x780')
    root.minsize(960, 600)
    root.configure(bg=APP_BG)
    try:
        root.attributes("-alpha", 0.98)
    except tk.TclError:
        pass
    try:
        root.iconbitmap(resource_path("angel.ico"))
    except Exception:
        pass
    # Row 0 holds the fixed header; row 1 holds the scrollable body that expands.
    root.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)

def glass_panel(parent, title, icon="", accent=ACCENT_CYAN, description="", info=""):
    outer = tk.Frame(
        parent,
        bg=GLASS_BG,
        highlightbackground=GLASS_BORDER,
        highlightthickness=1,
        bd=0,
    )
    tk.Frame(outer, bg=accent, height=2, bd=0).pack(fill="x", side="top")
    inner = tk.Frame(outer, bg=GLASS_BG, padx=14, pady=12)
    inner.pack(fill="both", expand=True)

    header = tk.Frame(inner, bg=GLASS_BG)
    header.pack(fill="x")
    label_text = f"{icon}  {title}".strip()
    tk.Label(
        header,
        text=label_text,
        bg=GLASS_BG,
        fg=TEXT_MAIN,
        font=("Segoe UI Semibold", 11),
        anchor="w",
    ).pack(side="left")
    if info:
        marker = tk.Label(
            header,
            text="ⓘ",
            bg=GLASS_BG,
            fg=TEXT_MUTED,
            font=("Segoe UI Symbol", 10),
            cursor="hand2",
        )
        marker.pack(side="right")
        Tooltip(marker, info)

    if description:
        tk.Label(
            inner,
            text=description,
            bg=GLASS_BG,
            fg=TEXT_MUTED,
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            wraplength=520,
        ).pack(fill="x", pady=(2, 8))
    else:
        tk.Frame(inner, bg=GLASS_BG, height=8).pack(fill="x")

    body = tk.Frame(inner, bg=GLASS_BG)
    body.pack(fill="both", expand=True)
    return outer, body

def glass_label(parent, text, muted=False, **kwargs):
    return tk.Label(
        parent,
        text=text,
        bg=kwargs.pop("bg", GLASS_BG),
        fg=TEXT_MUTED if muted else TEXT_MAIN,
        font=kwargs.pop("font", ("Segoe UI", 10)),
        anchor=kwargs.pop("anchor", "w"),
        justify=kwargs.pop("justify", "left"),
        **kwargs,
    )

def glass_button(parent, text, command, accent=ACCENT_CYAN):
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=BUTTON_DARK,
        fg=TEXT_MAIN,
        activebackground=accent,
        activeforeground="#08111f",
        relief="flat",
        bd=0,
        padx=12,
        pady=10,
        cursor="hand2",
        font=("Segoe UI Semibold", 10),
        highlightthickness=1,
        highlightbackground=GLASS_BORDER,
    )

def glass_action_button(parent, label, sublabel, command, accent=ACCENT_CYAN):
    """A clickable card with a bold label and a muted explanatory sub-label."""
    card = tk.Frame(
        parent,
        bg=BUTTON_DARK,
        highlightthickness=1,
        highlightbackground=GLASS_BORDER,
        cursor="hand2",
    )
    top = tk.Label(
        card,
        text=label,
        bg=BUTTON_DARK,
        fg=TEXT_MAIN,
        font=("Segoe UI Semibold", 10),
        anchor="w",
    )
    top.pack(fill="x", padx=12, pady=(8, 0))
    sub = tk.Label(
        card,
        text=sublabel,
        bg=BUTTON_DARK,
        fg=TEXT_MUTED,
        font=("Segoe UI", 8),
        anchor="w",
    )
    sub.pack(fill="x", padx=12, pady=(0, 8))

    def on_enter(_event=None):
        for widget in (card, top, sub):
            widget.config(bg=accent)
        top.config(fg="#08111f")
        sub.config(fg="#08111f")

    def on_leave(_event=None):
        for widget in (card, top, sub):
            widget.config(bg=BUTTON_DARK)
        top.config(fg=TEXT_MAIN)
        sub.config(fg=TEXT_MUTED)

    def on_click(_event=None):
        command()

    for widget in (card, top, sub):
        widget.bind("<Button-1>", on_click)
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    return card


def set_ml_status(ready):
    """Update the header ML status chip from the model load result."""
    if ready:
        ml_status.config(text="● ML model ready", fg=ACCENT_MINT)
    else:
        ml_status.config(text="● ML unavailable", fg=ACCENT_ROSE)


def glass_entry(parent, show=""):
    return tk.Entry(
        parent,
        bg=APP_BG_ALT,
        fg=TEXT_MAIN,
        insertbackground=ACCENT_CYAN,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=GLASS_BORDER,
        highlightcolor=ACCENT_CYAN,
        font=("Segoe UI", 10),
        show=show,
    )

def glass_listbox(parent, height=5):
    return tk.Listbox(
        parent,
        exportselection=0,
        bg=APP_BG_ALT,
        fg=TEXT_MAIN,
        selectbackground=ACCENT_CYAN,
        selectforeground="#08111f",
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=GLASS_BORDER,
        font=("Cascadia Mono", 9),
        height=height,
    )

def glass_text(parent, height=8):
    return tk.Text(
        parent,
        bg="#07101d",
        fg=ACCENT_MINT,
        insertbackground=ACCENT_CYAN,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=GLASS_BORDER,
        font=("Cascadia Mono", 9),
        height=height,
        state="disabled",
        wrap="word",
    )
    
    
if __name__ == '__main__':    

    application_path, game_window_title = load_start_config()

    openlist = []
    olderlist = []
    alltitles = gw.getAllTitles()
    for t in alltitles:
        if game_window_title in t:
            openlist.append(t)
            olderlist.append(t)

    print(openlist)
    print(olderlist)


    root = tk.Tk()
    configure_window(root)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    def run_async(target, *args):
        threading.Thread(target=target, args=args, daemon=True).start()

    header = tk.Frame(root, bg=APP_BG, padx=18, pady=14)
    header.grid(row=0, column=0, columnspan=2, sticky="ew")
    header.columnconfigure(0, weight=1)

    tk.Label(
        header,
        text="Angels Online Helper",
        bg=APP_BG,
        fg=TEXT_MAIN,
        font=("Segoe UI Semibold", 22),
        anchor="w",
    ).grid(row=0, column=0, sticky="w")

    mouse_position = tk.Label(
        header,
        text="Mouse position",
        bg=APP_BG,
        fg=ACCENT_CYAN,
        font=("Cascadia Mono", 9),
        anchor="e",
    )
    mouse_position.grid(row=0, column=1, sticky="e")
    ml_status = tk.Label(
        header,
        text="● ML model loading…",
        bg=APP_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 9),
        anchor="e",
    )
    ml_status.grid(row=1, column=1, sticky="e")
    Tooltip(
        ml_status,
        "Status of the bundled navigation model. 'ML model ready' means the "
        "coordinate-reading model loaded, so Auto Navigate can read your "
        "character's on-screen position. 'ML unavailable' means it failed to "
        "load and Auto Navigate is disabled.",
    )
    get_mouse_pos()

    # Scrollable body: the panels live in `content`, embedded in a canvas so the
    # window stays usable on short screens instead of clipping the lower panels.
    scroll_canvas = tk.Canvas(root, bg=APP_BG, highlightthickness=0, bd=0)
    scroll_canvas.grid(row=1, column=0, sticky="nsew")
    scrollbar = tk.Scrollbar(root, orient="vertical", command=scroll_canvas.yview)
    scrollbar.grid(row=1, column=1, sticky="ns")
    scroll_canvas.configure(yscrollcommand=scrollbar.set)

    content = tk.Frame(scroll_canvas, bg=APP_BG)
    content_id = scroll_canvas.create_window((0, 0), window=content, anchor="nw")
    for col in range(12):
        content.columnconfigure(col, weight=1, uniform="main")

    def _sync_scrollregion(_event=None):
        scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))

    def _stretch_content(event):
        scroll_canvas.itemconfigure(content_id, width=event.width)

    def _scroll_with_wheel(event):
        scroll_canvas.yview_scroll(int(-event.delta / 120), "units")

    def _bind_inner_wheel(widget):
        # Let a scrollable child consume the wheel so the page does not also move.
        def _inner(event):
            widget.yview_scroll(int(-event.delta / 120), "units")
            return "break"
        widget.bind("<MouseWheel>", _inner)

    content.bind("<Configure>", _sync_scrollregion)
    scroll_canvas.bind("<Configure>", _stretch_content)
    scroll_canvas.bind_all("<MouseWheel>", _scroll_with_wheel)

    link_frame, link_body = glass_panel(
        content, "Linked Install", "◇", accent=ACCENT_CYAN,
        description="The game launcher and window this helper drives.",
        info="The helper launches this START.EXE and waits for a window whose title matches the text below.",
    )
    link_frame.grid(row=1, column=0, columnspan=12, sticky="ew", padx=16, pady=(0, 10))
    link_path_label = glass_label(link_body, f"Launcher: {application_path}", muted=True)
    link_path_label.pack(fill="x")
    link_title_label = glass_label(link_body, f"Window title match: {game_window_title}", muted=True)
    link_title_label.pack(fill="x")
    link_status_label = glass_label(link_body, "", muted=True)
    link_status_label.pack(fill="x", pady=(6, 0))
    edit_link_button = glass_button(link_body, "✎ Edit Launcher Path", open_launcher_editor, ACCENT_CYAN)
    edit_link_button.pack(anchor="w", pady=(8, 0))
    attach_tooltip(
        edit_link_button,
        "Set where the game is installed. Enter the full path to START.EXE and "
        "the window title the helper should wait for. Saved to start_game.json.",
    )
    update_link_status()

    accounts_frame, accounts_body = glass_panel(
        content, "Account Vault", "▣", accent=ACCENT_MINT,
        description="Saved logins. Passwords stay hidden until you reveal them.",
        info="Save adds an account to the list now; Write data.json stores the whole list for next launch.",
    )
    accounts_frame.grid(row=2, column=0, columnspan=7, sticky="nsew", padx=(16, 8), pady=8)
    accounts_body.columnconfigure(0, weight=1)
    accounts_body.columnconfigure(1, weight=1)

    glass_label(accounts_body, "Accounts", muted=True).grid(row=0, column=0, sticky="w")
    password_header = tk.Frame(accounts_body, bg=GLASS_BG)
    password_header.grid(row=0, column=1, sticky="ew", padx=(8, 0))
    password_header.columnconfigure(0, weight=1)
    glass_label(password_header, "Passwords", muted=True).grid(row=0, column=0, sticky="w")
    reveal_button = tk.Button(
        password_header,
        text="Show passwords",
        command=toggle_password_visibility,
        bd=0,
        relief="flat",
        bg=APP_BG_ALT,
        fg=ACCENT_CYAN,
        activebackground=APP_BG_ALT,
        activeforeground=ACCENT_AMBER,
        cursor="hand2",
        font=("Segoe UI", 8),
    )
    reveal_button.grid(row=0, column=1, sticky="e")
    myaccountlist = glass_listbox(accounts_body, height=7)
    mypasswordlist = glass_listbox(accounts_body, height=7)
    myaccountlist.grid(row=1, column=0, sticky="nsew", pady=(4, 10))
    mypasswordlist.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(4, 10))

    data_file = config_path('data.json')
    if os.path.exists(data_file):
        try:
            with open(data_file, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            # A corrupt or partially-written data.json must not crash startup.
            data = []
    else:
        data = []
    # Iterating through the json
    # list
    for i in data:
        add_account_data(
            AccountData(
                i.get('account', ''),
                i.get('password', ''),
                i.get('second_password', ''),
                i.get('trade_password', ''),
            )
        )
    myaccountlist.bind("<<ListboxSelect>>", listbox_event)

    glass_label(accounts_body, "Account").grid(row=2, column=0, sticky="w")
    glass_label(accounts_body, "Password").grid(row=2, column=1, sticky="w", padx=(8, 0))
    input_account = glass_entry(accounts_body)
    password_field, input_password = make_password_field(accounts_body)
    input_account.grid(row=3, column=0, sticky="ew", pady=(4, 8))
    password_field.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(4, 8))

    glass_label(accounts_body, "Secondary password").grid(row=4, column=0, sticky="w")
    glass_label(accounts_body, "Trade password").grid(row=4, column=1, sticky="w", padx=(8, 0))
    input_second_password = glass_entry(accounts_body, show="•")
    vcmd = (root.register(validate), '%P')
    input_trade_password = glass_entry(accounts_body, show="•")
    input_trade_password.config(validate='key', validatecommand=vcmd)
    input_second_password.grid(row=5, column=0, sticky="ew", pady=(4, 12))
    input_trade_password.grid(row=5, column=1, sticky="ew", padx=(8, 0), pady=(4, 12))

    save_btn = glass_action_button(
        accounts_body, "＋ Save Account", "add this account to the list now",
        savedata, ACCENT_MINT,
    )
    output_btn = glass_action_button(
        accounts_body, "⇩ Save Accounts to Disk", "store all accounts for next launch",
        lambda: preview_write_data(outputdata), ACCENT_AMBER,
    )
    save_btn.grid(row=6, column=0, sticky="ew", pady=(2, 0))
    output_btn.grid(row=6, column=1, sticky="ew", padx=(8, 0), pady=(2, 0))
    attach_tooltip(
        save_btn,
        "Add the account and password typed below to the list right now. "
        "This only updates the in-memory list; use Save Accounts to Disk to keep them.",
    )
    attach_tooltip(
        output_btn,
        "Write every account in the vault to data.json beside the app, so they "
        "load automatically next launch. Shows a preview before writing.",
    )

    actions_frame, actions_body = glass_panel(
        content, "Launch Controls", "▶", accent=ACCENT_CYAN,
        description="Open account groups and collect timed rewards.",
        info="Open buttons launch and log in accounts; Claim buttons restore each window and click the reward timer.",
    )
    actions_frame.grid(row=2, column=7, columnspan=5, sticky="nsew", padx=(8, 16), pady=8)
    for col in range(2):
        actions_body.columnconfigure(col, weight=1)
    action_buttons = [
        ("▶ Launch Main Group (1-3)", "accounts 1-3, tiled on screen",
         lambda: preview_open_group(
             "1", "Launch Main Group (1-3)",
             "Launch saved accounts 1-3 and log each one in.",
             lambda: run_async(AutoOpen, "1")),
         ACCENT_CYAN,
         "Launches and logs in saved accounts 1-3, tiles their windows, then minimizes them. Shows a preview first."),
        ("▶ Launch Second Group (4-7)", "accounts 4-7, tiled on screen",
         lambda: preview_open_group(
             "2", "Launch Second Group (4-7)",
             "Launch saved accounts 4-7 and log each one in.",
             lambda: run_async(AutoOpen, "2")),
         ACCENT_CYAN,
         "Launches and logs in saved accounts 4-7. Needs at least 7 saved accounts. Shows a preview first."),
        ("▶ Launch Alt PC Group", "accounts 8-13, tiled on screen",
         lambda: preview_open_group(
             "3", "Launch Alt PC Group",
             "Launch the alternate-PC account group (accounts 8-13).",
             lambda: run_async(AutoOpen, "3")),
         ACCENT_CYAN,
         "Launches and logs in accounts 8-13. Needs at least 13 saved accounts. Shows a preview first."),
        ("▶ Launch Selected Account", "the account highlighted in the vault",
         lambda: preview_open_group(
             " ", "Launch Selected Account",
             "Launch only the account selected in the Account Vault.",
             lambda: run_async(AutoOpen, " ")),
         ACCENT_MINT,
         "Launches only the account you highlighted in the Account Vault list. Shows a preview first."),
        ("◷ Claim Rewards Once", "claim the reward timer in every window once",
         lambda: preview_claim("1", lambda: run_async(exe_time, "1")), ACCENT_AMBER,
         "Restores each open game window, clicks its reward timer once, then minimizes it. Shows a preview first."),
        ("◷ Claim Rewards Every 10 min", "keep claiming on a 10-minute loop",
         lambda: preview_claim("2", lambda: run_async(exe_time, "2")), ACCENT_AMBER,
         "Repeats the reward claim across all windows every 10 minutes (5 passes). Shows a preview first."),
    ]
    for index, (label, sublabel, command, accent, tip) in enumerate(action_buttons, start=0):
        button = glass_action_button(actions_body, label, sublabel, command, accent)
        button.grid(row=index, column=0, columnspan=2, sticky="ew", pady=4)
        attach_tooltip(button, tip)

    windows_frame, windows_body = glass_panel(
        content, "Game Windows & Navigation", "⌖", accent=ACCENT_ROSE,
        description="Find running game windows and auto-walk to a target.",
        info="Refresh lists open game windows; Auto Navigate reads on-screen coordinates and walks the selected window to the target.",
    )
    windows_frame.grid(row=3, column=0, columnspan=7, sticky="nsew", padx=(16, 8), pady=8)
    windows_body.columnconfigure(0, weight=1)
    windows_body.columnconfigure(1, weight=1)

    glass_label(windows_body, "Detected game windows", muted=True).grid(row=0, column=0, sticky="w")
    glass_label(windows_body, "Navigation targets", muted=True).grid(row=0, column=1, sticky="w", padx=(8, 0))
    myrefreshlist = glass_listbox(windows_body, height=6)
    mypgotargetlist = glass_listbox(windows_body, height=6)
    mypgotargetlist.insert(tk.END, '150, 124, Merchant')
    mypgotargetlist.select_set(0)
    myrefreshlist.grid(row=1, column=0, sticky="nsew", pady=(4, 10))
    mypgotargetlist.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(4, 10))
    refresh_button = glass_button(windows_body, "⟳ Refresh Window List", refresh, ACCENT_CYAN)
    refresh_button.grid(row=2, column=0, sticky="ew")
    attach_tooltip(
        refresh_button,
        "Scan for open Angels Online windows and list them on the left. "
        "Read-only - run this before Auto Navigate so a window is available to pick.",
    )
    navigate_button = glass_button(
        windows_body, "⌖ Auto Navigate",
        lambda: preview_auto_navigate(lambda: run_async(autopilot)), ACCENT_ROSE,
    )
    navigate_button.grid(row=2, column=1, sticky="ew", padx=(8, 0))
    attach_tooltip(
        navigate_button,
        "Walk the selected game window to the selected target using the navigation "
        "model. Needs the model ready and a window + target selected. Shows a preview first.",
    )

    guide_frame, guide_body = glass_panel(
        content, "What Happens In Game", "ℹ", accent=ACCENT_AMBER,
        description="Step-by-step of an automated launch and claim run.",
    )
    guide_frame.grid(row=3, column=7, columnspan=5, sticky="nsew", padx=(8, 16), pady=8)
    guide_lines = [
        "1. Open: starts START.EXE and clicks the Global launcher START button.",
        "2. Login: accepts the prompt, switches keyboard layout, and enters credentials.",
        "3. Combat: opens the attack page and enables Auto Attack.",
        "4. Rewards: restores each game window, waits for the timer icon, clicks it, then minimizes.",
        "5. Navigate: reads on-screen coordinates with the bundled model and clicks toward the target.",
    ]
    for index, line in enumerate(guide_lines):
        glass_label(guide_body, line, muted=index > 0, wraplength=430).pack(fill="x", pady=3)

    log_frame, log_body = glass_panel(
        content, "Activity Log", "▤", accent=ACCENT_CYAN,
        description="Live output from the helper. The release .exe shows it here instead of a console window.",
    )
    log_frame.grid(row=4, column=0, columnspan=12, sticky="nsew", padx=16, pady=(8, 16))
    log_output = glass_text(log_body, height=8)
    log_scroll = tk.Scrollbar(log_body, orient="vertical", command=log_output.yview)
    log_output.configure(yscrollcommand=log_scroll.set)
    log_scroll.pack(side="right", fill="y")
    log_output.pack(side="left", fill="both", expand=True)
    redirector = TextRedirector(log_output)
    if isinstance(sys.stdout, SafeStream):
        sys.stdout.attach(redirector)
    else:
        sys.stdout = redirector
    if isinstance(sys.stderr, SafeStream):
        sys.stderr.attach(redirector)
    else:
        sys.stderr = redirector
    print("UI ready. Console output is shown here because the release executable runs without a command window.")
    print(f"Loaded {len(AccountList)} saved account(s).")

    for _scrollable in (myaccountlist, mypasswordlist, myrefreshlist, mypgotargetlist, log_output):
        _bind_inner_wheel(_scrollable)

    content.update_idletasks()
    scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))

    set_ml_status(ensure_model_loaded())
    root.mainloop()
