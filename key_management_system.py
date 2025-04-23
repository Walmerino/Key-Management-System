import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import serial


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
        messagebox.showerror("Serial Error", f"Error reading RFID: {e}")
    except KeyboardInterrupt:
        return None

def add_user_and_key_view():
    clear_right_frame()

    tk.Label(right_frame, text="Name:").grid(row=0, column=0, sticky="w")
    name_entry = tk.Entry(right_frame)
    name_entry.grid(row=0, column=1)

    def scan_rfid():
        rfid_token = read_rfid_as_decimal_string()
        if rfid_token:
            rfid_var.set(rfid_token)

    rfid_var = tk.StringVar()
    tk.Label(right_frame, text="RFID Token:").grid(row=1, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=rfid_var, state="readonly").grid(row=1, column=1)
    tk.Button(right_frame, text="Scan RFID", command=scan_rfid).grid(row=1, column=2)

    def add_user_and_key():
        name = name_entry.get()
        token = rfid_var.get()
        if not name or not token:
            messagebox.showerror("Error", "Name and RFID token are required.")
            return
        conn = sqlite3.connect("key_management.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, rfid_token) VALUES (?, ?)", (name, token))
        cursor.execute("INSERT INTO keys (rfid_token, status) VALUES (?, 'available')", (token,))
        conn.commit()
        conn.close()
        name_entry.delete(0, tk.END)
        rfid_var.set("")
        messagebox.showinfo("Success", "User and key added successfully.")

    tk.Button(right_frame, text="Add User and Key", command=add_user_and_key).grid(row=2, columnspan=3, pady=10)

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
                messagebox.showerror("Error", "No user associated with this RFID.")
            conn.close()

    tk.Label(right_frame, text="RFID Token:").grid(row=0, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=rfid_var, state="readonly").grid(row=0, column=1)
    tk.Label(right_frame, text="User Name:").grid(row=1, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=name_var, state="readonly").grid(row=1, column=1)
    tk.Button(right_frame, text="Scan RFID", command=scan_rfid).grid(row=1, column=2)

    def delete_user_and_key():
        rfid_token = rfid_var.get()
        if not rfid_token:
            messagebox.showerror("Error", "RFID token not detected.")
            return
        confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this user and their associated key?")
        if confirm:
            conn = sqlite3.connect("key_management.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE rfid_token = ?", (rfid_token,))
            cursor.execute("DELETE FROM keys WHERE rfid_token = ?", (rfid_token,))
            conn.commit()
            conn.close()
            rfid_var.set("")
            name_var.set("")
            messagebox.showinfo("Success", "User and associated key deleted successfully.")

    tk.Button(right_frame, text="Delete User and Key", command=delete_user_and_key).grid(row=2, columnspan=3, pady=10)

