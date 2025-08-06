"""
翻牌後GTO分析器
考慮實際牌面強度和對手範圍
"""

from hand_evaluator import HandEvaluator, HandRank
from typing import List, Tuple

class PostflopAnalyzer:
    """翻牌後策略分析"""
    
    @staticmethod
    def get_postflop_recommendation(hole_cards: List, community_cards: List, 
                                   position: str, current_bet: float, pot: float, 
                                   big_blind: float) -> Tuple[str, float, str]:
        """
        獲取翻牌後建議
        返回: (action, amount, explanation)
        """
        if not community_cards:
            return "check", 0, "沒有公共牌"
        
        # 評估手牌強度
        all_cards = hole_cards + community_cards
        hand_rank, values = HandEvaluator.evaluate_hand(all_cards)
        hand_name = HandEvaluator.get_hand_name(hand_rank)
        
        # 計算相對牌力
        relative_strength = PostflopAnalyzer._calculate_relative_strength(hand_rank, community_cards)
        
        # 是否有人下注
        facing_bet = current_bet > 0
        
        # 根據牌力和情況決定行動
        if hand_rank.value >= HandRank.FLUSH.value:
            # 同花或更好 - 強牌，要價值下注
            if facing_bet:
                # 面對下注，加注或跟注
                if hand_rank.value >= HandRank.FULL_HOUSE.value:
                    # 葫蘆以上，強力加注
                    raise_amount = min(pot * 1.5, current_bet * 3)
                    return "raise", raise_amount, f"你有{hand_name}，這是非常強的牌，應該加注獲取最大價值"
                else:
                    # 同花或順子，根據情況決定
                    if current_bet < pot * 0.5:
                        return "raise", current_bet * 2.5, f"你有{hand_name}，對手下注較小，可以加注"
                    else:
                        return "call", current_bet, f"你有{hand_name}，跟注即可"
            else:
                # 沒人下注，主動下注
                bet_amount = pot * 0.75
                return "bet", bet_amount, f"你有{hand_name}，應該下注獲取價值"
        
        elif hand_rank.value >= HandRank.TWO_PAIR.value:
            # 兩對到順子 - 中等強牌
            if facing_bet:
                pot_odds = current_bet / (pot + current_bet)
                if pot_odds < 0.3:  # 賠率合適
                    return "call", current_bet, f"你有{hand_name}，賠率合適可以跟注"
                else:
                    return "fold", 0, f"你有{hand_name}，但對手下注太大，棄牌"
            else:
                # 下注或過牌
                if relative_strength > 0.6:
                    return "bet", pot * 0.5, f"你有{hand_name}，可以適度下注"
                else:
                    return "check", 0, f"你有{hand_name}，過牌控制底池"
        
        elif hand_rank.value == HandRank.PAIR.value:
            # 一對
            if facing_bet:
                # 通常棄牌，除非賠率極好
                pot_odds = current_bet / (pot + current_bet)
                if pot_odds < 0.2 and values[0] >= 10:  # 大對子且賠率好
                    return "call", current_bet, f"你有{hand_name}，賠率不錯可以跟注"
                else:
                    return "fold", 0, f"你只有{hand_name}，面對下注應該棄牌"
            else:
                # 小心地過牌
                return "check", 0, f"你有{hand_name}，過牌看免費牌"
        
        else:
            # 高牌
            if facing_bet:
                # 面對下注通常棄牌
                pot_odds = current_bet / (pot + current_bet)
                if pot_odds < 0.15:  # 極好的賠率
                    return "call", current_bet, f"你只有{hand_name}，但賠率很好可以跟注"
                else:
                    return "fold", 0, f"你只有{hand_name}，應該棄牌"
            else:
                # 沒人下注，絕對不應該fold！
                if PostflopAnalyzer._has_bluff_potential(hole_cards, community_cards):
                    return "bet", pot * 0.33, f"你有{hand_name}但有詐唬機會，小額下注"
                else:
                    return "check", 0, f"你只有{hand_name}，免費看牌"
    
    @staticmethod
    def _calculate_relative_strength(hand_rank: HandRank, community_cards: List) -> float:
        """計算相對牌力（0-1）"""
        # 簡化的相對牌力計算
        base_strength = {
            HandRank.HIGH_CARD: 0.1,
            HandRank.PAIR: 0.3,
            HandRank.TWO_PAIR: 0.5,
            HandRank.THREE_OF_KIND: 0.65,
            HandRank.STRAIGHT: 0.7,
            HandRank.FLUSH: 0.8,
            HandRank.FULL_HOUSE: 0.9,
            HandRank.FOUR_OF_KIND: 0.95,
            HandRank.STRAIGHT_FLUSH: 0.99,
            HandRank.ROYAL_FLUSH: 1.0
        }
        
        strength = base_strength.get(hand_rank, 0.1)
        
        # 根據公共牌調整
        # 如果公共牌很危險（如四張同花），降低非同花牌的強度
        flush_cards = {}
        for card in community_cards:
            if hasattr(card, 'suit'):
                suit = card.suit
                flush_cards[suit] = flush_cards.get(suit, 0) + 1
        
        max_flush = max(flush_cards.values()) if flush_cards else 0
        if max_flush >= 4 and hand_rank != HandRank.FLUSH:
            strength *= 0.5
        
        return strength
    
    @staticmethod
    def _has_bluff_potential(hole_cards: List, community_cards: List) -> bool:
        """檢查是否有詐唬潛力"""
        # 檢查是否有抽牌可能（順子抽牌、同花抽牌等）
        all_cards = hole_cards + community_cards
        
        # 簡化版：檢查是否接近順子或同花
        # 實際應該更複雜
        ranks = []
        suits = {}
        
        for card in all_cards:
            if hasattr(card, 'rank') and hasattr(card, 'suit'):
                rank_value = HandEvaluator.get_rank_value(card.rank)
                ranks.append(rank_value)
                suits[card.suit] = suits.get(card.suit, 0) + 1
        
        # 檢查同花抽牌
        for suit, count in suits.items():
            if count == 4:  # 差一張同花
                return True
        
        # 檢查順子抽牌（簡化版）
        ranks = sorted(set(ranks))
        for i in range(len(ranks) - 3):
            if ranks[i+3] - ranks[i] <= 4:  # 可能的順子抽牌
                return True
        
        return False