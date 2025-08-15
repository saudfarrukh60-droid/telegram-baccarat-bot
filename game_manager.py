import asyncio
import time
from typing import Dict, List
from baccarat_game import BaccaratGame
from user_service import UserService
from config import GAME_TIMER, MESSAGES

class GameSession:
    """게임 세션 클래스"""
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.bets = {}  # {user_id: {'type': str, 'amount': int, 'username': str}}
        self.start_time = time.time()
        self.is_active = True
        self.timer_task = None
        self.message_id = None
        
    def add_bet(self, user_id, username, bet_type, amount):
        """배팅 추가/업데이트"""
        self.bets[user_id] = {
            'type': bet_type,
            'amount': amount,
            'username': username or f"User{user_id}"
        }
    
    def get_remaining_time(self):
        """남은 시간 계산"""
        elapsed = time.time() - self.start_time
        remaining = max(0, GAME_TIMER - elapsed)
        return int(remaining)
    
    def is_expired(self):
        """게임 시간 만료 여부"""
        return self.get_remaining_time() <= 0
    
    def get_bet_status(self):
        """배팅 현황 문자열 생성"""
        if not self.bets:
            return "아직 배팅이 없습니다."
        
        status_lines = []
        total_by_type = {'플레이어': 0, '뱅커': 0, '무승부': 0}
        
        for user_id, bet_info in self.bets.items():
            bet_type = bet_info['type']
            amount = bet_info['amount']
            username = bet_info['username']
            
            total_by_type[bet_type] += amount
            status_lines.append(f"👤 {username}: {bet_type} {amount:,}원")
        
        # 타입별 총합 추가
        summary_lines = []
        for bet_type, total in total_by_type.items():
            if total > 0:
                emoji = "👤" if bet_type == "플레이어" else "🏦" if bet_type == "뱅커" else "🤝"
                summary_lines.append(f"{emoji} {bet_type}: {total:,}원")
        
        result = "\n".join(status_lines)
        if summary_lines:
            result += "\n\n📊 총 배팅:\n" + "\n".join(summary_lines)
        
        return result

