"""
德州撲克 GTO 訓練器 - 簡化版
移除所有特殊字符，確保在各種環境下都能正常運行
"""

import streamlit as st
import random
import json
import time
from enum import Enum
from typing import List, Optional, Dict, Tuple

# 導入所有類
from texas_holdem_complete import *
from debug_logger import DebugLogger
from postflop_analyzer import PostflopAnalyzer

# 創建全局debug logger
debug_logger = DebugLogger()

class GTOAnalyzer:
    """統一的GTO分析器，確保建議和分析的一致性"""
    
    def __init__(self, gto_ranges):
        self.gto_ranges = gto_ranges
        
    def get_preflop_recommendation(self, hand, position, current_bet, big_blind, street=None, game=None):
        """獲取建議（統一邏輯）"""
        debug_logger.log(f"GTO建議: {hand} 在 {position}, 當前下注: {current_bet}, BB: {big_blind}")
        
        # 如果是翻牌後且有遊戲狀態，使用翻牌後分析器
        if street and street != Street.PREFLOP and game and hasattr(game, 'community_cards'):
            # 獲取玩家的手牌
            current_player = None
            for player in game.players:
                if player.position == position and not player.is_folded:
                    current_player = player
                    break
            
            if current_player and current_player.hole_cards and game.community_cards:
                return PostflopAnalyzer.get_postflop_recommendation(
                    current_player.hole_cards,
                    game.community_cards,
                    position,
                    current_bet,
                    game.pot,
                    big_blind
                )
            
            # 否則使用原本的簡化策略
            if current_bet == 0:
                # 沒人下注，有強牌就下注
                if hand in ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "AKs", "AKo", "AQs", "AQo"]:
                    return "bet", big_blind * 2, f"{hand} 在 {street.name} 可以下注"
                else:
                    return "check", 0, f"{hand} 在 {street.name} 過牌"
            else:
                # 有人下注，只有強牌跟注
                if hand in ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo"]:
                    return "call", current_bet, f"{hand} 在 {street.name} 可以跟注"
                else:
                    return "fold", 0, f"{hand} 在 {street.name} 應該棄牌"
        
        # 標準化手牌格式
        normalized_hand = self._normalize_hand(hand)
        debug_logger.log(f"標準化手牌: {normalized_hand} - 大牌: {normalized_hand in ['AA', 'KK', 'QQ', 'JJ', 'AKs', 'AKo']}, 中等牌: {self._is_medium_hand(normalized_hand)}")
        
        # 特殊情況：BB面對limpers（只需付大盲）
        if position == "BB" and current_bet == big_blind:
            # BB可以免費看牌
            return "check", 0, f"{normalized_hand} 在 BB 可以免費看牌"
        
        # 面對加注的情況
        if current_bet > big_blind:
            # BB面對加注
            if position == "BB":
                facing_raise_ranges = self.gto_ranges.get("preflop", {}).get("facing_raise", {}).get("BB_vs_raise", {})
                
                if normalized_hand in facing_raise_ranges.get("3bet", []):
                    # 3bet 到 2.5-3倍原加注
                    recommended_amount = current_bet * 2.5
                    return "raise", recommended_amount, f"{normalized_hand} 在 BB 面對加注應該3bet"
                elif normalized_hand in facing_raise_ranges.get("call", []):
                    return "call", current_bet, f"{normalized_hand} 在 BB 面對加注可以跟注"
                else:
                    return "fold", 0, f"{normalized_hand} 在 BB 面對加注應該棄牌"
            else:
                # 其他位置面對加注，使用vs_UTG_open作為保守策略
                facing_raise_ranges = self.gto_ranges.get("preflop", {}).get("facing_raise", {}).get("vs_UTG_open", {})
                
                if normalized_hand in facing_raise_ranges.get("3bet", []):
                    recommended_amount = current_bet * 2.5
                    return "raise", recommended_amount, f"{normalized_hand} 面對加注應該3bet"
                elif normalized_hand in facing_raise_ranges.get("call", []):
                    return "call", current_bet, f"{normalized_hand} 面對加注可以跟注"
                else:
                    return "fold", 0, f"{normalized_hand} 面對加注應該棄牌"
        
        # 正常RFI情況（沒有人加注）
        position_ranges = self.gto_ranges.get("preflop", {}).get("positions", {}).get(position, {}).get("rfi", {})
        
        if not position_ranges:
            return "fold", 0, f"未找到 {position} 位置的範圍"
        
        # Debug: 顯示範圍內容
        raise_range = position_ranges.get("raise", [])
        debug_logger.log(f"檢查 {normalized_hand} 是否在 {position} 的加注範圍中: {normalized_hand in raise_range}")
        if normalized_hand in ["KQO", "KQS"]:
            debug_logger.log(f"{position} 加注範圍前10張: {raise_range[:10]}...")
            debug_logger.log(f"是否包含KQo: {'KQo' in raise_range}, 是否包含KQO: {'KQO' in raise_range}")
        
        if normalized_hand in position_ranges.get("raise", []):
            # 標準開局加注 2.5BB
            recommended_amount = big_blind * 2.5
            return "raise", recommended_amount, f"{normalized_hand} 在 {position} 是加注牌"
        elif normalized_hand in position_ranges.get("call", []):
            return "call", current_bet, f"{normalized_hand} 在 {position} 可以跟注"
        else:
            return "fold", 0, f"{normalized_hand} 在 {position} 應該棄牌"
    
    def _normalize_hand(self, hand):
        """標準化手牌表示"""
        hand = hand.replace(" ", "")  # 移除空格
        
        if len(hand) == 2:
            return hand.upper()
        elif len(hand) == 3:
            if hand[2].lower() in ['s', 'o']:
                return hand[:2].upper() + hand[2].lower()
            else:
                return hand[:2].upper() + 'o'
        elif len(hand) == 4:
            # Format: "AsKh" or "A♠K♥" -> "AKs" or "AKo"
            # 處理花色符號
            if '♠' in hand or '♥' in hand or '♦' in hand or '♣' in hand:
                card1_rank = hand[0].upper()
                card2_rank = hand[2].upper()
                # 檢查花色是否相同
                suit1 = hand[1]
                suit2 = hand[3]
                suited = 's' if suit1 == suit2 else 'o'
            else:
                # Format: "AsKh" -> "AKs" or "AKo"
                card1_rank = hand[0].upper()
                card2_rank = hand[2].upper()
                suited = 's' if hand[1] == hand[3] else 'o'
            
            # 確保高牌在前
            if "AKQJT98765432".index(card1_rank) > "AKQJT98765432".index(card2_rank):
                card1_rank, card2_rank = card2_rank, card1_rank
            
            if card1_rank == card2_rank:
                return card1_rank + card2_rank
            else:
                return card1_rank + card2_rank + suited.lower()
        return hand.upper()
    
    def _is_medium_hand(self, hand):
        """判斷是否為中等強度手牌"""
        medium_hands = ["TT", "99", "88", "77", "AQs", "AQo", "AJs", "AJo", "KQs", "KQo"]
        return hand in medium_hands
    
    def analyze_decision(self, hand, position, action, amount, current_bet, big_blind, street=None, game=None):
        """分析玩家決策是否符合GTO"""
        recommended_action, recommended_amount, explanation = self.get_preflop_recommendation(
            hand, position, current_bet, big_blind, street, game
        )
        
        # 行動匹配判斷
        if action.lower() == recommended_action.lower():
            if action in ["raise", "bet"] and amount > 0:
                # 檢查金額是否合理
                amount_ratio = amount / max(recommended_amount, 1)
                
                if 0.7 <= amount_ratio <= 1.5:  # 金額在建議的70%-150%之間
                    return True, f"[正確] {explanation}", self._get_detailed_analysis(hand, position, action, amount, True, explanation, current_bet, big_blind)
                elif amount_ratio > 2.5:  # 加注超過建議的2.5倍，可能是3bet/4bet
                    context = "強力3bet！" if current_bet > big_blind else "大幅加注！"
                    return True, f"[正確] {context} {explanation}", self._get_detailed_analysis(hand, position, action, amount, True, explanation, current_bet, big_blind)
                elif amount_ratio < 0.5:  # 金額太小
                    return False, f"[需改進] 行動正確但加注太小（建議約${int(recommended_amount)}）。{explanation}", self._get_detailed_analysis(hand, position, action, amount, False, explanation, current_bet, big_blind)
                else:
                    # 金額偏差但還算合理
                    return True, f"[可接受] 行動正確，金額${amount}略有偏差但仍合理。{explanation}", self._get_detailed_analysis(hand, position, action, amount, True, explanation, current_bet, big_blind)
            else:
                return True, f"[正確] {explanation}", self._get_detailed_analysis(hand, position, action, amount, True, explanation, current_bet, big_blind)
        else:
            return False, f"[錯誤] 建議{recommended_action}而不是{action}。{explanation}", self._get_detailed_analysis(hand, position, action, amount, False, explanation, current_bet, big_blind)
    
    def _get_detailed_analysis(self, hand, position, action, amount, is_correct, explanation, current_bet, big_blind):
        """生成詳細分析，提供當下最佳建議和解釋"""
        result_emoji = "[正確]" if is_correct else "[錯誤]"
        
        # 獲取最佳建議
        best_action, best_amount, best_explanation = self.get_preflop_recommendation(hand, position, current_bet, big_blind)
        
        # 分析當前情況
        situation_analysis = self._analyze_situation(hand, position, current_bet, big_blind)
        
        # 生成具體建議
        specific_advice = self._get_specific_advice(hand, position, action, best_action, is_correct)
        
        return f"""
{result_emoji} **決策分析**

**你的選擇:** {action.upper()} ${amount if amount > 0 else '0'}
**最佳建議:** {best_action.upper()} ${int(best_amount) if best_amount and best_amount > 0 else '0'}

**當下情況分析:**
{situation_analysis}

**最佳策略解釋:**
{best_explanation}

**具體建議:**
{specific_advice}

**學習要點:**
- 在{position}位置面對${current_bet}的下注時，{hand}的標準GTO策略是{best_action}
- {'你的決策完全符合GTO原則，繼續保持！' if is_correct else f'考慮調整為{best_action}以優化長期收益'}
        """
    
    def _analyze_situation(self, hand, position, current_bet, big_blind):
        """分析當前牌局情況"""
        # 判斷是否面對加注
        facing_raise = current_bet > big_blind
        
        # 手牌強度分析
        hand_strength = self._get_hand_strength(hand)
        
        # 位置分析
        position_advantage = self._get_position_analysis(position)
        
        if facing_raise:
            pot_odds = current_bet / (current_bet + big_blind + (current_bet - big_blind))
            return f"""
- **手牌強度:** {hand_strength}
- **位置狀況:** {position_advantage}  
- **面對加注:** ${current_bet} (需要{pot_odds:.1%}的勝率才值得跟注)
- **決策要點:** 在此情況下需要較強的手牌才能繼續
            """
        else:
            return f"""
- **手牌強度:** {hand_strength}
- **位置狀況:** {position_advantage}
- **行動成本:** 只需支付大盲${big_blind}
- **決策要點:** 可以用較寬的範圍進行遊戲
            """
    
    def _get_hand_strength(self, hand):
        """評估手牌強度"""
        premium_hands = ["AA", "KK", "QQ", "JJ", "AKs", "AKo"]
        strong_hands = ["TT", "99", "88", "77", "AQs", "AQo", "AJs", "AJo", "KQs", "KQo"]
        
        if hand in premium_hands:
            return f"{hand} - 頂級強牌，幾乎在任何位置都應該積極遊戲"
        elif hand in strong_hands:
            return f"{hand} - 強牌，在大多數情況下值得遊戲"
        else:
            return f"{hand} - 邊緣牌或弱牌，需要謹慎選擇遊戲時機"
    
    def _get_position_analysis(self, position):
        """分析位置優勢"""
        position_info = {
            "UTG": "最早位置，需要最緊的範圍，因為後面還有很多對手",
            "MP": "中間位置，可以比UTG稍寬但仍需謹慎",
            "CO": "後期位置，可以用較寬的範圍，有位置優勢",
            "BTN": "最佳位置，可以用最寬的範圍，後續所有輪次都有位置優勢",
            "SB": "不利位置，雖然有折扣但後續輪次沒有位置優勢",
            "BB": "已投入大盲，有折扣優勢，但位置不佳"
        }
        return position_info.get(position, "未知位置")
    
    def _get_specific_advice(self, hand, position, player_action, best_action, is_correct):
        """提供具體的改進建議"""
        if is_correct:
            return f"""
[正確] **優秀的決策！** 你選擇了{player_action}，這正是GTO建議的最佳行動。
   在{position}位置拿到{hand}時，{best_action}是數學上最優的選擇。
   繼續保持這種決策水準，你的長期收益會很可觀。
            """
        else:
            advice_map = {
                ("fold", "raise"): f"你選擇了棄牌，但{hand}在{position}位置實際上足夠強，應該加注進場。這樣的強牌棄掉是浪費了價值。",
                ("fold", "call"): f"你選擇了棄牌，但{hand}在當前情況下有足夠的勝率可以跟注。錯過了這個有利可圖的機會。",
                ("call", "raise"): f"你選擇了跟注，但{hand}實際上夠強可以加注。加注能夠建立底池並獲得主動權。",
                ("call", "fold"): f"你選擇了跟注，但{hand}在當前情況下勝率不足，應該棄牌以避免損失。",
                ("raise", "fold"): f"你選擇了加注，但{hand}在{position}位置太弱，應該棄牌。這樣的激進決策長期會造成損失。",
                ("raise", "call"): f"你選擇了加注，但{hand}在當前情況下更適合跟注。過度激進可能面臨更大的對抗。"
            }
            
            key = (player_action, best_action)
            specific_advice = advice_map.get(key, f"建議改為{best_action}，這是當前情況下的最佳選擇。")
            
            # 如果行動相同只是金額不同，調整建議
            if player_action == best_action:
                return f"""
[可調整] **金額優化:** 你的{player_action}決策正確，但可以優化金額選擇。
   GTO建議的金額會帶來更好的長期收益。
                """
            else:
                return f"""
[需改進] **策略調整:** {specific_advice}
   
   **記住這個要點:** 在{position}位置，面對當前的下注結構，{hand}的最佳策略是{best_action}。
                """

