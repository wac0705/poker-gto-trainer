"""
Debug Logger - 記錄遊戲執行過程的詳細信息
"""

import datetime
import os

class DebugLogger:
    def __init__(self, log_file="poker_debug.txt"):
        self.log_file = log_file
        self.clear_log()
    
    def clear_log(self):
        """清空日誌文件"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"=== 德州撲克 GTO 訓練器 Debug Log ===\n")
            f.write(f"開始時間: {datetime.datetime.now()}\n")
            f.write("=" * 50 + "\n\n")
    
    def log(self, message, category="INFO"):
        """記錄日誌"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {category}: {message}\n"
        
        print(f"DEBUG: {message}")  # 也在控制台顯示
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def log_game_state(self, game):
        """記錄遊戲狀態"""
        self.log("=" * 30)
        self.log(f"遊戲狀態快照", "GAME_STATE")
        self.log(f"街道: {game.street.value}")
        self.log(f"底池: ${game.pot}")
        self.log(f"當前下注: ${game.current_bet}")
        self.log(f"當前玩家索引: {game.current_player_index}")
        
        current_player = game.players[game.current_player_index]
        self.log(f"當前玩家: {current_player.name} ({current_player.position})")
        self.log(f"是人類: {current_player.is_human}")
        self.log(f"已fold: {current_player.is_folded}")
        self.log(f"已行動: {current_player.has_acted_this_street}")
        
        active_players = [p for p in game.players if not p.is_folded]
        self.log(f"活躍玩家數: {len(active_players)}")
        
        for i, player in enumerate(game.players):
            status = "FOLDED" if player.is_folded else "ACTIVE"
            self.log(f"玩家 {i}: {player.name} ({player.position}) - {status}, 籌碼:${player.stack}, 當前下注:${player.current_bet}")
        
        if game.community_cards:
            cards_str = " ".join([f"{c.rank}{c.suit}" for c in game.community_cards])
            self.log(f"公共牌: {cards_str}")
        
        self.log("=" * 30)
    
    def log_action(self, player, action, amount=0):
        """記錄玩家動作"""
        self.log(f"{player.name} ({player.position}) -> {action.value.upper()} ${amount if amount > 0 else ''}", "ACTION")
    
    def log_decision(self, decision):
        """記錄玩家決策"""
        self.log(f"決策記錄: {decision}", "DECISION")
    
    def log_error(self, error_msg):
        """記錄錯誤"""
        self.log(f"錯誤: {error_msg}", "ERROR")
    
    def log_gto_analysis(self, analysis_result):
        """記錄GTO分析結果"""
        is_correct, suggestion, detailed = analysis_result
        self.log(f"GTO分析 - 正確: {is_correct}", "GTO")
        self.log(f"建議: {suggestion}", "GTO")

# 全局logger實例
debug_logger = DebugLogger()