def add_key_and_house_view():
    clear_right_frame()

    tk.Label(right_frame, text="House:").grid(row=0, column=0, sticky="w")
    house_entry = tk.Entry(right_frame)
    house_entry.grid(row=0, column=1)

    def scan_rfid():
        rfid_token = read_rfid_as_decimal_string()
        if rfid_token:
            rfid_var.set(rfid_token)

    rfid_var = tk.StringVar()
    tk.Label(right_frame, text="RFID Token:").grid(row=1, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=rfid_var, state="readonly").grid(row=1, column=1)
    tk.Button(right_frame, text="Scan RFID", command=scan_rfid).grid(row=1, column=2)

    def add_key_and_house():
        house = house_entry.get()
        token = rfid_var.get()
        if not house or not token:
            messagebox.showerror("Error", "House and RFID token are required.")
            return
        try:
            conn = sqlite3.connect("key_management.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO houses (house_name, rfid_token) VALUES (?, ?)", (house, token))
            cursor.execute("INSERT INTO keys (rfid_token, status) VALUES (?, 'available')", (token,))
            conn.commit()
            conn.close()
            house_entry.delete(0, tk.END)
            rfid_var.set("")
            messagebox.showinfo("Success", "Key and house added successfully.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "This RFID token is already registered.")

    tk.Button(right_frame, text="Add Key and House", command=add_key_and_house).grid(row=2, columnspan=3, pady=10)

def delete_key_and_house_view():
    clear_right_frame()

    rfid_var = tk.StringVar()
    house_var = tk.StringVar()

    def scan_rfid():
        rfid_token = read_rfid_as_decimal_string()
        if not rfid_token:
            messagebox.showerror("Error", "RFID token not detected.")
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
            messagebox.showerror("Error", "No house associated with this RFID.")

    def delete_key_and_house():
        rfid_token = rfid_var.get()
        house_name = house_var.get()
        if not rfid_token:
            messagebox.showerror("Error", "RFID token not detected.")
            return
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete house '{house_name}' and its associated key (RFID: {rfid_token})?"
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
            messagebox.showinfo("Success", "Key and associated house deleted successfully.")

    tk.Label(right_frame, text="RFID Token:").grid(row=0, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=rfid_var, state="readonly").grid(row=0, column=1)

    tk.Label(right_frame, text="House Name:").grid(row=1, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=house_var, state="readonly").grid(row=1, column=1)

    tk.Button(right_frame, text="Scan RFID", command=scan_rfid).grid(row=1, column=2, padx=5)
    tk.Button(right_frame, text="Delete Key and House", command=delete_key_and_house).grid(row=2, columnspan=3, pady=10)

def view_users_view():
    clear_right_frame()

    tree = ttk.Treeview(right_frame, columns=("ID", "Name", "RFID"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Name", text="Name")
    tree.heading("RFID", text="RFID Token")
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
    tree.heading("RFID", text="RFID Token")
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
    house_rfid_var = tk.StringVar()
    house_name_var = tk.StringVar()

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
            else:
                messagebox.showerror("Error", "User not found.")

    def scan_house_rfid():
        token = read_rfid_as_decimal_string()
        if token:
            house_rfid_var.set(token)
            conn = sqlite3.connect("key_management.db")
            cursor = conn.cursor()
            cursor.execute("SELECT house_name FROM houses WHERE rfid_token = ?", (token,))
            result = cursor.fetchone()
            conn.close()
            if result:
                house_name_var.set(result[0])
            else:
                messagebox.showerror("Error", "House not found.")

    # Layout
    tk.Label(right_frame, text="User RFID:").grid(row=0, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=user_rfid_var, state="readonly").grid(row=0, column=1)
    tk.Button(right_frame, text="Scan User RFID", command=scan_user_rfid).grid(row=0, column=2)

    tk.Label(right_frame, text="User Name:").grid(row=1, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=user_name_var, state="readonly").grid(row=1, column=1)

    tk.Label(right_frame, text="House RFID:").grid(row=2, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=house_rfid_var, state="readonly").grid(row=2, column=1)
    tk.Button(right_frame, text="Scan House RFID", command=scan_house_rfid).grid(row=2, column=2)

    tk.Label(right_frame, text="House Name:").grid(row=3, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=house_name_var, state="readonly").grid(row=3, column=1)

    def confirm_pickup():
        user_rfid = user_rfid_var.get()
        house_rfid = house_rfid_var.get()
        if not user_rfid or not house_rfid:
            messagebox.showerror("Error", "Both RFID values are required.")
            return
        confirm = messagebox.askyesno("Confirm Pickup", f"Confirm key pickup?\n\nUser: {user_name_var.get()}\nHouse: {house_name_var.get()}")
        if confirm:
            conn = sqlite3.connect("key_management.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO key_pickups (user_rfid, house_rfid) VALUES (?, ?)", (user_rfid, house_rfid))
            cursor.execute("UPDATE keys SET status = 'picked_up' WHERE rfid_token = ?", (house_rfid,))
            conn.commit()
            conn.close()
            user_rfid_var.set("")
            user_name_var.set("")
            house_rfid_var.set("")
            house_name_var.set("")
            messagebox.showinfo("Success", "Key pickup recorded.")

    tk.Button(right_frame, text="Confirm Pickup", command=confirm_pickup).grid(row=4, columnspan=3, pady=10)

def return_key_view():
    clear_right_frame()

    rfid_var = tk.StringVar()
    house_rfid_var = tk.StringVar()
    name_var = tk.StringVar()
    house_name_var = tk.StringVar()

    def scan_user_rfid():
        rfid_token = read_rfid_as_decimal_string()
        if rfid_token:
            rfid_var.set(rfid_token)
            # Retrieve user associated with the RFID
            conn = sqlite3.connect("key_management.db")
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM users WHERE rfid_token = ?", (rfid_token,))
            user = cursor.fetchone()
            if user:
                name_var.set(user[0])
            else:
                messagebox.showerror("Error", "No user associated with this RFID.")
            conn.close()

    def scan_house_rfid():
        house_rfid = read_rfid_as_decimal_string()
        if house_rfid:
            house_rfid_var.set(house_rfid)
            # Retrieve house associated with the RFID
            conn = sqlite3.connect("key_management.db")
            cursor = conn.cursor()
            cursor.execute("SELECT house_name FROM houses WHERE rfid_token = ?", (house_rfid,))
            house = cursor.fetchone()
            if house:
                house_name_var.set(house[0])
            else:
                messagebox.showerror("Error", "No house associated with this RFID.")
            conn.close()

    tk.Label(right_frame, text="User RFID:").grid(row=0, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=rfid_var, state="readonly").grid(row=0, column=1)
    tk.Button(right_frame, text="Scan User RFID", command=scan_user_rfid).grid(row=0, column=2)

    tk.Label(right_frame, text="User Name:").grid(row=1, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=name_var, state="readonly").grid(row=1, column=1)

    tk.Label(right_frame, text="House RFID:").grid(row=2, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=house_rfid_var, state="readonly").grid(row=2, column=1)
    tk.Button(right_frame, text="Scan House RFID", command=scan_house_rfid).grid(row=2, column=2)

    tk.Label(right_frame, text="House Name:").grid(row=3, column=0, sticky="w")
    tk.Entry(right_frame, textvariable=house_name_var, state="readonly").grid(row=3, column=1)

    def return_key():
        user_rfid = rfid_var.get()
        house_rfid = house_rfid_var.get()

        if not user_rfid or not house_rfid:
            messagebox.showerror("Error", "Both User and House RFID are required.")
            return

        # Confirm the return action
        confirm = messagebox.askyesno("Confirm Return", f"Are you sure you want to return the key for user '{name_var.get()}' to house '{house_name_var.get()}'?")
        if confirm:
            # Record the return in the 'key_pickups' table
            conn = sqlite3.connect("key_management.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO key_pickups (user_rfid, house_rfid, timestamp)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (user_rfid, house_rfid))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Key returned successfully.")

    tk.Button(right_frame, text="Return Key", command=return_key).grid(row=4, columnspan=3, pady=10)

def view_assigned_keys_view():
    clear_right_frame()

    # Table
    tree = ttk.Treeview(right_frame, columns=("User", "House", "Pickup Time", "Return Time"), show="headings")
    tree.heading("User", text="User")
    tree.heading("House", text="House")
    tree.heading("Pickup Time", text="Pickup Time")
    tree.heading("Return Time", text="Return Time")
    tree.grid(row=0, column=0, sticky="nsew")

    # Scrollbar
    scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.grid(row=0, column=1, sticky="ns")

    # Load data from database
    conn = sqlite3.connect("key_management.db")
    cursor = conn.cursor()

    # Get pickup and return events sorted by user, house, and time
    cursor.execute("""
        SELECT 
            u.name AS user_name,
            h.house_name,
            kp.timestamp
        FROM key_pickups kp
        LEFT JOIN users u ON kp.user_rfid = u.rfid_token
        LEFT JOIN houses h ON kp.house_rfid = h.rfid_token
        ORDER BY u.name, h.house_name, kp.timestamp
    """)
    records = cursor.fetchall()
    conn.close()

    # Pair entries: pickup and return (every two rows)
    paired_records = []
    i = 0
    while i < len(records) - 1:
        user1, house1, pickup_time = records[i]
        user2, house2, return_time = records[i + 1]

        if user1 == user2 and house1 == house2:
            paired_records.append((user1, house1, pickup_time, return_time))
            i += 2
        else:
            paired_records.append((user1, house1, pickup_time, "—"))
            i += 1

    # Add remaining unpaired record
    if i == len(records) - 1:
        user, house, pickup_time = records[i]
        paired_records.append((user, house, pickup_time, "—"))

    # Insert into the tree view
    for rec in paired_records:
        tree.insert("", "end", values=rec)


# GUI Setup
root = tk.Tk()
root.title("Key Management System")
root.geometry("900x500")

main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True)

left_frame = tk.Frame(main_frame, width=200, bg="#f0f0f0")
left_frame.pack(side="left", fill="y")

right_frame = tk.Frame(main_frame)
right_frame.pack(side="right", fill="both", expand=True)

button_list = [
    ("Pickup Key", pickup_key_view),
    ("Return Key", return_key_view),
    ("View Assigned Keys", view_assigned_keys_view),
    ("Add User", add_user_and_key_view),
    ("Delete User", delete_user_and_key_view),
    ("View Users", view_users_view),
    ("Add Key and House", add_key_and_house_view),
    ("Delete Key and House", delete_key_and_house_view),
    ("View Houses", view_houses_view),
    
]

for label, command in button_list:
    btn = tk.Button(left_frame, text=label, command=command, height=2, width=20)
    btn.pack(fill="x", pady=2)

root.mainloop()
