from database import Database
from config import MIN_BET, MAX_BET, DAILY_ATTENDANCE_REWARD, WEEKLY_BONUS
import datetime

class UserService:
    """사용자 관리 서비스"""
    
    def __init__(self):
        self.db = Database()
    
    def register_user(self, user_id, username=None, first_name=None, last_name=None):
        """사용자 등록"""
        return self.db.create_user(user_id, username, first_name, last_name)
    
    def get_user_info(self, user_id):
        """사용자 정보 조회"""
        return self.db.get_user(user_id)
    
    def get_balance(self, user_id):
        """사용자 잔액 조회"""
        user = self.db.get_user(user_id)
        return user['balance'] if user else 0
    
    def update_balance(self, user_id, new_balance):
        """잔액 업데이트"""
        return self.db.update_balance(user_id, new_balance)
    
    def add_balance(self, user_id, amount):
        """잔액 추가"""
        current_balance = self.get_balance(user_id)
        new_balance = current_balance + amount
        return self.update_balance(user_id, new_balance)
    
    def subtract_balance(self, user_id, amount):
        """잔액 차감"""
        current_balance = self.get_balance(user_id)
        if current_balance >= amount:
            new_balance = current_balance - amount
            return self.update_balance(user_id, new_balance)
        return False
    
    def can_bet(self, user_id, bet_amount):
        """베팅 가능 여부 확인"""
        if bet_amount < MIN_BET or bet_amount > MAX_BET:
            return False, f"베팅 금액은 {MIN_BET}원 ~ {MAX_BET}원 사이여야 합니다."
        
        current_balance = self.get_balance(user_id)
        if current_balance < bet_amount:
            return False, f"잔액이 부족합니다. 현재 잔액: {current_balance}원"
        
        return True, "베팅 가능"
    
    def process_game_result(self, user_id, bet_amount, bet_type, game_result, payout):
        """게임 결과 처리"""
        current_balance = self.get_balance(user_id)
        balance_before = current_balance
        
        # 베팅 금액 차감
        new_balance = current_balance - bet_amount
        
        # 당첨시 배당금 추가
        if payout > 0:
            new_balance += payout
        
        # 잔액 업데이트
        success = self.update_balance(user_id, new_balance)
        
        if success:
            # 게임 기록 저장
            self.db.add_game_record(
                user_id=user_id,
                bet_amount=bet_amount,
                bet_type=bet_type,
                player_cards=game_result.get('player_cards_str', ''),
                banker_cards=game_result.get('banker_cards_str', ''),
                player_total=game_result.get('player_total', 0),
                banker_total=game_result.get('banker_total', 0),
                winner=game_result.get('winner', ''),
                payout=payout,
                balance_before=balance_before,
                balance_after=new_balance
            )
        
        return success, new_balance
    
    def get_game_history(self, user_id, limit=10):
        """게임 기록 조회"""
        records = self.db.get_game_history(user_id, limit)
        
        formatted_records = []
        for record in records:
            formatted_record = {
                'id': record[0],
                'bet_amount': record[2],
                'bet_type': record[3],
                'player_cards': record[4],
                'banker_cards': record[5],
                'player_total': record[6],
                'banker_total': record[7],
                'winner': record[8],
                'payout': record[9],
                'balance_before': record[10],
                'balance_after': record[11],
                'created_at': record[12]
            }
            formatted_records.append(formatted_record)
        
        return formatted_records
    
    def transfer_money(self, sender_id, recipient_username, amount):
        """송금 처리"""
        # 송금자 정보 확인
        sender = self.db.get_user(sender_id)
        if not sender:
            return False, "송금자 정보를 찾을 수 없습니다."
        
        # 수신자 정보 확인
        recipient = self.db.get_user_by_username(recipient_username.replace('@', ''))
        if not recipient:
            return False, f"사용자 '{recipient_username}'를 찾을 수 없습니다."
        
        # 자기 자신에게 송금 방지
        if sender_id == recipient['user_id']:
            return False, "자기 자신에게는 송금할 수 없습니다."
        
        # 송금 금액 검증
        if amount <= 0:
            return False, "송금 금액은 0원보다 커야 합니다."
        
        if sender['balance'] < amount:
            return False, f"잔액이 부족합니다. 현재 잔액: {sender['balance']}원"
        
        # 송금 처리
        sender_balance_before = sender['balance']
        recipient_balance_before = recipient['balance']
        
        sender_balance_after = sender_balance_before - amount
        recipient_balance_after = recipient_balance_before + amount
        
        # 잔액 업데이트
        sender_success = self.update_balance(sender_id, sender_balance_after)
        recipient_success = self.update_balance(recipient['user_id'], recipient_balance_after)
        
        if sender_success and recipient_success:
            # 송금 기록 저장
            self.db.add_transfer_record(
                sender_id=sender_id,
                recipient_id=recipient['user_id'],
                amount=amount,
                sender_balance_before=sender_balance_before,
                sender_balance_after=sender_balance_after,
                recipient_balance_before=recipient_balance_before,
                recipient_balance_after=recipient_balance_after
            )
            return True, f"송금이 완료되었습니다. 현재 잔액: {sender_balance_after}원"
        else:
            return False, "송금 처리 중 오류가 발생했습니다."
    
    def format_balance_info(self, user_id):
        """잔액 정보 포맷"""
        user = self.get_user_info(user_id)
        if user:
            return f"💰 현재 잔액: {user['balance']:,}원"
        return "❌ 사용자 정보를 찾을 수 없습니다."
    
    def format_game_history(self, user_id, limit=5):
        """게임 기록 포맷"""
        records = self.get_game_history(user_id, limit)
        
        if not records:
            return "📊 게임 기록이 없습니다."
        
        history_text = "📊 최근 게임 기록:\n\n"
        
        for i, record in enumerate(records, 1):
            result_emoji = "✅" if record['payout'] > 0 else "❌"
            balance_change = record['balance_after'] - record['balance_before']
            change_text = f"+{balance_change:,}" if balance_change > 0 else f"{balance_change:,}"
            
            history_text += f"{i}. {result_emoji} {record['bet_type']} 베팅\n"
            history_text += f"   💰 베팅: {record['bet_amount']:,}원\n"
            history_text += f"   🎯 결과: {record['winner']} 승리\n"
            history_text += f"   💵 수익: {change_text}원\n"
            history_text += f"   📅 {record['created_at'][:16]}\n\n"
        
        return history_text.strip()

    def check_attendance(self, user_id):
        """출석 체크 처리"""
        # 오늘 이미 출석했는지 확인
        if self.db.check_attendance_today(user_id):
            consecutive_days = self.db.get_consecutive_attendance(user_id)
            return False, f"오늘 이미 출석했습니다.", consecutive_days
        
        # 연속 출석 일수 계산
        consecutive_days = self.db.get_consecutive_attendance(user_id) + 1
        
        # 기본 출석 보상
        reward = DAILY_ATTENDANCE_REWARD
        bonus_message = ""
        
        # 7일 연속 출석 보너스
        if consecutive_days % 7 == 0:
            reward += WEEKLY_BONUS
            bonus_message = f"\n🎉 7일 연속 출석 달성! 보너스 {WEEKLY_BONUS:,}원 추가!"
        
        # 잔액 추가
        success = self.add_balance(user_id, reward)
        
        if success:
            # 출석 기록 저장
            self.db.add_attendance_record(user_id, reward, consecutive_days)
            current_balance = self.get_balance(user_id)
            
            return True, f"출석 체크 완료! {reward:,}원 지급{bonus_message}", consecutive_days, current_balance
        else:
            return False, "출석 처리 중 오류가 발생했습니다.", consecutive_days

# 테스트 함수
def test_user_service():
    """사용자 서비스 테스트"""
    service = UserService()
    
    # 테스트 사용자 생성
    test_user_id = 12345
    service.register_user(test_user_id, "testuser", "Test", "User")
    
    print("=== 사용자 서비스 테스트 ===")
    
    # 잔액 확인
    balance = service.get_balance(test_user_id)
    print(f"초기 잔액: {balance}원")
    
    # 베팅 가능 여부 확인
    can_bet, message = service.can_bet(test_user_id, 1000)
    print(f"1000원 베팅 가능: {can_bet} - {message}")
    
    # 잔액 추가/차감 테스트
    service.add_balance(test_user_id, 5000)
    print(f"5000원 추가 후 잔액: {service.get_balance(test_user_id)}원")
    
    service.subtract_balance(test_user_id, 2000)
    print(f"2000원 차감 후 잔액: {service.get_balance(test_user_id)}원")

if __name__ == "__main__":
    test_user_service()

