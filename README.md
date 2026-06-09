# Otomata FSM Chatbot

Project ini adalah chatbot berbasis **Finite State Machine (FSM)**. Bot bekerja seperti CS bot: user bisa mengetik bebas, bot mengklasifikasi topik ke menu/group yang relevan, lalu user menavigasi state lewat tombol.

Domain contoh yang dipakai saat ini adalah pendampingan pertanian padi/sawah, termasuk obat pertanian, analisa gejala, budidaya, air sawah, gulma, hama, dan panen.

Tersedia **dua frontend** yang berbagi core logic yang sama (`app/`):

- **UI Streamlit** (`frontend.py`) - multipage: Home, Chat, Atur Bot.
- **UI editorial** (`api_server.py` + `webui/`) - backend FastAPI + HTML/CSS/JS murni, gaya cream/beige minimalis.

Core FSM di `app/` tidak bergantung pada framework UI apa pun, sehingga kedua frontend memanggil fungsi yang sama tanpa duplikasi logika.

## Objective

Tujuan project:

- Menerapkan konsep otomata/FSM dalam bentuk chatbot interaktif.
- Membuat state, event, transition, output, dan final state terlihat jelas.
- Menyediakan dashboard admin untuk mengatur state tree tanpa mengedit kode.
- Menampilkan flow log proses bot agar alur keputusan bot mudah dipahami.
- Menyediakan stress test untuk berbagai kemungkinan input production-like.
- Memisahkan core logic dari UI agar bisa dipakai oleh banyak frontend (Streamlit dan web HTML/CSS/JS).

## Konsep FSM

Dalam project ini:

```text
State       = node/group di data/bot_tree.json
Transition  = children dari sebuah node
Event/Input = FREE_TEXT, SELECT_NODE, BACK, RESET
Output      = menu button atau answer final
Final State = node tanpa children dan punya answer
```

Event utama:

```text
FREE_TEXT
  User mengetik bebas.
  Bot masuk GLOBAL_ROUTER dan mencari Top 3 state/group paling relevan.

SELECT_NODE
  User memilih button.
  Bot validasi transition lalu pindah ke state tujuan.

BACK
  Bot kembali ke state sebelumnya dari state_history.

RESET
  Bot mengosongkan current state dan history.
```

## Fitur Utama

- Dua frontend: UI Streamlit dan UI editorial (FastAPI + HTML/CSS/JS).
- FSM formal dengan `current_node_id`, `state_history`, `state_type`, dan `breadcrumb`.
- Global router untuk mengklasifikasi free text ke group yang relevan.
- Button navigation untuk masuk ke state/sub-state.
- Transition validation: state menu hanya boleh pindah ke children-nya.
- Back dan Reset.
- Flow log per trigger; di UI editorial bisa disembunyikan/ditampilkan lewat tombol.
- Area chat scrollable dengan input yang selalu terlihat.
- Admin dashboard dengan tree explorer visual, terproteksi password.
- Tambah group menggunakan dropdown parent.
- Pilihan jenis group: `Menu / punya turunan` atau `Jawaban final`.
- Data bot disimpan di JSON: `data/bot_tree.json`.
- Proteksi loop children, missing child, disabled node, duplicate id, dan corrupt JSON.
- 56 unit/stress tests.

## Struktur Project

```text
app/                      Core logic FSM (bebas framework UI)
  fsm_engine.py             FSM formal: event handling, current state, history,
                            transition validation, breadcrumb, edge export.
  chat_engine.py            Classifier global, scoring keyword, build menu response,
                            resolve node selection.
  tree_store.py             Load/save/normalisasi tree JSON, parent dropdown, auto attach child.
  flow_logger.py            Trace proses bot per trigger.
  text.py                   Normalisasi teks dan slug id.

frontend.py               UI Streamlit - Home (landing).
pages/
  1_Chat.py                 Page chat Streamlit.
  2_Atur_Bot.py             Page admin Streamlit (terproteksi password).
views/
  chat_page.py              Render chat Streamlit.
  admin_page.py             Render admin + password gate Streamlit.
  theme.py                  Tema/CSS editorial untuk Streamlit.

api_server.py             UI editorial - backend FastAPI, membungkus app/ jadi JSON API.
webui/
  index.html                Home editorial.
  chat.html                 Chat editorial (scrollable + toggle flow log).
  admin.html                Admin editorial.
  static/                   style.css, home.js, chat.js, admin.js.

data/bot_tree.json        Data state, transition, dan output bot.
tests/test_chat_engine.py Unit test dan stress test production-style.
```

