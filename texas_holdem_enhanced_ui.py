"""
德州撲克 GTO 訓練器 - 增強版 UI
Enhanced UI version with better visual design
"""

import streamlit as st
import random
import json
import time
from enum import Enum
from typing import List, Optional, Dict, Tuple
import sys
import io

# 設定頁面配置
st.set_page_config(
    page_title="德州撲克 GTO 訓練器",
    page_icon="🃏",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定義 CSS
st.markdown("""
<style>
    /* 主要背景 */
    .stApp {
        background: linear-gradient(135deg, #0f3d0f 0%, #1a5c1a 100%);
    }
    
    /* 撲克桌樣式 */
    .poker-table {
        background: radial-gradient(ellipse at center, #2d5a2d 0%, #1e3d1e 70%);
        border: 8px solid #8B4513;
        border-radius: 150px;
        padding: 40px;
        margin: 20px auto;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    
    /* 玩家資訊卡片 */
    .player-card {
        background: rgba(0,0,0,0.7);
        border: 2px solid #FFD700;
        border-radius: 10px;
        padding: 15px;
        margin: 10px;
        color: white;
        text-align: center;
    }
    
    /* 手牌樣式 */
    .hole-card {
        display: inline-block;
        width: 60px;
        height: 80px;
        margin: 0 5px;
        background: white;
        border: 2px solid #333;
        border-radius: 5px;
        text-align: center;
        line-height: 80px;
        font-size: 24px;
        font-weight: bold;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    }
    
    .hole-card.red {
        color: #FF0000;
    }
    
    .hole-card.black {
        color: #000000;
    }
    
    /* 公共牌樣式 */
    .community-card {
        display: inline-block;
        width: 70px;
        height: 90px;
        margin: 0 5px;
        background: white;
        border: 2px solid #333;
        border-radius: 5px;
        text-align: center;
        line-height: 90px;
        font-size: 28px;
        font-weight: bold;
        box-shadow: 0 3px 8px rgba(0,0,0,0.4);
    }
    
    .community-card.red {
        color: #FF0000;
    }
    
    .community-card.black {
        color: #000000;
    }
    
    /* 按鈕樣式 */
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #45a049;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    
    /* 籌碼顯示 */
    .chip-display {
        background: #FFD700;
        color: #000;
        border-radius: 20px;
        padding: 5px 15px;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
    }
    
    /* 動作歷史 */
    .action-history {
        background: rgba(0,0,0,0.5);
        border: 1px solid #444;
        border-radius: 5px;
        padding: 10px;
        color: #FFF;
        font-family: monospace;
        max-height: 200px;
        overflow-y: auto;
    }
    
    /* GTO 建議框 */
    .gto-suggestion {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white;
        margin: 10px 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    
    /* 分析報告 */
    .analysis-report {
        background: rgba(255,255,255,0.95);
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 5px 20px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# 從簡化版本導入所有必要的類和函數
from texas_holdem_simple import *
from hand_evaluator import HandEvaluator, HandRank

def get_card_html(card, size="normal"):
    """生成卡片的 HTML"""
    # Map both letter codes and symbols
    suit_symbols = {
        "s": ("♠", "black"),
        "h": ("♥", "red"),
        "d": ("♦", "red"),
        "c": ("♣", "black"),
        "♠": ("♠", "black"),
        "♥": ("♥", "red"),
        "♦": ("♦", "red"),
        "♣": ("♣", "black")
    }
    
    # Handle Card object - it's a Card class instance from texas_holdem_complete
    if hasattr(card, 'rank') and hasattr(card, 'suit'):
        rank = card.rank
        suit = card.suit
    else:
        # Fallback for dict-like objects
        rank = card.get("rank", "?") if hasattr(card, 'get') else "?"
        suit = card.get("suit", "?") if hasattr(card, 'get') else "?"
    
    # Get symbol and color
    symbol, color = suit_symbols.get(suit, (suit, "black"))  # Use suit directly if not found
    
    # Make sure we have valid values
    if not rank or rank == "?":
        rank = "?"
    if not symbol:
        symbol = "?"
    
    if size == "normal":
        return f'<div class="hole-card {color}">{rank}{symbol}</div>'
    else:
        return f'<div class="community-card {color}">{rank}{symbol}</div>'

def display_poker_table(game):
    """顯示撲克桌"""
    st.markdown('<div class="poker-table">', unsafe_allow_html=True)
    
    # 顯示底池
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f'<h2 style="text-align: center; color: white;">底池: <span class="chip-display">${game.pot}</span></h2>', unsafe_allow_html=True)
        
        # 顯示公共牌
        if game.community_cards and len(game.community_cards) > 0:
            # Create community cards container
            cards_container = '<div style="text-align: center; margin: 20px 0;">'
            
            for card in game.community_cards:
                if hasattr(card, 'rank') and hasattr(card, 'suit'):
                    rank = card.rank
                    suit = card.suit
                    # Determine color based on suit
                    if suit in ['♥', '♦', 'h', 'd']:
                        color = '#FF0000'
                    else:
                        color = '#000000'
                    # Create card HTML as a single line
                    cards_container += f'<div style="display: inline-block; width: 70px; height: 90px; margin: 0 5px; background: white; border: 2px solid #333; border-radius: 5px; text-align: center; line-height: 90px; font-size: 28px; font-weight: bold; box-shadow: 0 3px 8px rgba(0,0,0,0.4); color: {color};">{rank}{suit}</div>'
                else:
                    cards_container += get_card_html(card, "large")
            
            cards_container += '</div>'
            st.markdown(cards_container, unsafe_allow_html=True)
        else:
            # 顯示空的牌位或等待訊息
            if game.street == Street.PREFLOP:
                st.markdown('<div style="text-align: center; margin: 20px 0; color: white;">等待翻牌...</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="text-align: center; margin: 20px 0; color: white;">沒有公共牌</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_player_info(player, game):
    """顯示玩家資訊"""
    if player.is_human:
        st.markdown('<div class="player-card" style="border-color: #FFD700;">', unsafe_allow_html=True)
    else:
        st.markdown('<div class="player-card">', unsafe_allow_html=True)
    
    # 玩家名稱和位置
    st.markdown(f'<h4>{player.name} ({player.position})</h4>', unsafe_allow_html=True)
    
    # 籌碼
    st.markdown(f'<p>籌碼: <span class="chip-display">${player.stack}</span></p>', unsafe_allow_html=True)
    
    # 手牌（只顯示人類玩家的）
    if player.is_human and player.hole_cards:
        cards_html = "".join([get_card_html(card) for card in player.hole_cards])
        st.markdown(f'<div style="text-align: center;">{cards_html}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_gto_suggestion(suggestion):
    """顯示 GTO 建議"""
    st.markdown('<div class="gto-suggestion">', unsafe_allow_html=True)
    
    action_emoji = {
        "fold": "❌",
        "check": "✅",
        "call": "📞",
        "bet": "💰",
        "raise": "🚀"
    }
    
    emoji = action_emoji.get(suggestion['action'], "❓")
    
    st.markdown(f"""
    <h3 style="color: white; margin: 0;">{emoji} GTO 建議</h3>
    <p style="font-size: 20px; margin: 10px 0;">
        <strong>{suggestion['action'].upper()}</strong>
        {f"${suggestion['amount']}" if suggestion['amount'] > 0 else ""}
    </p>
    <p style="margin: 0;">{suggestion['explanation']}</p>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_action_history(game):
    """顯示行動歷史"""
    if game.action_history:
        st.markdown('<div class="action-history">', unsafe_allow_html=True)
        for action in game.action_history[-10:]:  # 只顯示最近10個行動
            st.text(action)
        st.markdown('</div>', unsafe_allow_html=True)

def display_analysis_report(decisions, gto_analyzer, game=None):
    """顯示增強版分析報告"""
    st.markdown('<div class="analysis-report">', unsafe_allow_html=True)
    
    st.markdown("## 📊 手牌分析報告")
    
    total = len(decisions)
    correct = sum(1 for d in decisions if d['is_correct'])
    accuracy = (correct / total * 100) if total > 0 else 0
    
    # 總體表現
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("總決策數", total)
    with col2:
        st.metric("正確決策", correct)
    with col3:
        st.metric("準確率", f"{accuracy:.1f}%")
    
    # 評級
    if accuracy >= 90:
        grade_color = "#4CAF50"
        grade_text = "🏆 卓越表現！"
    elif accuracy >= 75:
        grade_color = "#8BC34A"
        grade_text = "👍 表現良好！"
    elif accuracy >= 60:
        grade_color = "#FFC107"
        grade_text = "💪 繼續努力！"
    else:
        grade_color = "#F44336"
        grade_text = "📚 需要更多練習！"
    
    st.markdown(f'<h3 style="color: {grade_color}; text-align: center;">{grade_text}</h3>', unsafe_allow_html=True)
    
    # 詳細分析
    st.markdown("### 🎯 決策細節")
    
    for i, decision in enumerate(decisions):
        with st.expander(f"決策 {i+1}: {decision['street'].upper()} - {decision['hand']} @ {decision['position']}"):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.write(f"**你的行動:** {decision['action'].upper()}")
                if decision['amount'] > 0:
                    st.write(f"**下注金額:** ${decision['amount']}")
                
                # 顯示手牌強度（如果有公牌的話）
                if game and game.community_cards and len(game.community_cards) >= 3:
                    human_player = next((p for p in game.players if p.is_human), None)
                    if human_player and human_player.hole_cards:
                        all_cards = human_player.hole_cards + game.community_cards
                        hand_rank, _ = HandEvaluator.evaluate_hand(all_cards)
                        hand_name = HandEvaluator.get_hand_name(hand_rank)
                        st.write(f"**手牌強度:** {hand_name}")
                
                if decision['is_correct']:
                    st.success("✅ 正確決策")
                else:
                    st.error("❌ 可以改進")
            
            with col2:
                st.info(decision['suggestion'])
                
                if 'detailed' in decision and decision['detailed']:
                    st.markdown("**詳細分析:**")
                    st.markdown(decision['detailed'])
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    # 標題
    st.markdown("""
    <h1 style='text-align: center; color: #FFD700; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);'>
        🃏 德州撲克 GTO 訓練器 🃏
    </h1>
    <p style='text-align: center; color: #FFF; font-size: 18px;'>
        學習最優遊戲理論策略，成為更好的撲克玩家
    </p>
    """, unsafe_allow_html=True)
    
    # 側邊欄設定
    with st.sidebar:
        st.header("⚙️ 遊戲設定")
        
        starting_stack = st.slider("起始籌碼", 1000, 10000, 5000, step=500)
        small_blind = st.slider("小盲", 25, 250, 50, step=25)
        big_blind = small_blind * 2
        
        st.divider()
        
        # 統計資訊
        if "hand_count" in st.session_state:
            st.metric("已玩手數", st.session_state.hand_count)
        
        if st.button("🆕 開始新局", type="primary", use_container_width=True):
            # 初始化遊戲邏輯（與簡化版相同）
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
            st.session_state.hand_count = st.session_state.get('hand_count', 0) + 1
            st.session_state.player_decisions = []
            st.session_state.gto_analyzer = gto_analyzer
            st.session_state.ai_action_count = 0  # 重置AI行動計數器
            
            st.rerun()
    
    # 主遊戲區域
    game = st.session_state.get('game')
    if game:
        # 顯示撲克桌
        display_poker_table(game)
        
        # 顯示所有玩家
        st.markdown("### 👥 玩家")
        cols = st.columns(6)
        for i, player in enumerate(game.players):
            with cols[i]:
                display_player_info(player, game)
        
        # 顯示行動歷史
        with st.expander("📝 行動歷史", expanded=False):
            display_action_history(game)
        
        # 遊戲邏輯
        if game.street == Street.SHOWDOWN or len(game.get_active_players()) == 1:
            # 遊戲結束，顯示結果
            st.markdown("## 🏁 手牌結束")
            
            # 處理結算
            if len(game.get_active_players()) == 1:
                winner = next(p for p in game.players if not p.is_folded)
                st.success(f"🎉 {winner.name} 贏得底池 ${game.pot}")
            else:
                # Multiple players - determine winner using hand evaluator
                st.info(f"🤝 攤牌！底池 ${game.pot}")
                
                # 顯示所有玩家的手牌
                active_players = game.get_active_players()
                winners = HandEvaluator.determine_winner(game.players, game.community_cards)
                
                # 顯示每個玩家的手牌和牌型
                st.markdown("### 🎴 攤牌結果")
                cols = st.columns(len(active_players))
                
                for i, player in enumerate(active_players):
                    with cols[i]:
                        # 顯示玩家手牌
                        cards_html = "".join([get_card_html(card) for card in player.hole_cards])
                        st.markdown(f"**{player.name}**", unsafe_allow_html=True)
                        st.markdown(f'<div style="text-align: center;">{cards_html}</div>', unsafe_allow_html=True)
                        
                        # 評估手牌
                        all_cards = player.hole_cards + game.community_cards
                        hand_rank, values = HandEvaluator.evaluate_hand(all_cards)
                        hand_name = HandEvaluator.get_hand_name(hand_rank)
                        
                        if player in winners:
                            st.success(f"🏆 {hand_name}")
                        else:
                            st.info(f"{hand_name}")
                
                # 分配底池
                pot_share = game.pot // len(winners)
                if len(winners) == 1:
                    st.success(f"🎉 {winners[0].name} 贏得底池 ${game.pot}！")
                else:
                    winner_names = ", ".join([w.name for w in winners])
                    st.success(f"🤝 平手！{winner_names} 各獲得 ${pot_share}")
            
            # 顯示分析報告
            if st.session_state.get('player_decisions'):
                display_analysis_report(
                    st.session_state.player_decisions,
                    st.session_state.gto_analyzer,
                    game
                )
            
            # 下一手按鈕
            if st.button("🎲 下一手牌", type="primary", use_container_width=True):
                # 開始新手牌的邏輯...
                new_game = TexasHoldemGame(
                    starting_stack=game.starting_stack,
                    small_blind=game.small_blind,
                    big_blind=game.big_blind
                )
                human_position = random.randint(0, 5)
                new_game.initialize_players(human_seat=human_position)
                new_game.start_new_hand()
                
                st.session_state.game = new_game
                st.session_state.hand_count += 1
                st.session_state.player_decisions = []
                st.session_state.ai_action_count = 0  # 重置AI行動計數器
                
                st.rerun()
        
        else:
            # 遊戲進行中
            # 檢查是否所有玩家都all-in或fold（除了一個以外）
            active_non_allin = [p for p in game.players if not p.is_folded and not p.is_all_in]
            
            if len(active_non_allin) <= 1:
                # 所有玩家都all-in或fold了，直接跑到攤牌
                while game.street != Street.SHOWDOWN:
                    game.move_to_next_street()
                st.rerun()
            
            current_player_idx = game.get_next_player_index()
            if current_player_idx != -1:
                current_player = game.players[current_player_idx]
                
                if current_player.is_human:
                    # 顯示當前玩家資訊
                    st.markdown(f"### 🎮 輪到你行動了！")
                    
                    # 獲取並顯示 GTO 建議
                    hand_str = game.get_hand_string(current_player.hole_cards)
                    action, amount, explanation = st.session_state.gto_analyzer.get_preflop_recommendation(
                        hand_str, current_player.position, game.current_bet, game.big_blind, game.street, game
                    )
                    
                    suggestion = {
                        'action': action,
                        'amount': amount,
                        'explanation': explanation
                    }
                    
                    display_gto_suggestion(suggestion)
                    
                    # 行動按鈕
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("❌ FOLD 棄牌", use_container_width=True):
                            # 處理棄牌邏輯...
                            is_correct, suggestion_text, detailed = st.session_state.gto_analyzer.analyze_decision(
                                hand_str, current_player.position, "fold", 0, game.current_bet, game.big_blind, game.street, game
                            )
                            
                            st.session_state.player_decisions.append({
                                'street': game.street.name,
                                'hand': hand_str,
                                'position': current_player.position,
                                'action': 'fold',
                                'amount': 0,
                                'is_correct': is_correct,
                                'suggestion': suggestion_text,
                                'detailed': detailed
                            })
                            
                            game.process_action(current_player_idx, Action.FOLD, 0)
                            
                            # Check if only one player remains
                            if len(game.get_active_players()) == 1:
                                # Hand ends immediately
                                st.rerun()
                            else:
                                # Check if we should move to next street or next player
                                next_idx = game.get_next_player_index()
                                if next_idx != -1:
                                    game.current_player_index = next_idx
                                elif game.is_betting_round_complete():
                                    game.move_to_next_street()
                            
                            st.rerun()
                    
                    with col2:
                        if game.current_bet == 0 or (current_player.position == "BB" and game.current_bet == game.big_blind):
                            if st.button("✅ CHECK 過牌", use_container_width=True):
                                # 處理過牌邏輯...
                                is_correct, suggestion_text, detailed = st.session_state.gto_analyzer.analyze_decision(
                                    hand_str, current_player.position, "check", 0, game.current_bet, game.big_blind, game.street, game
                                )
                                
                                st.session_state.player_decisions.append({
                                    'street': game.street.name,
                                    'hand': hand_str,
                                    'position': current_player.position,
                                    'action': 'check',
                                    'amount': 0,
                                    'is_correct': is_correct,
                                    'suggestion': suggestion_text,
                                    'detailed': detailed
                                })
                                
                                game.process_action(current_player_idx, Action.CHECK, 0)
                                
                                # Check if we should move to next street or next player
                                next_idx = game.get_next_player_index()
                                if next_idx != -1:
                                    game.current_player_index = next_idx
                                elif game.is_betting_round_complete():
                                    game.move_to_next_street()
                                
                                st.rerun()
                        else:
                            call_amount = game.current_bet - current_player.current_bet
                            if st.button(f"📞 CALL 跟注 ${call_amount}", use_container_width=True):
                                # 處理跟注邏輯...
                                is_correct, suggestion_text, detailed = st.session_state.gto_analyzer.analyze_decision(
                                    hand_str, current_player.position, "call", game.current_bet, game.current_bet, game.big_blind, game.street, game
                                )
                                
                                st.session_state.player_decisions.append({
                                    'street': game.street.name,
                                    'hand': hand_str,
                                    'position': current_player.position,
                                    'action': 'call',
                                    'amount': game.current_bet,
                                    'is_correct': is_correct,
                                    'suggestion': suggestion_text,
                                    'detailed': detailed
                                })
                                
                                game.process_action(current_player_idx, Action.CALL, game.current_bet)
                                
                                # Check if we should move to next street or next player
                                next_idx = game.get_next_player_index()
                                if next_idx != -1:
                                    game.current_player_index = next_idx
                                elif game.is_betting_round_complete():
                                    game.move_to_next_street()
                                
                                st.rerun()
                    
                    with col3:
                        # 下注/加注選項
                        if game.current_bet == 0:
                            min_bet = int(game.big_blind)
                            default_bet = int(game.big_blind * 2.5)
                        else:
                            min_bet = int(game.current_bet * 2)
                            default_bet = int(game.current_bet * 2.5)
                        
                        # Handle all-in situations - if player doesn't have enough chips for min raise
                        player_total_chips = int(current_player.stack + current_player.current_bet)
                        if min_bet > player_total_chips:
                            # Player can only go all-in
                            min_bet = int(current_player.stack)
                            default_bet = int(current_player.stack)
                        
                        bet_amount = st.number_input(
                            "下注金額",
                            min_value=min_bet,
                            max_value=int(current_player.stack),
                            value=min(default_bet, int(current_player.stack)),
                            step=int(game.big_blind),
                            label_visibility="collapsed"
                        )
                        
                        # Update button text for all-in situations
                        if bet_amount == int(current_player.stack):
                            action_text = "💎 ALL-IN 全下"
                        elif game.current_bet == 0:
                            action_text = "💰 BET 下注"
                        else:
                            action_text = "🚀 RAISE 加注"
                        
                        if st.button(f"{action_text} ${bet_amount}", use_container_width=True):
                            action_type = "bet" if game.current_bet == 0 else "raise"
                            
                            is_correct, suggestion_text, detailed = st.session_state.gto_analyzer.analyze_decision(
                                hand_str, current_player.position, action_type, bet_amount, game.current_bet, game.big_blind, game.street, game
                            )
                            
                            st.session_state.player_decisions.append({
                                'street': game.street.name,
                                'hand': hand_str,
                                'position': current_player.position,
                                'action': action_type,
                                'amount': bet_amount,
                                'is_correct': is_correct,
                                'suggestion': suggestion_text,
                                'detailed': detailed
                            })
                            
                            if game.current_bet == 0:
                                game.process_action(current_player_idx, Action.BET, bet_amount)
                            else:
                                game.process_action(current_player_idx, Action.RAISE, bet_amount)
                            
                            # Check if we should move to next street or next player
                            next_idx = game.get_next_player_index()
                            if next_idx != -1:
                                game.current_player_index = next_idx
                            elif game.is_betting_round_complete():
                                game.move_to_next_street()
                            
                            st.rerun()
                
                else:
                    # AI 玩家自動行動
                    # 防止無窮迴圈：檢查是否應該強制行動
                    if 'ai_action_count' not in st.session_state:
                        st.session_state.ai_action_count = 0
                    
                    st.session_state.ai_action_count += 1
                    
                    # 如果AI行動次數過多，強制結束
                    if st.session_state.ai_action_count > 50:
                        st.error("遊戲出現異常，正在重置...")
                        st.session_state.ai_action_count = 0
                        # 強制進入下一街或結束遊戲
                        if game.street == Street.RIVER:
                            game.street = Street.SHOWDOWN
                        else:
                            game.move_to_next_street()
                        st.rerun()
                    
                    with st.spinner(f"{current_player.name} 思考中..."):
                        time.sleep(0.1)  # 減少延遲
                        
                        # AI 行動邏輯...
                        comp_hand = game.get_hand_string(current_player.hole_cards)
                        comp_action, comp_amount, _ = st.session_state.gto_analyzer.get_preflop_recommendation(
                            comp_hand, current_player.position, game.current_bet, game.big_blind, game.street, game
                        )
                        
                        # 執行行動並重置計數器
                        st.session_state.ai_action_count = 0
                        
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
                        else:
                            # 如果沒有有效行動，默認check或fold
                            if game.current_bet == 0:
                                game.process_action(current_player_idx, Action.CHECK, 0)
                            else:
                                game.process_action(current_player_idx, Action.FOLD, 0)
                        
                        # Check if only one player remains
                        if len(game.get_active_players()) == 1:
                            # Hand ends immediately
                            st.rerun()
                        else:
                            # Check if we should move to next street or next player
                            next_idx = game.get_next_player_index()
                            if next_idx != -1:
                                game.current_player_index = next_idx
                            elif game.is_betting_round_complete():
                                game.move_to_next_street()
                        
                        st.rerun()
    
    else:
        # 歡迎畫面
        st.markdown("""
        <div style='text-align: center; padding: 50px; background: rgba(0,0,0,0.5); border-radius: 10px; margin: 50px auto; max-width: 600px;'>
            <h2 style='color: #FFD700;'>歡迎來到德州撲克 GTO 訓練器！</h2>
            <p style='color: white; font-size: 18px;'>
                學習遊戲理論最優策略，提升你的撲克技巧！
            </p>
            <p style='color: #AAA;'>
                👈 點擊左側的「開始新局」按鈕開始遊戲
            </p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()