import streamlit as st
import chess
import chess.variant
import chess.svg
import random
import base64
from streamlit_image_coordinates import streamlit_image_coordinates

# --- AYARLAR ---
st.set_page_config(page_title="Atomic Touch", page_icon="👆", layout="centered")

# CSS: Mobilde daha temiz görünüm
st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem; max-width: 100%;}
    h1 {text-align: center; font-size: 1.5rem;}
    div[data-testid="stImage"] {display: block; margin-left: auto; margin-right: auto;}
    </style>
    """, unsafe_allow_html=True)

st.title("👆 Atomic Dokunmatik")

# --- MANTIK FONKSİYONLARI ---

def generate_puzzle():
    """Rastgele bir Atomic pozisyonu üretir (Mat Fırsatlı)"""
    attempts = 0
    while attempts < 500:
        board = chess.variant.AtomicBoard()
        moves_count = random.randint(15, 50)
        try:
            for _ in range(moves_count):
                if board.is_game_over(): break
                lm = list(board.legal_moves)
                if not lm: break
                board.push(random.choice(lm))
            
            if board.is_game_over(): 
                attempts += 1
                continue

            solutions = []
            for move in board.legal_moves:
                board.push(move)
                if board.is_checkmate():
                    solutions.append(move.uci())
                board.pop()
            
            if solutions:
                return board.fen(), solutions
        except: pass
        attempts += 1
    return None, None

def get_square_from_coords(x, y, board_width, is_white_perspective):
    """Tıklanan pikselden (x,y) satranç karesini (e2) bulur"""
    square_size = board_width / 8
    col = int(x // square_size)
    row = int(y // square_size)
    
    # Eğer siyah oynuyorsa veya tahta tersse koordinatları çevir
    if is_white_perspective:
        # SVG render'da 0,0 sol üsttür (a8)
        # Sütun: 0->a, 1->b ...
        # Satır: 0->8, 1->7 ...
        file_idx = col
        rank_idx = 7 - row
    else:
        # Siyah perspektifi (h1 sol üst gibi düşünülürse - ama genelde svg ters basar)
        # python-chess svg'sinde "flipped" parametresi kullanılırsa:
        # Sol üst h1 olur.
        file_idx = 7 - col
        rank_idx = row

    # Sınır kontrolü
    if 0 <= file_idx <= 7 and 0 <= rank_idx <= 7:
        return chess.square_name(chess.square(file_idx, rank_idx))
    return None

# --- STATE YÖNETİMİ ---
if 'fen' not in st.session_state:
    st.session_state.fen = None
if 'selected_square' not in st.session_state:
    st.session_state.selected_square = None
if 'last_move_uci' not in st.session_state:
    st.session_state.last_move_uci = None

# Puzzle Yükleme
if not st.session_state.fen:
    with st.spinner("Mat aranıyor..."):
        fen, sols = generate_puzzle()
        if fen:
            st.session_state.fen = fen
            st.session_state.solutions = sols
            st.session_state.selected_square = None
            st.rerun()
        else:
            st.error("Bulunamadı.")

# --- OYUN ALANI ---

board = chess.variant.AtomicBoard(st.session_state.fen)
is_white = (board.turn == chess.WHITE)

# Bilgi Çubuğu
turn_str = "BEYAZ" if is_white else "SİYAH"
st.info(f"Sıra: **{turn_str}**. Hedef: 1 Hamlede Mat!")

# --- SVG OLUŞTURMA ---
# Seçili kareyi boyamak için
arrows = []
fill = {}

if st.session_state.selected_square:
    sq = chess.parse_square(st.session_state.selected_square)
    # Seçili kareyi sarı yap (RGBA formatı)
    fill[sq] = "#ffe066cc" 
    
    # Olası hamleleri nokta ile göster (İsteğe bağlı, mobilde karmaşık olabilir diye kapalı)
    # Ama seçili taştan gidilebilecek yerleri hesaplayabiliriz.

# SVG verisini al
svg_board = chess.svg.board(
    board,
    size=350,
    flipped=not is_white, # Sırası gelen aşağıda olsun
    fill=fill,
    coordinates=False # Telefondaki karmaşayı azaltmak için
)

# SVG'yi Base64'e çevir (Dokunmatik kütüphanesi için)
b64 = base64.b64encode(svg_board.encode('utf-8')).decode("utf-8")

# --- DOKUNMATİK ALAN ---
# Bu bileşen resmi basar ve tıklamayı dinler
width = 350
value = streamlit_image_coordinates(
    f"data:image/svg+xml;base64,{b64}",
    width=width,
    key="board_click"
)

# --- TIKLAMA MANTIĞI ---
if value:
    x = value['x']
    y = value['y']
    
    clicked_sq = get_square_from_coords(x, y, width, is_white)
    
    if clicked_sq:
        # Durum 1: Henüz bir şey seçilmemiş -> Seç
        if st.session_state.selected_square is None:
            # Sadece kendi taşını seçebilir
            piece = board.piece_at(chess.parse_square(clicked_sq))
            if piece and piece.color == board.turn:
                st.session_state.selected_square = clicked_sq
                st.rerun()
        
        # Durum 2: Zaten seçili -> Hamle Yap veya Seçimi Değiştir
        else:
            source = st.session_state.selected_square
            target = clicked_sq
            
            # Aynı taşa tıkladıysa seçimi iptal et
            if source == target:
                st.session_state.selected_square = None
                st.rerun()
            
            # Kendi taşının üstüne tıkladıysa seçimi değiştir
            piece = board.piece_at(chess.parse_square(target))
            if piece and piece.color == board.turn:
                st.session_state.selected_square = target
                st.rerun()
            else:
                # Hamle dene
                # Vezir çıkma varsayımı (Atomic'te genelde vezir gerekir)
                move_uci = f"{source}{target}"
                
                # Piyon promosyonu mu?
                p_source = board.piece_at(chess.parse_square(source))
                if p_source and p_source.piece_type == chess.PAWN:
                    if (source[1]=='7' and target[1]=='8') or (source[1]=='2' and target[1]=='1'):
                        move_uci += 'q'
                
                # Hamle Kontrolü
                if move_uci in st.session_state.solutions:
                    st.toast("🔥 HARİKA! DOĞRU!", icon="✅")
                    time.sleep(1)
                    st.session_state.fen = None # Yeni puzzle için sıfırla
                    st.session_state.selected_square = None
                    st.rerun()
                else:
                    # Yasal ama yanlış mı?
                    try:
                        m = chess.Move.from_uci(move_uci)
                        if m in board.legal_moves:
                            st.toast("Yasal ama mat etmiyor.", icon="⚠️")
                            st.session_state.selected_square = None
                            st.rerun()
                        else:
                            st.toast("Geçersiz hamle.", icon="🚫")
                            st.session_state.selected_square = None
                            st.rerun()
                    except:
                        st.session_state.selected_square = None
                        st.rerun()

# --- ALT BUTONLAR ---
col1, col2 = st.columns(2)
with col1:
    if st.button("Pas Geç"):
        st.session_state.fen = None
        st.session_state.selected_square = None
        st.rerun()
with col2:
    if st.button("Çözümü Gör"):
        st.warning(f"Cevap: {', '.join(st.session_state.solutions)}")

import time
            
