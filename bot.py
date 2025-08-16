import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN, MESSAGES, MIN_BET, MAX_BET, DAILY_ATTENDANCE_REWARD, WEEKLY_BONUS
from user_service import UserService
from game_manager import GameManager

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 전역 서비스 인스턴스
user_service = UserService()
game_manager = None  # 나중에 초기화

class BotHandler:
    """텔레그램 봇 핸들러 클래스"""
    
    @staticmethod
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """시작 명령어 처리"""
        user = update.effective_user
        user_id = user.id
        
        # 사용자 등록
        user_service.register_user(
            user_id=user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        balance = user_service.get_balance(user_id)
        welcome_message = MESSAGES['welcome'].format(balance=f"{balance:,}")
        
        # 메인 메뉴 키보드
        keyboard = [
            [InlineKeyboardButton("💰 잔액 확인", callback_data="check_balance")],
            [InlineKeyboardButton("💸 송금하기", callback_data="transfer_money")],
            [InlineKeyboardButton("📊 게임 기록", callback_data="game_history")],
            [InlineKeyboardButton("🎁 출석 체크", callback_data="attendance")],
            [InlineKeyboardButton("❓ 도움말", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    
    @staticmethod
    async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """잔액 확인 명령어"""
        user_id = update.effective_user.id
        balance_info = user_service.format_balance_info(user_id)
        await update.message.reply_text(balance_info)
    
    @staticmethod
    async def transfer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """송금 명령어"""
        user_id = update.effective_user.id
        
        if len(context.args) < 2:
            await update.message.reply_text(MESSAGES['transfer_request'])
            return
        
        try:
            recipient_username = context.args[0]
            amount = int(context.args[1])
            
            success, message = user_service.transfer_money(user_id, recipient_username, amount)
            
            if success:
                balance = user_service.get_balance(user_id)
                response = MESSAGES['transfer_success'].format(
                    recipient=recipient_username,
                    amount=f"{amount:,}",
                    balance=f"{balance:,}"
                )
            else:
                response = MESSAGES['transfer_failed'].format(reason=message)
            
            await update.message.reply_text(response)
            
        except (ValueError, IndexError):
            await update.message.reply_text(MESSAGES['transfer_request'])
    
    @staticmethod
    async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """게임 기록 명령어"""
        user_id = update.effective_user.id
        history = user_service.format_game_history(user_id)
        await update.message.reply_text(history)
    
    @staticmethod
    async def attendance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """출석 체크 명령어"""
        user_id = update.effective_user.id
        
        try:
            success, message, consecutive_days, *extra = user_service.check_attendance(user_id)
            
            if success:
                current_balance = extra[0] if extra else user_service.get_balance(user_id)
                response = MESSAGES['attendance_success'].format(
                    reward=DAILY_ATTENDANCE_REWARD + (WEEKLY_BONUS if consecutive_days % 7 == 0 else 0),
                    streak=consecutive_days,
                    balance=f"{current_balance:,}"
                )
                
                if consecutive_days % 7 == 0:
                    response += f"\n{MESSAGES['attendance_bonus'].format(bonus=f'{WEEKLY_BONUS:,}')}"
            else:
                response = MESSAGES['attendance_already'].format(streak=consecutive_days)
            
            await update.message.reply_text(response)
            
        except Exception as e:
            await update.message.reply_text("출석 체크 중 오류가 발생했습니다.")
            logger.error(f"출석 체크 오류: {e}")
    
    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """도움말 명령어"""
        await update.message.reply_text(MESSAGES['help'])
    
    @staticmethod
    async def bet_command(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_type: str):
        """배팅 명령어 처리"""
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        chat_id = update.effective_chat.id
        
        if not context.args:
            await update.message.reply_text(f"배팅 금액을 입력해주세요.\n예: /{bet_type} 10000")
            return
        
        try:
            amount = int(context.args[0].replace(',', ''))
            
            # 게임 매니저를 통해 배팅 처리
            success, message = await game_manager.start_game(chat_id, user_id, username, bet_type, amount)
            
            if success:
                # 잔액에서 배팅 금액 차감 (임시)
                user_service.subtract_balance(user_id, amount)
                current_balance = user_service.get_balance(user_id)
                
                if "새 게임" in message:
                    response = f"🎮 새 게임이 시작되었습니다!\n✅ {bet_type} {amount:,}원 배팅\n💰 잔액: {current_balance:,}원\n\n⏰ 60초 후 결과 발표!"
                else:
                    response = MESSAGES['bet_updated'].format(
                        bet_type=bet_type,
                        amount=f"{amount:,}",
                        balance=f"{current_balance:,}"
                    )
            else:
                response = f"❌ {message}"
            
            await update.message.reply_text(response)
            
        except ValueError:
            await update.message.reply_text("올바른 숫자를 입력해주세요.")
        except Exception as e:
            await update.message.reply_text("배팅 처리 중 오류가 발생했습니다.")
            logger.error(f"배팅 오류: {e}")
    
    @staticmethod
    async def player_bet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """플레이어 배팅 명령어"""
        await BotHandler.bet_command(update, context, "플레이어")
    
    @staticmethod
    async def banker_bet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """뱅커 배팅 명령어"""
        await BotHandler.bet_command(update, context, "뱅커")
    
    @staticmethod
    async def tie_bet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """무승부 배팅 명령어"""
        await BotHandler.bet_command(update, context, "무승부")
    
    @staticmethod
    async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """인라인 키보드 버튼 콜백"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        
        if callback_data == "check_balance":
            await BotHandler.check_balance_callback(update, context)
        elif callback_data == "transfer_money":
            await BotHandler.transfer_money_callback(update, context)
        elif callback_data == "game_history":
            await BotHandler.game_history_callback(update, context)
        elif callback_data == "attendance":
            await BotHandler.attendance_callback(update, context)
        elif callback_data == "help":
            await BotHandler.help_callback(update, context)
        elif callback_data == "main_menu":
            await BotHandler.main_menu_callback(update, context)
    
    @staticmethod
    async def check_balance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """잔액 확인 콜백"""
        user_id = update.effective_user.id
        balance_info = user_service.format_balance_info(user_id)
        
        keyboard = [[InlineKeyboardButton("🏠 메인 메뉴", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(balance_info, reply_markup=reply_markup)
    
    @staticmethod
    async def transfer_money_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """송금 콜백"""
        message = MESSAGES['transfer_request']
        
        keyboard = [[InlineKeyboardButton("🏠 메인 메뉴", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
    
    @staticmethod
    async def game_history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """게임 기록 콜백"""
        user_id = update.effective_user.id
        history = user_service.format_game_history(user_id)
        
        keyboard = [[InlineKeyboardButton("🏠 메인 메뉴", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(history, reply_markup=reply_markup)
    
    @staticmethod
    async def attendance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """출석 체크 콜백"""
        user_id = update.effective_user.id
        
        try:
            success, message, consecutive_days, *extra = user_service.check_attendance(user_id)
            
            if success:
                current_balance = extra[0] if extra else user_service.get_balance(user_id)
                response = MESSAGES['attendance_success'].format(
                    reward=DAILY_ATTENDANCE_REWARD + (WEEKLY_BONUS if consecutive_days % 7 == 0 else 0),
                    streak=consecutive_days,
                    balance=f"{current_balance:,}"
                )
                
                if consecutive_days % 7 == 0:
                    response += f"\n{MESSAGES['attendance_bonus'].format(bonus=f'{WEEKLY_BONUS:,}')}"
            else:
                response = MESSAGES['attendance_already'].format(streak=consecutive_days)
            
        except Exception as e:
            response = "출석 체크 중 오류가 발생했습니다."
            logger.error(f"출석 체크 오류: {e}")
        
        keyboard = [[InlineKeyboardButton("🏠 메인 메뉴", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(response, reply_markup=reply_markup)
    
    @staticmethod
    async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """도움말 콜백"""
        keyboard = [[InlineKeyboardButton("🏠 메인 메뉴", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(MESSAGES['help'], reply_markup=reply_markup)
    
    @staticmethod
    async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """메인 메뉴 콜백"""
        user_id = update.effective_user.id
        balance = user_service.get_balance(user_id)
        welcome_message = MESSAGES['welcome'].format(balance=f"{balance:,}")
        
        keyboard = [
            [InlineKeyboardButton("💰 잔액 확인", callback_data="check_balance")],
            [InlineKeyboardButton("💸 송금하기", callback_data="transfer_money")],
            [InlineKeyboardButton("📊 게임 기록", callback_data="game_history")],
            [InlineKeyboardButton("🎁 출석 체크", callback_data="attendance")],
            [InlineKeyboardButton("❓ 도움말", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(welcome_message, reply_markup=reply_markup)
    
    @staticmethod
    async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일반 메시지 처리"""
        text = update.message.text
        
        # 일반 메시지에 대한 응답
        await update.message.reply_text(
            "배팅 명령어를 사용해주세요:\n"
            "🎯 /banker [금액] - 뱅커 배팅\n"
            "🎯 /player [금액] - 플레이어 배팅\n"
            "🎯 /tie [금액] - 무승부 배팅\n\n"
            "또는 /help로 전체 도움말을 확인하세요."
        )

def main():
    """메인 함수"""
    global game_manager
    
    # 애플리케이션 생성
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 게임 매니저 초기화
    game_manager = GameManager(application)
    
    # 핸들러 등록
    application.add_handler(CommandHandler("start", BotHandler.start_command))
    application.add_handler(CommandHandler("balance", BotHandler.balance_command))
    application.add_handler(CommandHandler("transfer", BotHandler.transfer_command))
    application.add_handler(CommandHandler("history", BotHandler.history_command))
    application.add_handler(CommandHandler("attendance", BotHandler.attendance_command))
    application.add_handler(CommandHandler("help", BotHandler.help_command))
    
    # 배팅 명령어 핸들러
    application.add_handler(CommandHandler("player", BotHandler.player_bet_command))
    application.add_handler(CommandHandler("banker", BotHandler.banker_bet_command))
    application.add_handler(CommandHandler("bank", BotHandler.banker_bet_command))  # 줄임말
    application.add_handler(CommandHandler("tie", BotHandler.tie_bet_command))
    application.add_handler(CommandHandler("draw", BotHandler.tie_bet_command))  # 줄임말
    
    application.add_handler(CallbackQueryHandler(BotHandler.button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandler.message_handler))
    
    # 봇 시작
    print("🎰 바카라 게임 봇이 시작되었습니다!")
    print("📋 새로운 기능:")
    print("   - /banker [금액] - 뱅커 배팅")
    print("   - /player [금액] - 플레이어 배팅") 
    print("   - /tie [금액] - 무승부 배팅")
    print("   - /attendance - 출석 체크")
    print("   - 60초 타이머 멀티플레이어 게임")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

