import sys
import os
import json
import keyboard
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QSlider, QCheckBox, QDoubleSpinBox, QComboBox)
import sounddevice as sd
from superqt import QDoubleRangeSlider
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from sound import Sound, SoundPlayer

class MacroSignal(QObject):
    trigger = pyqtSignal()

CONFIG_FILE = "config.json"
macros_active = True
shortcut_buttons = []
stop_signal = MacroSignal()

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_config(config_data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=4)

config = load_config()
player = SoundPlayer(output_id=45) 

sound_dir = "sounds"
if not os.path.exists(sound_dir):
    os.makedirs(sound_dir)

valid_extensions = ('.wav', '.mp3')
sound_files = [f for f in os.listdir(sound_dir) if f.endswith(valid_extensions)]
stop_signal.trigger.connect(player.stop)

def create_sound_row(filename):
    layout = QHBoxLayout()
    file_config = config.get(filename, {})
    macro_signal = MacroSignal()

    filepath = os.path.join(sound_dir, filename)
    sound_obj = Sound(filename, filepath, target_fs=48000)
    duration = len(sound_obj.original_data) / sound_obj.fs

    range_slider = QDoubleRangeSlider(Qt.Horizontal)
    range_slider.setRange(0.0, duration)
    
    play_btn = QPushButton(filename)
    play_btn.setFixedWidth(150)
    
    vol_slider = QSlider(Qt.Horizontal)
    vol_slider.setRange(0, 100)
    vol_slider.setValue(file_config.get("volume", 100))
    vol_slider.setFixedWidth(150)
    
    saved_name = file_config.get("shortcut_name", "Set Key")
    saved_code = file_config.get("shortcut_code", None)
    
    shortcut_btn = QPushButton(saved_name)
    shortcut_btn.setFixedWidth(80)
    shortcut_buttons.append(shortcut_btn)

    reset_btn = QPushButton("Reset")
    reset_btn.setFixedWidth(50)
    
    start_spin = QDoubleSpinBox()
    start_spin.setPrefix("Start: ")
    start_spin.setSuffix(" s")
    start_spin.setSingleStep(0.1)
    start_spin.setValue(file_config.get("start", 0.0))
    start_spin.setFixedWidth(100)

    end_spin = QDoubleSpinBox()
    end_spin.setPrefix("End: ")
    end_spin.setSuffix(" s")
    end_spin.setSingleStep(0.1)
    end_spin.setValue(file_config.get("end", 0.0))
    end_spin.setFixedWidth(100)

    layout.addWidget(play_btn)
    layout.addWidget(vol_slider)
    layout.addWidget(shortcut_btn)
    layout.addWidget(reset_btn)
    layout.addWidget(range_slider)


    saved_start = file_config.get("start", 0.0)
    saved_end = file_config.get("end", duration)
    if saved_end == 0.0:
        saved_end = duration

    range_slider.setValue((saved_start, saved_end))
    range_slider.setFixedWidth(200)

    current_hook = [None]

    def bind_key(scan_code):
        if current_hook[0] is not None:
            try:
                keyboard.remove_hotkey(current_hook[0])
            except Exception:
                pass
                
        current_hook[0] = keyboard.on_press_key(
            scan_code, 
            lambda _: macro_signal.trigger.emit() if macros_active else None, 
            suppress=False
        )

    def get_current_settings():
        start_val, end_val = range_slider.value()
        return start_val, end_val, vol_slider.value()

    def save_current_state(*args):
        start_val, end_val = range_slider.value()
        
        if filename not in config:
            config[filename] = {}
            
        config[filename].update({
            "volume": vol_slider.value(),
            "start": start_val,
            "end": end_val
        })
        save_config(config)

    vol_slider.valueChanged.connect(save_current_state)
    range_slider.valueChanged.connect(save_current_state)

    def ui_play():
        start, end, vol = get_current_settings()
        sound_obj.apply_settings(start, end, vol)
        player.play(sound_obj)

    macro_signal.trigger.connect(ui_play)

    def assign_hotkey(button):
        button.setText("Press a key...")
        
        def on_key_event(event):
            keyboard.unhook(hook)
            button.setText(str(event.name))
            
            if filename not in config:
                config[filename] = {}
                
            config[filename]["shortcut_name"] = event.name
            config[filename]["shortcut_code"] = event.scan_code
            save_config(config)
            bind_key(event.scan_code)

        hook = keyboard.on_press(on_key_event)

    def reset_hotkey():
        if current_hook[0] is not None:
            try:
                keyboard.remove_hotkey(current_hook[0])
            except Exception:
                pass
            current_hook[0] = None
            
        shortcut_btn.setText("Set Key")
        if filename in config:
            config[filename]["shortcut_name"] = "Set Key"
            config[filename]["shortcut_code"] = None
            save_config(config)

    vol_slider.valueChanged.connect(save_current_state)
    start_spin.valueChanged.connect(save_current_state)
    end_spin.valueChanged.connect(save_current_state)
    play_btn.clicked.connect(ui_play)
    shortcut_btn.clicked.connect(lambda: assign_hotkey(shortcut_btn))
    reset_btn.clicked.connect(reset_hotkey)

    if saved_code is not None:
        bind_key(saved_code)

    return layout

