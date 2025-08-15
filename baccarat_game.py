import random
from typing import List, Tuple, Dict

class Card:
    """카드 클래스"""
    def __init__(self, suit: str, rank: str):
        self.suit = suit  # 스페이드, 하트, 다이아몬드, 클럽
        self.rank = rank  # A, 2-9, 10, J, Q, K
    
    def get_value(self) -> int:
        """바카라에서의 카드 값 반환"""
        if self.rank in ['J', 'Q', 'K']:
            return 0
        elif self.rank == 'A':
            return 1
        elif self.rank == '10':
            return 0
        else:
            return int(self.rank)
    
    def __str__(self):
        suit_symbols = {'스페이드': '♠', '하트': '♥', '다이아몬드': '♦', '클럽': '♣'}
        return f"{suit_symbols.get(self.suit, self.suit)}{self.rank}"

class Deck:
    """카드 덱 클래스"""
    def __init__(self):
        self.cards = []
        self.reset_deck()
    
    def reset_deck(self):
        """덱 초기화 (52장)"""
        suits = ['스페이드', '하트', '다이아몬드', '클럽']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        
        self.cards = []
        for suit in suits:
            for rank in ranks:
                self.cards.append(Card(suit, rank))
        
        self.shuffle()
    
    def shuffle(self):
        """카드 섞기"""
        random.shuffle(self.cards)
    
    def deal_card(self) -> Card:
        """카드 한 장 뽑기"""
        if len(self.cards) < 10:  # 카드가 부족하면 새 덱으로 교체
            self.reset_deck()
        return self.cards.pop()

class BaccaratGame:
    """바카라 게임 클래스"""
    def __init__(self):
        self.deck = Deck()
        self.player_cards = []
        self.banker_cards = []
    
    def calculate_hand_value(self, cards: List[Card]) -> int:
        """핸드 값 계산 (바카라 규칙: 일의 자리만)"""
        total = sum(card.get_value() for card in cards)
        return total % 10
    
    def should_draw_third_card_player(self, player_total: int) -> bool:
        """플레이어 세 번째 카드 뽑기 규칙"""
        return player_total <= 5
    
    def should_draw_third_card_banker(self, banker_total: int, player_total: int, player_third_card: Card = None) -> bool:
        """뱅커 세 번째 카드 뽑기 규칙"""
        if banker_total <= 2:
            return True
        elif banker_total == 3:
            if player_third_card is None:
                return False
            return player_third_card.get_value() != 8
        elif banker_total == 4:
            if player_third_card is None:
                return False
            return player_third_card.get_value() in [2, 3, 4, 5, 6, 7]
        elif banker_total == 5:
            if player_third_card is None:
                return False
            return player_third_card.get_value() in [4, 5, 6, 7]
        elif banker_total == 6:
            if player_third_card is None:
                return False
            return player_third_card.get_value() in [6, 7]
        else:
            return False
    
    def play_round(self) -> Dict:
        """한 라운드 게임 진행"""
        # 초기화
        self.player_cards = []
        self.banker_cards = []
        
        # 초기 2장씩 딜
        self.player_cards.append(self.deck.deal_card())
        self.banker_cards.append(self.deck.deal_card())
        self.player_cards.append(self.deck.deal_card())
        self.banker_cards.append(self.deck.deal_card())
        
        # 초기 점수 계산
        player_total = self.calculate_hand_value(self.player_cards)
        banker_total = self.calculate_hand_value(self.banker_cards)
        
        # 내추럴 체크 (8 또는 9)
        if player_total >= 8 or banker_total >= 8:
            # 내추럴이면 게임 종료
            pass
        else:
            # 세 번째 카드 규칙 적용
            player_third_card = None
            
            # 플레이어 세 번째 카드
            if self.should_draw_third_card_player(player_total):
                player_third_card = self.deck.deal_card()
                self.player_cards.append(player_third_card)
                player_total = self.calculate_hand_value(self.player_cards)
            
            # 뱅커 세 번째 카드
            if self.should_draw_third_card_banker(banker_total, player_total, player_third_card):
                self.banker_cards.append(self.deck.deal_card())
                banker_total = self.calculate_hand_value(self.banker_cards)
        
        # 승부 판정
        if player_total > banker_total:
            winner = "플레이어"
        elif banker_total > player_total:
            winner = "뱅커"
        else:
            winner = "무승부"
        
        return {
            'player_cards': self.player_cards,
            'banker_cards': self.banker_cards,
            'player_total': player_total,
            'banker_total': banker_total,
            'winner': winner
        }
    
    def calculate_payout(self, bet_amount: int, bet_type: str, winner: str) -> int:
        """배당금 계산"""
        if bet_type == winner:
            if bet_type == "플레이어":
                return bet_amount * 2  # 1:1 배당
            elif bet_type == "뱅커":
                return int(bet_amount * 1.95)  # 1:0.95 배당 (5% 수수료)
            elif bet_type == "무승부":
                return bet_amount * 8  # 8:1 배당
        return 0  # 패배시 0원
    
    def format_cards(self, cards: List[Card]) -> str:
        """카드 목록을 문자열로 포맷"""
        return " ".join(str(card) for card in cards)

# 게임 테스트 함수
def test_baccarat_game():
    """바카라 게임 테스트"""
    game = BaccaratGame()
    
    print("=== 바카라 게임 테스트 ===")
    for i in range(3):
        print(f"\n--- 라운드 {i+1} ---")
        result = game.play_round()
        
        print(f"플레이어: {game.format_cards(result['player_cards'])} (총합: {result['player_total']})")
        print(f"뱅커: {game.format_cards(result['banker_cards'])} (총합: {result['banker_total']})")
        print(f"승자: {result['winner']}")
        
        # 배당 테스트
        bet_amount = 1000
        for bet_type in ["플레이어", "뱅커", "무승부"]:
            payout = game.calculate_payout(bet_amount, bet_type, result['winner'])
            print(f"{bet_type} 베팅 ({bet_amount}원) -> {payout}원")

if __name__ == "__main__":
    test_baccarat_game()

