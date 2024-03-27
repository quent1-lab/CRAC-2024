import tkinter as tk
from client import Client
import os

class Application(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.client_socket = Client("127.0.0.4", 22050, 9, self.receive_to_server)
        self.client_socket.set_callback_stop(self.quit)
        self.client_socket.start()
        
        self.title("Application IHM")
        #self.geometry("800x480")
        self.attributes('-fullscreen', True)
        
        self.pages = ["Favori", "Stratégie", "Énergie", "Autre"]
        self.current_page = tk.StringVar(value=self.pages[0])
        
        self.menu_frame = tk.Frame(self, bg="lightgray")
        self.menu_frame.pack(side="top", fill="x")

        self.Energie = {
            "Tension" : {"Main": 0, "Bat1" : 0, "Bat2" : 0, "Bat3" : 0},
            "Courant" : {"Bat1" : 0, "Bat2" : 0, "Bat3" : 0},
            "Switch" : {"Bat1" : False, "Bat2" : False, "Bat3" : False}
        }
        
        self.buttons = []

        # Supposons que vous ayez un nombre total de boutons
        total_buttons = len(self.pages)

        for i, page in enumerate(self.pages):
            button = tk.Button(self.menu_frame, text=page, font=("Arial", 18),
                            command=lambda p=page: self.change_page(p), padx=20, pady=10, bg="#4CAF50", fg="white",
                            activebackground="#2F6400", activeforeground="white", borderwidth=2, highlightthickness=5)
            # Utilisez grid au lieu de pack
            button.grid(row=0, column=i, padx=(20, 0), pady=10)
            self.buttons.append(button)
        
        button = tk.Button(self.menu_frame, text="Quitter", font=("Arial", 18),
                            command=self.quit, padx=20, pady=10, bg="#4CAF50", fg="white",
                            activebackground="#2F6400", activeforeground="white", borderwidth=2, highlightthickness=5)
        
        button.grid(row=0, column=total_buttons, padx=(20, 0), pady=10)
        self.buttons.append(button)
                
        self.pages_frame = tk.Frame(self, bg="#f0f0f0")
        self.pages_frame.pack(expand=True, fill="both")
        
        self.change_page(self.current_page.get())
        #self.show_current_page()
    
    def show_current_page(self):
        # Clear previous page widgets
        for widget in self.pages_frame.winfo_children():
            widget.destroy()
        
        # Show widgets for current page
        label = tk.Label(self.pages_frame, text=f"Page: {self.current_page.get()}", font=("Arial", 30), bg="#f0f0f0")
        if self.current_page.get() == "Favori":
            self.display_energie()
        label.pack(pady=50)

    def change_page(self, page):
        self.current_page.set(page)
        self.show_current_page()
        # Highlight the selected button
        for button in self.buttons:
            if button["text"] == page:
                button.config(bg="#006400")
            else:
                button.config(bg="#4CAF50")

    def display_energie(self):
        # Créer un nouveau cadre pour les labels
        energie_frame = tk.Frame(self)
        energie_frame.pack(side="top", fill="x")

        colors = ["red", "green", "blue", "yellow"]

        for i, (category, values) in enumerate(self.Energie.items()):
            # Créer un cadre pour chaque catégorie
            category_frame = tk.Frame(self, bg=colors[i], width=200, height=200)
            category_frame.pack(side="left", padx=10, expand=True, fill="both")

            for name, value in values.items():
                # Créer un label pour le nom de la batterie
                name_label = tk.Label(category_frame, text=f"{category} {name}", bg=colors[i])
                name_label.pack()

                # Créer un label pour la valeur de la batterie
                value_label = tk.Label(category_frame, text=f"Valeur: {value}", bg=colors[i])
                value_label.pack()

    def receive_to_server(self, message):
        if message["cmd"] == "energie":
            energie = message["data"]
            self.update_energie(energie)

        elif message["cmd"] == "stop":
            self.client_socket.stop()
        
    def update_energie(self, _json):
        print("IHM : Update energie")
        if _json is None:
            return
        else:
            data = _json
        print(data)
        for key in data:
            if key in self.Energie:
                for subkey in data[key]:
                    if subkey in self.Energie[key]:
                        self.Energie[key][subkey] = data[key][subkey]

if __name__ == "__main__":
    # Vérifie si la variable $DISPLAY est définie
    if 'DISPLAY' not in os.environ:
        print("No display found, using :0")
        os.environ['DISPLAY'] = ':0'
    app = Application()
    app.mainloop()