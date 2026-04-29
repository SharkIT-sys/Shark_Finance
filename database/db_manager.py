import sqlite3
import os
import hashlib
import time
from utils.crypto_manager import CryptoManager

class DBManager:
    def __init__(self, db_path="budget_app.db"):
        self.db_path = db_path
        self.crypto = CryptoManager()
        self._init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def _mark_updated(self, conn=None):
        timestamp = str(int(time.time() * 1000))
        if conn:
            conn.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', ('last_updated', timestamp))
        else:
            with self.get_connection() as c:
                c.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', ('last_updated', timestamp))
                c.commit()

    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create Categories Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    color TEXT NOT NULL
                )
            ''')
            
            # Create Transactions Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    category_id INTEGER,
                    name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    recurrence_type TEXT DEFAULT 'one_time',
                    recurrence_interval INTEGER DEFAULT 1,
                    recurrence_duration INTEGER DEFAULT NULL,
                    FOREIGN KEY(category_id) REFERENCES categories(id)
                )
            ''')
            
            # Create Config Table for settings/password
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            
            # Create Commitments Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS commitments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    total_amount TEXT NOT NULL,
                    date TEXT NOT NULL
                )
            ''')
            
            # Create Commitment Payments Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS commitment_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    commitment_id INTEGER,
                    amount TEXT NOT NULL,
                    date TEXT NOT NULL,
                    FOREIGN KEY(commitment_id) REFERENCES commitments(id)
                )
            ''')
            
            # Create Savings Goals Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS savings_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    target_amount TEXT NOT NULL,
                    date TEXT NOT NULL
                )
            ''')
            
            # Create Savings Contributions Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS savings_contributions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    savings_id INTEGER,
                    amount TEXT NOT NULL,
                    date TEXT NOT NULL,
                    FOREIGN KEY(savings_id) REFERENCES savings_goals(id)
                )
            ''')
            
            conn.commit()
            
            # Initialize Default Categories if empty
            cursor.execute('SELECT COUNT(*) FROM categories')
            if cursor.fetchone()[0] == 0:
                self._insert_default_categories(cursor)
                conn.commit()

    def _insert_default_categories(self, cursor):
        # Default expense colors specified by user
        default_expenses = [
            ("Vivienda", "expense", "#E74C3C"),
            ("Comida", "expense", "#F39C12"),
            ("Transporte", "expense", "#3498DB"),
            ("Ocio", "expense", "#9B59B6"),
            ("Suscripciones", "expense", "#2ECC71")
        ]
        
        # Some default income categories
        default_incomes = [
            ("Salario", "income", "#27AE60"),
            ("Freelance", "income", "#F1C40F"),
            ("Regalos", "income", "#8E44AD"),
            ("Inversiones", "income", "#2980B9")
        ]
        
        for name, c_type, color in default_expenses + default_incomes:
            cursor.execute(
                'INSERT INTO categories (name, type, color) VALUES (?, ?, ?)',
                (name, c_type, color)
            )

    def add_category(self, name, c_type, color):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO categories (name, type, color) VALUES (?, ?, ?)',
                (name, c_type, color)
            )
            self._mark_updated(conn)
            return cursor.lastrowid

    def get_categories(self, c_type=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if c_type:
                cursor.execute('SELECT * FROM categories WHERE type = ?', (c_type,))
            else:
                cursor.execute('SELECT * FROM categories')
            return cursor.fetchall()
            
    def delete_category(self, cat_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM categories WHERE id = ?', (cat_id,))
            self._mark_updated(conn)
            conn.commit()

    def update_category(self, cat_id, name, c_type, color):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE categories SET name=?, type=?, color=? WHERE id=?',
                (name, c_type, color, cat_id)
            )
            self._mark_updated(conn)
            conn.commit()

    def add_transaction(self, t_type, category_id, name, amount, date, r_type='one_time', r_interval=1, r_duration=None):
        enc_name = self.crypto.encrypt(name)
        enc_amount = self.crypto.encrypt(str(amount))
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions 
                (type, category_id, name, amount, date, recurrence_type, recurrence_interval, recurrence_duration) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (t_type, category_id, enc_name, enc_amount, date, r_type, r_interval, r_duration))
            self._mark_updated(conn)
            return cursor.lastrowid

    def update_transaction(self, t_id, category_id, name, amount, date, r_type, r_interval, r_duration):
        enc_name = self.crypto.encrypt(name)
        enc_amount = self.crypto.encrypt(str(amount))
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE transactions 
                SET category_id=?, name=?, amount=?, date=?, recurrence_type=?, recurrence_interval=?, recurrence_duration=?
                WHERE id=?
            ''', (category_id, enc_name, enc_amount, date, r_type, r_interval, r_duration, t_id))
            self._mark_updated(conn)
            conn.commit()

    def delete_transaction(self, t_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM transactions WHERE id = ?', (t_id,))
            self._mark_updated(conn)
            conn.commit()

    def get_transactions(self, t_type=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if t_type:
                cursor.execute('SELECT * FROM transactions WHERE type = ? ORDER BY date DESC', (t_type,))
            else:
                cursor.execute('SELECT * FROM transactions ORDER BY date DESC')
            rows = cursor.fetchall()
            
            # Decrypt the rows before returning
            decrypted_rows = []
            for r in rows:
                r_list = list(r)
                r_list[3] = self.crypto.decrypt(r_list[3]) # name
                try:
                    decrypted_amount = float(self.crypto.decrypt(str(r_list[4])))
                except ValueError:
                    decrypted_amount = 0.0
                r_list[4] = decrypted_amount
                decrypted_rows.append(tuple(r_list))
                
            return decrypted_rows

    def get_transaction_by_id(self, t_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM transactions WHERE id = ?', (t_id,))
            row = cursor.fetchone()
            if row:
                r_list = list(row)
                r_list[3] = self.crypto.decrypt(r_list[3]) # name
                try:
                    decrypted_amount = float(self.crypto.decrypt(str(r_list[4])))
                except:
                    decrypted_amount = 0.0
                r_list[4] = decrypted_amount
                return tuple(r_list)
            return None

    def get_category_by_id(self, category_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM categories WHERE id = ?', (category_id,))
            return cursor.fetchone()

    def get_config(self, key):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row[0] if row else None

    def set_config(self, key, value):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', (key, value))
            conn.commit()

    # --- SECURITY AND AUTODESTRUCTION ---
    def wipe_all_data(self):
        # 1. Borrar la estructura de SQLite interna (por seguridad en memoria/disco)
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM transactions')
                cursor.execute('DELETE FROM categories')
                cursor.execute('DELETE FROM commitments')
                cursor.execute('DELETE FROM commitment_payments')
                cursor.execute('DELETE FROM savings_goals')
                cursor.execute('DELETE FROM savings_contributions')
                cursor.execute('DELETE FROM config')
                self._mark_updated(conn)
                conn.commit()
        except:
            pass

        # 2. Borrar archivo y carpeta principal de la app
        try:
            import shutil
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                
            db_dir = os.path.dirname(self.db_path)
            if os.path.exists(db_dir) and "Shark Contabilidad" in db_dir:
                shutil.rmtree(db_dir, ignore_errors=True)
        except:
            pass

        # 3. Borrar accesos directos
        try:
            desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
            start_menu = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs')
            startup = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            
            links = [
                os.path.join(desktop, "Shark Contabilidad.lnk"),
                os.path.join(start_menu, "Shark Contabilidad.lnk"),
                os.path.join(startup, "Shark Contabilidad.lnk")
            ]
            for lnk in links:
                if os.path.exists(lnk):
                    os.remove(lnk)
        except:
            pass

    def get_failed_attempts(self):
        val = self.get_config('failed_attempts')
        return int(val) if val else 0

    def increment_failed_attempts(self):
        attempts = self.get_failed_attempts() + 1
        self.set_config('failed_attempts', str(attempts))
        if attempts >= 5:
            self.wipe_all_data()
            return True # Wiped
        return False

    def reset_failed_attempts(self):
        self.set_config('failed_attempts', '0')

    def setup_security_question(self, question, answer, raw_master_password):
        ans_hash = hashlib.sha256(answer.lower().strip().encode()).hexdigest()
        
        temp_crypto = CryptoManager()
        temp_crypto.initialize_from_password(answer.lower().strip())
        enc_pwd = temp_crypto.encrypt(raw_master_password)
        
        self.set_config('security_question', question)
        self.set_config('security_answer_hash', ans_hash)
        self.set_config('encrypted_master_pwd', enc_pwd)

    def update_security_question(self, current_password, question, answer):
        stored_hash = self.get_config('app_password')
        if hashlib.sha256(current_password.encode()).hexdigest() != stored_hash:
            return False, "La contraseÃƒÂ±a actual es incorrecta."

        question = question.strip()
        answer = answer.strip()
        if not question or not answer:
            return False, "Debes indicar una pregunta y una respuesta de seguridad."

        ans_hash = hashlib.sha256(answer.lower().strip().encode()).hexdigest()

        temp_crypto = CryptoManager()
        temp_crypto.initialize_from_password(answer.lower().strip())
        enc_pwd = temp_crypto.encrypt(current_password)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', ('security_question', question))
            cursor.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', ('security_answer_hash', ans_hash))
            cursor.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', ('encrypted_master_pwd', enc_pwd))
            self._mark_updated(conn)
            conn.commit()

        return True, "Pregunta de seguridad actualizada correctamente."

    def recover_master_password(self, answer):
        ans_hash = hashlib.sha256(answer.lower().strip().encode()).hexdigest()
        stored_hash = self.get_config('security_answer_hash')
        
        if ans_hash != stored_hash:
            return False, None, self.increment_failed_attempts()
            
        enc_pwd = self.get_config('encrypted_master_pwd')
        if not enc_pwd:
             return False, None, False
             
        temp_crypto = CryptoManager()
        temp_crypto.initialize_from_password(answer.lower().strip())
        try:
            raw_pwd = temp_crypto.decrypt(enc_pwd)
            self.reset_failed_attempts()
            return True, raw_pwd, False
        except Exception:
            return False, None, self.increment_failed_attempts()

    # --- COMMITMENTS ---
    def add_commitment(self, name, total_amount, date):
        enc_name = self.crypto.encrypt(name)
        enc_amount = self.crypto.encrypt(str(total_amount))
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO commitments (name, total_amount, date) VALUES (?, ?, ?)',
                           (enc_name, enc_amount, date))
            self._mark_updated(conn)
            return cursor.lastrowid

    def delete_commitment(self, c_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM commitment_payments WHERE commitment_id = ?', (c_id,))
            cursor.execute('DELETE FROM commitments WHERE id = ?', (c_id,))
            self._mark_updated(conn)
            conn.commit()

    def update_commitment(self, c_id, name, total_amount, date):
        enc_name = self.crypto.encrypt(name)
        enc_amount = self.crypto.encrypt(str(total_amount))
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE commitments SET name=?, total_amount=?, date=? WHERE id=?',
                           (enc_name, enc_amount, date, c_id))
            self._mark_updated(conn)
            conn.commit()

    def add_commitment_payment(self, commitment_id, amount, date):
        enc_amount = self.crypto.encrypt(str(amount))
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO commitment_payments (commitment_id, amount, date) VALUES (?, ?, ?)',
                           (commitment_id, enc_amount, date))
            self._mark_updated(conn)
            return cursor.lastrowid

    def get_commitments(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM commitments ORDER BY date DESC')
            rows = cursor.fetchall()
            
            decrypted_rows = []
            for r in rows:
                r_list = list(r)
                r_list[1] = self.crypto.decrypt(r_list[1]) # name
                try:
                    decrypted_amount = float(self.crypto.decrypt(str(r_list[2])))
                except ValueError:
                    decrypted_amount = 0.0
                r_list[2] = decrypted_amount
                decrypted_rows.append(tuple(r_list))
            return decrypted_rows
            
    def get_commitment_payments(self, commitment_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM commitment_payments WHERE commitment_id = ? ORDER BY date DESC', (commitment_id,))
            rows = cursor.fetchall()
            
            decrypted_rows = []
            for r in rows:
                r_list = list(r)
                try:
                    decrypted_amount = float(self.crypto.decrypt(str(r_list[2])))
                except ValueError:
                    decrypted_amount = 0.0
                r_list[2] = decrypted_amount
                decrypted_rows.append(tuple(r_list))
            return decrypted_rows

    def get_all_commitment_payments_decrypted(self):
        """Returns all commitment payments across all commitments, decrypted."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM commitment_payments ORDER BY date DESC')
            rows = cursor.fetchall()

            decrypted_rows = []
            for r in rows:
                r_list = list(r)
                try:
                    decrypted_amount = float(self.crypto.decrypt(str(r_list[2])))
                except ValueError:
                    decrypted_amount = 0.0
                r_list[2] = decrypted_amount
                decrypted_rows.append(tuple(r_list))
            return decrypted_rows

    def delete_commitment_payment(self, payment_id):
        """Delete a single commitment payment by its ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM commitment_payments WHERE id = ?', (payment_id,))
            self._mark_updated(conn)
            conn.commit()

    # --- SAVINGS / HUCHAS ---
    def add_savings_goal(self, name, target_amount, date):
        enc_name = self.crypto.encrypt(name)
        enc_amount = self.crypto.encrypt(str(target_amount))
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO savings_goals (name, target_amount, date) VALUES (?, ?, ?)',
                           (enc_name, enc_amount, date))
            self._mark_updated(conn)
            return cursor.lastrowid

    def delete_savings_goal(self, s_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM savings_contributions WHERE savings_id = ?', (s_id,))
            cursor.execute('DELETE FROM savings_goals WHERE id = ?', (s_id,))
            self._mark_updated(conn)
            conn.commit()

    def add_savings_contribution(self, savings_id, amount, date):
        enc_amount = self.crypto.encrypt(str(amount))
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO savings_contributions (savings_id, amount, date) VALUES (?, ?, ?)',
                           (savings_id, enc_amount, date))
            self._mark_updated(conn)
            return cursor.lastrowid

    def get_savings_goals(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM savings_goals ORDER BY date DESC')
            rows = cursor.fetchall()
            
            decrypted_rows = []
            for r in rows:
                r_list = list(r)
                r_list[1] = self.crypto.decrypt(r_list[1]) # name
                try:
                    decrypted_amount = float(self.crypto.decrypt(str(r_list[2])))
                except ValueError:
                    decrypted_amount = 0.0
                r_list[2] = decrypted_amount
                decrypted_rows.append(tuple(r_list))
            return decrypted_rows
            
    def get_savings_contributions(self, savings_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM savings_contributions WHERE savings_id = ? ORDER BY date DESC', (savings_id,))
            rows = cursor.fetchall()
            
            decrypted_rows = []
            for r in rows:
                r_list = list(r)
                try:
                    decrypted_amount = float(self.crypto.decrypt(str(r_list[2])))
                except ValueError:
                    decrypted_amount = 0.0
                r_list[2] = decrypted_amount
                decrypted_rows.append(tuple(r_list))
            return decrypted_rows

    def change_password(self, old_password, new_password):
        # 1. Verificar contraseÃ±a actual
        old_hash = self.get_config('app_password')
        if hashlib.sha256(old_password.encode()).hexdigest() != old_hash:
            return False, "La contraseÃ±a actual es incorrecta."

        # 2. Desencriptar todo con la contraseÃ±a vieja en memoria
        # Solo necesitamos desencriptar en memoria y guardarlos temporalmente
        self.crypto.initialize_from_password(old_password)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Fetch raw data
            cursor.execute('SELECT id, name, amount FROM transactions')
            raw_txs = cursor.fetchall()
            
            cursor.execute('SELECT id, name, total_amount FROM commitments')
            raw_comms = cursor.fetchall()
            
            cursor.execute('SELECT id, amount FROM commitment_payments')
            raw_comm_pays = cursor.fetchall()

            cursor.execute('SELECT id, name, target_amount FROM savings_goals')
            raw_savings = cursor.fetchall()

            cursor.execute('SELECT id, amount FROM savings_contributions')
            raw_savings_conts = cursor.fetchall()
            
            # Desencriptar en memoria
            dec_txs = []
            for t_id, enc_name, enc_amount in raw_txs:
                dec_txs.append((t_id, self.crypto.decrypt(enc_name), self.crypto.decrypt(enc_amount)))
                
            dec_comms = []
            for c_id, enc_name, enc_total in raw_comms:
                dec_comms.append((c_id, self.crypto.decrypt(enc_name), self.crypto.decrypt(enc_total)))
                
            dec_comm_pays = []
            for cp_id, enc_amount in raw_comm_pays:
                dec_comm_pays.append((cp_id, self.crypto.decrypt(enc_amount)))

            dec_savings = []
            for s_id, enc_name, enc_target in raw_savings:
                dec_savings.append((s_id, self.crypto.decrypt(enc_name), self.crypto.decrypt(enc_target)))

            dec_savings_conts = []
            for sc_id, enc_amount in raw_savings_conts:
                dec_savings_conts.append((sc_id, self.crypto.decrypt(enc_amount)))

            # 3. Inicializar el crypto con la nueva contraseÃ±a
            self.crypto.initialize_from_password(new_password)
            new_hash = hashlib.sha256(new_password.encode()).hexdigest()

            # 4. Re-encriptar todo usando una transacciÃ³n para asegurar integridad
            try:
                for t_id, dec_name, dec_amount in dec_txs:
                    new_enc_name = self.crypto.encrypt(dec_name)
                    new_enc_amount = self.crypto.encrypt(dec_amount)
                    cursor.execute('UPDATE transactions SET name=?, amount=? WHERE id=?', 
                                   (new_enc_name, new_enc_amount, t_id))

                for c_id, dec_name, dec_total in dec_comms:
                    new_enc_name = self.crypto.encrypt(dec_name)
                    new_enc_total = self.crypto.encrypt(dec_total)
                    cursor.execute('UPDATE commitments SET name=?, total_amount=? WHERE id=?',
                                   (new_enc_name, new_enc_total, c_id))

                for cp_id, dec_amount in dec_comm_pays:
                    new_enc_amount = self.crypto.encrypt(dec_amount)
                    cursor.execute('UPDATE commitment_payments SET amount=? WHERE id=?',
                                   (new_enc_amount, cp_id))

                for s_id, dec_name, dec_target in dec_savings:
                    new_enc_name = self.crypto.encrypt(dec_name)
                    new_enc_target = self.crypto.encrypt(dec_target)
                    cursor.execute('UPDATE savings_goals SET name=?, target_amount=? WHERE id=?',
                                   (new_enc_name, new_enc_target, s_id))

                for sc_id, dec_amount in dec_savings_conts:
                    new_enc_amount = self.crypto.encrypt(dec_amount)
                    cursor.execute('UPDATE savings_contributions SET amount=? WHERE id=?',
                                   (new_enc_amount, sc_id))

                # Guardar nuevo hash
                cursor.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', ('app_password', new_hash))
                # Limpiamos la pregunta de seguridad por usar una nueva contraseÃ±a
                cursor.execute("DELETE FROM config WHERE key IN ('security_question', 'security_answer_hash', 'encrypted_master_pwd')")
                self._mark_updated(conn)
                conn.commit()
                return True, "Contrase\u00f1a actualizada correctamente. Por seguridad, vuelve a configurar la pregunta de seguridad."
            except Exception as e:
                # Si algo falla, revertimos
                conn.rollback()
                # Volvemos a inicializar el crypto con la contraseÃ±a vieja para mantener estado funcional
                self.crypto.initialize_from_password(old_password)
                return False, f"Error durante la actualizaciÃ³n: {str(e)}"
