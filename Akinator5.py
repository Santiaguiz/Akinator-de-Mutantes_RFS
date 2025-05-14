import json
import os
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk

class AkinatorApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Akinator X-Men - Mutantes")

        # Definir la ruta correcta del archivo JSON
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.correct_json_path = os.path.join(current_dir, "mutants.json")
        self.filename = self.verify_json_location()
        
        if not self.filename:
            messagebox.showerror("Error", f"No se encontró el archivo mutants.json en la ruta especificada.")
            self.master.destroy()
            return

        self.mutants = self.load_mutants()

        if not self.mutants:
            messagebox.showerror("Error", f"No se encontró o está vacío el archivo {self.filename}. El programa no puede continuar.")
            self.master.destroy()
            return

        self.facts = {"yes": {}, "no": {}}
        self.asked_categories = set()
        self.asked_questions = set()  # Track asked (category, option) pairs to avoid repeats
        self.possible_mutants = self.mutants.copy()
        self.current_category = None
        self.current_option = None
        self.mutant_to_add = None  # Para almacenar el nuevo mutante si no se adivina

        # Resto del código de inicialización GUI...
        self.frame = tk.Frame(master, padx=20, pady=20)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.label_title = tk.Label(
            self.frame,
            text="Piensa en un mutante de X-Men.\nResponde las preguntas.",
            font=("Segoe UI", 16),
            fg="navy",
        )
        self.label_title.pack(pady=(0, 20))

        self.label_question = tk.Label(
            self.frame,
            text="",
            font=("Segoe UI", 14),
            wraplength=380,
            justify=tk.CENTER,
        )
        self.label_question.pack(pady=10)

        self.image_label = tk.Label(self.frame)
        self.image_label.pack(pady=10)

        self.button_frame = tk.Frame(self.frame)
        self.button_frame.pack(pady=10)

        self.btn_yes = tk.Button(
            self.button_frame,
            text="Sí",
            width=10,
            command=lambda: self.answer(True),
        )
        self.btn_yes.grid(row=0, column=0, padx=5)

        self.btn_no = tk.Button(
            self.button_frame,
            text="No",
            width=10,
            command=lambda: self.answer(False),
        )
        self.btn_no.grid(row=0, column=1, padx=5)

        self.btn_dontknow = tk.Button(
            self.button_frame,
            text="No sé",
            width=10,
            command=lambda: self.answer(None),
        )
        self.btn_dontknow.grid(row=0, column=2, padx=5)

        self.btn_restart = tk.Button(
            self.frame, text="Reiniciar Juego", command=self.restart_game
        )
        self.btn_restart.pack(pady=(20, 0))
        self.btn_restart.config(state=tk.DISABLED)

        self.current_image = None  # Referencia para evitar recolección basura

        self.next_question()  # Comenzar el juego

    def verify_json_location(self):
        """Verifica si el archivo JSON existe en la ruta correcta o en la local"""
        # Primero verificar la ruta correcta
        if os.path.exists(self.correct_json_path):
            return self.correct_json_path
        # Si no está en la ruta correcta, verificar en la local
        local_path = "mutants.json"
        if os.path.exists(local_path):
            return local_path
        return None

    def load_mutants(self):
        """Carga los mutantes desde el archivo JSON"""
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el archivo: {str(e)}")
            return []

    def save_mutants(self):
        """Guarda los mutantes en el archivo JSON"""
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.mutants, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {str(e)}")
            return False

    def select_next_question(self):
        # Seleccionar atributos en orden fijo para preguntar: gender, hair, affiliation, powers
        attributes = ["gender", "hair", "affiliation", "powers"]
        remaining_attributes = [cat for cat in attributes if cat not in self.asked_categories]
        for cat in remaining_attributes:
            options = set()
            for m in self.possible_mutants:
                if cat in ["powers", "hair"]:
                    # hair can be list or str, powers always list
                    if isinstance(m[cat], list):
                        options.update(m[cat])
                    else:
                        options.add(m[cat])
                else:
                    options.add(m[cat])
            # Para cada opción, verificar si pregunta ya fue hecha (cat, option)
            # Solo preguntas que no se hayan hecho antes
            filtered_options = [opt for opt in options if (cat, opt) not in self.asked_questions]
            if len(filtered_options) > 0:
                # Elegir opción más común para pregunta solo entre las no preguntadas
                freq = {}
                for m in self.possible_mutants:
                    if cat in ["powers", "hair"]:
                        vals = m[cat] if isinstance(m[cat], list) else [m[cat]]
                        for val in vals:
                            if (cat, val) in self.asked_questions:
                                continue
                            freq[val] = freq.get(val, 0) + 1
                    else:
                        v = m[cat]
                        if (cat, v) in self.asked_questions:
                            continue
                        freq[v] = freq.get(v, 0) + 1
                if not freq:
                    continue
                sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
                for option, _ in sorted_freq:
                    if (cat, option) not in self.asked_questions:
                        return cat, option
        return None, None

    def forward_chaining(self, yes_facts=None, no_facts=None):
        # Filtrar mutantes según hechos "sí" y "no"
        yes_facts = yes_facts if yes_facts is not None else self.facts["yes"]
        no_facts = no_facts if no_facts is not None else self.facts["no"]

        filtered = self.mutants
        for cat, values in yes_facts.items():
            if cat in ["powers", "hair"]:
                filtered = [m for m in filtered if any(p in values for p in (m[cat] if isinstance(m[cat], list) else [m[cat]]))]
            else:
                filtered = [m for m in filtered if m[cat] in values]
        for cat, values in no_facts.items():
            if cat in ["powers", "hair"]:
                filtered = [m for m in filtered if all(p not in values for p in (m[cat] if isinstance(m[cat], list) else [m[cat]]))]
            else:
                filtered = [m for m in filtered if m[cat] not in values]
        return filtered

    def backward_chaining(self):
        # Solo devuelve mutante si queda uno exacto
        if len(self.possible_mutants) == 1:
            return self.possible_mutants[0]
        return None

    def answer(self, res):
        if self.current_category is None or self.current_option is None:
            return
        if res is True:
            self.facts["yes"].setdefault(self.current_category, set()).add(
                self.current_option
            )
        elif res is False:
            self.facts["no"].setdefault(self.current_category, set()).add(
                self.current_option
            )
        else:
            # No sé - no añade para evitar repetir pregunta
            pass
        self.asked_categories.add(self.current_category)
        self.asked_questions.add((self.current_category, self.current_option))
        self.possible_mutants = self.forward_chaining()

        guess = self.backward_chaining()
        if guess:
            self.show_guess(guess)
        else:
            if not self.possible_mutants:
                no_facts_backup = self.facts["no"].copy()
                self.facts["no"] = {}
                self.possible_mutants = self.forward_chaining(yes_facts=self.facts["yes"], no_facts={})
                self.asked_categories -= set(no_facts_backup.keys())
                if self.possible_mutants:
                    self.next_question()
                else:
                    self.cannot_guess()
            else:
                self.next_question()

    def format_question(self, cat, option):
        texts = {
            "hair": f"¿El mutante tiene el cabello de color '{option}'?",
            "powers": f"¿El mutante tiene el poder de '{option}'?",
            "affiliation": f"¿El mutante pertenece a la afiliación '{option}'?",
            "gender": f"¿El mutante es de género '{option}'?",
            "nationality": f"¿El mutante es de nacionalidad '{option}'?",
        }
        return texts.get(cat, f"¿El mutante tiene caracteristica '{option}' en '{cat}'?")

    def show_guess(self, mutant):
        self.label_question.config(text=f"Creo que tu mutante es: {mutant['name']}")
        self.display_image(mutant)
        answer = messagebox.askyesno(
            "Confirmar", f"¿Es correcto que el mutante es {mutant['name']}?"
        )
        if answer:
            messagebox.showinfo("¡Éxito!", "¡Genial! He adivinado correctamente.")
            self.enable_restart()
        else:
            self.handle_incorrect_guess(mutant)

    def handle_incorrect_guess(self, guessed_mutant):
        """Maneja el caso cuando la suposición es incorrecta"""
        response = messagebox.askyesno(
            "No adivinado",
            "No he adivinado correctamente. ¿Deseas agregar el mutante que pensaste a la base de datos?"
        )
        
        if response:
            self.add_new_mutant(guessed_mutant)
        else:
            messagebox.showinfo(
                "Información",
                "No se agregó ningún mutante nuevo. Puedes reiniciar el juego para intentar de nuevo."
            )
            self.enable_restart()

    def add_new_mutant(self, guessed_mutant):
        """Solicita información para agregar un nuevo mutante"""
        name = simpledialog.askstring(
            "Nuevo Mutante",
            "Por favor ingresa el nombre del mutante que pensaste:",
            parent=self.master
        )
        
        if not name:
            return
            
        # Verificar si el mutante ya existe
        if any(m['name'].lower() == name.lower() for m in self.mutants):
            messagebox.showinfo(
                "Mutante Existente",
                f"El mutante '{name}' ya existe en la base de datos."
            )
            self.enable_restart()
            return
            
        # Crear nuevo mutante basado en las respuestas dadas
        new_mutant = {
            "name": name,
            "gender": "",
            "hair": "",
            "powers": [],
            "affiliation": "",
            "nationality": ""
        }
        
        # Preguntar por cada atributo
        for attr in ["gender", "hair", "affiliation", "nationality"]:
            value = simpledialog.askstring(
                "Nuevo Mutante",
                f"Ingresa el/la {attr} de {name}:",
                parent=self.master
            )
            if value:
                if attr == "hair":
                    new_mutant[attr] = value
                else:
                    new_mutant[attr] = value
        
        # Preguntar por poderes (pueden ser múltiples)
        powers = []
        while True:
            power = simpledialog.askstring(
                "Nuevo Mutante",
                f"Ingresa un poder de {name} (deja vacío para terminar):",
                parent=self.master
            )
            if not power:
                break
            powers.append(power)
        new_mutant["powers"] = powers
        
        # Mostrar resumen y confirmar
        summary = "\n".join(f"{k}: {v}" for k, v in new_mutant.items())
        confirm = messagebox.askyesno(
            "Confirmar",
            f"¿Deseas agregar este mutante?\n\n{summary}"
        )
        
        if confirm:
            self.mutants.append(new_mutant)
            if self.save_mutants():
                messagebox.showinfo(
                    "Éxito",
                    f"El mutante {name} ha sido agregado exitosamente a la base de datos."
                )
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo guardar el nuevo mutante en el archivo."
                )
        
        self.enable_restart()

    def cannot_guess(self):
        self.label_question.config(text="No pude adivinar tu mutante.")
        self.image_label.config(image="")
        self.current_image = None
        
        response = messagebox.askyesno(
            "Sin resultado",
            "No pude encontrar el mutante que tienes en mente.\n¿Deseas agregarlo a la base de datos?"
        )
        
        if response:
            self.add_new_mutant(None)
        else:
            messagebox.showinfo(
                "Información",
                "No se agregó ningún mutante nuevo. Puedes reiniciar el juego para intentarlo otra vez."
            )
            self.enable_restart()

    def display_image(self, mutant):
        path_img = os.path.join(
            "images", mutant["name"].lower().replace(" ", "_") + ".jpg"
        )
        if os.path.exists(path_img):
            try:
                img = Image.open(path_img)
                img.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(img)
                self.image_label.config(image=photo)
                self.current_image = photo
            except Exception:
                self.image_label.config(image="")
                self.current_image = None
        else:
            self.image_label.config(image="")
            self.current_image = None

    def enable_restart(self):
        self.btn_yes.config(state=tk.DISABLED)
        self.btn_no.config(state=tk.DISABLED)
        self.btn_dontknow.config(state=tk.DISABLED)
        self.btn_restart.config(state=tk.NORMAL)

    def restart_game(self):
        self.facts = {"yes": {}, "no": {}}
        self.asked_categories.clear()
        self.asked_questions.clear()
        self.possible_mutants = self.mutants.copy()
        self.current_category = None
        self.current_option = None
        self.btn_yes.config(state=tk.NORMAL)
        self.btn_no.config(state=tk.NORMAL)
        self.btn_dontknow.config(state=tk.NORMAL)
        self.btn_restart.config(state=tk.DISABLED)
        self.label_title.config(text="Piensa en un mutante de X-Men.\nResponde las preguntas.")
        self.label_question.config(text="")
        self.image_label.config(image="")
        self.current_image = None
        self.next_question()

    def user_select_final_mutant(self, mutants):
        # Dialog to let user select one of the final mutants
        names = [m["name"] for m in mutants]
        selection = simpledialog.askstring(
            "Seleccione Mutante",
            f"No puedo decidir seguro. Por favor, elige uno de estos mutantes:\n{', '.join(names)}\n\nEscribe el nombre exactamente:"
        )
        if selection:
            selection = selection.strip().lower()
            for m in mutants:
                if m["name"].lower() == selection:
                    self.show_guess(m)
                    return
            messagebox.showinfo("No válido", "El nombre no coincide con las opciones dadas.")
            self.user_select_final_mutant(mutants)
        else:
            messagebox.showinfo("Sin selección", "No se seleccionó mutante. Puedes reiniciar el juego.")
            self.enable_restart()

    def next_question(self):
        self.current_category, self.current_option = self.select_next_question()

        if self.current_category is None:
            count = len(self.possible_mutants)
            if count > 2:
                # Intenta liberar categorías negativas y sigue preguntando
                no_facts_backup = self.facts["no"].copy()
                self.facts["no"] = {}
                self.asked_categories -= set(no_facts_backup.keys())
                self.possible_mutants = self.forward_chaining(yes_facts=self.facts["yes"], no_facts={})
                if self.possible_mutants:
                    self.next_question()
                    return
                else:
                    self.label_question.config(
                        text="No tengo suficientes pistas para adivinar correctamente."
                    )
                    self.image_label.config(image="")
                    self.current_image = None
                    self.enable_restart()
                    return
            if count == 2:
                # Permitir que el usuario elija manualmente entre las dos opciones finales
                self.user_select_final_mutant(self.possible_mutants)
                return
            elif 1 < count < 2:
                nombres = ", ".join(m["name"] for m in self.possible_mutants)
                self.label_question.config(
                    text=f"No puedo decidir seguro. Puede que sea uno de estos:\n{nombres}"
                )
            elif count == 1:
                self.show_guess(self.possible_mutants[0])
                return
            else:
                self.label_question.config(
                    text="No tengo suficientes pistas para adivinar correctamente."
                )
            self.image_label.config(image="")
            self.current_image = None
            self.enable_restart()
            return
        texto = self.format_question(self.current_category, self.current_option)
        self.label_question.config(text=texto)
        self.image_label.config(image="")
        self.current_image = None


def main():
    root = tk.Tk()
    root.geometry("450x450")
    app = AkinatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