app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("Soundboard")

macro_toggle = QCheckBox("Enable Macros")
macro_toggle.setChecked(True)

def toggle_macros(state):
    global macros_active
    macros_active = (state == Qt.Checked)

macro_toggle.stateChanged.connect(toggle_macros)

main_layout = QVBoxLayout()
main_layout.addWidget(macro_toggle)
global_controls_layout = QHBoxLayout()

stop_btn = QPushButton("Stop All Sounds")
stop_btn.clicked.connect(player.stop)

saved_stop_name = config.get("stop_shortcut_name", "Set Key")
saved_stop_code = config.get("stop_shortcut_code", None)
stop_shortcut_btn = QPushButton(saved_stop_name)

stop_hook_ref = [None]

def bind_stop_key(scan_code):
    if stop_hook_ref[0] is not None:
        try:
            keyboard.remove_hotkey(stop_hook_ref[0])
        except Exception:
            pass
    stop_hook_ref[0] = keyboard.on_press_key(
        scan_code, 
        lambda _: stop_signal.trigger.emit() if macros_active else None, 
        suppress=False
    )

def assign_stop_hotkey():
    stop_shortcut_btn.setText("Press a key...")
    def on_key_event(event):
        keyboard.unhook(hook)
        stop_shortcut_btn.setText(str(event.name))
        config["stop_shortcut_name"] = event.name
        config["stop_shortcut_code"] = event.scan_code
        save_config(config)
        bind_stop_key(event.scan_code)
        
    hook = keyboard.on_press(on_key_event)

stop_shortcut_btn.clicked.connect(assign_stop_hotkey)

if saved_stop_code is not None:
    bind_stop_key(saved_stop_code)

reset_btn = QPushButton("Reset All Macros")

def reset_macros():
    keyboard.unhook_all()
    
    stop_shortcut_btn.setText("Set Key")
    config["stop_shortcut_name"] = "Set Key"
    config["stop_shortcut_code"] = None

    for btn in shortcut_buttons:
        btn.setText("Set Key")
        
    for key in config:
        if isinstance(config[key], dict) and "shortcut_code" in config[key]:
            config[key]["shortcut_name"] = "Set Key"
            config[key]["shortcut_code"] = None
            
    save_config(config)

reset_btn.clicked.connect(reset_macros)

global_controls_layout.addWidget(stop_btn)
global_controls_layout.addWidget(stop_shortcut_btn)
global_controls_layout.addWidget(reset_btn)

device_combo = QComboBox()

devices = sd.query_devices()
for i, dev in enumerate(devices):
    if dev['max_output_channels'] > 0:
        device_combo.addItem(f"{i} - {dev['name']}", i)

saved_device_id = config.get("output_device_id", 45)
player.output_id = saved_device_id

index = device_combo.findData(saved_device_id)
if index >= 0:
    device_combo.setCurrentIndex(index)

def update_output_device(idx):
    device_id = device_combo.itemData(idx)
    player.output_id = device_id
    config["output_device_id"] = device_id
    save_config(config)

device_combo.currentIndexChanged.connect(update_output_device)

global_controls_layout.addWidget(device_combo)

main_layout.addLayout(global_controls_layout)

for audio_file in sound_files:
    row_layout = create_sound_row(audio_file)
    main_layout.addLayout(row_layout)

window.setLayout(main_layout)
window.show()
sys.exit(app.exec_())