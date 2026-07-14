import os
import tkinter as tk
import pygame

# Initialisation du moteur audio
pygame.mixer.init()

def play_sound(filepath):
    pygame.mixer.Sound(filepath).play()

def stop_all_sounds():
    pygame.mixer.stop()

# Configuration de la fenêtre principale
root = tk.Tk()
root.title("Meme Soundboard")
root.config(bg="#2c3e50") # Couleur de fond sombre

sound_dir = "./sounds"

# Bouton "Stop All" en haut
stop_btn = tk.Button(
    root, text="⏹ COUPER LES SONS", command=stop_all_sounds,
    bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), width=20, height=2
)
stop_btn.grid(row=0, column=0, columnspan=3, pady=15, padx=10)

# Création de la grille de boutons
if os.path.exists(sound_dir):
    row, col = 1, 0
    for filename in os.listdir(sound_dir):
        if filename.endswith((".mp3", ".wav")):
            path = os.path.join(sound_dir, filename)
            # Nettoie le nom du fichier (enlève l'extension et les tirets)
            btn_name = os.path.splitext(filename)[0].replace("_", " ").title()
            
            button = tk.Button(
                root, 
                text=btn_name, 
                command=lambda p=path: play_sound(p),
                bg="#3498db", fg="white", font=("Arial", 9, "bold"),
                width=15, height=3, wraplength=100
            )
            button.grid(row=row, column=col, padx=10, pady=10)
            
            # Gestion des colonnes (3 boutons par ligne)
            col += 1
            if col > 2:
                col = 0
                row += 1
else:
    print(f"Attention : Le dossier '{sound_dir}' est introuvable ou vide.")

root.mainloop()