## Struktur Data FSM

Contoh node/state:

```json
{
  "id": "obat_pertanian",
  "title": "Obat Pertanian",
  "description": "Bantuan memilih, memahami, dan memakai obat pertanian.",
  "keywords": ["obat", "pestisida", "fungisida"],
  "children": ["analisa_gejala_obat", "belajar_jenis_obat"],
  "answer": "",
  "enabled": true
}
```

Arti field:

- `id`: identitas state.
- `title`: label tombol.
- `description`: keterangan pilihan untuk user.
- `keywords`: kata pemicu classifier global.
- `children`: daftar state tujuan.
- `answer`: output final.
- `enabled`: jika `false`, state tidak dapat dipilih/disarankan.

## Flow Logging

Panel kiri di tab Chat menampilkan alur proses bot untuk trigger terakhir saja.

Contoh:

```text
Trigger: FREE_TEXT
Input: saya mau beli obat

1. handle_free_text
2. normalize_text
3. count_keyword_matches
4. score_node
5. suggest_groups
6. build_group_reply

Response:
Menampilkan 1 button pilihan.
```

Log tidak menumpuk. Setiap trigger baru mengganti log sebelumnya.

## Admin Dashboard

Tab `Atur Bot` dipakai untuk mengatur FSM tree.

Cara berpikir:

```text
Group = State
Children = Transition
Answer = Final State Output
Keywords = Global Router Classifier
```

Cara tambah group:

```text
1. Pilih parent di field "Letakkan di".
2. Pilih jenis group:
   - Menu / punya turunan
   - Jawaban final
3. Isi Judul button, Description, dan Keywords.
4. Jika final, isi Answer final.
5. Klik Tambah group.
```

Sistem otomatis menghubungkan group baru ke parent yang dipilih.

## Menjalankan Lokal

Install dependency dulu:

```bash
pip install -r requirements.txt
```

### UI Streamlit

```bash
streamlit run frontend.py
```

Atau dengan virtualenv project:

```bash
venv/bin/python -m streamlit run frontend.py
```

### UI editorial (FastAPI + HTML/CSS/JS)

```bash
uvicorn api_server:app --port 8000
```

Atau dengan virtualenv project:

```bash
venv/bin/python -m uvicorn api_server:app --port 8000
```

Lalu buka `http://localhost:8000`. Halaman: `/` (Home), `/chat`, `/admin`.

### Password admin

Kedua UI memproteksi halaman admin dengan password. Default `admin`.

- UI Streamlit: set lewat `.streamlit/secrets.toml` -> `admin_password = "..."`.
- UI editorial: set lewat environment variable `ADMIN_PASSWORD`.

```bash
ADMIN_PASSWORD=rahasia venv/bin/python -m uvicorn api_server:app --port 8000
```

## Testing

```bash
python -m pytest -q
```

Atau:

```bash
venv/bin/python -m pytest -q
```

Test suite mencakup:

- normalisasi input
- classifier exact/loose keyword
- random/empty input
- disabled node
- invalid transition
- loop protection
- shared child
- corrupt JSON fallback
- FSM state/history/back/reset
- flow logging trace
- admin tree key uniqueness

## Deploy ke Streamlit Community Cloud

1. Push repo ini ke GitHub.
2. Buka `https://share.streamlit.io` atau Streamlit Community Cloud.
3. Pilih repository:

```text
nabilulilalbab/otomatafsm
```

4. Set main file:

```text
frontend.py
```

5. Deploy.

Streamlit akan membaca `requirements.txt` otomatis.

## Status

FSM sudah formal:

- State: ada
- Transition: ada
- Event: ada
- Output: ada
- Current state: ada
- History/back: ada
- Flow logging: ada
- Admin editor: ada
- Stress test: ada
- Dua frontend (Streamlit + FastAPI/web): ada
