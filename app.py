import streamlit as st
import chess
import chess.variant
import random
import time
from streamlit_chessboard import chessboard

# --- SAYFA AYARLARI (MOBİL ODAKLI) ---
st.set_page_config(page_title="Atomic Dojo", page_icon="⚛️", layout="centered")

# Mobil görünümü iyileştiren CSS (Gereksiz boşlukları siler, butonları büyütür)
st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem; max-width: 100%;}
    .stButton>button {
        width: 100%; 
        border-radius: 12px; 
        height: 3.5em; 
        font-weight: bold; 
        background-color: #f0f2f6;
    }
    h1 {text-align: center; font-size: 1.8rem; margin-bottom: 0.5rem;}
    .element-container {margin-bottom: 0.5rem;}
    </style>
    """, unsafe_allow_html=True)

st.title("⚛️ Atomic Dojo")

# --- MANTIK FONKSİYONLARI ---

def generate_puzzle():
    """
    Rastgele maç simüle edip 'Mate-in-1' (1 hamlede mat) pozisyonu arar.
    Patlamalı veya patlamasız tüm matları kabul eder.
    """
    attempts = 0
    while attempts < 1000:
        board = chess.variant.AtomicBoard()
        # Oyun ortası/sonu pozisyonları için rastgele hamle sayısı
        moves_count = random.randint(10, 60)
        
        try:
            # Rastgele maç oynat
            for _ in range(moves_count):
                if board.is_game_over(): break
                legal_moves = list(board.legal_moves)
                if not legal_moves: break
                board.push(random.choice(legal_moves))
            
            if board.is_game_over(): 
                attempts += 1
                continue

            # Şu anki pozisyonda mat eden hamleleri bul
            winning_moves = []
            for move in board.legal_moves:
                board.push(move)
                if board.is_checkmate():
                    winning_moves.append(move.uci())
                board.pop()
            
            # Eğer en az 1 tane mat eden hamle varsa bunu soru olarak döndür
            if winning_moves:
                return board.fen(), winning_moves
                
        except:
            pass
        attempts += 1
    return None, None

def load_new_puzzle():
    """Yeni puzzle üretir ve session state'e kaydeder"""
    with st.spinner("Yeni rakip aranıyor..."):
        fen, solutions = generate_puzzle()
        if fen:
            st.session_state.fen = fen
            st.session_state.solutions = solutions
            st.session_state.show_solution = False
            # Sayfayı yenilemeye gerek yok, state değişince otomatik çizilir
        else:
            st.error("Puzzle bulunamadı, tekrar dene.")

# --- STATE YÖNETİMİ ---
if 'fen' not in st.session_state:
    load_new_puzzle() # İlk açılışta puzzle yükle
if 'solutions' not in st.session_state:
    st.session_state.solutions = []
if 'show_solution' not in st.session_state:
    st.session_state.show_solution = False

# --- ARAYÜZ VE OYUN ALANI ---

if st.session_state.fen:
    board = chess.variant.AtomicBoard(st.session_state.fen)
    
    # Bilgilendirme Çubuğu
    turn_text = "Sıra: BEYAZ" if board.turn == chess.WHITE else "Sıra: SİYAH"
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info(f"🎯 **{turn_text}** (1 Hamlede Mat Et)")
    with col2:
        if st.button("Pas Geç ⏩"):
            load_new_puzzle()
            st.rerun()

    # --- TAHTA (INTERAKTİF) ---
    # Not: streamlit-chessboard kütüphanesi 'highlight' özelliğini tarayıcı tarafında 
    # yönetir. Tıklayıp sürükleyebilir veya tıklayıp-tıklayarak (click-click) oynayabilirsin.
    move_data = chessboard(
        search=False,
        fen=st.session_state.fen,
        board_width=350, # Mobilde ideal genişlik
        key=st.session_state.fen # Fen değiştikçe tahtayı sıfırlar
    )

    # --- HAMLE KONTROLÜ ---
    if move_data:
        # Kütüphaneden gelen veri: {'source': 'e2', 'target': 'e4', ...}
        try:
            src = move_data['source']
            tgt = move_data['target']
            
            # Piyon terfisi (Promotion) kontrolü
            # Atomic'te genelde vezir çıkılır, otomatik vezir (q) ekliyoruz.
            uci_move = f"{src}{tgt}"
            piece = board.piece_at(chess.parse_square(src))
            
            if piece and piece.piece_type == chess.PAWN:
                # Beyaz 7->8 veya Siyah 2->1 gidiyorsa
                if (src[1]=='7' and tgt[1]=='8') or (src[1]=='2' and tgt[1]=='1'):
                    uci_move += 'q'

            # Hamle Kontrolü
            if uci_move in st.session_state.solutions:
                # DOĞRU HAMLE!
                st.toast("🔥 HARİKA! Doğru Hamle.", icon="✅")
                time.sleep(0.5) # Kullanıcı kısa bir süre görsün
                load_new_puzzle() # Hemen yenisine geç
                st.rerun()
            else:
                # YANLIŞ HAMLE
                # Yasal mı diye bak
                move_obj = chess.Move.from_uci(uci_move)
                if move_obj in board.legal_moves:
                    st.toast("Hamle yasal ama MAT değil. Tekrar dene.", icon="❌")
                else:
                    # Bazen boş yere tıklanınca hata vermesin
                    pass
        except:
            pass

    # --- ALT BUTONLAR ---
    if st.button("🏳️ Çözümü Göster"):
        st.session_state.show_solution = True

    if st.session_state.show_solution:
        st.warning(f"💡 Çözüm Hamleleri: {', '.join(st.session_state.solutions)}")
        if st.button("Tamam, yenisine geç"):
            load_new_puzzle()
            st.rerun()

else:
    st.write("Yükleniyor...")

