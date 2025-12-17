import streamlit as st
import chess
import chess.variant
import chess.svg
import random

st.set_page_config(page_title="Atomic Dojo", page_icon="⚛️")

# --- MANTIK ---
def generate_puzzle():
    # (Buradaki kod aynı, yer kaplamasın diye kısalttım)
    # ...Puzzle üretme fonksiyonun...
    attempts = 0
    while attempts < 1000:
        board = chess.variant.AtomicBoard()
        moves_count = random.randint(10, 50)
        try:
            for _ in range(moves_count):
                if board.is_game_over(): break
                lm = list(board.legal_moves)
                if not lm: break
                board.push(random.choice(lm))
            if board.is_game_over(): 
                attempts += 1
                continue
            winning_moves = []
            for move in board.legal_moves:
                board.push(move)
                if board.is_checkmate():
                    winning_moves.append(move.uci())
                board.pop()
            if winning_moves:
                return board.fen(), winning_moves
        except: pass
        attempts += 1
    return None, None

# State
if 'fen' not in st.session_state:
    st.session_state.fen = None
    st.session_state.solutions = []
    
# Puzzle Yoksa Yükle
if not st.session_state.fen:
    fen, sols = generate_puzzle()
    if fen:
        st.session_state.fen = fen
        st.session_state.solutions = sols
        st.rerun()

# --- ARAYÜZ (KÜTÜPHANESİZ) ---
board = chess.variant.AtomicBoard(st.session_state.fen)

st.title("Atomic Mat")
st.image(chess.svg.board(board=board, size=350), output_format="svg")

# Hamle Seçici (Yazmak YOK, Seçmek VAR)
# Yasal hamleleri listele
legal_moves = [m.uci() for m in board.legal_moves]
selected_move = st.selectbox("Hamleni Seç:", ["Seçiniz..."] + sorted(legal_moves))

if selected_move != "Seçiniz...":
    if selected_move in st.session_state.solutions:
        st.success(f"✅ TEBRİKLER! {selected_move} mat etti!")
        if st.button("Sonraki Puzzle"):
            st.session_state.fen = None
            st.rerun()
    else:
        st.error("Bu hamle mat etmiyor.")
