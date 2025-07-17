import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import serial
from datetime import datetime
import csv
from PIL import Image, ImageTk

def initialize_database():
    conn = sqlite3.connect("key_management.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            rfid_token TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rfid_token TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY(rfid_token) REFERENCES users(rfid_token)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS houses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            house_name TEXT NOT NULL,
            rfid_token TEXT UNIQUE NOT NULL,
            FOREIGN KEY(rfid_token) REFERENCES keys(rfid_token)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS key_pickups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_rfid TEXT NOT NULL,
            house_rfid TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_rfid) REFERENCES users (rfid_token),
            FOREIGN KEY (house_rfid) REFERENCES houses (rfid_token)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS key_returns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_rfid TEXT NOT NULL,
            house_rfid TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (user_rfid) REFERENCES users (rfid_token),
            FOREIGN KEY (house_rfid) REFERENCES houses (rfid_token)
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pickups_user ON key_pickups(user_rfid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pickups_house ON key_pickups(house_rfid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_returns_user ON key_returns(user_rfid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_returns_house ON key_returns(house_rfid)")
    
    conn.commit()
    conn.close()
    messagebox.showinfo("Erfolg", "Datenbank initialisiert oder bereits vorhanden.")
    

def dashboard_view():
    clear_right_frame()

    tk.Label(right_frame, text="🔑 Sentinela", font=("Arial", 20, "bold")).pack(pady=20)

    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    tk.Label(right_frame, text=f"📅 Aktuelles Datum und Uhrzeit: {now}", font=("Arial", 12)).pack(pady=5)

    try:
        conn = sqlite3.connect("key_management.db")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        tk.Label(right_frame, text=f"👥 Anzahl Benutzer: {user_count}", font=("Arial", 12)).pack(pady=5)

        cursor.execute("""
            SELECT COUNT(*) FROM key_pickups
            WHERE DATE(timestamp) = DATE('now', 'localtime')
        """)
        today_pickups = cursor.fetchone()[0]
        tk.Label(right_frame, text=f"📦 Abholungen heute: {today_pickups}", font=("Arial", 12)).pack(pady=5)

        conn.close()
    except Exception as e:
        tk.Label(right_frame, text=f"Fehler beim Laden der Daten: {e}", fg="red").pack(pady=5)

    # Load and display image
    try:
        image = Image.open("logo1.png")
        image = image.resize((300, 350), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)

        img_label = tk.Label(right_frame, image=photo)
        img_label.image = photo  # Keep a reference!
        img_label.pack(pady=20)
    except Exception as e:
        tk.Label(right_frame, text=f"Bild konnte nicht geladen werden: {e}", fg="red").pack(pady=5)

def clear_right_frame():
    for widget in right_frame.winfo_children():
        widget.destroy()

def read_rfid_as_decimal_string(serial_port="/dev/ttyUSB0", baud_rate=9600):
    try:        
        with serial.Serial(serial_port, baud_rate, timeout=5) as ser:
            while True:
                line = ser.readline().decode('utf-8').strip()
                if line.startswith("Card UID:"): 
                    uid_hex = line.replace("Card UID:", "").strip()
                    uid_bytes = [int(byte, 16) for byte in uid_hex.split()]
                    token = ''.join([f"{byte:03d}" for byte in uid_bytes])
                    return token
    except serial.SerialException as e:
        messagebox.showerror("Serial Error", "Fehler beim Lesen des RFID: {e}")
    except KeyboardInterrupt:
        return None

def add_user_and_key_view():
    clear_right_frame()

    tk.Label(right_frame, text="Name:").grid(row=0, column=0, sticky="w")
    name_entry = tk.Entry(right_frame)
    name_entry.grid(row=0, column=1)

    rfid_var = tk.StringVar()

    def scan_rfid():
        rfid_token = read_rfid_as_decimal_string()
        if rfid_token:
            rfid_var.set(rfid_token)

    tk.Label(right_frame, text="RFID-Token:").grid(row=1, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=rfid_var, state="readonly").grid(row=1, column=1)
    tk.Button(right_frame, text="RFID scannen", command=scan_rfid).grid(row=1, column=2)

    def clear_inputs():
        name_entry.delete(0, tk.END)
        rfid_var.set("")

    def add_user_and_key():
        name = name_entry.get().strip()
        token = rfid_var.get().strip()
        if not name or not token:
            messagebox.showerror("Error", "Name und RFID-Token sind erforderlich.")
            clear_inputs()
            return

        conn = sqlite3.connect("key_management.db")
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM users WHERE rfid_token = ?", (token,))
        if cursor.fetchone():
            messagebox.showerror("Error", "Dieses RFID ist bereits einem Benutzer zugewiesen.")
            conn.close()
            clear_inputs()
            return

        cursor.execute("SELECT 1 FROM users WHERE name = ?", (name,))
        if cursor.fetchone():
            messagebox.showerror("Error", "Dieser Name ist bereits registriert.")
            conn.close()
            clear_inputs()
            return

        cursor.execute("INSERT INTO users (name, rfid_token) VALUES (?, ?)", (name, token))
        cursor.execute("INSERT INTO keys (rfid_token, status) VALUES (?, 'available')", (token,))
        conn.commit()
        conn.close()

        clear_inputs()
        messagebox.showinfo("Success", "Benutzer und Schlüssel erfolgreich hinzugefügt.")

    tk.Button(right_frame, text="Benutzer und Schlüssel hinzufügen", command=add_user_and_key).grid(row=2, columnspan=3, pady=10)



def delete_user_and_key_view():
    clear_right_frame()

    rfid_var = tk.StringVar()
    name_var = tk.StringVar()

    def scan_rfid():
        rfid_token = read_rfid_as_decimal_string()
        if rfid_token:
            rfid_var.set(rfid_token)
            conn = sqlite3.connect("key_management.db")
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM users WHERE rfid_token = ?", (rfid_token,))
            user = cursor.fetchone()
            if user:
                name_var.set(user[0])
            else:
                messagebox.showerror("Error", "Kein Benutzer mit diesem RFID gefunden.")
            conn.close()

    tk.Label(right_frame, text="RFID-Token:").grid(row=0, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=rfid_var, state="readonly").grid(row=0, column=1)
    tk.Label(right_frame, text="Benutzername:").grid(row=1, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=name_var, state="readonly").grid(row=1, column=1)
    tk.Button(right_frame, text="RFID scannen", command=scan_rfid).grid(row=1, column=2)

    def delete_user_and_key():
        rfid_token = rfid_var.get()
        if not rfid_token:
            messagebox.showerror("Error", "RFID-Token not detected.")
            return
        confirm = messagebox.askyesno("Löschung bestätigen", "Möchten Sie diesen Benutzer und seinen Schlüssel wirklich löschen?")
        if confirm:
            conn = sqlite3.connect("key_management.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE rfid_token = ?", (rfid_token,))
            cursor.execute("DELETE FROM keys WHERE rfid_token = ?", (rfid_token,))
            conn.commit()
            conn.close()
            rfid_var.set("")
            name_var.set("")
            messagebox.showinfo("Erfolg", "Benutzer und zugehöriger Schlüssel erfolgreich gelöscht.")

    tk.Button(right_frame, text="Benutzer und Schlüssel löschen", command=delete_user_and_key).grid(row=2, columnspan=3, pady=10)

def add_key_and_house_view():
    clear_right_frame()

    tk.Label(right_frame, text="Haus:").grid(row=0, column=0, sticky="w")
    house_entry = tk.Entry(right_frame)
    house_entry.grid(row=0, column=1)

    rfid_var = tk.StringVar()

    def scan_rfid():
        rfid_token = read_rfid_as_decimal_string()
        if rfid_token:
            rfid_var.set(rfid_token)

    tk.Label(right_frame, text="RFID-Token:").grid(row=1, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=rfid_var, state="readonly").grid(row=1, column=1)
    tk.Button(right_frame, text="RFID scannen", command=scan_rfid).grid(row=1, column=2)

    def add_key_and_house():
        house = house_entry.get().strip()
        token = rfid_var.get().strip()
        if not house or not token:
            messagebox.showerror("Error", "Haus und RFID-Token sind erforderlich.")
            return

        conn = sqlite3.connect("key_management.db")
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM houses WHERE rfid_token = ?", (token,))
        if cursor.fetchone():
            messagebox.showerror("Error", "Dieses RFID ist bereits einem Haus zugeordnet.")
            conn.close()
            return

        cursor.execute("SELECT 1 FROM houses WHERE house_name = ?", (house,))
        if cursor.fetchone():
            messagebox.showerror("Fehler", "Dieser Hausname existiert bereits.")
            conn.close()
            return

        cursor.execute("INSERT INTO houses (house_name, rfid_token) VALUES (?, ?)", (house, token))
        cursor.execute("INSERT INTO keys (rfid_token, status) VALUES (?, 'available')", (token,))
        conn.commit()
        conn.close()

        house_entry.delete(0, tk.END)      # Clear house name
        rfid_var.set("")                   # Clear RFID
        messagebox.showinfo("Erfolg", "Schlüssel und Haus wurden erfolgreich hinzugefügt.")


    tk.Button(right_frame, text="Schlüssel und Haus hinzufügen", command=add_key_and_house).grid(row=2, columnspan=3, pady=10)



def delete_key_and_house_view():
    clear_right_frame()

    rfid_var = tk.StringVar()
    house_var = tk.StringVar()

    def scan_rfid():
        rfid_token = read_rfid_as_decimal_string()
        if not rfid_token:
            messagebox.showerror("Error", "RFID-Token not detected.")
            return
        rfid_var.set(rfid_token)
        conn = sqlite3.connect("key_management.db")
        cursor = conn.cursor()
        cursor.execute("SELECT house_name FROM houses WHERE rfid_token = ?", (rfid_token,))
        result = cursor.fetchone()
        conn.close()
        if result:
            house_var.set(result[0])
        else:
            house_var.set("")
            messagebox.showerror("Error", "Kein Haus mit diesem RFID gefunden.")

    def delete_key_and_house():
        rfid_token = rfid_var.get()
        house_name = house_var.get()
        if not rfid_token:
            messagebox.showerror("Error", "RFID-Token nicht erkannt.")
            return
        confirm = messagebox.askyesno(
            "Löschung bestätigen",
            f"Möchten Sie dieses Haus'{house_name}' und seinen Schlüssel wirklich löschen (RFID: {rfid_token})?"
        )
        if confirm:
            conn = sqlite3.connect("key_management.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM houses WHERE rfid_token = ?", (rfid_token,))
            cursor.execute("DELETE FROM keys WHERE rfid_token = ?", (rfid_token,))
            conn.commit()
            conn.close()
            rfid_var.set("")
            house_var.set("")
            messagebox.showinfo("Erfolg", "Schlüssel und zugehöriges Haus wurden erfolgreich gelöscht.")


    tk.Label(right_frame, text="RFID-Token:").grid(row=0, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=rfid_var, state="readonly").grid(row=0, column=1)

    tk.Label(right_frame, text="Hausname:").grid(row=1, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=house_var, state="readonly").grid(row=1, column=1)

    tk.Button(right_frame, text="RFID scannen", command=scan_rfid).grid(row=1, column=2, padx=5)
    tk.Button(right_frame, text="Schlüssel und Haus löschen", command=delete_key_and_house).grid(row=2, columnspan=3, pady=10)

def view_users_view():
    clear_right_frame()

    tree = ttk.Treeview(right_frame, columns=("ID", "Name", "RFID"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Name", text="Name")
    tree.heading("RFID", text="RFID-Token")
    tree.pack(fill="both", expand=True)

    conn = sqlite3.connect("key_management.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, rfid_token FROM users")
    for row in cursor.fetchall():
        tree.insert("", "end", values=row)
    conn.close()
    
def view_houses_view():
    clear_right_frame()

    tree = ttk.Treeview(right_frame, columns=("ID", "House", "RFID"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("House", text="House Name")
    tree.heading("RFID", text="RFID-Token")
    tree.pack(fill="both", expand=True)

    conn = sqlite3.connect("key_management.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, house_name, rfid_token FROM houses")
    for row in cursor.fetchall():
        tree.insert("", "end", values=row)
    conn.close()

def pickup_key_view():
    clear_right_frame()

    user_rfid_var = tk.StringVar()
    user_name_var = tk.StringVar()
    picked_keys = []

    tk.Label(right_frame, text="Benutzer-RFID:").grid(row=0, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=user_rfid_var, state="readonly").grid(row=0, column=1)
    tk.Button(right_frame, text="Benutzer-RFID scannen", command=lambda: scan_user_rfid()).grid(row=0, column=2)

    tk.Label(right_frame, text="Benutzername:").grid(row=1, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=user_name_var, state="readonly").grid(row=1, column=1)

    listbox_label = tk.Label(right_frame, text="Abgeholte Schlüssel:")
    listbox_label.grid(row=2, column=0, sticky="w", pady=(10, 0))

    key_listbox = tk.Listbox(right_frame, width=40, height=8)
    key_listbox.grid(row=3, column=0, columnspan=3, padx=5, pady=5)

    def scan_user_rfid():
        token = read_rfid_as_decimal_string()
        if token:
            user_rfid_var.set(token)
            conn = sqlite3.connect("key_management.db")
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM users WHERE rfid_token = ?", (token,))
            result = cursor.fetchone()
            conn.close()
            if result:
                user_name_var.set(result[0])
                messagebox.showinfo("Bereit", "Benutzer erkannt. Jetzt Hausschlüssel einscannen.")
            else:
                messagebox.showerror("Fehler", "Benutzer nicht gefunden.")

    def scan_next_key():
        token = read_rfid_as_decimal_string()
        if not token:
            return
        conn = sqlite3.connect("key_management.db")
        cursor = conn.cursor()
        cursor.execute("SELECT house_name FROM houses WHERE rfid_token = ?", (token,))
        result = cursor.fetchone()
        if result:
            house_name = result[0]
            house_rfid = token
            cursor.execute("INSERT INTO key_pickups (user_rfid, house_rfid) VALUES (?, ?)", 
                           (user_rfid_var.get(), house_rfid))
            cursor.execute("UPDATE keys SET status = 'picked_up' WHERE rfid_token = ?", (house_rfid,))
            conn.commit()
            picked_keys.append(house_name)
            key_listbox.insert(tk.END, house_name)
        else:
            messagebox.showerror("Fehler", "Haus nicht gefunden.")
        conn.close()

    def finish_pickup():
        user_rfid_var.set("")
        user_name_var.set("")
        picked_keys.clear()
        key_listbox.delete(0, tk.END)
        messagebox.showinfo("Fertig", "Schlüsselabholungen abgeschlossen.")

    # Extra buttons
    tk.Button(right_frame, text="Hausschlüssel scannen", command=scan_next_key, bg="#f0f0f0").grid(row=4, column=0, pady=10)
    tk.Button(right_frame, text="Fertig", command=finish_pickup, bg="#d0ffd0").grid(row=4, column=1, pady=10)


def return_key_view():
    clear_right_frame()

    user_rfid_var = tk.StringVar()
    user_name_var = tk.StringVar()
    returned_keys = []

    # Layout
    tk.Label(right_frame, text="Benutzer-RFID:").grid(row=0, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=user_rfid_var, state="readonly").grid(row=0, column=1)
    tk.Button(right_frame, text="Benutzer-RFID scannen", command=lambda: scan_user_rfid()).grid(row=0, column=2)

    tk.Label(right_frame, text="Benutzername:").grid(row=1, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=user_name_var, state="readonly").grid(row=1, column=1)

    listbox_label = tk.Label(right_frame, text="Zurückgegebene Schlüssel:")
    listbox_label.grid(row=2, column=0, sticky="w", pady=(10, 0))

    key_listbox = tk.Listbox(right_frame, width=40, height=8)
    key_listbox.grid(row=3, column=0, columnspan=3, padx=5, pady=5)

    def scan_user_rfid():
        token = read_rfid_as_decimal_string()
        if token:
            user_rfid_var.set(token)
            conn = sqlite3.connect("key_management.db")
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM users WHERE rfid_token = ?", (token,))
            result = cursor.fetchone()
            conn.close()
            if result:
                user_name_var.set(result[0])
                messagebox.showinfo("Bereit", "Benutzer erkannt. Jetzt Hausschlüssel zum Zurückgeben einscannen.")
            else:
                messagebox.showerror("Fehler", "Benutzer nicht gefunden.")

    def scan_next_return_key():
        token = read_rfid_as_decimal_string()
        if not token:
            return

        conn = sqlite3.connect("key_management.db")
        cursor = conn.cursor()

        cursor.execute("SELECT house_name FROM houses WHERE rfid_token = ?", (token,))
        result = cursor.fetchone()

        if result:
            house_name = result[0]
            house_rfid = token

            # Insert return record
            cursor.execute("""
                INSERT INTO key_returns (user_rfid, house_rfid, timestamp)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (user_rfid_var.get(), house_rfid))

            # Update key status (optional if tracked)
            cursor.execute("UPDATE keys SET status = 'available' WHERE rfid_token = ?", (house_rfid,))
            conn.commit()
            conn.close()

            returned_keys.append(house_name)
            key_listbox.insert(tk.END, house_name)
        else:
            conn.close()
            messagebox.showerror("Fehler", "Haus nicht gefunden.")

    def finish_return():
        user_rfid_var.set("")
        user_name_var.set("")
        returned_keys.clear()
        key_listbox.delete(0, tk.END)
        messagebox.showinfo("Fertig", "Schlüsselrückgaben abgeschlossen.")

    tk.Button(right_frame, text="Hausschlüssel scannen", command=scan_next_return_key, bg="#f0f0f0").grid(row=4, column=0, pady=10)
    tk.Button(right_frame, text="Fertig", command=finish_return, bg="#d0ffd0").grid(row=4, column=1, pady=10)


def view_assigned_keys_view():
    clear_right_frame()
    
    # 1. Create frames with visible borders for debugging
    top_frame = tk.Frame(right_frame, bd=2, relief=tk.RAISED, bg="#f0f0f0")
    top_frame.pack(fill=tk.X, padx=5, pady=5)
    
    middle_frame = tk.Frame(right_frame)
    middle_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    bottom_frame = tk.Frame(right_frame, bd=2, relief=tk.SUNKEN, bg="#f0f0f0")
    bottom_frame.pack(fill=tk.X, padx=5, pady=5)

    # 2. Add buttons with distinct colors
    btn_style = {
        'padx': 10, 
        'pady': 5,
        'bd': 2,
        'relief': tk.RAISED,
        'font': ('Arial', 10)
    }
    
    refresh_btn = tk.Button(top_frame, text="Refresh", bg="#e6f3ff", **btn_style)
    show_nr_btn = tk.Button(top_frame, text="Non-Returned", bg="#fff2e6", **btn_style)
    export_nr_btn = tk.Button(top_frame, text="Export NR CSV", bg="#e6ffe6", **btn_style) 
    export_all_btn = tk.Button(top_frame, text="Export All CSV", bg="#f0e6ff", **btn_style)
    
    # Pack buttons horizontally
    refresh_btn.pack(side=tk.LEFT, padx=5)
    show_nr_btn.pack(side=tk.LEFT, padx=5)
    export_nr_btn.pack(side=tk.LEFT, padx=5)
    export_all_btn.pack(side=tk.LEFT, padx=5)

    # 3. Add treeview with scrollbars (all assignments)
    tree = ttk.Treeview(middle_frame, columns=("User", "House", "Pickup", "Return"), show="headings")
    tree.heading("User", text="User")
    tree.heading("House", text="House")
    tree.heading("Pickup", text="Pickup Time")
    tree.heading("Return", text="Return Time")
    
    vsb = ttk.Scrollbar(middle_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(middle_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    
    middle_frame.grid_rowconfigure(0, weight=1)
    middle_frame.grid_columnconfigure(0, weight=1)

    # --- 3b. Add Treeview for non-returned keys ---
    nr_label = tk.Label(middle_frame, text="🔒 Currently Non-returned Keys", font=('Arial', 11, 'bold'), anchor="w")
    nr_label.grid(row=2, column=0, sticky="w", pady=(10, 0))

    nr_tree = ttk.Treeview(middle_frame, columns=("User", "House", "Pickup"), show="headings")
    nr_tree.heading("User", text="User")
    nr_tree.heading("House", text="House")
    nr_tree.heading("Pickup", text="Pickup Time")
    nr_tree.grid(row=3, column=0, sticky="nsew", pady=(0, 5))

    nr_scrollbar = ttk.Scrollbar(middle_frame, orient="vertical", command=nr_tree.yview)
    nr_tree.configure(yscrollcommand=nr_scrollbar.set)
    nr_scrollbar.grid(row=3, column=1, sticky="ns")

    middle_frame.grid_rowconfigure(3, weight=1)

    # 4. Add status label
    status_var = tk.StringVar()
    status_var.set("Ready")
    status_label = tk.Label(bottom_frame, textvariable=status_var, bg="#f0f0f0")
    status_label.pack()

    # 5. Database functions
    def load_data():
        try:
            tree.delete(*tree.get_children())
            nr_tree.delete(*nr_tree.get_children())
            with sqlite3.connect("key_management.db") as conn:
                cursor = conn.cursor()
                
                # Get all key assignments
                cursor.execute("""
                    SELECT u.name, h.house_name, kp.timestamp, 
                           (SELECT MIN(kr.timestamp) 
                            FROM key_returns kr 
                            WHERE kr.user_rfid = kp.user_rfid 
                            AND kr.house_rfid = kp.house_rfid
                            AND kr.timestamp > kp.timestamp)
                    FROM key_pickups kp
                    JOIN users u ON kp.user_rfid = u.rfid_token
                    JOIN houses h ON kp.house_rfid = h.rfid_token
                    ORDER BY kp.timestamp DESC
                """)
                
                for row in cursor.fetchall():
                    return_time = row[3] if row[3] else "Not Returned"
                    tree.insert("", tk.END, values=row[:3] + (return_time,))
                
                # Count and show non-returned keys
                cursor.execute("""
                    SELECT COUNT(*) FROM key_pickups kp
                    WHERE NOT EXISTS (
                        SELECT 1 FROM key_returns kr 
                        WHERE kr.user_rfid = kp.user_rfid
                        AND kr.house_rfid = kp.house_rfid
                        AND kr.timestamp > kp.timestamp
                    )
                """)
                count = cursor.fetchone()[0]
                status_var.set(f"Non-returned Keys: {count}")

                # Load non-returned details into nr_tree
                cursor.execute("""
                    SELECT u.name, h.house_name, kp.timestamp
                    FROM key_pickups kp
                    JOIN users u ON kp.user_rfid = u.rfid_token
                    JOIN houses h ON kp.house_rfid = h.rfid_token
                    WHERE NOT EXISTS (
                        SELECT 1 FROM key_returns kr 
                        WHERE kr.user_rfid = kp.user_rfid
                        AND kr.house_rfid = kp.house_rfid
                        AND kr.timestamp > kp.timestamp
                    )
                    ORDER BY kp.timestamp DESC
                """)
                for row in cursor.fetchall():
                    nr_tree.insert("", tk.END, values=row)

        except Exception as e:
            messagebox.showerror("Error", f"Database error: {str(e)}")
            status_var.set("Error loading data")

    def export_csv(records, headers, filename_prefix):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(records)
            messagebox.showinfo("Success", f"Exported to {filename}")
            status_var.set(f"Exported {len(records)} records")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Error: {str(e)}")
            status_var.set("Export failed")

    def export_non_returned():
        try:
            with sqlite3.connect("key_management.db") as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.name, h.house_name, kp.timestamp
                    FROM key_pickups kp
                    JOIN users u ON kp.user_rfid = u.rfid_token
                    JOIN houses h ON kp.house_rfid = h.rfid_token
                    WHERE NOT EXISTS (
                        SELECT 1 FROM key_returns kr 
                        WHERE kr.user_rfid = kp.user_rfid
                        AND kr.house_rfid = kp.house_rfid
                        AND kr.timestamp > kp.timestamp
                    )
                    ORDER BY kp.timestamp DESC
                """)
                export_csv(cursor.fetchall(), 
                           ["User", "House", "Pickup Time"],
                           "non_returned_keys")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")

    def export_all_assignments():
        try:
            with sqlite3.connect("key_management.db") as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT 
                    u.name AS user_name,
                    h.house_name,
                    kp.timestamp AS pickup_time,
                    (
                        SELECT MIN(kr.timestamp)
                        FROM key_returns kr
                        WHERE kr.user_rfid = kp.user_rfid
                          AND kr.house_rfid = kp.house_rfid
                          AND kr.timestamp > kp.timestamp
                    ) AS return_time
                FROM key_pickups kp
                JOIN users u ON kp.user_rfid = u.rfid_token
                JOIN houses h ON kp.house_rfid = h.rfid_token
                ORDER BY kp.timestamp DESC
            """)
            rows = cursor.fetchall()

            # Add 'Not Returned' if return_time is NULL
            formatted_rows = [
                (user, house, pickup, return_time if return_time else "Not Returned")
                for user, house, pickup, return_time in rows
            ]

            export_csv(formatted_rows,
                       ["User", "House", "Pickup Time", "Return Time"],
                       "all_key_assignments")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")
    # 6. Configure button commands
    refresh_btn.config(command=load_data)
    show_nr_btn.config(command=lambda: messagebox.showinfo("Non-Returned Keys", status_var.get()))
    export_nr_btn.config(command=export_non_returned)
    export_all_btn.config(command=export_all_assignments)

    # 7. Initial data load
    load_data()




# GUI Setup
root = tk.Tk()
root.title("Sentinela")
root.geometry("1000x600")

main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True)

left_frame = tk.Frame(main_frame, width=200, bg="#f0f0f0")
left_frame.pack(side="left", fill="y")

right_frame = tk.Frame(main_frame)
right_frame.pack(side="right", fill="both", expand=True)

button_list = [
    ("🏠 Startseite", dashboard_view),
    ("Abholschlüssel", pickup_key_view),
    ("Rückgabeschlüssel", return_key_view),
    ("Zugewiesene Schlüssel anzeigen", view_assigned_keys_view),
    ("Benutzer hinzufügen", add_user_and_key_view),
    ("Benutzer löschen", delete_user_and_key_view),
    ("Benutzer anzeigen", view_users_view),
    ("Schlüssel und Haus hinzufügen", add_key_and_house_view),
    ("Schlüssel und Haus löschen", delete_key_and_house_view),
    ("Häuser ansehen", view_houses_view),
    ("Datenbank initialisieren",initialize_database),

]

for label, command in button_list:
    btn = tk.Button(left_frame, text=label, command=command, height=2, width=24)
    btn.pack(fill="x", pady=2)

# Show dashboard at startup
dashboard_view()

root.mainloop()
