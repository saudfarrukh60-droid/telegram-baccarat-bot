import sqlite3
import datetime
from config import DATABASE_PATH, INITIAL_BALANCE

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """데이터베이스 테이블 초기화"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 사용자 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                balance INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 게임 기록 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                bet_amount INTEGER,
                bet_type TEXT,
                player_cards TEXT,
                banker_cards TEXT,
                player_total INTEGER,
                banker_total INTEGER,
                winner TEXT,
                payout INTEGER,
                balance_before INTEGER,
                balance_after INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # 송금 기록 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER,
                recipient_id INTEGER,
                amount INTEGER,
                sender_balance_before INTEGER,
                sender_balance_after INTEGER,
                recipient_balance_before INTEGER,
                recipient_balance_after INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users (user_id),
                FOREIGN KEY (recipient_id) REFERENCES users (user_id)
            )
        ''')
        
        # 출석 기록 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                attendance_date DATE,
                reward_amount INTEGER,
                consecutive_days INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(user_id, attendance_date)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, user_id, username=None, first_name=None, last_name=None):
        """새 사용자 생성"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, balance)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, INITIAL_BALANCE))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"사용자 생성 오류: {e}")
            return False
        finally:
            conn.close()
    
    def get_user(self, user_id):
        """사용자 정보 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'user_id': user[0],
                'username': user[1],
                'first_name': user[2],
                'last_name': user[3],
                'balance': user[4],
                'created_at': user[5],
                'last_active': user[6]
            }
        return None
    
    def update_balance(self, user_id, new_balance):
        """사용자 잔액 업데이트"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users SET balance = ?, last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (new_balance, user_id))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"잔액 업데이트 오류: {e}")
            return False
        finally:
            conn.close()
    
    def add_game_record(self, user_id, bet_amount, bet_type, player_cards, banker_cards,
                       player_total, banker_total, winner, payout, balance_before, balance_after):
        """게임 기록 추가"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO game_history 
                (user_id, bet_amount, bet_type, player_cards, banker_cards, 
                 player_total, banker_total, winner, payout, balance_before, balance_after)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, bet_amount, bet_type, player_cards, banker_cards,
                  player_total, banker_total, winner, payout, balance_before, balance_after))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"게임 기록 추가 오류: {e}")
            return False
        finally:
            conn.close()
    
    def get_game_history(self, user_id, limit=10):
        """사용자 게임 기록 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM game_history 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        records = cursor.fetchall()
        conn.close()
        
        return records
    
    def add_transfer_record(self, sender_id, recipient_id, amount, 
                           sender_balance_before, sender_balance_after,
                           recipient_balance_before, recipient_balance_after):
        """송금 기록 추가"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO transfers 
                (sender_id, recipient_id, amount, sender_balance_before, sender_balance_after,
                 recipient_balance_before, recipient_balance_after)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (sender_id, recipient_id, amount, sender_balance_before, sender_balance_after,
                  recipient_balance_before, recipient_balance_after))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"송금 기록 추가 오류: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_by_username(self, username):
        """사용자명으로 사용자 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'user_id': user[0],
                'username': user[1],
                'first_name': user[2],
                'last_name': user[3],
                'balance': user[4],
                'created_at': user[5],
                'last_active': user[6]
            }
        return None
    
    def check_attendance_today(self, user_id):
        """오늘 출석 체크 여부 확인"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM attendance 
            WHERE user_id = ? AND attendance_date = DATE('now')
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    
    def get_consecutive_attendance(self, user_id):
        """연속 출석 일수 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT consecutive_days FROM attendance 
            WHERE user_id = ? 
            ORDER BY attendance_date DESC 
            LIMIT 1
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # 어제 출석했는지 확인
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM attendance 
                WHERE user_id = ? AND attendance_date = DATE('now', '-1 day')
            ''', (user_id,))
            
            yesterday_attendance = cursor.fetchone()
            conn.close()
            
            if yesterday_attendance:
                return result[0]  # 연속 출석 유지
            else:
                return 0  # 연속 출석 끊김
        
        return 0
    
    def add_attendance_record(self, user_id, reward_amount, consecutive_days):
        """출석 기록 추가"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO attendance (user_id, attendance_date, reward_amount, consecutive_days)
                VALUES (?, DATE('now'), ?, ?)
            ''', (user_id, reward_amount, consecutive_days))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"출석 기록 추가 오류: {e}")
            return False
        finally:
            conn.close()

