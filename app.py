import streamlit as st
import chess
import chess.variant
import chess.svg
import random
import base64
import time
from streamlit_image_coordinates import streamlit_image_coordinates

# --- AYARLAR ---
st.set_page_config(page_title="Atomic Pro", page_icon="🧩", layout="centered")

# CSS: Görünüm iyileştirme
st.markdown("""
    <style>
    .stButton>button {width: 100%; height: 3.5em; font-weight: bold; font-size: 18px; border-radius: 12px;}
    h1 {text-align: center; margin-bottom: 0px;}
    div[data-testid="stImage"] {display: block; margin-left: auto; margin-right: auto;}
    </style>
    """, unsafe_allow_html=True)

st.title("🧩 Atomic Satranç")

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

# --- STATE YÖNETİMİ ---
if 'fen' not in st.session_state:
    st.session_state.fen = None
if 'selected_square' not in st.session_state:
    st.session_state.selected_square = None
if 'show_solution' not in st.session_state:
    st.session_state.show_solution = False

# --- PUZZLE KONTROLÜ ---
if not st.session_state.fen:
    # Başlangıç ekranı
    st.info("Hazır olduğunda başla.")
    if st.button("🚀 BAŞLA (PUZZLE BUL)"):
        with st.spinner("Mat aranıyor..."):
            fen, sols = generate_fast_puzzle()
            if fen:
                st.session_state.fen = fen
                st.session_state.solutions = sols
                st.session_state.show_solution = False
                st.session_state.selected_square = None
                st.rerun()
            else:
                st.error("Bulunamadı, tekrar dene.")
else:
    # --- OYUN EKRANI ---
    board = chess.variant.AtomicBoard(st.session_state.fen)
    is_white = (board.turn == chess.WHITE)
    
    # Bilgilendirme
    if st.session_state.show_solution:
        st.warning("Çözüm tahtada ok ile gösterildi.")
    else:
        turn_str = "BEYAZ" if is_white else "SİYAH"
        st.success(f"Sıra: {turn_str} | 1 Hamlede Mat Et!")

    # --- SVG OLUŞTURMA ---
    # Seçili kareyi boyama
    fill = {}
    if st.session_state.selected_square:
        sq = chess.parse_square(st.session_state.selected_square)
        fill[sq] = "#ffe066cc" # Sarı vurgu

    # Çözüm okları (Eğer 'Cevabı Göster' dendi ise)
    arrows = []
    if st.session_state.show_solution:
        for sol in st.session_state.solutions:
            move = chess.Move.from_uci(sol)
            # Yeşil ok ekle
            arrows.append(chess.svg.Arrow(move.from_square, move.to_square, color="#00aa00cc"))

    # SVG verisini oluştur
    svg = chess.svg.board(
        board, 
        size=350, 
        flipped=not is_white,
        fill=fill,
        arrows=arrows,
        coordinates=False
    )
    
    # Base64 dönüşümü (Dosya kaydetme sorununu çözer)
    b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
    image_source = f"data:image/svg+xml;base64,{b64}"

    # Dokunmatik Tahta
    # 'key' parametresini dinamik yapıyoruz ki tahta donmasın, her hamlede yenilensin
    coords = streamlit_image_coordinates(
        image_source,
        width=350,
        key=f"board_{st.session_state.fen}_{st.session_state.selected_square}_{st.session_state.show_solution}"
    )

    # --- TIKLAMA MANTIĞI ---
    if coords:
        # Eğer çözüm gösterildiyse tıklamayı engelle (yeni soruya geçsin)
        if not st.session_state.show_solution:
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
                
            if 0 <= file_idx <= 7 and 0 <= rank_idx <= 7:
                clicked_sq = chess.square_name(chess.square(file_idx, rank_idx))

                # Mantık: Seç -> Oyna
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
                    
                    # Piyon terfi kontrolü
                    p = board.piece_at(chess.parse_square(src))
                    if p and p.piece_type == chess.PAWN:
                        if (src[1]=='7' and tgt[1]=='8') or (src[1]=='2' and tgt[1]=='1'):
                            move_uci += 'q'

                    if move_uci in st.session_state.solutions:
                        st.balloons()
                        st.toast("🔥 DOĞRU! YENİSİ GELİYOR...", icon="✅")
                        time.sleep(1.0)
                        # Sıfırla ve yeni puzzle
                        st.session_state.fen = None
                        st.session_state.selected_square = None
                        st.session_state.show_solution = False
                        st.rerun()
                    else:
                        st.toast("Yanlış Hamle", icon="❌")
                        st.session_state.selected_square = None
                        st.rerun()

    # --- BUTONLAR ---
    col1, col2 = st.columns(2)
    
    with col1:
        # Eğer zaten çözüm açıksa "Sıradaki" butonu olsun
        if st.session_state.show_solution:
            if st.button("Sonraki Soru ⏩"):
                st.session_state.fen = None
                st.session_state.show_solution = False
                st.rerun()
        else:
            if st.button("👁️ Cevabı Göster"):
                st.session_state.show_solution = True
                st.rerun()
                
    with col2:
        if st.button("Yenile / Pas Geç"):
            st.session_state.fen = None
            st.session_state.show_solution = False
            st.rerun()
        
