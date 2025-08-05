"""
德州撲克手牌評估器
"""

from enum import Enum
from typing import List, Tuple
from collections import Counter

class HandRank(Enum):
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10

class HandEvaluator:
    """評估德州撲克手牌強度"""
    
    @staticmethod
    def get_rank_value(rank: str) -> int:
        """將牌面轉換為數值"""
        rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
                       '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        return rank_values.get(rank, 0)
    
    @staticmethod
    def evaluate_hand(cards: List) -> Tuple[HandRank, List[int]]:
        """
        評估手牌
        返回：(手牌類型, 比較值列表)
        """
        if len(cards) < 5:
            return HandRank.HIGH_CARD, []
        
        # 獲取所有7張牌的最佳5張組合
        from itertools import combinations
        best_rank = HandRank.HIGH_CARD
        best_values = []
        
        for five_cards in combinations(cards, 5):
            rank, values = HandEvaluator._evaluate_five_cards(list(five_cards))
            if rank.value > best_rank.value or (rank == best_rank and values > best_values):
                best_rank = rank
                best_values = values
        
        return best_rank, best_values
    
    @staticmethod
    def _evaluate_five_cards(cards: List) -> Tuple[HandRank, List[int]]:
        """評估5張牌的組合"""
        # 提取牌面和花色
        ranks = []
        suits = []
        
        for card in cards:
            if hasattr(card, 'rank'):
                ranks.append(HandEvaluator.get_rank_value(card.rank))
                suits.append(card.suit)
            else:
                # 處理字典格式
                ranks.append(HandEvaluator.get_rank_value(card.get('rank', '')))
                suits.append(card.get('suit', ''))
        
        ranks.sort(reverse=True)
        
        # 檢查同花
        is_flush = len(set(suits)) == 1
        
        # 檢查順子
        is_straight = HandEvaluator._is_straight(ranks)
        straight_high = HandEvaluator._get_straight_high(ranks)
        
        # 計算相同牌面的數量
        rank_counts = Counter(ranks)
        counts = sorted(rank_counts.values(), reverse=True)
        rank_groups = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        
        # 判斷手牌類型
        if is_straight and is_flush:
            if straight_high == 14:  # A high straight
                return HandRank.ROYAL_FLUSH, [14]
            return HandRank.STRAIGHT_FLUSH, [straight_high]
        
        if counts[0] == 4:
            # 四條
            four_kind = [r for r, c in rank_groups if c == 4][0]
            kicker = [r for r, c in rank_groups if c != 4][0]
            return HandRank.FOUR_OF_KIND, [four_kind, kicker]
        
        if counts[0] == 3 and counts[1] == 2:
            # 葫蘆
            three_kind = [r for r, c in rank_groups if c == 3][0]
            pair = [r for r, c in rank_groups if c == 2][0]
            return HandRank.FULL_HOUSE, [three_kind, pair]
        
        if is_flush:
            return HandRank.FLUSH, ranks
        
        if is_straight:
            return HandRank.STRAIGHT, [straight_high]
        
        if counts[0] == 3:
            # 三條
            three_kind = [r for r, c in rank_groups if c == 3][0]
            kickers = sorted([r for r, c in rank_groups if c != 3], reverse=True)
            return HandRank.THREE_OF_KIND, [three_kind] + kickers[:2]
        
        if counts[0] == 2 and counts[1] == 2:
            # 兩對
            pairs = sorted([r for r, c in rank_groups if c == 2], reverse=True)
            kicker = [r for r, c in rank_groups if c == 1][0]
            return HandRank.TWO_PAIR, pairs + [kicker]
        
        if counts[0] == 2:
            # 一對
            pair = [r for r, c in rank_groups if c == 2][0]
            kickers = sorted([r for r, c in rank_groups if c == 1], reverse=True)
            return HandRank.PAIR, [pair] + kickers[:3]
        
        # 高牌
        return HandRank.HIGH_CARD, ranks
    
    @staticmethod
    def _is_straight(ranks: List[int]) -> bool:
        """檢查是否為順子"""
        # 檢查普通順子
        unique_ranks = sorted(set(ranks), reverse=True)
        
        for i in range(len(unique_ranks) - 4):
            if unique_ranks[i] - unique_ranks[i+4] == 4:
                return True
        
        # 檢查 A-2-3-4-5 的特殊順子
        if set([14, 5, 4, 3, 2]).issubset(set(ranks)):
            return True
        
        return False
    
    @staticmethod
    def _get_straight_high(ranks: List[int]) -> int:
        """獲取順子的最高牌"""
        unique_ranks = sorted(set(ranks), reverse=True)
        
        # 檢查普通順子
        for i in range(len(unique_ranks) - 4):
            if unique_ranks[i] - unique_ranks[i+4] == 4:
                return unique_ranks[i]
        
        # A-2-3-4-5 的特殊順子
        if set([14, 5, 4, 3, 2]).issubset(set(ranks)):
            return 5
        
        return 0
    
    @staticmethod
    def compare_hands(hand1: Tuple[HandRank, List[int]], hand2: Tuple[HandRank, List[int]]) -> int:
        """
        比較兩手牌
        返回: 1 if hand1 wins, -1 if hand2 wins, 0 if tie
        """
        rank1, values1 = hand1
        rank2, values2 = hand2
        
        if rank1.value > rank2.value:
            return 1
        elif rank1.value < rank2.value:
            return -1
        else:
            # 相同牌型，比較數值
            for v1, v2 in zip(values1, values2):
                if v1 > v2:
                    return 1
                elif v1 < v2:
                    return -1
            return 0
    
    @staticmethod
    def get_hand_name(hand_rank: HandRank) -> str:
        """獲取手牌類型的中文名稱"""
        names = {
            HandRank.HIGH_CARD: "高牌",
            HandRank.PAIR: "一對",
            HandRank.TWO_PAIR: "兩對",
            HandRank.THREE_OF_KIND: "三條",
            HandRank.STRAIGHT: "順子",
            HandRank.FLUSH: "同花",
            HandRank.FULL_HOUSE: "葫蘆",
            HandRank.FOUR_OF_KIND: "四條",
            HandRank.STRAIGHT_FLUSH: "同花順",
            HandRank.ROYAL_FLUSH: "皇家同花順"
        }
        return names.get(hand_rank, "未知")

    @staticmethod
    def determine_winner(players: List, community_cards: List) -> List:
        """
        確定贏家
        返回贏家列表（可能有多個平手）
        """
        active_players = [p for p in players if not p.is_folded]
        if len(active_players) == 1:
            return active_players
        
        player_hands = []
        for player in active_players:
            all_cards = player.hole_cards + community_cards
            hand_rank, values = HandEvaluator.evaluate_hand(all_cards)
            player_hands.append((player, hand_rank, values))
        
        # 找出最佳手牌
        best_rank = max(ph[1].value for ph in player_hands)
        potential_winners = [(p, r, v) for p, r, v in player_hands if r.value == best_rank]
        
        if len(potential_winners) == 1:
            return [potential_winners[0][0]]
        
        # 比較相同牌型的數值
        winners = []
        best_values = potential_winners[0][2]
        
        for player, rank, values in potential_winners:
            comparison = 0
            for v1, v2 in zip(values, best_values):
                if v1 > v2:
                    comparison = 1
                    break
                elif v1 < v2:
                    comparison = -1
                    break
            
            if comparison > 0:
                winners = [player]
                best_values = values
            elif comparison == 0:
                winners.append(player)
        
        return winners