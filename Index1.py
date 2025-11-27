import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import json
import os
import google.generativeai as genai
from tkinter import font as tkfont
from collections import deque

class TreeNode:
    def __init__(self, recipe):
        self.recipe = recipe
        self.left = None
        self.right = None

class BinarySearchTree:
    def __init__(self):
        self.root = None

    def insert(self, recipe):
        if not self.root:
            self.root = TreeNode(recipe)
        else:
            self._insert_recursively(self.root, recipe)

    def _insert_recursively(self, node, recipe):
        if recipe['name'] < node.recipe['name']:
            if node.left is None:
                node.left = TreeNode(recipe)
            else:
                self._insert_recursively(node.left, recipe)
        else:
            if node.right is None:
                node.right = TreeNode(recipe)
            else:
                self._insert_recursively(node.right, recipe)

    def search(self, name):
        return self._search_recursively(self.root, name)

    def _search_recursively(self, node, name):
        if node is None:
            return None
        if node.recipe['name'] == name:
            return node.recipe
        elif name < node.recipe['name']:
            return self._search_recursively(node.left, name)
        else:
            return self._search_recursively(node.right, name)

class RecipeManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Recipe Management System")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)

        # Configure Google AI API
        genai.configure(api_key='AIzaSyDXqHSQeL47qDG9MBehoCo_-ijyM-OapdQ')  

        # Create GenerativeModel instance
        self.model = genai.GenerativeModel('gemini-1.5-flash')

        self.recipes = []
        self.recipe_tree = BinarySearchTree()  
        self.load_recipes()
        self.recently_viewed = deque(maxlen=5)  

        # Custom fonts
        self.title_font = tkfont.Font(family='Helvetica', size=14, weight='bold')
        self.button_font = tkfont.Font(family='Helvetica', size=10)
        self.text_font = tkfont.Font(family='Helvetica', size=10)
        self.chat_font = tkfont.Font(family='Helvetica', size=11)

        # Configure style
        self.style = ttk.Style()
        self.style.configure('TButton', font=self.button_font, padding=5)
        self.style.configure('TFrame', background='#f0f0f0')

        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Recipe list
        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Recipe list components
        self.setup_recipe_list()

        # Right panel - Recipe details
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Recipe details components
        self.setup_recipe_details()

        # AI Chatbot button
        self.setup_chat_button()

        # Update UI
        self.update_recipe_list()

    def load_recipes(self):
        """Load recipes from JSON file"""
        if os.path.exists('recipes.json'):
            try:
                with open('recipes.json', 'r') as f:
                    self.recipes = json.load(f)
                    for recipe in self.recipes:
                        self.recipe_tree.insert(recipe)  # Insert each recipe into the BST
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load recipes: {str(e)}")

    def save_recipes(self):
        """Save recipes to JSON file"""
        try:
            with open('recipes.json', 'w') as f:
                json.dump(self.recipes, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save recipes: {str(e)}")

    def setup_recipe_list(self):
        """Setup the recipe list components"""
        # Title label
        self.title_label = ttk.Label(self.left_frame, text="Your Recipes", font=self.title_font)
        self.title_label.pack(pady=10)

        # Recipe listbox with scrollbar
        self.listbox_frame = ttk.Frame(self.left_frame)
        self.listbox_frame.pack(fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.listbox_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.recipe_listbox = tk.Listbox(
            self.listbox_frame,
            yscrollcommand=self.scrollbar.set,
            font=self.text_font,
            selectbackground='#0078d7',
            selectforeground='white',
            height=15
        )
        self.recipe_listbox.pack(fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.recipe_listbox.yview)

        # Bind selection event
        self.recipe_listbox.bind('<<ListboxSelect>>', self.show_recipe_details)

        # Button frame
        self.button_frame = ttk.Frame(self.left_frame)
        self.button_frame.pack(fill=tk.X, pady=10)

        # Action buttons
        ttk.Button(self.button_frame, text="Add Recipe", command=self.add_recipe).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(self.button_frame, text="Edit Recipe", command=self.edit_recipe).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(self.button_frame, text="Delete Recipe", command=self.delete_recipe).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        # Search frame
        self.search_frame = ttk.Frame(self.left_frame)
        self.search_frame.pack(fill=tk.X, pady=(10, 0))

        self.search_entry = ttk.Entry(self.search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.search_recipes)

        ttk.Button(self.search_frame, text="Search", command=self.search_recipes).pack(side=tk.RIGHT)

    def setup_recipe_details(self):
        """Setup the recipe details components"""
        self.details_title = ttk.Label(self.right_frame, text="Recipe Details", font=self.title_font)
        self.details_title.pack(pady=10)

        self.details_container = ttk.Frame(self.right_frame)
        self.details_container.pack(fill=tk.BOTH, expand=True)

        # Notebook for details tabs
        self.notebook = ttk.Notebook(self.details_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Ingredients tab
        self.ingredients_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, font=self.text_font)
        self.notebook.add(self.ingredients_text, text="Ingredients")

        # Instructions tab
        self.instructions_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, font=self.text_font)
        self.notebook.add(self.instructions_text, text="Instructions")

    def setup_chat_button(self):
        """Add the AI chatbot button and functionality"""
        # Chatbot frame (initially hidden)
        self.chat_frame = ttk.Frame(self.right_frame)

        # Chatbot components
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            font=self.chat_font,
            height=15,
            state=tk.DISABLED
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Input frame
        input_frame = ttk.Frame(self.chat_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.chat_entry = ttk.Entry(input_frame, font=self.chat_font)
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.chat_entry.bind("<Return>", self.process_chat_input)

        send_button = ttk.Button(input_frame, text="Send", command=self.process_chat_input)
        send_button.pack(side=tk.RIGHT)

        # AI button in corner
        self.ai_button = ttk.Button(self.right_frame, text="Ask AI", command=self.toggle_chat)
        self.ai_button.place(relx=1.0, rely=0.0, anchor='ne', x=-10, y=10)

    def toggle_chat(self):
        """Toggle between recipe details and chatbot"""
        if self.chat_frame.winfo_ismapped():
            self.chat_frame.pack_forget()
            self.details_container.pack(fill=tk.BOTH, expand=True)
            self.ai_button.config(text="Ask AI")
        else:
            self.details_container.pack_forget()
            self.chat_frame.pack(fill=tk.BOTH, expand=True)
            self.ai_button.config(text="Close AI")
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.insert(tk.END, "AI Recipe Assistant\nType a recipe name to get instructions\n\n")
            self.chat_display.config(state=tk.DISABLED)
            self.chat_entry.focus()

    def process_chat_input(self, event=None):
        """Handle AI chat requests"""
        query = self.chat_entry.get().strip()
        if not query:
            return

        # Add user message to chat
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"You: {query}\n\n")

        try:
            # Show thinking indicator
            self.chat_display.insert(tk.END, "AI: Thinking...\n")
            self.chat_display.see(tk.END)
            self.chat_display.update()

            # Get AI response
            prompt = f"Provide a detailed recipe for {query}. Include:\n1. Ingredients list (bullet points)\n2. Step-by-step instructions (numbered)\n3. Cooking time\n4. Any special notes\n\nFormat the response neatly with clear section headings."
            response = self.model.generate_content(prompt)

            # Remove the "Thinking..." message
            self.chat_display.delete("end-2l", "end-1c")

            # Add AI response
            self.chat_display.insert(tk.END, f"AI: {response.text}\n\n")
        except Exception as e:
            self.chat_display.delete("end-2l", "end-1c")
            self.chat_display.insert(tk.END, f"AI: Error - {str(e)}\n\n")

        self.chat_display.config(state=tk.DISABLED)
        self.chat_entry.delete(0, tk.END)
        self.chat_display.see(tk.END)

    def update_recipe_list(self):
        """Update the listbox with current recipes"""
        self.recipe_listbox.delete(0, tk.END)
        for recipe in self.recipes:
            self.recipe_listbox.insert(tk.END, recipe['name'])

    def show_recipe_details(self, event=None):
        """Show details of the selected recipe"""
        selection = self.recipe_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        if 0 <= idx < len(self.recipes):
            recipe = self.recipes[idx]

            # Update ingredients tab
            self.ingredients_text.config(state=tk.NORMAL)
            self.ingredients_text.delete(1.0, tk.END)
            self.ingredients_text.insert(tk.END, "\n".join(recipe['ingredients']))
            self.ingredients_text.config(state=tk.DISABLED)

            # Update instructions tab
            self.instructions_text.config(state=tk.NORMAL)
            self.instructions_text.delete(1.0, tk.END)
            self.instructions_text.insert(tk.END, "\n".join(recipe['instructions']))
            self.instructions_text.config(state=tk.DISABLED)

            # Add to recently viewed stack
            if recipe['name'] not in self.recently_viewed:
                self.recently_viewed.append(recipe['name'])

    def add_recipe(self):
        """Add a new recipe"""
        name = simpledialog.askstring("Add Recipe", "Enter recipe name:")
        if not name:
            return

        # Check for duplicate names
        if any(r['name'].lower() == name.lower() for r in self.recipes):
            messagebox.showerror("Error", f"A recipe with name '{name}' already exists!")
            return

        # Get ingredients
        ingredients = []
        while True:
            ingredient = simpledialog.askstring("Add Ingredient", "Enter an ingredient (leave empty to finish):")
            if not ingredient:
                break
            ingredients.append(ingredient)

        # Get instructions
        instructions = []
        while True:
            instruction = simpledialog.askstring("Add Instruction", "Enter an instruction (leave empty to finish):")
            if not instruction:
                break
            instructions.append(instruction)

        # Create the new recipe
        new_recipe = {
            'name': name,
            'ingredients': ingredients,
            'instructions': instructions
        }

        # Add the new recipe to the list and the BST
        self.recipes.append(new_recipe)
        self.recipe_tree.insert(new_recipe)  # Insert into the BST

        # Update UI and save
        self.update_recipe_list()
        self.save_recipes()

    def edit_recipe(self):
        """Edit selected recipe"""
        selection = self.recipe_listbox.curselection()
        if not selection:
            messagebox.showwarning("Edit Recipe", "Please select a recipe to edit")
            return

        idx = selection[0]
        if 0 <= idx < len(self.recipes):
            recipe = self.recipes[idx]

            # Create edit dialog
            edit_window = tk.Toplevel(self.root)
            edit_window.title(f"Edit Recipe: {recipe['name']}")
            edit_window.geometry("600x500")

            # Name frame
            name_frame = ttk.Frame(edit_window)
            name_frame.pack(fill=tk.X, padx=10, pady=10)

            ttk.Label(name_frame, text="Recipe Name:").pack(side=tk.LEFT)
            name_entry = ttk.Entry(name_frame)
            name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            name_entry.insert(0, recipe['name'])

            # Notebook for ingredients and instructions
            edit_notebook = ttk.Notebook(edit_window)
            edit_notebook.pack(fill=tk.BOTH, expand=True, padx=10)

            # Ingredients tab
            ingredients_frame = ttk.Frame(edit_notebook)
            edit_notebook.add(ingredients_frame, text="Ingredients")

            ingredients_listbox = tk.Listbox(
                ingredients_frame,
                selectmode=tk.EXTENDED,
                font=self.text_font
            )
            ingredients_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            scrollbar = ttk.Scrollbar(ingredients_frame, orient=tk.VERTICAL)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            ingredients_listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=ingredients_listbox.yview)

            # Populate ingredients
            for ingredient in recipe['ingredients']:
                ingredients_listbox.insert(tk.END, ingredient)

            # Ingredients buttons
            buttons_frame = ttk.Frame(ingredients_frame)
            buttons_frame.pack(fill=tk.X, pady=5)

            def add_ingredient():
                ingredient = simpledialog.askstring("Add Ingredient", "Enter ingredient:")
                if ingredient:
                    ingredients_listbox.insert(tk.END, ingredient)

            add_button = ttk.Button(buttons_frame, text="Add", command=add_ingredient)
            add_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

            def remove_ingredient():
                for i in reversed(ingredients_listbox.curselection()):
                    ingredients_listbox.delete(i)

            remove_button = ttk.Button(buttons_frame, text="Remove", command=remove_ingredient)
            remove_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

            # Instructions tab
            instructions_frame = ttk.Frame(edit_notebook)
            edit_notebook.add(instructions_frame, text="Instructions")

            instructions_text = scrolledtext.ScrolledText(
                instructions_frame,
                wrap=tk.WORD,
                font=self.text_font
            )
            instructions_text.pack(fill=tk.BOTH, expand=True)
            instructions_text.insert(tk.END, "\n".join(recipe['instructions']))

            # Save button
            def save_changes():
                new_name = name_entry.get()
                if not new_name:
                    messagebox.showerror("Error", "Recipe name cannot be empty!")
                    return

                # Check for duplicate names
                if new_name != recipe['name']:
                    if any(r['name'].lower() == new_name.lower() for r in self.recipes):
                        messagebox.showerror("Error", f"A recipe with name '{new_name}' already exists!")
                        return

                # Update recipe
                self.recipes[idx] = {
                    'name': new_name,
                    'ingredients': list(ingredients_listbox.get(0, tk.END)),
                    'instructions': instructions_text.get("1.0", tk.END).splitlines()
                }

                # Update the BST
                self.recipe_tree = BinarySearchTree()  # Rebuild the tree
                for r in self.recipes:
                    self.recipe_tree.insert(r)

                # Update UI and save
                self.update_recipe_list()
                self.save_recipes()
                self.show_recipe_details()
                edit_window.destroy()
                messagebox.showinfo("Success", "Recipe updated successfully!")

            save_frame = ttk.Frame(edit_window)
            save_frame.pack(fill=tk.X, padx=10, pady=10)

            save_button = ttk.Button(save_frame, text="Save Changes", command=save_changes)
            save_button.pack(fill=tk.X)

    def delete_recipe(self):
        """Delete selected recipe"""
        selection = self.recipe_listbox.curselection()
        if not selection:
            messagebox.showwarning("Delete Recipe", "Please select a recipe to delete")
            return

        idx = selection[0]
        if 0 <= idx < len(self.recipes):
            recipe = self.recipes[idx]
            confirm = messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete the recipe '{recipe['name']}'?"
            )
            if confirm:
                del self.recipes[idx]
                self.recipe_tree = BinarySearchTree()  # Rebuild the tree
                for r in self.recipes:
                    self.recipe_tree.insert(r)

                self.update_recipe_list()
                self.save_recipes()

                # Clear the details panel if the deleted recipe was being shown
                self.ingredients_text.config(state=tk.NORMAL)
                self.ingredients_text.delete(1.0, tk.END)
                self.ingredients_text.config(state=tk.DISABLED)
                
                self.instructions_text.config(state=tk.NORMAL)
                self.instructions_text.delete(1.0, tk.END)
                self.instructions_text.config(state=tk.DISABLED)

    def search_recipes(self, event=None):
        """Search recipes by name using BST search"""
        query = self.search_entry.get().strip().lower()
        if not query:
            # If search is empty, show all recipes
            self.update_recipe_list()
            return

        # Search using the BST
        found_recipe = self.recipe_tree.search(query)
        
        if found_recipe:
            # Update the list to show only the found recipe
            self.recipe_listbox.delete(0, tk.END)
            self.recipe_listbox.insert(tk.END, found_recipe['name'])
            
            # Show the recipe details
            self.show_recipe_details_by_name(found_recipe['name'])
        else:
            # Search linearly through all recipes for partial matches
            matches = []
            for recipe in self.recipes:
                if query in recipe['name'].lower():
                    matches.append(recipe)
            
            if matches:
                # Show all partial matches in the list
                self.recipe_listbox.delete(0, tk.END)
                for recipe in matches:
                    self.recipe_listbox.insert(tk.END, recipe['name'])
                
                # Show details of first match
                self.show_recipe_details_by_name(matches[0]['name'])
            else:
                messagebox.showinfo("Search Results", f"No recipes found matching: '{query}'")

    def show_recipe_details_by_name(self, recipe_name):
        """Show details of a recipe by its name"""
        # First try BST search
        recipe = self.recipe_tree.search(recipe_name)
        
        if not recipe:
            # Fall back to linear search if not found in BST
            for r in self.recipes:
                if r['name'].lower() == recipe_name.lower():
                    recipe = r
                    break
        
        if recipe:
            # Update ingredients tab
            self.ingredients_text.config(state=tk.NORMAL)
            self.ingredients_text.delete(1.0, tk.END)
            self.ingredients_text.insert(tk.END, "\n".join(recipe['ingredients']))
            self.ingredients_text.config(state=tk.DISABLED)

            # Update instructions tab
            self.instructions_text.config(state=tk.NORMAL)
            self.instructions_text.delete(1.0, tk.END)
            self.instructions_text.insert(tk.END, "\n".join(recipe['instructions']))
            self.instructions_text.config(state=tk.DISABLED)

            # Find and select the recipe in the listbox
            for i in range(self.recipe_listbox.size()):
                if self.recipe_listbox.get(i) == recipe['name']:
                    self.recipe_listbox.selection_clear(0, tk.END)
                    self.recipe_listbox.selection_set(i)
                    self.recipe_listbox.activate(i)
                    break

            # Add to recently viewed stack
            if recipe['name'] not in self.recently_viewed:
                self.recently_viewed.append(recipe['name'])


if __name__ == "__main__":
    root = tk.Tk()
    app = RecipeManager(root)
    root.mainloop()