# Key-Management-System
Management System for keys and users.
This Python code defines a graphical user interface (GUI) for managing users, keys, and houses using RFID (Radio Frequency Identification) tokens. It uses the `tkinter` library for the GUI and interacts with a SQLite database to store and retrieve information. Additionally, it communicates with an RFID reader via a serial connection to capture RFID tokens.

 Key Components:
1. RFID Communication:
   - The code interacts with an RFID reader via the `serial` library to read RFID tokens. The `read_rfid_as_decimal_string()` function reads the UID of an RFID card, processes it into a decimal string, and returns it.

2. User Management:
   - `add_user_and_key_view()` allows adding users by entering their name and scanning their RFID token. The name and RFID are stored in the `users` table, and the key's status is set as 'available' in the `keys` table.
   - `delete_user_and_key_view()` allows the deletion of a user and their associated key by scanning the user's RFID token.

3. House Management:
   - `add_key_and_house_view()` allows adding a house and associating an RFID token with it. The key is marked as 'available'.
   - `delete_key_and_house_view()` allows deleting a house and its associated key by scanning the RFID token.
   - `view_houses_view()` shows all houses with their associated RFID tokens in a treeview.

4. Key Pickup and Return:
   - `pickup_key_view()` handles key pickups, where a user can scan their RFID token and the RFID of a house to record the pickup in the database. The key's status is changed to 'picked_up'.
   - `return_key_view()` allows users to return keys, and it records the return action in the `key_pickups` table.

5. Views:
   - `view_users_view()` displays a list of users with their IDs, names, and RFID tokens in a treeview.
   - `view_assigned_keys_view()` shows a list of key pickups and returns, displaying user names, house names, pickup times, and return times.

 Functionality Overview:
- Clear Right Frame: `clear_right_frame()` removes all existing widgets from the right side of the window before displaying new content.
- Scan RFID Tokens: Each view includes a button to scan an RFID token. When a token is scanned, the associated information (name, house) is retrieved from the database and displayed.
- Database Interactions: The SQLite database (`key_management.db`) is used to store and retrieve data about users, houses, and key pickups. SQL queries are executed to insert, select, and delete records from the `users`, `houses`, and `keys` tables.
- Dialogs: The code uses `messagebox` from `tkinter` to show success or error messages and confirmations (for actions like deletion or pickups).

 Detailed Breakdown of Specific Functions:
1. `add_user_and_key_view()`:
   - Clears the right frame.
   - Displays input fields for entering a user's name and scanning an RFID token.
   - Adds a user and key to the database when the "Add User and Key" button is clicked.

2. `delete_user_and_key_view()`:
   - Clears the right frame.
   - Scans an RFID token and retrieves the associated user's name.
   - Deletes the user and key from the database when the "Delete User and Key" button is clicked.

3. `add_key_and_house_view()`:
   - Clears the right frame.
   - Displays input fields for entering a house's name and scanning an RFID token.
   - Adds a key and house to the database when the "Add Key and House" button is clicked.

4. `delete_key_and_house_view()`:
   - Clears the right frame.
   - Scans an RFID token and retrieves the associated house's name.
   - Deletes the house and key from the database when the "Delete Key and House" button is clicked.

5. `pickup_key_view()`:
   - Clears the right frame.
   - Scans a user's RFID and a house's RFID to register the key pickup.
   - Updates the key's status to 'picked_up' in the database.

6. `return_key_view()`:
   - Clears the right frame.
   - Scans a user's RFID and a house's RFID to register the key return.
   - Records the return in the database and updates the status of the key.

7. `view_users_view()` and `view_houses_view()`:
   - Display lists of users and houses with their associated RFID tokens in a treeview.

 Overall Flow:
The code provides a GUI where users can interact with an RFID system to manage users, houses, and keys. The database stores information about users, houses, and keys, and actions like adding, deleting, picking up, and returning keys are reflected in the database.
