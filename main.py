import sys
import os
import json
import keyboard
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QSlider, QCheckBox, QDoubleSpinBox)
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

def assign_hotkey(button, sound_obj, player_obj, get_settings_cb, save_cb):
    button.setText("Press a key...")
    
    def on_key_event(event):
        keyboard.unhook(hook)
        button.setText(event.name)
        save_cb()
        
        def play_macro():
            if macros_active:
                start, end, vol = get_settings_cb()
                sound_obj.apply_settings(start, end, vol)
                player_obj.play(sound_obj)
                
        keyboard.on_press_key(event.name, lambda _: play_macro(), suppress=False)

    hook = keyboard.on_press(on_key_event)

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
    
    play_btn = QPushButton(filename)
    play_btn.setFixedWidth(150)
    
    vol_slider = QSlider(Qt.Horizontal)
    vol_slider.setRange(0, 100)
    vol_slider.setValue(file_config.get("volume", 100))
    vol_slider.setFixedWidth(150)
    
    shortcut_btn = QPushButton(file_config.get("shortcut", "Set Key"))
    shortcut_btn.setFixedWidth(80)
    shortcut_buttons.append(shortcut_btn)

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
    layout.addWidget(start_spin)
    layout.addWidget(end_spin)

    filepath = os.path.join(sound_dir, filename)
    sound_obj = Sound(filename, filepath, target_fs=48000)
    
    def get_current_settings():
        return start_spin.value(), end_spin.value(), vol_slider.value()

    def save_current_state(*args):
        config[filename] = {
            "volume": vol_slider.value(),
            "start": start_spin.value(),
            "end": end_spin.value(),
            "shortcut": shortcut_btn.text()
        }
        save_config(config)

    def ui_play():
        start, end, vol = get_current_settings()
        sound_obj.apply_settings(start, end, vol)
        player.play(sound_obj)

    macro_signal.trigger.connect(ui_play)
    def assign_hotkey(button):
        button.setText("Press a key...")
        
        def on_key_event(event):
            keyboard.unhook(hook)
            button.setText(event.name)
            save_current_state()
            
            # Au lieu de jouer l'audio, on émet le signal
            keyboard.on_press_key(
                event.name, 
                lambda _: macro_signal.trigger.emit() if macros_active else None, 
                suppress=False
            )

        hook = keyboard.on_press(on_key_event)

    vol_slider.valueChanged.connect(save_current_state)
    start_spin.valueChanged.connect(save_current_state)
    end_spin.valueChanged.connect(save_current_state)
    play_btn.clicked.connect(ui_play)
    
    shortcut_btn.clicked.connect(lambda: assign_hotkey(shortcut_btn))

    # Rechargement de la touche au démarrage
    saved_key = file_config.get("shortcut", "Set Key")
    if saved_key != "Set Key":
        keyboard.on_press_key(
            saved_key, 
            lambda _: macro_signal.trigger.emit() if macros_active else None, 
            suppress=False
        )

    return layout

app = QApplication(sys.argv)
window = QWidget()

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

stop_shortcut_btn = QPushButton(config.get("stop_shortcut", "Set Key"))

def assign_stop_hotkey():
    stop_shortcut_btn.setText("Press a key...")
    def on_key_event(event):
        keyboard.unhook(hook)
        stop_shortcut_btn.setText(event.name)
        config["stop_shortcut"] = event.name
        save_config(config)
        
        keyboard.on_press_key(
            event.name, 
            lambda _: stop_signal.trigger.emit() if macros_active else None, 
            suppress=False
        )
    hook = keyboard.on_press(on_key_event)

stop_shortcut_btn.clicked.connect(assign_stop_hotkey)

saved_stop_key = config.get("stop_shortcut", "Set Key")
if saved_stop_key != "Set Key":
    keyboard.on_press_key(
        saved_stop_key, 
        lambda _: stop_signal.trigger.emit() if macros_active else None, 
        suppress=False
    )

reset_btn = QPushButton("Reset All Macros")

def reset_macros():
    keyboard.unhook_all()
    
    stop_shortcut_btn.setText("Set Key")
    config["stop_shortcut"] = "Set Key"

    for btn in shortcut_buttons:
        btn.setText("Set Key")
        
    for key in config:
        if isinstance(config[key], dict) and "shortcut" in config[key]:
            config[key]["shortcut"] = "Set Key"
            
    save_config(config)

reset_btn.clicked.connect(reset_macros)

global_controls_layout.addWidget(stop_btn)
global_controls_layout.addWidget(stop_shortcut_btn)
global_controls_layout.addWidget(reset_btn)

main_layout.addLayout(global_controls_layout)

for audio_file in sound_files:
    row_layout = create_sound_row(audio_file)
    main_layout.addLayout(row_layout)

window.setLayout(main_layout)
window.show()
sys.exit(app.exec_())