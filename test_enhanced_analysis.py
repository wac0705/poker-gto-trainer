"""
Test the enhanced detailed analysis functionality
"""

from texas_holdem_consistent import GTOAnalyzer
import json

def test_enhanced_analysis():
    print("=== Testing Enhanced Analysis ===")
    
    # Load GTO ranges
    with open('gto_ranges_clean.json', 'r', encoding='utf-8') as f:
        gto_ranges = json.load(f)
    
    analyzer = GTOAnalyzer(gto_ranges)
    
    # Test enhanced analysis for a wrong decision
    print("\nTest: AA in UTG folds (wrong decision)")
    
    is_correct, suggestion, detailed = analyzer.analyze_decision(
        hand="AA", 
        position="UTG", 
        action="fold",
        amount=0, 
        current_bet=100,
        big_blind=100
    )
    
    print(f"Decision correct: {is_correct}")
    print("\n=== DETAILED ANALYSIS ===")
    print(detailed)
    print("\n" + "="*60)
    
    # Test enhanced analysis for a correct decision
    print("\nTest: AA in UTG raises (correct decision)")
    
    is_correct2, suggestion2, detailed2 = analyzer.analyze_decision(
        hand="AA", 
        position="UTG", 
        action="raise",
        amount=250, 
        current_bet=100,
        big_blind=100
    )
    
    print(f"Decision correct: {is_correct2}")
    print("\n=== DETAILED ANALYSIS ===")
    print(detailed2)
    print("\n" + "="*60)
    
    # Test BB facing raise scenario
    print("\nTest: QQ in BB vs raise (correct call)")
    
    is_correct3, suggestion3, detailed3 = analyzer.analyze_decision(
        hand="QQ", 
        position="BB", 
        action="call",
        amount=250, 
        current_bet=250,
        big_blind=100
    )
    
    print(f"Decision correct: {is_correct3}")
    print("\n=== DETAILED ANALYSIS ===")
    print(detailed3)

if __name__ == "__main__":
    test_enhanced_analysis()