class GameManager:
    """멀티플레이어 게임 매니저"""
    
    def __init__(self, bot_application):
        self.bot = bot_application
        self.user_service = UserService()
        self.active_sessions = {}  # {chat_id: GameSession}
        self.game_engine = BaccaratGame()
    
    async def start_game(self, chat_id, user_id, username, bet_type, amount):
        """게임 시작 또는 배팅 추가"""
        # 배팅 유효성 검사
        can_bet, message = self.user_service.can_bet(user_id, amount)
        if not can_bet:
            return False, message
        
        # 기존 게임 세션이 있는지 확인
        if chat_id in self.active_sessions:
            session = self.active_sessions[chat_id]
            
            # 게임이 만료되었으면 새 게임 시작
            if session.is_expired():
                await self.end_game(chat_id)
                return await self.start_game(chat_id, user_id, username, bet_type, amount)
            
            # 기존 게임에 배팅 추가
            session.add_bet(user_id, username, bet_type, amount)
            return True, "배팅이 추가되었습니다."
        
        # 새 게임 세션 생성
        session = GameSession(chat_id)
        session.add_bet(user_id, username, bet_type, amount)
        self.active_sessions[chat_id] = session
        
        # 타이머 시작
        session.timer_task = asyncio.create_task(self.game_timer(chat_id))
        
        return True, "새 게임이 시작되었습니다."
    
    async def game_timer(self, chat_id):
        """게임 타이머 관리"""
        session = self.active_sessions.get(chat_id)
        if not session:
            return
        
        try:
            # 초기 메시지 전송
            await self.send_game_status(chat_id)
            
            # 30초, 10초, 5초 카운트다운
            countdown_times = [30, 10, 5]
            
            while session.is_active and not session.is_expired():
                remaining = session.get_remaining_time()
                
                # 카운트다운 메시지
                if remaining in countdown_times:
                    await self.send_countdown_message(chat_id, remaining)
                    countdown_times.remove(remaining)
                
                await asyncio.sleep(1)
            
            # 게임 종료
            if session.is_active:
                await self.end_game(chat_id)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"게임 타이머 오류: {e}")
    
    async def send_game_status(self, chat_id):
        """게임 상태 메시지 전송"""
        session = self.active_sessions.get(chat_id)
        if not session:
            return
        
        bet_status = session.get_bet_status()
        remaining_time = session.get_remaining_time()
        
        message = MESSAGES['game_timer_start'].format(
            timer=remaining_time,
            bet_status=bet_status
        )
        
        try:
            sent_message = await self.bot.bot.send_message(
                chat_id=chat_id,
                text=message
            )
            session.message_id = sent_message.message_id
        except Exception as e:
            print(f"메시지 전송 오류: {e}")
    
    async def send_countdown_message(self, chat_id, remaining_time):
        """카운트다운 메시지 전송"""
        session = self.active_sessions.get(chat_id)
        if not session:
            return
        
        bet_status = session.get_bet_status()
        message = MESSAGES['game_countdown'].format(
            time=remaining_time,
            bet_status=bet_status
        )
        
        try:
            if session.message_id:
                await self.bot.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=session.message_id,
                    text=message
                )
            else:
                sent_message = await self.bot.bot.send_message(
                    chat_id=chat_id,
                    text=message
                )
                session.message_id = sent_message.message_id
        except Exception as e:
            print(f"카운트다운 메시지 오류: {e}")
    
    async def end_game(self, chat_id):
        """게임 종료 및 결과 처리"""
        session = self.active_sessions.get(chat_id)
        if not session:
            return
        
        session.is_active = False
        
        # 타이머 태스크 취소
        if session.timer_task:
            session.timer_task.cancel()
        
        # 배팅이 없으면 게임 취소
        if not session.bets:
            await self.bot.bot.send_message(
                chat_id=chat_id,
                text=MESSAGES['no_bets']
            )
            del self.active_sessions[chat_id]
            return
        
        # 게임 진행
        result = self.game_engine.play_round()
        
        # 카드 문자열 생성
        result['player_cards_str'] = self.game_engine.format_cards(result['player_cards'])
        result['banker_cards_str'] = self.game_engine.format_cards(result['banker_cards'])
        
        # 각 사용자의 결과 처리
        results_text = []
        
        for user_id, bet_info in session.bets.items():
            bet_type = bet_info['type']
            bet_amount = bet_info['amount']
            username = bet_info['username']
            
            # 배당금 계산
            payout = self.game_engine.calculate_payout(bet_amount, bet_type, result['winner'])
            
            # 게임 결과 처리
            success, new_balance = self.user_service.process_game_result(
                user_id, bet_amount, bet_type, result, payout
            )
            
            if success:
                if payout > 0:
                    profit = payout - bet_amount
                    result_emoji = "✅"
                    result_text = f"+{profit:,}원"
                else:
                    result_emoji = "❌"
                    result_text = f"-{bet_amount:,}원"
                
                results_text.append(
                    f"{result_emoji} {username}: {bet_type} {bet_amount:,}원 → {result_text}"
                )
        
        # 결과 메시지 전송
        final_message = MESSAGES['multi_game_result'].format(
            player_cards=result['player_cards_str'],
            player_total=result['player_total'],
            banker_cards=result['banker_cards_str'],
            banker_total=result['banker_total'],
            winner=result['winner'],
            results="\n".join(results_text)
        )
        
        try:
            await self.bot.bot.send_message(
                chat_id=chat_id,
                text=final_message
            )
        except Exception as e:
            print(f"결과 메시지 전송 오류: {e}")
        
        # 세션 정리
        del self.active_sessions[chat_id]
    
    def get_active_game(self, chat_id):
        """활성 게임 세션 조회"""
        return self.active_sessions.get(chat_id)
    
    def is_game_active(self, chat_id):
        """게임 활성 상태 확인"""
        session = self.active_sessions.get(chat_id)
        return session is not None and session.is_active and not session.is_expired()

