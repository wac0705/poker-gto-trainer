"""
德州撲克完整版 - GTO訓練器
規則：
1. 6人桌，位置順序：UTG -> MP -> CO -> BTN -> SB -> BB
2. Preflop行動順序：UTG先行動，BB最後（除非有加注）
3. Postflop行動順序：SB先行動（如果還在），BTN最後
4. 下注輪結束條件：所有未fold玩家都已行動且下注金額相同
5. 電腦玩家根據GTO策略行動
6. 每局結束後分析玩家決策
"""

import streamlit as st
import random
import json
import time
from enum import Enum
from typing import List, Optional, Dict, Tuple

class Action(Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"

class Street(Enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"

class Card:
    def __init__(self, rank: str, suit: str):
        self.rank = rank
        self.suit = suit
        self.value = self._get_value()
    
    def _get_value(self) -> int:
        rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
                       '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        return rank_values[self.rank]
    
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    def __repr__(self):
        return str(self)

class Deck:
    def __init__(self):
        self.reset()
    
    def reset(self):
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        suits = ['♠', '♥', '♦', '♣']
        self.cards = [Card(rank, suit) for rank in ranks for suit in suits]
        random.shuffle(self.cards)
    
    def deal(self, num: int = 1) -> List[Card]:
        return [self.cards.pop() for _ in range(num)]

class Player:
    def __init__(self, name: str, stack: int, position: str, is_human: bool = False):
        self.name = name
        self.stack = stack
        self.position = position
        self.is_human = is_human
        self.hole_cards: List[Card] = []
        self.current_bet = 0
        self.total_bet_this_street = 0
        self.has_acted_this_street = False
        self.is_folded = False
        self.is_all_in = False
        
    def reset_for_new_hand(self):
        self.hole_cards = []
        self.current_bet = 0
        self.total_bet_this_street = 0
        self.has_acted_this_street = False
        self.is_folded = False
        self.is_all_in = False
    
    def bet_amount(self, amount: int):
        """下注指定金額"""
        actual_bet = min(amount, self.stack)
        self.stack -= actual_bet
        self.current_bet += actual_bet
        self.total_bet_this_street += actual_bet
        if self.stack == 0:
            self.is_all_in = True
        return actual_bet

class TexasHoldemGame:
    def __init__(self, num_players: int = 6, starting_stack: int = 5000, 
                 small_blind: int = 50, big_blind: int = 100):
        self.num_players = num_players
        self.starting_stack = starting_stack
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.deck = Deck()
        self.players: List[Player] = []
        self.community_cards: List[Card] = []
        self.pot = 0
        self.current_bet = 0
        self.min_raise = big_blind
        self.street = Street.PREFLOP
        self.action_history: List[str] = []
        self.current_player_index = 0
        self.last_aggressor_index = -1
        self.num_players_to_act = 0
        
        # 載入GTO策略
        with open('gto_ranges_clean.json', 'r', encoding='utf-8') as f:
            self.gto_ranges = json.load(f)
    
    def initialize_players(self, human_seat: int = 0):
        """初始化玩家"""
        positions = ['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB']
        for i in range(self.num_players):
            name = "You" if i == human_seat else f"Player {i+1}"
            player = Player(name, self.starting_stack, positions[i], is_human=(i == human_seat))
            self.players.append(player)
    
    def start_new_hand(self):
        """開始新的一手牌"""
        self.deck.reset()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.min_raise = self.big_blind
        self.street = Street.PREFLOP
        self.action_history = []
        
        # 重置玩家狀態
        for player in self.players:
            player.reset_for_new_hand()
        
        # 發手牌
        for player in self.players:
            player.hole_cards = self.deck.deal(2)
        
        # 收盲注
        self.post_blinds()
        
        # 設定第一個行動玩家
        self.set_first_player_to_act()
    
    def post_blinds(self):
        """收取盲注"""
        sb_index = self.get_position_index('SB')
        bb_index = self.get_position_index('BB')
        
        # 小盲
        sb_amount = self.players[sb_index].bet_amount(self.small_blind)
        self.pot += sb_amount
        self.action_history.append(f"{self.players[sb_index].name} posts SB ${sb_amount}")
        
        # 大盲
        bb_amount = self.players[bb_index].bet_amount(self.big_blind)
        self.pot += bb_amount
        self.current_bet = self.big_blind
        self.action_history.append(f"{self.players[bb_index].name} posts BB ${bb_amount}")
        
        self.last_aggressor_index = bb_index
    
    def get_position_index(self, position: str) -> int:
        """獲取指定位置的玩家索引"""
        for i, player in enumerate(self.players):
            if player.position == position:
                return i
        return -1
    
    def set_first_player_to_act(self):
        """設定第一個需要行動的玩家"""
        if self.street == Street.PREFLOP:
            # Preflop: UTG第一個行動
            self.current_player_index = self.get_position_index('UTG')
        else:
            # Postflop: 從SB開始找第一個還在的玩家
            positions_order = ['SB', 'BB', 'UTG', 'MP', 'CO', 'BTN']
            for pos in positions_order:
                idx = self.get_position_index(pos)
                if idx >= 0 and not self.players[idx].is_folded:
                    self.current_player_index = idx
                    break
        
        self.count_players_to_act()
    
    def count_players_to_act(self):
        """計算還需要行動的玩家數"""
        self.num_players_to_act = sum(1 for p in self.players 
                                     if not p.is_folded and not p.is_all_in 
                                     and (not p.has_acted_this_street or p.current_bet < self.current_bet))
    
    def get_active_players(self) -> List[Player]:
        """獲取還在牌局中的玩家"""
        return [p for p in self.players if not p.is_folded]
    
    def get_players_in_pot(self) -> List[Player]:
        """獲取有資格贏得底池的玩家（未fold）"""
        return [p for p in self.players if not p.is_folded]
    
    def is_betting_round_complete(self) -> bool:
        """檢查當前下注輪是否結束"""
        active_players = [p for p in self.players if not p.is_folded and not p.is_all_in]
        
        # 只剩一個玩家
        if len(self.get_active_players()) <= 1:
            return True
        
        # 所有還能行動的玩家都已經行動且下注相同
        for player in active_players:
            if not player.has_acted_this_street:
                return False
            if player.current_bet < self.current_bet:
                return False
        
        return True
    
    def move_to_next_street(self):
        """進入下一條街"""
        # 重置玩家狀態
        for player in self.players:
            player.current_bet = 0
            player.total_bet_this_street = 0
            player.has_acted_this_street = False
        
        self.current_bet = 0
        self.min_raise = self.big_blind
        
        if self.street == Street.PREFLOP:
            self.street = Street.FLOP
            self.community_cards.extend(self.deck.deal(3))
            self.action_history.append(f"\n=== FLOP: {' '.join(str(c) for c in self.community_cards[-3:])} ===")
        elif self.street == Street.FLOP:
            self.street = Street.TURN
            self.community_cards.extend(self.deck.deal(1))
            self.action_history.append(f"\n=== TURN: {self.community_cards[-1]} ===")
        elif self.street == Street.TURN:
            self.street = Street.RIVER
            self.community_cards.extend(self.deck.deal(1))
            self.action_history.append(f"\n=== RIVER: {self.community_cards[-1]} ===")
        elif self.street == Street.RIVER:
            self.street = Street.SHOWDOWN
            self.action_history.append("\n=== SHOWDOWN ===")
        
        self.set_first_player_to_act()
        
        # Debug
        from debug_logger import DebugLogger
        debug_logger = DebugLogger()
        debug_logger.log(f"進入 {self.street.name}, 第一個行動玩家索引: {self.current_player_index}")
    
    def get_next_player_index(self) -> int:
        """獲取下一個需要行動的玩家索引"""
        start_idx = self.current_player_index
        idx = start_idx
        attempts = 0
        
        while attempts < self.num_players:
            idx = (idx + 1) % self.num_players
            attempts += 1
            player = self.players[idx]
            
            # 找到下一個需要行動的玩家
            if not player.is_folded and not player.is_all_in:
                # 如果還沒行動，或者下注不夠，則需要行動
                if not player.has_acted_this_street or player.current_bet < self.current_bet:
                    return idx
        
        # 沒有找到需要行動的玩家
        return -1
    
    def get_valid_actions(self, player: Player) -> List[Tuple[Action, int, int]]:
        """獲取玩家的有效動作 (action, min_amount, max_amount)"""
        actions = []
        
        if player.is_folded or player.is_all_in:
            return actions
        
        # Fold 總是可以的
        actions.append((Action.FOLD, 0, 0))
        
        # Check/Call
        call_amount = self.current_bet - player.current_bet
        if call_amount == 0:
            actions.append((Action.CHECK, 0, 0))
        else:
            actual_call = min(call_amount, player.stack)
            actions.append((Action.CALL, actual_call, actual_call))
        
        # Bet/Raise
        if self.current_bet == 0:
            # Bet
            min_bet = self.big_blind
            max_bet = player.stack
            if max_bet >= min_bet:
                actions.append((Action.BET, min_bet, max_bet))
        else:
            # Raise
            min_raise_to = self.current_bet + self.min_raise
            max_raise_to = player.stack + player.current_bet
            if max_raise_to >= min_raise_to:
                actions.append((Action.RAISE, min_raise_to, max_raise_to))
        
        return actions
    
    def process_action(self, player_index: int, action: Action, amount: int = 0):
        """處理玩家動作"""
        player = self.players[player_index]
        player.has_acted_this_street = True
        
        if action == Action.FOLD:
            player.is_folded = True
            self.action_history.append(f"{player.name} folds")
            
        elif action == Action.CHECK:
            self.action_history.append(f"{player.name} checks")
            
        elif action == Action.CALL:
            call_amount = self.current_bet - player.current_bet
            actual_bet = player.bet_amount(call_amount)
            self.pot += actual_bet
            self.action_history.append(f"{player.name} calls ${actual_bet}")
            
        elif action == Action.BET:
            actual_bet = player.bet_amount(amount)
            self.pot += actual_bet
            self.current_bet = player.current_bet
            self.min_raise = actual_bet
            self.last_aggressor_index = player_index
            self.action_history.append(f"{player.name} bets ${actual_bet}")
            
            # 其他玩家需要重新行動
            for p in self.players:
                if not p.is_folded and p != player:
                    p.has_acted_this_street = False
                    
        elif action == Action.RAISE:
            raise_to = amount
            actual_bet = player.bet_amount(raise_to - player.current_bet)
            self.pot += actual_bet
            
            # 計算加注大小用於下次最小加注
            raise_size = raise_to - self.current_bet
            self.min_raise = max(self.min_raise, raise_size)
            
            self.current_bet = raise_to
            self.last_aggressor_index = player_index
            self.action_history.append(f"{player.name} raises to ${raise_to}")
            
            # 其他玩家需要重新行動
            for p in self.players:
                if not p.is_folded and p != player:
                    p.has_acted_this_street = False
    
    def get_hand_string(self, cards: List[Card]) -> str:
        """轉換手牌為標準格式（如 AKs, 99）"""
        if len(cards) != 2:
            return ""
        
        rank1, rank2 = cards[0].rank, cards[1].rank
        suit1, suit2 = cards[0].suit, cards[1].suit
        
        # 按牌力排序
        if cards[1].value > cards[0].value:
            rank1, rank2 = rank2, rank1
            suit1, suit2 = suit2, suit1
        
        if rank1 == rank2:
            return rank1 + rank2
        else:
            suited = "s" if suit1 == suit2 else "o"
            return rank1 + rank2 + suited
    
    def get_gto_action(self, player: Player) -> Tuple[Action, int]:
        """根據GTO策略獲取建議動作"""
        hand = self.get_hand_string(player.hole_cards)
        valid_actions = self.get_valid_actions(player)
        
        # Preflop策略
        if self.street == Street.PREFLOP:
            # BB可以check
            if player.position == 'BB' and self.current_bet == self.big_blind and player.current_bet == self.big_blind:
                # BB面對limp，根據手牌決定
                if player.position in self.gto_ranges["preflop"]["positions"]:
                    ranges = self.gto_ranges["preflop"]["positions"][player.position]["rfi"]
                    if hand in ranges["raise"]:
                        # 強牌加注
                        for action, min_amt, max_amt in valid_actions:
                            if action == Action.RAISE:
                                return Action.RAISE, int(self.current_bet * 3)
                return Action.CHECK, 0
            
            # 一般RFI情況
            if self.current_bet <= self.big_blind:
                if player.position in self.gto_ranges["preflop"]["positions"]:
                    ranges = self.gto_ranges["preflop"]["positions"][player.position]["rfi"]
                    if hand in ranges["raise"]:
                        for action, min_amt, max_amt in valid_actions:
                            if action == Action.RAISE:
                                return Action.RAISE, int(self.current_bet * 2.5)
                        for action, min_amt, max_amt in valid_actions:
                            if action == Action.BET:
                                return Action.BET, int(self.big_blind * 2.5)
                return Action.FOLD, 0
            
            # 面對加注
            else:
                if player.position in self.gto_ranges["preflop"]["positions"]:
                    ranges = self.gto_ranges["preflop"]["positions"][player.position]["rfi"]
                    if hand in ranges["raise"]:
                        # 強牌可以跟注或3-bet
                        if random.random() < 0.3:  # 30% 3-bet
                            for action, min_amt, max_amt in valid_actions:
                                if action == Action.RAISE:
                                    return Action.RAISE, int(self.current_bet * 2.5)
                        for action, min_amt, max_amt in valid_actions:
                            if action == Action.CALL:
                                return Action.CALL, min_amt
                return Action.FOLD, 0
        
        # Postflop簡化策略
        else:
            # 沒有下注時
            if self.current_bet == 0:
                if random.random() < 0.3:  # 30%下注
                    for action, min_amt, max_amt in valid_actions:
                        if action == Action.BET:
                            bet_size = int(self.pot * 0.5)
                            return Action.BET, min(max(bet_size, min_amt), max_amt)
                return Action.CHECK, 0
            # 面對下注
            else:
                if random.random() < 0.7:  # 70%跟注
                    for action, min_amt, max_amt in valid_actions:
                        if action == Action.CALL:
                            return Action.CALL, min_amt
                return Action.FOLD, 0
    
    def should_continue_hand(self) -> bool:
        """判斷是否應該繼續這手牌"""
        active_players = self.get_active_players()
        return len(active_players) > 1 and self.street != Street.SHOWDOWN
    
    def determine_winner(self):
        """決定贏家（簡化版，只處理最後一人）"""
        active_players = self.get_active_players()
        
        if len(active_players) == 1:
            winner = active_players[0]
            winner.stack += self.pot
            self.action_history.append(f"\n{winner.name} wins ${self.pot}")
        else:
            # 簡化處理：隨機選一個贏家
            winner = random.choice(active_players)
            winner.stack += self.pot
            self.action_history.append(f"\n{winner.name} wins ${self.pot} at showdown")

def main():
    st.set_page_config(page_title="德州撲克 GTO 訓練器", layout="wide")
    st.title("🃏 德州撲克 GTO 訓練器 - 完整版")
    
    # 初始化session state
    if "game" not in st.session_state:
        st.session_state.game = None
        st.session_state.hand_count = 0
        st.session_state.player_decisions = []
        st.session_state.waiting_for_action = False
    
    # 側邊欄設定
    with st.sidebar:
        st.header("🎮 遊戲設定")
        starting_stack = st.slider("起始籌碼", 1000, 10000, 5000, step=500)
        small_blind = st.slider("小盲", 25, 250, 50, step=25)
        big_blind = small_blind * 2
        
        st.divider()
        
        if st.button("🎯 開始新局", type="primary", use_container_width=True):
            # 確保真正隨機化
            random.seed(int(time.time() * 1000) % 2**32)
            
            game = TexasHoldemGame(starting_stack=starting_stack, 
                                 small_blind=small_blind, 
                                 big_blind=big_blind)
            human_position = random.randint(0, 5)
            game.initialize_players(human_seat=human_position)
            game.start_new_hand()
            
            st.session_state.game = game
            st.session_state.hand_count += 1
            st.session_state.waiting_for_action = False
            st.session_state.player_decisions = []
            
            # 顯示位置資訊
            human_player = next(p for p in game.players if p.is_human)
            st.success(f"🎲 新局開始！你的位置：{human_player.position}")
            st.rerun()
    
    # 主遊戲區
    if st.session_state.game:
        game = st.session_state.game
        
        # 遊戲資訊
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("底池", f"${game.pot}")
        with col2:
            st.metric("街道", game.street.value.upper())
        with col3:
            st.metric("當前下注", f"${game.current_bet}")
        with col4:
            st.metric("手牌數", st.session_state.hand_count)
        
        # 公共牌
        if game.community_cards:
            st.markdown("### 🎴 公共牌")
            st.markdown(f"## {' '.join(str(c) for c in game.community_cards)}")
        
        # 玩家資訊
        human_player = next(p for p in game.players if p.is_human)
        st.markdown("---")
        st.markdown(f"### 👤 你的資訊")
        st.markdown(f"**位置:** {human_player.position} | **手牌:** {' '.join(str(c) for c in human_player.hole_cards)} | **籌碼:** ${human_player.stack}")
        
        # 行動歷史
        with st.expander("📝 行動歷史", expanded=True):
            for action in game.action_history:
                st.text(action)
        
        # 遊戲邏輯
        if game.should_continue_hand():
            # 檢查是否該進入下一街
            if game.is_betting_round_complete():
                game.move_to_next_street()
                st.rerun()
            
            # 當前玩家
            current_player = game.players[game.current_player_index]
            st.markdown(f"### 🎮 現在輪到: {current_player.name} ({current_player.position})")
            
            # 電腦玩家自動行動
            if not current_player.is_human:
                # 檢查玩家是否已經fold或all-in
                if current_player.is_folded or current_player.is_all_in:
                    next_idx = game.get_next_player_index()
                    if next_idx >= 0:
                        game.current_player_index = next_idx
                    st.rerun()
                
                with st.spinner(f"{current_player.name} 思考中..."):
                    time.sleep(0.5)
                    action, amount = game.get_gto_action(current_player)
                    game.process_action(game.current_player_index, action, amount)
                    
                    # 檢查遊戲狀態
                    active_players = game.get_active_players()
                    if len(active_players) <= 1:
                        # 遊戲結束
                        st.rerun()
                    elif game.is_betting_round_complete():
                        # 下注輪結束，進入下一街
                        game.move_to_next_street()
                        st.rerun()
                    else:
                        # 移到下一個玩家
                        next_idx = game.get_next_player_index()
                        if next_idx >= 0:
                            game.current_player_index = next_idx
                        st.rerun()
            
            # 玩家行動
            else:
                # 確保當前玩家是人類且未fold
                if not current_player.is_human or current_player.is_folded:
                    # 移到下一個玩家
                    next_idx = game.get_next_player_index()
                    if next_idx >= 0:
                        game.current_player_index = next_idx
                    st.rerun()
                
                valid_actions = game.get_valid_actions(current_player)
                
                # 獲取GTO建議
                gto_action, gto_amount = game.get_gto_action(current_player)
                gto_suggestion = f"GTO建議: {gto_action.value.upper()}"
                if gto_amount > 0:
                    gto_suggestion += f" ${int(gto_amount)}"
                
                st.info(f"💡 {gto_suggestion}")
                
                if not st.session_state.waiting_for_action:
                    col1, col2, col3 = st.columns(3)
                    
                    # Fold
                    with col1:
                        fold_text = "❌ FOLD"
                        if gto_action == Action.FOLD:
                            fold_text += " (GTO 👍)"
                        if st.button(fold_text, type="secondary", use_container_width=True):
                            st.session_state.player_decisions.append({
                                "street": game.street.value,
                                "position": current_player.position,
                                "hand": game.get_hand_string(current_player.hole_cards),
                                "action": "fold",
                                "pot": game.pot,
                                "current_bet": game.current_bet
                            })
                            
                            # 處理fold動作
                            game.process_action(game.current_player_index, Action.FOLD)
                            
                            # 檢查是否還有需要行動的玩家
                            active_players = game.get_active_players()
                            if len(active_players) <= 1:
                                # 遊戲結束，所有人都fold了
                                st.rerun()
                            else:
                                # 移到下一個玩家
                                next_idx = game.get_next_player_index()
                                if next_idx >= 0:
                                    game.current_player_index = next_idx
                                else:
                                    # 下注輪結束，進入下一街
                                    if game.is_betting_round_complete():
                                        game.move_to_next_street()
                                st.rerun()
                    
                    # Check/Call
                    with col2:
                        for action, min_amt, max_amt in valid_actions:
                            if action == Action.CHECK:
                                check_text = "✅ CHECK"
                                if gto_action == Action.CHECK:
                                    check_text += " (GTO 👍)"
                                if st.button(check_text, type="secondary", use_container_width=True):
                                    st.session_state.player_decisions.append({
                                        "street": game.street.value,
                                        "position": current_player.position,
                                        "hand": game.get_hand_string(current_player.hole_cards),
                                        "action": "check",
                                        "pot": game.pot,
                                        "current_bet": game.current_bet
                                    })
                                    
                                    game.process_action(game.current_player_index, Action.CHECK)
                                    next_idx = game.get_next_player_index()
                                    if next_idx >= 0:
                                        game.current_player_index = next_idx
                                    elif game.is_betting_round_complete():
                                        game.move_to_next_street()
                                    st.rerun()
                                break
                            elif action == Action.CALL:
                                call_text = f"📞 CALL ${min_amt}"
                                if gto_action == Action.CALL:
                                    call_text += " (GTO 👍)"
                                if st.button(call_text, type="secondary", use_container_width=True):
                                    st.session_state.player_decisions.append({
                                        "street": game.street.value,
                                        "position": current_player.position,
                                        "hand": game.get_hand_string(current_player.hole_cards),
                                        "action": "call",
                                        "amount": min_amt,
                                        "pot": game.pot,
                                        "current_bet": game.current_bet
                                    })
                                    
                                    game.process_action(game.current_player_index, Action.CALL)
                                    next_idx = game.get_next_player_index()
                                    if next_idx >= 0:
                                        game.current_player_index = next_idx
                                    elif game.is_betting_round_complete():
                                        game.move_to_next_street()
                                    st.rerun()
                                break
                    
                    # Bet/Raise
                    with col3:
                        for action, min_amt, max_amt in valid_actions:
                            if action in [Action.BET, Action.RAISE]:
                                action_text = "💰 BET" if action == Action.BET else "🚀 RAISE"
                                
                                # 下注選項
                                if max_amt > min_amt:
                                    options = []
                                    if action == Action.BET:
                                        options = [
                                            ("1/3 Pot", int(game.pot * 0.33)),
                                            ("1/2 Pot", int(game.pot * 0.5)),
                                            ("2/3 Pot", int(game.pot * 0.67)),
                                            ("Pot", game.pot),
                                            ("All-in", max_amt)
                                        ]
                                    else:  # RAISE
                                        options = [
                                            ("Min Raise", min_amt),
                                            ("2.5x", int(game.current_bet * 2.5)),
                                            ("3x", int(game.current_bet * 3)),
                                            ("Pot", min(game.current_bet * 2 + game.pot, max_amt)),
                                            ("All-in", max_amt)
                                        ]
                                    
                                    # 過濾有效選項
                                    valid_options = [(name, amt) for name, amt in options 
                                                   if min_amt <= amt <= max_amt]
                                    
                                    if valid_options:
                                        selected = st.selectbox(
                                            "選擇金額",
                                            options=[amt for _, amt in valid_options],
                                            format_func=lambda x: f"${x} ({[n for n,a in valid_options if a==x][0]})"
                                        )
                                        
                                        # 檢查是否符合GTO建議
                                        button_text = action_text
                                        if ((action == Action.BET and gto_action == Action.BET) or 
                                            (action == Action.RAISE and gto_action == Action.RAISE)):
                                            # 檢查金額是否接近GTO建議
                                            if abs(selected - gto_amount) / max(selected, gto_amount, 1) < 0.2:  # 20%誤差範圍
                                                button_text += " (GTO 👍)"
                                        
                                        if st.button(button_text, type="primary", use_container_width=True):
                                            st.session_state.player_decisions.append({
                                                "street": game.street.value,
                                                "position": current_player.position,
                                                "hand": game.get_hand_string(current_player.hole_cards),
                                                "action": action.value,
                                                "amount": selected,
                                                "pot": game.pot,
                                                "current_bet": game.current_bet
                                            })
                                            
                                            game.process_action(game.current_player_index, action, selected)
                                            next_idx = game.get_next_player_index()
                                            if next_idx >= 0:
                                                game.current_player_index = next_idx
                                            st.rerun()
                                break
        
        # 手牌結束
        else:
            game.determine_winner()
            st.markdown("### 🏁 本手牌結束")
            
            # GTO分析報告
            if st.session_state.player_decisions:
                st.divider()
                st.markdown("### 📊 GTO 分析報告")
                
                correct_decisions = 0
                total_decisions = 0
                
                for decision in st.session_state.player_decisions:
                    if decision["street"] == "preflop":
                        total_decisions += 1
                        
                        # 簡化分析：只分析preflop
                        hand = decision["hand"]
                        position = decision["position"]
                        action = decision["action"]
                        
                        # 檢查GTO建議
                        is_correct = False
                        suggestion = ""
                        
                        if position in st.session_state.game.gto_ranges["preflop"]["positions"]:
                            ranges = st.session_state.game.gto_ranges["preflop"]["positions"][position]["rfi"]
                            
                            if decision["current_bet"] <= st.session_state.game.big_blind:
                                # RFI情況
                                if hand in ranges["raise"]:
                                    is_correct = (action in ["bet", "raise"])
                                    suggestion = f"{hand} 在 {position} 應該加注"
                                else:
                                    is_correct = (action == "fold")
                                    suggestion = f"{hand} 在 {position} 應該棄牌"
                            else:
                                # 面對加注
                                if hand in ranges["raise"]:
                                    is_correct = (action in ["call", "raise"])
                                    suggestion = f"{hand} 在 {position} 面對加注可以跟注或再加注"
                                else:
                                    is_correct = (action == "fold")
                                    suggestion = f"{hand} 在 {position} 面對加注應該棄牌"
                        
                        if is_correct:
                            correct_decisions += 1
                            st.success(f"✅ Preflop {position}: {action} - 正確！{suggestion}")
                        else:
                            st.error(f"❌ Preflop {position}: {action} - 錯誤！{suggestion}")
                
                if total_decisions > 0:
                    accuracy = (correct_decisions / total_decisions) * 100
                    st.metric("Preflop 準確率", f"{accuracy:.1f}%")
            
            # 重新開始按鈕
            if st.button("🎲 下一手牌", type="primary", use_container_width=True):
                # 重新隨機化位置
                random.seed(int(time.time() * 1000) % 2**32)
                
                # 重建遊戲
                new_game = TexasHoldemGame(starting_stack=game.starting_stack,
                                         small_blind=game.small_blind,
                                         big_blind=game.big_blind)
                human_position = random.randint(0, 5)
                new_game.initialize_players(human_seat=human_position)
                new_game.start_new_hand()
                
                st.session_state.game = new_game
                st.session_state.hand_count += 1
                st.session_state.player_decisions = []
                
                # 顯示新位置
                human_player = next(p for p in new_game.players if p.is_human)
                st.success(f"🎆 新手牌！你的新位置：{human_player.position}")
                st.rerun()
    
    else:
        st.info("👈 請在左側設定遊戲參數，然後點擊「開始新局」")

if __name__ == "__main__":
    main()