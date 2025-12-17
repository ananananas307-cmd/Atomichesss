import streamlit as st
import chess
import chess.variant
import chess.svg
import random
import time
from streamlit_image_coordinates import streamlit_image_coordinates

# --- AYARLAR ---
st.set_page_config(page_title="Atomic Hızlı", page_icon="⚡", layout="centered")

st.markdown("""
    <style>
    .stButton>button {width: 100%; height: 3em; font-weight: bold; font-size: 20px;}
    h1 {text-align: center; margin-bottom: 0px;}
    div[data-testid="stImage"] {display: block; margin-left: auto; margin-right: auto;}
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Atomic Dokunmatik")

# --- MANTIK ---
def generate_fast_puzzle():
    for _ in range(100):
        board = chess.variant.AtomicBoard()
        moves_count = random.randint(5, 30)
        try:
            for _ in range(moves_count):
                if board.is_game_over(): break
                lm = list(board.legal_moves)
                if not lm: break
                board.push(random.choice(lm))
            
            if board.is_game_over(): continue

            solutions = []
            for move in board.legal_moves:
                board.push(move)
                if board.is_checkmate():
                    solutions.append(move.uci())
                board.pop()
            
            if solutions:
                return board.fen(), solutions
        except:
            pass
    return None, None

if 'fen' not in st.session_state:
    st.session_state.fen = None
if 'selected_square' not in st.session_state:
    st.session_state.selected_square = None

# --- ANA EKRAN ---
if not st.session_state.fen:
    st.info("Hazır olduğunda butona bas.")
    if st.button("🧩 PUZZLE BUL (BAŞLA)"):
        with st.spinner("Hızlı bir mat aranıyor..."):
            fen, sols = generate_fast_puzzle()
            if fen:
                st.session_state.fen = fen
                st.session_state.solutions = sols
                st.rerun()
            else:
                st.error("Uygun pozisyon denk gelmedi, tekrar bas.")
else:
    # PUZZLE GÖSTERİMİ
    board = chess.variant.AtomicBoard(st.session_state.fen)
    is_white = (board.turn == chess.WHITE)
    
    turn_str = "BEYAZ" if is_white else "SİYAH"
    st.success(f"Sıra: {turn_str} | 1 Hamlede Mat Et!")

    # SVG Hazırla
    fill = {}
    if st.session_state.selected_square:
        sq = chess.parse_square(st.session_state.selected_square)
        fill[sq] = "#ffe066cc"

    svg_content = chess.svg.board(
        board, 
        size=350, 
        flipped=not is_white,
        fill=fill,
        coordinates=False
    )
    
    # --- DÜZELTME BURADA: Resmi dosyaya yazıyoruz ---
    image_path = "current_board.svg"
    with open(image_path, "w") as f:
        f.write(svg_content)

    # Dokunmatik Tahta (Artık dosyadan okuyor)
    coords = streamlit_image_coordinates(
        image_path,
        width=350,
        key="board_tap"
    )

    if coords:
        x, y = coords['x'], coords['y']
        sq_size = 350 / 8
        col = int(x // sq_size)
        row = int(y // sq_size)
        
        if is_white:
            file_idx = col
            rank_idx = 7 - row
        else:
            file_idx = 7 - col
            rank_idx = row
            
        # Sınır kontrolü (Bazen kenara tıklanınca hata olmasın)
        if 0 <= file_idx <= 7 and 0 <= rank_idx <= 7:
            clicked_sq = chess.square_name(chess.square(file_idx, rank_idx))

            if st.session_state.selected_square == clicked_sq:
                st.session_state.selected_square = None
                st.rerun()
            
            elif st.session_state.selected_square is None:
                p = board.piece_at(chess.parse_square(clicked_sq))
                if p and p.color == board.turn:
                    st.session_state.selected_square = clicked_sq
                    st.rerun()
            else:
                src = st.session_state.selected_square
                tgt = clicked_sq
                move_uci = f"{src}{tgt}"
                
                p = board.piece_at(chess.parse_square(src))
                if p and p.piece_type == chess.PAWN:
                    if (src[1]=='7' and tgt[1]=='8') or (src[1]=='2' and tgt[1]=='1'):
                        move_uci += 'q'

                if move_uci in st.session_state.solutions:
                    st.balloons()
                    st.toast("🔥 DOĞRU! YENİSİ GELİYOR...", icon="✅")
                    time.sleep(1.0)
                    st.session_state.fen = None
                    st.session_state.selected_square = None
                    st.rerun()
                else:
                    st.toast("Yanlış Hamle", icon="❌")
                    st.session_state.selected_square = None
                    st.rerun()

    if st.button("Bu soruyu geç"):
        st.session_state.fen = None
        st.session_state.selected_square = None
        st.rerun()
