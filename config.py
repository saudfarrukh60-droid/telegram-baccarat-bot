# 텔레그램 바카라 봇 설정 파일

# 텔레그램 봇 토큰
BOT_TOKEN = "8446673548:AAG3Ra2j8TE7K-G3VGyX8FM6qEcG2rnS3Q8"

# 데이터베이스 설정
DATABASE_PATH = "baccarat_bot.db"

# 게임 설정
INITIAL_BALANCE = 10000  # 초기 잔액
MIN_BET = 100           # 최소 베팅 금액
MAX_BET = 50000         # 최대 베팅 금액
GAME_TIMER = 60         # 게임 타이머 (초)

# 출석 설정
DAILY_ATTENDANCE_REWARD = 5000  # 일일 출석 보상
WEEKLY_BONUS = 10000           # 7일 연속 출석 보너스

# 메시지 설정
MESSAGES = {
    'welcome': '🎰 바카라 게임 봇에 오신 것을 환영합니다!\n\n💰 초기 잔액: {balance}원\n\n게임을 시작하려면 /game 명령어를 사용하세요.',
    'balance': '💰 현재 잔액: {balance}원',
    'insufficient_funds': '❌ 잔액이 부족합니다. 현재 잔액: {balance}원',
    'invalid_bet': '❌ 잘못된 베팅 금액입니다. {min_bet}원 ~ {max_bet}원 사이로 베팅해주세요.',
    'game_start': '🎮 바카라 게임을 시작합니다!\n\n💰 현재 잔액: {balance}원\n🎯 베팅할 금액을 입력하세요 ({min_bet}원 ~ {max_bet}원)',
    'choose_bet_type': '🎯 베팅 타입을 선택하세요:\n\n👤 플레이어 승리\n🏦 뱅커 승리\n🤝 무승부',
    'game_result': '🎲 게임 결과:\n\n👤 플레이어: {player_cards} (총합: {player_total})\n🏦 뱅커: {banker_cards} (총합: {banker_total})\n\n🏆 승자: {winner}\n💰 베팅 결과: {bet_result}\n💵 잔액 변화: {balance_change}\n💰 현재 잔액: {current_balance}원',
    'transfer_request': '💸 송금할 사용자 ID와 금액을 입력하세요.\n예: /transfer @username 1000',
    'transfer_success': '✅ 송금이 완료되었습니다.\n받는 사람: {recipient}\n금액: {amount}원\n💰 현재 잔액: {balance}원',
    'transfer_failed': '❌ 송금에 실패했습니다: {reason}',
    'help': '''🎰 바카라 게임 봇 도움말

📋 명령어:
/start - 봇 시작 및 계정 생성
/game - 바카라 게임 시작
/balance - 잔액 확인
/transfer - 다른 사용자에게 송금
/history - 게임 기록 확인
/attendance - 출석 체크
/help - 도움말

🎮 배팅 명령어:
/플레이어 [금액] - 플레이어 승리에 배팅
/뱅커 [금액] - 뱅커 승리에 배팅 (줄임: /뱅)
/무승부 [금액] - 무승부에 배팅 (줄임: /무)

예시: /뱅 10000, /플레이어 5000, /무 1000

🎮 게임 규칙:
- 플레이어와 뱅커 중 9에 가까운 쪽이 승리
- 카드 값: A=1, 2-9=숫자값, 10,J,Q,K=0
- 두 카드 합의 일의 자리가 최종 점수
- 플레이어 승리: 2배 배당
- 뱅커 승리: 1.95배 배당 (수수료 5%)
- 무승부: 8배 배당

⏰ 게임 진행:
- 배팅 후 60초 뒤 자동으로 카드 공개
- 60초 동안 다른 사용자들도 배팅 가능
- 타이머 종료 시 결과 발표

🎁 출석 체크:
- 매일 출석시 5,000원 지급
- 7일 연속 출석시 추가 10,000원 보너스''',
    'attendance_success': '🎁 출석 체크 완료!\n💰 {reward}원을 받았습니다.\n📅 연속 출석: {streak}일\n💵 현재 잔액: {balance}원',
    'attendance_already': '✅ 오늘 이미 출석 체크를 완료했습니다.\n📅 연속 출석: {streak}일',
    'attendance_bonus': '🎉 7일 연속 출석 달성!\n💎 보너스 {bonus}원 추가 지급!',
    'game_timer_start': '⏰ 게임이 시작되었습니다!\n\n🎯 배팅 시간: {timer}초\n💰 현재 배팅 현황:\n{bet_status}\n\n배팅 명령어:\n/뱅 [금액] - 뱅커\n/플레이어 [금액] - 플레이어\n/무 [금액] - 무승부',
    'bet_placed': '✅ 배팅 완료!\n🎯 {bet_type}: {amount}원\n💰 잔액: {balance}원',
    'bet_updated': '🔄 배팅 업데이트!\n🎯 {bet_type}: {amount}원\n💰 잔액: {balance}원',
    'game_countdown': '⏰ 남은 시간: {time}초\n💰 현재 배팅 현황:\n{bet_status}',
    'no_bets': '❌ 배팅이 없어 게임이 취소되었습니다.',
    'multi_game_result': '''🎲 게임 결과:

👤 플레이어: {player_cards} (총합: {player_total})
🏦 뱅커: {banker_cards} (총합: {banker_total})

🏆 승자: {winner}

💰 배팅 결과:
{results}'''
}

