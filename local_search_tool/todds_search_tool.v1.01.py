#!/usr/bin/env python3
import requests
from tkinter import ttk, messagebox, Tk
import webbrowser
import json
import urllib.parse
import threading
import time
import subprocess
import atexit

class SearXNGSearchApp:
    def __init__(self, root):
        # Start Docker containers
        self.start_docker_containers()
        
        # Register cleanup function to stop containers on exit
        atexit.register(self.stop_docker_containers)
        
        self.root = root
        self.root.title('SearXNG Search Tool')
        self.root.geometry('800x600')

        # Create and place the search entry widget
        self.search_entry = ttk.Entry(root, width=50)
        self.search_entry.pack(pady=20)
        self.search_entry.bind('<Return>', lambda event: self.perform_search()) # Allow Enter key

        # Create and place the search button
        self.search_button = ttk.Button(root, text='Search', command=self.perform_search)
        self.search_button.pack()

        # Status label to show current state
        self.status_label = ttk.Label(root, text='Ready')
        self.status_label.pack(pady=5)

        # Treeview widget to display results (for demonstration only)
        self.results_tree = ttk.Treeview(root, columns=('URL'), show='headings')
        self.results_tree.heading('URL', text='Results')
        self.results_tree.column('URL', width=700)
        self.results_tree.pack(expand=True, fill='both', padx=20, pady=10)

        # Bind the treeview to open URLs (will be used when search works properly)
        self.results_tree.bind('<Double-1>', self.open_url)

    def perform_search(self):
        query = self.search_entry.get()
        if not query:
            messagebox.showwarning('Search Error', 'Please enter a search query.')
            return

        # Show that we're searching
        self.status_label.config(text='Searching...')
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.results_tree.insert('', 'end', values=('Searching...',))

        # Run search in background to avoid freezing GUI
        threading.Thread(target=self._search_background, args=(query,), daemon=True).start()

    def _search_background(self, query):
        """Search in background thread"""
        try:
            # Create the search URL that will work with your local SearXNG instance
            search_url = f'http://localhost:8080/search?q={urllib.parse.quote(query)}&format=html'
            
            # Try to access the actual SearXNG instance directly in browser for results
            # This bypasses API limitations by opening the web interface
            self.root.after(0, lambda: self.open_browser_search(query))
            
            # Update UI on main thread
            self.root.after(0, lambda: self.status_label.config(text='Search completed - results opened in browser'))
            
            # Clear search indicator and show status
            self.root.after(0, lambda: self._clear_search_indicator())

        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text='Error occurred'))
            self.root.after(0, lambda: messagebox.showerror('Search Error', f'Failed to process search: {e}'))

    def open_browser_search(self, query):
        """Open search in browser instead of trying to fetch API directly"""
        try:
            # Create the URL that will open in the browser
            search_url = f'http://localhost:8080/search?q={urllib.parse.quote(query)}'
            
            # Open in default browser (bypassing the API rate limiting restrictions)  
            webbrowser.open_new(search_url)
            
            # Update UI to show what happened
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            self.results_tree.insert('', 'end', values=(f'Opened search results for "{query}" in browser',))
            
        except Exception as e:
            messagebox.showerror('Browser Error', f'Failed to open browser: {e}')

    def _clear_search_indicator(self):
        """Clear the search indicator from the tree"""
        # This is just for demonstration - we'll actually update with proper browser results
        pass

    def open_url(self, event):
        """Open URL in browser for double-clicked items"""
        selected_item = self.results_tree.selection()
        if selected_item:
            url = self.results_tree.item(selected_item)['values'][0]
            if url and not url.startswith('Opened search'):
                webbrowser.open_new(url)

    def start_docker_containers(self):
        """Start the Docker containers for Valkey and SearXNG"""
        try:
            # First check if containers already exist and stop/remove them
            try:
                subprocess.run(['docker', 'stop', 'searxng'], check=True, capture_output=True)
                subprocess.run(['docker', 'rm', 'searxng'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                # Containers don't exist, which is fine
                pass
            
            try:
                subprocess.run(['docker', 'stop', 'searxng-valkey'], check=True, capture_output=True)
                subprocess.run(['docker', 'rm', 'searxng-valkey'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                # Containers don't exist, which is fine
                pass
            
            # Start Valkey container
            subprocess.run([
                'docker', 'run', '-d', '--name', 'searxng-valkey', 
                'valkey/valkey:9-alpine'
            ], check=True, capture_output=True)
            
            # Wait a moment for Valkey to start
            time.sleep(2)
            
            # Start SearXNG container with proper linking and port mapping
            subprocess.run([
                'docker', 'run', '-d', '--name', 'searxng', 
                '-p', '8080:8080', '--link', 'searxng-valkey:redis',
                'searxng/searxng:latest'
            ], check=True, capture_output=True)
            
            # Wait for containers to fully initialize
            time.sleep(5)
            
            print("Docker containers started successfully")
            
        except subprocess.CalledProcessError as e:
            messagebox.showerror('Docker Error', 
                                f'Failed to start Docker containers: {e.stderr.decode()}')
            raise

    def stop_docker_containers(self):
        """Stop and remove the Docker containers"""
        try:
            # Stop containers if they exist
            subprocess.run(['docker', 'stop', 'searxng'], check=True, capture_output=True)
            subprocess.run(['docker', 'stop', 'searxng-valkey'], check=True, capture_output=True)
            
            # Remove containers if they exist
            subprocess.run(['docker', 'rm', 'searxng'], check=True, capture_output=True)
            subprocess.run(['docker', 'rm', 'searxng-valkey'], check=True, capture_output=True)
            
            print("Docker containers stopped and removed successfully")
            
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to stop/remove Docker containers: {e.stderr.decode()}")

if __name__ == '__main__':
    root = Tk()
    app = SearXNGSearchApp(root)
    root.mainloop()