def main():
    st.set_page_config(page_title="德州撲克 GTO 訓練器", layout="wide")
    st.title("德州撲克 GTO 訓練器")
    
    debug_logger.log("簡化版本啟動")
    
    # 初始化session state
    if "game" not in st.session_state:
        st.session_state.game = None
        st.session_state.hand_count = 0
        st.session_state.player_decisions = []
        st.session_state.gto_analyzer = None
    
    # 側邊欄設定
    with st.sidebar:
        st.header("遊戲設定")
        starting_stack = st.slider("起始籌碼", 1000, 10000, 5000, step=500)
        small_blind = st.slider("小盲", 25, 250, 50, step=25)
        big_blind = small_blind * 2
        
        st.divider()
        
        if st.button("開始新局", type="primary", use_container_width=True):
            debug_logger.log("=== 開始新局 ===")
            
            # 確保真正隨機化
            seed = int(time.time() * 1000) % 2**32
            random.seed(seed)
            debug_logger.log(f"Random seed: {seed}")
            
            game = TexasHoldemGame(starting_stack=starting_stack, 
                                 small_blind=small_blind, 
                                 big_blind=big_blind)
            human_position = random.randint(0, 5)
            game.initialize_players(human_seat=human_position)
            game.start_new_hand()
            
            # 創建GTO分析器
            with open('gto_ranges_clean.json', 'r', encoding='utf-8') as f:
                gto_ranges = json.load(f)
            gto_analyzer = GTOAnalyzer(gto_ranges)
            
            st.session_state.game = game
            st.session_state.hand_count = 1
            st.session_state.player_decisions = []
            st.session_state.gto_analyzer = gto_analyzer
            
            human_player = next(p for p in game.players if p.is_human)
            st.success(f"新局開始！你的位置：{human_player.position}")
            st.rerun()
        
        st.divider()
        st.metric("手牌數", st.session_state.hand_count)
    
    # 主遊戲區域
    game = st.session_state.game
    if game:
        # 顯示遊戲狀態
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### 第 {st.session_state.hand_count} 手牌")
            
            # 顯示公共牌
            if game.community_cards:
                community_str = " ".join([f"{card.rank}{card.suit}" for card in game.community_cards])
                st.markdown(f"**公共牌:** {community_str}")
            
            # 顯示底池
            st.markdown(f"**底池:** ${game.pot}")
            
            # 顯示行動歷史
            if game.action_history:
                st.markdown("**行動歷史:**")
                for action in game.action_history[-5:]:  # 顯示最近5個行動
                    st.text(action)
        
        with col2:
            # 顯示玩家手牌
            human_player = next(p for p in game.players if p.is_human)
            if human_player.hole_cards:
                hand_str = f"{human_player.hole_cards[0].rank}{human_player.hole_cards[0].suit} {human_player.hole_cards[1].rank}{human_player.hole_cards[1].suit}"
                st.markdown(f"**你的手牌:** {hand_str}")
                st.markdown(f"**你的位置:** {human_player.position}")
                st.markdown(f"**你的籌碼:** ${human_player.stack}")
        
        st.divider()
        
        # 檢查遊戲是否結束
        if game.street == Street.SHOWDOWN or len(game.get_active_players()) == 1:
            # 顯示結果
            st.markdown("### 手牌結束")
            
            # 先自動執行電腦玩家的行動直到真正結束
            if game.street != Street.SHOWDOWN:
                while len(game.get_active_players()) > 1 and game.street != Street.SHOWDOWN:
                    current_player_idx = game.get_next_player_index()
                    if current_player_idx == -1:
                        break
                    
                    current_player = game.players[current_player_idx]
                    if not current_player.is_human and current_player.hole_cards:
                        # 獲取電腦玩家的手牌
                        comp_hand = game.get_hand_string(current_player.hole_cards)
                        
                        # 獲取GTO建議
                        comp_action, comp_amount, comp_explanation = st.session_state.gto_analyzer.get_preflop_recommendation(
                            comp_hand, current_player.position, game.current_bet, game.big_blind, game.street
                        )
                        
                        # 執行建議的行動
                        if comp_action == "fold":
                            game.process_action(current_player_idx, Action.FOLD, 0)
                        elif comp_action == "check":
                            game.process_action(current_player_idx, Action.CHECK, 0)
                        elif comp_action == "call":
                            game.process_action(current_player_idx, Action.CALL, game.current_bet)
                        elif comp_action == "raise":
                            if game.current_bet == 0:
                                game.process_action(current_player_idx, Action.BET, comp_amount)
                            else:
                                game.process_action(current_player_idx, Action.RAISE, comp_amount)
            
            # 處理結算
            if len(game.get_active_players()) == 1:
                winner = next(p for p in game.players if not p.is_folded)
                st.success(f"{winner.name} 贏得底池 ${game.pot}")
            else:
                # 實際攤牌
                game.determine_winner()
                # determine_winner 不返回值，所以我們需要查看誰贏了
                st.success(f"底池 ${game.pot} 已分配給贏家")
            
            # 顯示分析報告
            if st.session_state.player_decisions:
                st.markdown("### GTO 分析報告")
                
                total_decisions = len(st.session_state.player_decisions)
                correct_decisions = sum(1 for d in st.session_state.player_decisions if d['is_correct'])
                
                for i, decision in enumerate(st.session_state.player_decisions):
                    st.markdown(f"#### 決策 {i+1}: {decision['street'].upper()}")
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if decision['is_correct']:
                            st.success("正確")
                        else:
                            st.error("錯誤")
                    
                    with col2:
                        st.markdown(f"**手牌:** {decision['hand']}")
                        st.markdown(f"**位置:** {decision['position']}")
                        st.markdown(f"**你的行動:** {decision['action']} ${decision['amount']}")
                        st.markdown(f"**建議:** {decision['suggestion']}")
                        
                        # 顯示詳細分析
                        detailed = decision.get('detailed', '')
                        if detailed:
                            with st.expander("詳細分析", expanded=False):
                                st.markdown(detailed)
                    
                    st.markdown("---")
                
                # 總結統計
                if total_decisions > 0:
                    accuracy = (correct_decisions / total_decisions) * 100
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("總決策數", total_decisions)
                    with col2:
                        st.metric("正確決策", correct_decisions)
                    with col3:
                        st.metric("準確率", f"{accuracy:.1f}%")
                    
                    if accuracy >= 90:
                        st.success("卓越！你的GTO技巧非常出色！")
                    elif accuracy >= 75:
                        st.success("很棒！你的決策大部分符合GTO！")
                    elif accuracy >= 60:
                        st.warning("不錯！還有一些改進空間！")
                    else:
                        st.error("繼續努力！多練習GTO策略！")
            
            # 重新開始按鈕
            if st.button("下一手牌", type="primary", use_container_width=True):
                # 重新隨機化位置
                seed = int(time.time() * 1000) % 2**32
                random.seed(seed)
                
                new_game = TexasHoldemGame(starting_stack=game.starting_stack,
                                         small_blind=game.small_blind,
                                         big_blind=game.big_blind)
                human_position = random.randint(0, 5)
                new_game.initialize_players(human_seat=human_position)
                new_game.start_new_hand()
                
                # 創建新的分析器
                new_gto_analyzer = GTOAnalyzer(new_game.gto_ranges)
                
                st.session_state.game = new_game
                st.session_state.hand_count += 1
                st.session_state.player_decisions = []
                st.session_state.gto_analyzer = new_gto_analyzer
                
                human_player = next(p for p in new_game.players if p.is_human)
                st.success(f"新手牌！你的新位置：{human_player.position}")
                st.rerun()
    
        else:
            # 檢查是否只剩一個玩家
            active_players = game.get_active_players()
            if len(active_players) == 1:
                # 只剩一個玩家，直接結束
                debug_logger.log(f"只剩一個玩家，手牌結束")
                st.rerun()
            
            # 使用當前索引而不是尋找下一個
            current_player = game.players[game.current_player_index]
            
            # 如果當前玩家已fold或all-in，找下一個玩家
            if current_player.is_folded or current_player.is_all_in:
                next_idx = game.get_next_player_index()
                if next_idx == -1:
                    # 沒有玩家需要行動，檢查是否該進入下一街
                    if game.is_betting_round_complete():
                        debug_logger.log(f"下注輪結束，進入下一街")
                        game.move_to_next_street()
                        st.rerun()
                    else:
                        # 不應該發生這種情況
                        debug_logger.log(f"錯誤：沒有玩家需要行動但下注輪未結束")
                        st.error("遊戲狀態錯誤")
                        return
                else:
                    game.current_player_index = next_idx
                    st.rerun()
            
            # Debug: 顯示當前狀態
            debug_logger.log(f"當前玩家索引: {game.current_player_index}, 當前下注: {game.current_bet}, 街道: {game.street.name}")
            for i, p in enumerate(game.players):
                if not p.is_folded:
                    debug_logger.log(f"  玩家{i} {p.name}({p.position}): bet={p.current_bet}, acted={p.has_acted_this_street}")
            
            # 顯示當前玩家
            st.markdown(f"### 現在輪到: {current_player.name} ({current_player.position})")
            
            if current_player.is_human:
                # 人類玩家行動
                debug_logger.log(f"人類玩家行動: {current_player.position}")
                hand_str = game.get_hand_string(current_player.hole_cards)
                
                # 獲取GTO建議（使用統一的分析器）
                gto_action, gto_amount, gto_explanation = st.session_state.gto_analyzer.get_preflop_recommendation(
                    hand_str, current_player.position, game.current_bet, game.big_blind, game.street
                )
                
                # 顯示行動選項
                col1, col2, col3 = st.columns(3)
                
                action_taken = None
                amount_taken = 0
                
                with col1:
                    fold_text = "Fold 棄牌"
                    if gto_action == "fold":
                        fold_text += " (GTO建議)"
                    
                    if st.button(fold_text, key=f"fold_{st.session_state.hand_count}_{game.street.value}", 
                               use_container_width=True):
                        action_taken = "fold"
                        amount_taken = 0
                        
                        # 記錄決策用於分析
                        is_correct, suggestion, detailed = st.session_state.gto_analyzer.analyze_decision(
                            hand_str, current_player.position, "fold", 0, game.current_bet, game.big_blind
                        )
                        
                        st.session_state.player_decisions.append({
                            'street': game.street.name,
                            'hand': hand_str,
                            'position': current_player.position,
                            'action': 'fold',
                            'amount': 0,
                            'is_correct': is_correct,
                            'suggestion': suggestion,
                            'detailed': detailed
                        })
                        
                        # 執行行動
                        game.process_action(game.current_player_index, Action.FOLD, 0)
                        
                        # 更新到下一個玩家
                        next_idx = game.get_next_player_index()
                        if next_idx != -1:
                            game.current_player_index = next_idx
                        elif game.is_betting_round_complete():
                            game.move_to_next_street()
                        
                        st.rerun()
                
                with col2:
                        # Check/Call 選項
                        if game.current_bet == 0 or (current_player.position == "BB" and game.current_bet == game.big_blind):
                            check_text = "Check 過牌"
                            if gto_action == "check":
                                check_text += " (GTO建議)"
                            
                            if st.button(check_text, key=f"check_{st.session_state.hand_count}_{game.street.value}",
                                       use_container_width=True):
                                action_taken = "check"
                                amount_taken = 0
                                
                                # 記錄決策
                                is_correct, suggestion, detailed = st.session_state.gto_analyzer.analyze_decision(
                                    hand_str, current_player.position, "check", 0, game.current_bet, game.big_blind
                                )
                                
                                st.session_state.player_decisions.append({
                                    'street': game.street.name,
                                    'hand': hand_str,
                                    'position': current_player.position,
                                    'action': 'check',
                                    'amount': 0,
                                    'is_correct': is_correct,
                                    'suggestion': suggestion,
                                    'detailed': detailed
                                })
                                
                                game.process_action(game.current_player_index, Action.CHECK, 0)
                                
                                # 更新到下一個玩家
                                next_idx = game.get_next_player_index()
                                if next_idx != -1:
                                    game.current_player_index = next_idx
                                elif game.is_betting_round_complete():
                                    game.move_to_next_street()
                                
                                st.rerun()
                        else:
                            call_amount = game.current_bet - current_player.current_bet
                            call_text = f"Call 跟注 ${call_amount}"
                            if gto_action == "call":
                                call_text += " (GTO建議)"
                            
                            if st.button(call_text, key=f"call_{st.session_state.hand_count}_{game.street.value}",
                                       use_container_width=True):
                                action_taken = "call"
                                amount_taken = game.current_bet
                                
                                # 記錄決策
                                is_correct, suggestion, detailed = st.session_state.gto_analyzer.analyze_decision(
                                    hand_str, current_player.position, "call", game.current_bet, game.current_bet, game.big_blind
                                )
                                
                                st.session_state.player_decisions.append({
                                    'street': game.street.name,
                                    'hand': hand_str,
                                    'position': current_player.position,
                                    'action': 'call',
                                    'amount': game.current_bet,
                                    'is_correct': is_correct,
                                    'suggestion': suggestion,
                                    'detailed': detailed
                                })
                                
                                game.process_action(game.current_player_index, Action.CALL, game.current_bet)
                                
                                # 更新到下一個玩家
                                next_idx = game.get_next_player_index()
                                if next_idx != -1:
                                    game.current_player_index = next_idx
                                elif game.is_betting_round_complete():
                                    game.move_to_next_street()
                                
                                st.rerun()
                
                with col3:
                    # Bet/Raise 選項
                    if game.current_bet == 0:
                        action_text = "Bet 下注"
                        min_amount = game.big_blind
                        default_amount = game.big_blind * 2.5
                    else:
                        action_text = "Raise 加注"
                        min_amount = game.current_bet * 2
                        default_amount = game.current_bet * 2.5
                    
                    if gto_action in ["bet", "raise"]:
                        action_text += f" ${int(gto_amount)} (GTO建議)"
                        default_amount = gto_amount
                    
                    # 金額選擇
                    bet_amount = st.number_input(
                        "下注金額",
                        min_value=int(min_amount),
                        max_value=int(current_player.stack),
                        value=int(min(default_amount, current_player.stack)),
                        step=int(game.big_blind),
                        key=f"bet_amount_{st.session_state.hand_count}_{game.street.value}"
                    )
                    
                    if st.button(action_text, key=f"raise_{st.session_state.hand_count}_{game.street.value}",
                               use_container_width=True):
                        action_taken = "raise" if game.current_bet > 0 else "bet"
                        amount_taken = bet_amount
                        
                        # 記錄決策
                        is_correct, suggestion, detailed = st.session_state.gto_analyzer.analyze_decision(
                            hand_str, current_player.position, action_taken, bet_amount, game.current_bet, game.big_blind
                        )
                        
                        st.session_state.player_decisions.append({
                            'street': game.street.name,
                            'hand': hand_str,
                            'position': current_player.position,
                            'action': action_taken,
                            'amount': bet_amount,
                            'is_correct': is_correct,
                            'suggestion': suggestion,
                            'detailed': detailed
                        })
                        
                        if game.current_bet == 0:
                            game.process_action(game.current_player_index, Action.BET, bet_amount)
                        else:
                            game.process_action(game.current_player_index, Action.RAISE, bet_amount)
                        
                        # 更新到下一個玩家
                        next_idx = game.get_next_player_index()
                        if next_idx != -1:
                            game.current_player_index = next_idx
                        elif game.is_betting_round_complete():
                            game.move_to_next_street()
                        
                        st.rerun()
            
            else:
                # 電腦玩家自動行動
                debug_logger.log(f"電腦玩家 {current_player.name} 行動")
                
                # 獲取電腦玩家的手牌
                if current_player.hole_cards:
                    comp_hand = game.get_hand_string(current_player.hole_cards)
                    
                    # 獲取GTO建議
                    comp_action, comp_amount, comp_explanation = st.session_state.gto_analyzer.get_preflop_recommendation(
                        comp_hand, current_player.position, game.current_bet, game.big_blind, game.street
                    )
                    
                    # 執行建議的行動
                    if comp_action == "fold":
                        game.process_action(game.current_player_index, Action.FOLD, 0)
                    elif comp_action == "check":
                        game.process_action(game.current_player_index, Action.CHECK, 0)
                    elif comp_action == "call":
                        game.process_action(game.current_player_index, Action.CALL, game.current_bet)
                    elif comp_action == "raise":
                        if game.current_bet == 0:
                            game.process_action(game.current_player_index, Action.BET, comp_amount)
                        else:
                            game.process_action(game.current_player_index, Action.RAISE, comp_amount)
                    
                    debug_logger.log(f"{current_player.name} 執行 {comp_action} ${comp_amount if comp_action != 'fold' else 0}")
                    
                    # 更新到下一個玩家
                    next_idx = game.get_next_player_index()
                    if next_idx != -1:
                        game.current_player_index = next_idx
                    elif game.is_betting_round_complete():
                        game.move_to_next_street()
                
                st.rerun()
    
    else:
        st.info("請在左側點擊「開始新局」")

if __name__ == "__main__":
    main()